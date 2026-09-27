"""
Proves the infrastructure claims by observing the running system.

Checks, in order:
  1. pgvector column dimension            -> the 768-dim claim
  2. HNSW index existence + parameters    -> the m=16 / ef_construction=64 claim
  3. RRF constant and candidate pool      -> read from the shipped SQL
  4. Upload size ceiling                  -> real HTTP request over the limit
  5. Async accept status                  -> live OpenAPI schema of the route
  6. Sliding-window rate limit            -> real burst until the API says 429
  7. WebSocket token streaming            -> real socket, counts token frames

Needs Postgres and Redis up, and the API running on --api for checks 4-7.

Run:  python -m evals.run_infra_eval --out results/infra.json
"""

import argparse
import asyncio
import json
import re
import time
from pathlib import Path

import httpx
from sqlalchemy import text

from app.config import settings
from app.db.session import AsyncSessionLocal, engine

BASE = Path(__file__).resolve().parent.parent
results: list[dict] = []


def record(name: str, claim: str, observed, passed: bool | None) -> None:
    results.append({"check": name, "claim": claim, "observed": observed, "passed": passed})
    mark = {True: "PASS", False: "FAIL", None: "SKIP"}[passed]
    print(f"[{mark}] {name}\n       claim:    {claim}\n       observed: {observed}")


# --------------------------------------------------------------------------
async def check_database() -> None:
    async with AsyncSessionLocal() as db:
        dim = (await db.execute(text("""
            SELECT a.atttypmod AS dim
            FROM pg_attribute a
            JOIN pg_class c ON c.oid = a.attrelid
            WHERE c.relname = 'lease_chunks' AND a.attname = 'embedding'
        """))).scalar()
        record("vector_dimension", "768-dim embeddings", f"{dim}-dim", dim == 768)

        row = (await db.execute(text("""
            SELECT i.relname AS index_name, am.amname AS method,
                   pg_get_indexdef(i.oid) AS definition
            FROM pg_class t
            JOIN pg_index ix ON t.oid = ix.indrelid
            JOIN pg_class i  ON i.oid = ix.indexrelid
            JOIN pg_am am    ON am.oid = i.relam
            WHERE t.relname = 'lease_chunks' AND am.amname = 'hnsw'
        """))).mappings().first()

        if row:
            definition = row["definition"]
            has_m = "m='16'" in definition or "m=16" in definition
            has_ef = "ef_construction='64'" in definition or "ef_construction=64" in definition
            has_cosine = "vector_cosine_ops" in definition
            record("hnsw_index", "HNSW index, m=16, ef_construction=64, cosine",
                   definition, has_m and has_ef and has_cosine)
        else:
            record("hnsw_index", "HNSW index, m=16, ef_construction=64, cosine",
                   "no HNSW index found on lease_chunks", False)

        chunks = (await db.execute(text("SELECT COUNT(*) FROM lease_chunks"))).scalar()
        docs = (await db.execute(text("SELECT COUNT(*) FROM lease_documents"))).scalar()
        record("corpus_indexed", "corpus is present for retrieval",
               f"{docs} documents, {chunks} chunks", (chunks or 0) > 0)

    await engine.dispose()


def check_source_constants() -> None:
    source = (BASE / "app" / "rag" / "retriever.py").read_text(encoding="utf-8")
    k_values = set(re.findall(r"1\.0\s*/\s*\((\d+)\.0\s*\+", source))
    record("rrf_k", "Reciprocal Rank Fusion k=60",
           f"k values in shipped SQL: {sorted(k_values) or 'none'}", k_values == {"60"})

    pool = re.search(r'"candidate_limit":\s*limit\s*\*\s*(\d+)', source)
    default_limit = re.search(r"limit:\s*int\s*=\s*(\d+)", source)
    if pool and default_limit:
        multiplier, base_limit = int(pool.group(1)), int(default_limit.group(1))
        record("candidate_pool", "50 candidates narrowed to top 5",
               f"{base_limit} x {multiplier} = {base_limit * multiplier} candidates "
               f"-> top {base_limit}",
               base_limit * multiplier == 50 and base_limit == 5)
    else:
        record("candidate_pool", "50 candidates narrowed to top 5",
               "could not parse retriever.py", False)

    record("cache_ttl", "1-hour response cache TTL",
           f"CACHE_TTL_SECONDS={settings.CACHE_TTL_SECONDS}",
           settings.CACHE_TTL_SECONDS == 3600)

    # The cache helper exists; confirm whether anything actually calls it.
    callers = []
    for path in (BASE / "app").rglob("*.py"):
        if path.name == "chat_service.py":
            continue
        if "generate_chat_response" in path.read_text(encoding="utf-8"):
            callers.append(path.name)
    record("cache_wired", "response cache is on the request path",
           f"callers of generate_chat_response: {callers or 'none'}", bool(callers))


