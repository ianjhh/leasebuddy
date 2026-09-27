"""
Generation quality eval over the large golden dataset.

Two modes:
  oracle - feed the gold clause pages straight into the production prompt.
           Isolates answer quality from retrieval. Needs Ollama only.
  e2e    - run the real LangGraph agent end to end against Postgres.
           Measures the system as deployed. Needs Ollama + Postgres.

Scoring is deterministic (exact ground-truth match, refusal handling, citation
page match). The LLM judge is optional and reported separately.

Run:  python -m evals.run_generation_eval --mode oracle --out results/gen_oracle.json
"""

import argparse
import asyncio
import json
import time
from pathlib import Path
from uuid import UUID, uuid4

import httpx

from app.config import settings
from evals import scoring

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "tests" / "evaluation" / "data"


def load_dataset() -> list[dict]:
    return json.loads((DATA / "golden_qa_large.json").read_text(encoding="utf-8"))


def load_corpus() -> list[dict]:
    return json.loads((DATA / "corpus.json").read_text(encoding="utf-8"))


def stratified(items: list[dict], per_category: int | None) -> list[dict]:
    if per_category is None:
        return items
    buckets: dict[str, list[dict]] = {}
    for item in items:
        buckets.setdefault(item["category"], []).append(item)
    out: list[dict] = []
    for cat in sorted(buckets):
        out.extend(buckets[cat][:per_category])
    return out


# --------------------------------------------------------------------------
# oracle mode
# --------------------------------------------------------------------------
def oracle_chunks(item: dict, corpus: list[dict]):
    """Build the retrieved-chunk list from the gold pages of the right lease."""
    from app.rag.agent import ChunkResult

    lease = corpus[item["lease_index"]]
    pages = {p["page_num"]: p["text"] for p in lease["pages"]}
    targets = item["gold_pages"] or [1]
    return [
        ChunkResult(id=str(uuid4()), text=pages[p], page=p, score=1.0)
        for p in targets
        if p in pages
    ]


async def run_oracle(item: dict, corpus: list[dict]) -> dict:
    from app.rag.agent import QAState, generate_answer

    state = QAState(
        lease_id=uuid4(),
        query=item["question"],
        retrieved_chunks=oracle_chunks(item, corpus),
    )
    started = time.perf_counter()
    final = await generate_answer(state)
    return {
        "answer": (final.answer or "").strip(),
        "latency_s": round(time.perf_counter() - started, 2),
        "retry_count": 0,
        "retrieved_pages": [c.page for c in state.retrieved_chunks],
    }


# --------------------------------------------------------------------------
# e2e mode
# --------------------------------------------------------------------------
async def run_e2e(item: dict, lease_ids: dict[int, str]) -> dict:
    from app.rag.agent import run_agent

    lease_id = UUID(lease_ids[str(item["lease_index"])])
    started = time.perf_counter()
    final = await run_agent(lease_id, item["question"])
    return {
        "answer": (final.answer or "").strip(),
        "latency_s": round(time.perf_counter() - started, 2),
        "retry_count": final.retry_count,
        "relevance_score": final.relevance_score,
        "retrieved_pages": [c.page for c in final.retrieved_chunks],
    }


# --------------------------------------------------------------------------
# optional LLM judge
# --------------------------------------------------------------------------
async def ollama(prompt: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json={"model": settings.LLM_MODEL, "prompt": prompt, "stream": False},
            timeout=180.0,
        )
        return response.json()["response"]


async def judge(item: dict, answer: str, context: str) -> dict:
    faith_prompt = (
        "Determine whether the ANSWER is fully supported by the CONTEXT, with no "
        "invented facts.\n\n"
        f"CONTEXT:\n{context}\n\nANSWER:\n{answer}\n\n"
        'Reply with only "1" if fully supported, or "0" if not.'
    )
    rel_prompt = (
        "Determine whether the ANSWER directly addresses the QUESTION.\n\n"
        f"QUESTION:\n{item['question']}\n\nANSWER:\n{answer}\n\n"
        'Reply with only "1" if it does, or "0" if it does not.'
    )
    faith, rel = await asyncio.gather(ollama(faith_prompt), ollama(rel_prompt))
    return {
        "judge_faithful": 1.0 if "1" in faith[:10] else 0.0,
        "judge_relevant": 1.0 if "1" in rel[:10] else 0.0,
    }


