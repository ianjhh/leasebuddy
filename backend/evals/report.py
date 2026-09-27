"""
Assembles every eval result file into one evidence report.

Run:  python -m evals.report
Out:  results/METRICS.md
"""

import json
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RESULTS = BASE / "results"
DATA = BASE / "tests" / "evaluation" / "data"


def load(name: str):
    path = RESULTS / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def pct(num: int, den: int) -> str:
    return f"{100 * num / den:.1f}% ({num}/{den})" if den else "n/a"


def generation_section(rows: list[dict], title: str) -> list[str]:
    answerable = [r for r in rows if r["category"] != "unanswerable"]
    unanswerable = [r for r in rows if r["category"] == "unanswerable"]
    cited = [r for r in answerable if r["citation_correct"] is not None]
    judged = [r for r in rows if "judge_faithful" in r]

    out = [f"### {title}", "", f"{len(rows)} questions.", "",
           "| Metric | Value |", "|---|---|"]
    out.append(f"| Exact answer accuracy (answerable) | **{pct(sum(r['correct'] for r in answerable), len(answerable))}** |")
    out.append(f"| Refusal accuracy (unanswerable) | **{pct(sum(r['correct'] for r in unanswerable), len(unanswerable))}** |")
    out.append(f"| False refusal rate (answerable) | {pct(sum(r['false_refusal'] for r in answerable), len(answerable))} |")
    out.append(f"| Citation page accuracy | **{pct(sum(bool(r['citation_correct']) for r in cited), len(cited))}** |")
    if judged:
        out.append(f"| LLM-judge faithfulness | {pct(int(sum(r['judge_faithful'] for r in judged)), len(judged))} |")
        out.append(f"| LLM-judge relevancy | {pct(int(sum(r['judge_relevant'] for r in judged)), len(judged))} |")

    latencies = sorted(r["latency_s"] for r in rows if r.get("latency_s"))
    if latencies:
        out.append(f"| Latency median / p95 | {latencies[len(latencies)//2]:.1f}s / "
                   f"{latencies[int(len(latencies)*0.95)-1]:.1f}s |")

    out += ["", "By category:", "", "| Category | Accuracy |", "|---|---|"]
    for cat in sorted({r["category"] for r in rows}):
        sub = [r for r in rows if r["category"] == cat]
        out.append(f"| {cat} | {pct(sum(r['correct'] for r in sub), len(sub))} |")

    retries = [r["retry_count"] for r in rows if r.get("retry_count", -1) >= 0]
    if retries and max(retries) > 0:
        out += ["", "Retrieval passes actually taken by the agent:", "",
                "| Passes | Questions |", "|---|---|"]
        for value in sorted(set(retries)):
            out.append(f"| {value} | {retries.count(value)} |")
    out.append("")
    return out


def retrieval_section(rows: list[dict]) -> list[str]:
    methods = ["hybrid_rrf", "vector_only", "keyword_only"]
    total = len(rows)
    out = ["### Retrieval quality (deterministic gold-clause matching)", "",
           f"{total} answerable questions, top-5 retrieval, identical queries across all three arms.",
           "", "| Method | recall@1 | recall@3 | recall@5 | page@5 | MRR | p50 latency |",
           "|---|---|---|---|---|---|---|"]
    for name in methods:
        ranks = [r[name]["rank"] for r in rows if r[name]["rank"]]
        mrr = sum(1 / r for r in ranks) / total if total else 0
        lat = sorted(r[name]["latency_ms"] for r in rows)
        cells = [pct(sum(bool(r[name][k]) for r in rows), total)
                 for k in ("hit@1", "hit@3", "hit@5", "page_hit@5")]
        label = f"**{name}**" if name == "hybrid_rrf" else name
        out.append(f"| {label} | {cells[0]} | {cells[1]} | {cells[2]} | {cells[3]} | "
                   f"{mrr:.3f} | {lat[len(lat)//2]:.0f} ms |")

    out += ["", "recall@5 by category:", "",
            "| Category | " + " | ".join(methods) + " |",
            "|---|" + "---|" * len(methods)]
    for cat in sorted({r["category"] for r in rows}):
        sub = [r for r in rows if r["category"] == cat]
        cells = [pct(sum(bool(r[m]["hit@5"]) for r in sub), len(sub)) for m in methods]
        out.append(f"| {cat} | " + " | ".join(cells) + " |")
    out.append("")
    return out


def infra_section(rows: list[dict]) -> list[str]:
    out = ["### Infrastructure claims", "", "| Check | Claim | Observed | Result |", "|---|---|---|---|"]
    for r in rows:
        mark = {True: "PASS", False: "**FAIL**", None: "skipped"}[r["passed"]]
        observed = str(r["observed"]).replace("|", "\\|")
        if len(observed) > 130:
            observed = observed[:127] + "..."
        out.append(f"| {r['check']} | {r['claim']} | `{observed}` | {mark} |")
    out.append("")
    return out


def main() -> None:
    corpus = json.loads((DATA / "corpus.json").read_text(encoding="utf-8"))
    dataset = json.loads((DATA / "golden_qa_large.json").read_text(encoding="utf-8"))

    pages = sum(len(c["pages"]) for c in corpus)
    words = sum(len(p["text"].split()) for c in corpus for p in c["pages"])
    by_cat: dict[str, int] = {}
    for item in dataset:
        by_cat[item["category"]] = by_cat.get(item["category"], 0) + 1

    lines = [
        "# LeaseBuddy — measured metrics",
        "",
        f"Generated {date.today().isoformat()}. Every number below comes from a run in this "
        "repository; nothing is estimated.",
        "",
        "## Dataset",
        "",
        f"- **{len(corpus)} synthetic leases**, {pages} pages, {words:,} words "
        "(`evals/build_dataset.py`, fixed seed)",
        f"- **{len(dataset)} questions** with recorded ground truth, gold page(s) and gold clause(s)",
        "",
        "| Category | Count | What it tests |",
        "|---|---|---|",
        f"| lookup | {by_cat.get('lookup', 0)} | a single clause answers it |",
        f"| multi_hop | {by_cat.get('multi_hop', 0)} | needs two clauses combined, usually with arithmetic |",
        f"| adversarial | {by_cat.get('adversarial', 0)} | a confusable clause sits nearby (pet rent vs pet deposit, late fee vs NSF fee) |",
        f"| unanswerable | {by_cat.get('unanswerable', 0)} | the lease does not contain the answer; refusing is correct |",
        "",
        "Each lease also carries two distractor pages (a fee schedule and a maintenance "
        "addendum) that repeat similar dollar amounts in a non-authoritative context.",
        "",
    ]

    oracle = load("gen_oracle_full.json")
    e2e = load("gen_e2e.json")
    retrieval = load("retrieval.json")
    infra = load("infra.json")

    lines += ["## Results", ""]
    if retrieval:
        lines += retrieval_section(retrieval)
    if e2e:
        lines += generation_section(e2e, "End-to-end generation (real retrieval + LangGraph agent)")
    if oracle:
        lines += generation_section(oracle, "Generation with gold context (retrieval isolated out)")
    if infra:
        lines += infra_section(infra)

    missing = [n for n, v in [("retrieval", retrieval), ("end-to-end generation", e2e),
                              ("infrastructure", infra)] if v is None]
    if missing:
        lines += ["> Not yet run: " + ", ".join(missing) +
                  " (these need Postgres and Redis up).", ""]

    out = RESULTS / "METRICS.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
