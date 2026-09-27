"""
Retrieval eval: production hybrid RRF vs vector-only vs keyword-only.

Fully deterministic - no LLM generates or grades anything here. A question is a
hit when the chunks actually returned contain every gold clause it needs. The
hybrid arm calls app.rag.retriever.hybrid_search unmodified, so the numbers
describe the shipped query, not a reimplementation.

Run:  python -m evals.run_retrieval_eval --out results/retrieval.json
"""

import argparse
import asyncio
import json
import re
import time
from pathlib import Path

from sqlalchemy import text

from app.db.session import AsyncSessionLocal, engine
from app.rag import embedding_model
from app.rag.retriever import hybrid_search

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "tests" / "evaluation" / "data"

CLAUSE_PREFIX_CHARS = 80


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


async def vector_only(db, lease_id: str, query: str, limit: int = 5) -> list[dict]:
    vector = await embedding_model.aget_text_embedding(query)
    vector_str = "[" + ",".join(str(x) for x in vector) + "]"
    rows = await db.execute(text("""
        SELECT lc.id, lc.text_content,
               (lc.chunk_metadata->>'page_number')::int AS page_number
        FROM lease_chunks lc
        WHERE lc.document_id = CAST(:lease_id AS uuid)
        ORDER BY lc.embedding <=> CAST(:query_embedding AS vector)
        LIMIT :limit
    """), {"query_embedding": vector_str, "lease_id": lease_id, "limit": limit})
    return [{"text": r.text_content, "page": r.page_number} for r in rows.fetchall()]


async def keyword_only(db, lease_id: str, query: str, limit: int = 5) -> list[dict]:
    rows = await db.execute(text("""
        SELECT lc.id, lc.text_content,
               (lc.chunk_metadata->>'page_number')::int AS page_number,
               ts_rank(to_tsvector('english', lc.text_content),
                       plainto_tsquery('english', :q)) AS rank
        FROM lease_chunks lc
        WHERE lc.document_id = CAST(:lease_id AS uuid)
          AND to_tsvector('english', lc.text_content) @@ plainto_tsquery('english', :q)
        ORDER BY rank DESC
        LIMIT :limit
    """), {"q": query, "lease_id": lease_id, "limit": limit})
    return [{"text": r.text_content, "page": r.page_number} for r in rows.fetchall()]


async def hybrid(db, lease_id: str, query: str, limit: int = 5) -> list[dict]:
    chunks = await hybrid_search(db, lease_id, query, limit=limit)
    return [{"text": c["text"], "page": c["page"]} for c in chunks]


def clause_hit(chunks: list[dict], gold_clauses: list[str], k: int) -> bool:
    """True when the top-k chunks jointly contain every gold clause."""
    blob = normalize(" ".join(c["text"] for c in chunks[:k]))
    return all(normalize(g)[:CLAUSE_PREFIX_CHARS] in blob for g in gold_clauses)


def page_hit(chunks: list[dict], gold_pages: list[int], k: int) -> bool:
    got = {c["page"] for c in chunks[:k]}
    return all(p in got for p in gold_pages)


def first_hit_rank(chunks: list[dict], gold_clauses: list[str]) -> int | None:
    """1-based rank of the first chunk containing any gold clause."""
    for i, chunk in enumerate(chunks, start=1):
        blob = normalize(chunk["text"])
        if any(normalize(g)[:CLAUSE_PREFIX_CHARS] in blob for g in gold_clauses):
            return i
    return None


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5, help="top-k to retrieve")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    dataset = json.loads((DATA / "golden_qa_large.json").read_text(encoding="utf-8"))
    lease_ids = json.loads((DATA / "ingested_lease_ids.json").read_text(encoding="utf-8"))

    # Unanswerable questions have no gold clause, so they are not retrieval targets.
    items = [d for d in dataset if d["gold_clauses"]]
    print(f"Scoring {len(items)} answerable questions, top-{args.limit}, 3 retrieval methods")

    methods = {"hybrid_rrf": hybrid, "vector_only": vector_only, "keyword_only": keyword_only}
    records: list[dict] = []

    async with AsyncSessionLocal() as db:
        for n, item in enumerate(items, start=1):
            lease_id = lease_ids[str(item["lease_index"])]
            row = {
                "question": item["question"],
                "category": item["category"],
                "gold_pages": item["gold_pages"],
            }
            for name, fn in methods.items():
                started = time.perf_counter()
                try:
                    chunks = await fn(db, lease_id, item["question"], args.limit)
                    err = None
                except Exception as exc:
                    chunks, err = [], f"{type(exc).__name__}: {exc}"
                row[name] = {
                    "hit@1": clause_hit(chunks, item["gold_clauses"], 1),
                    "hit@3": clause_hit(chunks, item["gold_clauses"], 3),
                    "hit@5": clause_hit(chunks, item["gold_clauses"], args.limit),
                    "page_hit@5": page_hit(chunks, item["gold_pages"], args.limit),
                    "rank": first_hit_rank(chunks, item["gold_clauses"]),
                    "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                    "returned": len(chunks),
                    "error": err,
                }
            records.append(row)
            if n % 25 == 0 or n == len(items):
                print(f"  {n}/{len(items)}", flush=True)

    out_path = Path(args.out) if args.out else BASE / "results" / "retrieval.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"\nWrote {len(records)} records to {out_path}")
    summarize(records, list(methods))

    await engine.dispose()


def summarize(records: list[dict], methods: list[str]) -> None:
    total = len(records)

    def pct(name: str, key: str, rows: list[dict]) -> str:
        n = sum(bool(r[name][key]) for r in rows)
        return f"{100 * n / len(rows):5.1f}%" if rows else "  n/a"

    print("\n" + "=" * 74)
    print("RETRIEVAL QUALITY  (deterministic gold-clause matching)")
    print("=" * 74)
    print(f"{'method':<14}{'recall@1':>10}{'recall@3':>10}{'recall@5':>10}"
          f"{'page@5':>10}{'MRR':>8}{'p50 ms':>9}")
    for name in methods:
        ranks = [r[name]["rank"] for r in records if r[name]["rank"]]
        mrr = sum(1 / r for r in ranks) / total if total else 0
        lat = sorted(r[name]["latency_ms"] for r in records)
        p50 = lat[len(lat) // 2] if lat else 0
        print(f"{name:<14}{pct(name,'hit@1',records):>10}{pct(name,'hit@3',records):>10}"
              f"{pct(name,'hit@5',records):>10}{pct(name,'page_hit@5',records):>10}"
              f"{mrr:>8.3f}{p50:>9.0f}")

    print("\nrecall@5 by question category:")
    cats = sorted({r["category"] for r in records})
    print(f"{'category':<14}" + "".join(f"{m:>14}" for m in methods))
    for cat in cats:
        rows = [r for r in records if r["category"] == cat]
        line = f"{cat:<14}"
        for name in methods:
            line += f"{pct(name,'hit@5',rows) + f' ({len(rows)})':>14}"
        print(line)

    errors = [r for r in records for m in methods if r[m]["error"]]
    if errors:
        print(f"\nErrors: {len(errors)}")


if __name__ == "__main__":
    asyncio.run(main())