# --------------------------------------------------------------------------
async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["oracle", "e2e"], default="oracle")
    parser.add_argument("--per-category", type=int, default=None,
                        help="cap questions per category (default: all)")
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--judge", action="store_true", help="also run the LLM judge")
    parser.add_argument("--model", default=None,
                        help="override LLM_MODEL (must be set before the agent is imported)")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    if args.model:
        settings.LLM_MODEL = args.model

    dataset = stratified(load_dataset(), args.per_category)
    corpus = load_corpus()

    lease_ids: dict[int, str] = {}
    if args.mode == "e2e":
        ids_path = DATA / "ingested_lease_ids.json"
        if not ids_path.exists():
            raise SystemExit("Run `python -m evals.ingest_corpus` first (needs Postgres).")
        lease_ids = json.loads(ids_path.read_text(encoding="utf-8"))

    print(f"mode={args.mode}  questions={len(dataset)}  model={settings.LLM_MODEL}  "
          f"concurrency={args.concurrency}  judge={args.judge}")

    semaphore = asyncio.Semaphore(args.concurrency)
    done = 0
    results: list[dict] = []

    async def process(index: int, item: dict) -> dict:
        nonlocal done
        async with semaphore:
            try:
                run = await (run_oracle(item, corpus) if args.mode == "oracle"
                             else run_e2e(item, lease_ids))
            except Exception as exc:  # keep the sweep alive; record the failure
                run = {"answer": "", "latency_s": 0.0, "retry_count": -1,
                       "retrieved_pages": [], "error": f"{type(exc).__name__}: {exc}"}

            record = {**item, **run}
            record.update(scoring.score_item(item, run["answer"]))
            record["citation_correct"] = scoring.citation_correct(
                run["answer"], item["gold_pages"]
            )

            if args.judge and run["answer"]:
                lease = corpus[item["lease_index"]]
                pages = {p["page_num"]: p["text"] for p in lease["pages"]}
                context = "\n".join(pages[p] for p in run["retrieved_pages"] if p in pages)
                try:
                    record.update(await judge(item, run["answer"], context))
                except Exception:
                    pass

            done += 1
            if done % 10 == 0 or done == len(dataset):
                print(f"  {done}/{len(dataset)}", flush=True)
            return record

    results = await asyncio.gather(*(process(i, it) for i, it in enumerate(dataset)))

    out_path = Path(args.out) if args.out else BASE / "results" / f"gen_{args.mode}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote {len(results)} records to {out_path}")
    summarize(results)


def summarize(results: list[dict]) -> None:
    def pct(num: int, den: int) -> str:
        return f"{100 * num / den:5.1f}% ({num}/{den})" if den else "    n/a"

    answerable = [r for r in results if r["category"] != "unanswerable"]
    unanswerable = [r for r in results if r["category"] == "unanswerable"]
    cited = [r for r in answerable if r["citation_correct"] is not None]

    print("\n" + "=" * 62)
    print("DETERMINISTIC METRICS")
    print("=" * 62)
    print(f"Exact answer accuracy (answerable)  {pct(sum(r['correct'] for r in answerable), len(answerable))}")
    print(f"Refusal accuracy (unanswerable)     {pct(sum(r['correct'] for r in unanswerable), len(unanswerable))}")
    print(f"False refusal rate (answerable)     {pct(sum(r['false_refusal'] for r in answerable), len(answerable))}")
    print(f"Citation page accuracy              {pct(sum(bool(r['citation_correct']) for r in cited), len(cited))}")

    print("\nBy category:")
    for cat in sorted({r["category"] for r in results}):
        rows = [r for r in results if r["category"] == cat]
        print(f"  {cat:<14} {pct(sum(r['correct'] for r in rows), len(rows))}")

    judged = [r for r in results if "judge_faithful" in r]
    if judged:
        print("\nLLM-JUDGE METRICS (secondary)")
        print(f"  Faithfulness  {pct(int(sum(r['judge_faithful'] for r in judged)), len(judged))}")
        print(f"  Relevancy     {pct(int(sum(r['judge_relevant'] for r in judged)), len(judged))}")

    retries = [r["retry_count"] for r in results if r.get("retry_count", -1) >= 0]
    if retries and max(retries) > 0:
        print("\nAgent retrieval passes (retry_count):")
        for value in sorted(set(retries)):
            print(f"  {value} passes: {retries.count(value)}")

    latencies = sorted(r["latency_s"] for r in results if r.get("latency_s"))
    if latencies:
        mid = latencies[len(latencies) // 2]
        p95 = latencies[int(len(latencies) * 0.95) - 1]
        print(f"\nLatency  median {mid:.1f}s   p95 {p95:.1f}s")

    errors = [r for r in results if r.get("error")]
    if errors:
        print(f"\nErrors: {len(errors)} (e.g. {errors[0]['error'][:90]})")


if __name__ == "__main__":
    asyncio.run(main())