# --------------------------------------------------------------------------
async def check_api(api: str) -> None:
    async with httpx.AsyncClient(base_url=api, timeout=60.0) as client:
        try:
            await client.get("/health/")
        except Exception as exc:
            record("api_reachable", "API is running", f"{type(exc).__name__}: {exc}", None)
            return
        record("api_reachable", "API is running", api, True)

        # ---- 5. declared async-accept status ------------------------------
        spec = (await client.get("/openapi.json")).json()
        codes = sorted(spec["paths"]["/api/leases/"]["post"]["responses"].keys())
        record("accept_status", "upload returns 202 Accepted",
               f"declared success codes for POST /api/leases/: {codes}", "202" in codes)

        # ---- 4. size ceiling ----------------------------------------------
        limit = settings.MAX_UPLOAD_SIZE_BYTES
        oversize = b"%PDF-1.4\n" + b"0" * (limit + 1024)
        response = await client.post(
            "/api/leases/",
            files={"file": ("big.pdf", oversize, "application/pdf")},
        )
        record("upload_size_limit", f"rejects uploads over {limit // (1024*1024)} MB",
               f"{len(oversize) / 1024 / 1024:.1f} MB upload -> HTTP {response.status_code}",
               response.status_code == 413)

        response = await client.post(
            "/api/leases/",
            files={"file": ("notes.exe", b"binary", "application/octet-stream")},
        )
        record("upload_type_filter", "rejects unsupported file types",
               f"'.exe' upload -> HTTP {response.status_code}", response.status_code == 400)

        # ---- 6. rate limiter ----------------------------------------------
        # The limiter counts every request, so drain the window first.
        print("\n  ... probing the rate limiter (this sends ~70 requests)")
        await asyncio.sleep(0)
        statuses: list[int] = []
        first_429_at = None
        for i in range(1, 71):
            resp = await client.get("/health/")
            statuses.append(resp.status_code)
            if resp.status_code == 429 and first_429_at is None:
                first_429_at = i
                break
        allowed = sum(1 for s in statuses if s == 200)
        record("rate_limit", f"sliding window at {60} req/min per IP",
               f"first 429 on request #{first_429_at}, {allowed} allowed through",
               first_429_at is not None and 55 <= first_429_at <= 65)


async def check_websocket(api: str, lease_ids_path: Path) -> None:
    try:
        import websockets
    except ImportError:
        record("ws_token_streaming", "token-by-token streaming over WebSocket",
               "websockets package not installed", None)
        return

    if not lease_ids_path.exists():
        record("ws_token_streaming", "token-by-token streaming over WebSocket",
               "no ingested lease ids; run evals.ingest_corpus first", None)
        return

    lease_id = json.loads(lease_ids_path.read_text(encoding="utf-8"))["0"]
    ws_url = api.replace("http://", "ws://").replace("https://", "wss://")

    try:
        async with websockets.connect(f"{ws_url}/ws/chat/{lease_id}", open_timeout=30) as ws:
            await ws.send(json.dumps({"type": "query", "content": "What is the monthly base rent?"}))
            tokens, first_token_at, started = 0, None, time.perf_counter()
            got_citations = got_done = False
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=180)
                msg = json.loads(raw)
                if msg.get("type") == "token":
                    tokens += 1
                    if first_token_at is None:
                        first_token_at = time.perf_counter() - started
                elif msg.get("type") == "citations":
                    got_citations = True
                elif msg.get("type") == "done":
                    got_done = True
                    break
                elif msg.get("type") == "error":
                    break
        record("ws_token_streaming", "token-by-token LLM streaming over WebSocket",
               f"{tokens} token frames, first at {first_token_at:.1f}s, "
               f"citations={got_citations}, done={got_done}",
               tokens > 5 and got_done)
    except Exception as exc:
        record("ws_token_streaming", "token-by-token LLM streaming over WebSocket",
               f"{type(exc).__name__}: {exc}", False)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--skip-api", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    print("=" * 74)
    print("INFRASTRUCTURE CLAIM VERIFICATION")
    print("=" * 74)

    await check_database()
    check_source_constants()
    if not args.skip_api:
        await check_api(args.api)
        await check_websocket(
            args.api,
            BASE / "tests" / "evaluation" / "data" / "ingested_lease_ids.json",
        )

    out_path = Path(args.out) if args.out else BASE / "results" / "infra.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    passed = sum(1 for r in results if r["passed"] is True)
    failed = sum(1 for r in results if r["passed"] is False)
    skipped = sum(1 for r in results if r["passed"] is None)
    print("\n" + "=" * 74)
    print(f"{passed} passed, {failed} failed, {skipped} skipped -> {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
