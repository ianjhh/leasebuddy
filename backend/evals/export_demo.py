"""
Exports recorded agent answers for the frontend's static demo mode.

The hosted demo can't run Ollama, so it plays back answers the real agent gave
during the end-to-end evaluation. Only the answers are replayed; nothing is
rewritten. It keeps the questions the agent got right with the correct page
cited, plus its refusals on unanswerable questions.

Run:  python -m evals.export_demo
In:   results/gen_e2e.json, tests/evaluation/data/corpus.json
Out:  ../frontend/src/lib/demo-data.json
"""

import json
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
RESULTS = BACKEND_DIR / "results" / "gen_e2e.json"
CORPUS = BACKEND_DIR / "tests" / "evaluation" / "data" / "corpus.json"
OUT = BACKEND_DIR.parent / "frontend" / "src" / "lib" / "demo-data.json"

LEASE_INDEX = 0

# Shown as one-click chips, one per question type.
SUGGESTED = [
    "What is the monthly base rent?",
    "What is the monthly pet rent, as opposed to the pet deposit?",
    "How much is the returned check fee, not the late fee?",
    "If I stay past the expiration date without consent, what is the monthly rent?",
    "Do I have to pay a pet deposit for a service animal?",
    "Does the building have a swimming pool or fitness center?",
]


def keep(item: dict) -> bool:
    if item["lease_index"] != LEASE_INDEX or not item["correct"]:
        return False
    if item["category"] == "unanswerable":
        return item["refused"]
    return bool(item["citation_correct"])


def main() -> None:
    results = json.loads(RESULTS.read_text(encoding="utf-8"))
    lease = json.loads(CORPUS.read_text(encoding="utf-8"))[LEASE_INDEX]

    answers = []
    for item in filter(keep, results):
        citations = [
            {
                "chunkId": f"page-{page}-{i}",
                "pageNumber": page,
                "sectionTitle": f"Section {item['gold_section']}",
                "snippet": clause,
            }
            for i, (page, clause) in enumerate(zip(item["gold_pages"], item["gold_clauses"]))
        ]
        answers.append({
            "question": item["question"],
            "category": item["category"],
            "answer": item["answer"],
            "citations": citations,
            "latencySeconds": item["latency_s"],
            "retrievalPasses": item["retry_count"],
        })

    known = {a["question"] for a in answers}
    missing = [q for q in SUGGESTED if q not in known]
    if missing:
        raise SystemExit(f"Suggested questions without a kept answer: {missing}")

    unit = lease["facts"]["unit"]
    data = {
        "lease": {
            "id": "sample-lease",
            "filename": f"Residential Lease - {unit}.pdf",
            "status": "completed",
            "pageCount": len(lease["pages"]),
            "createdAt": "2026-09-06T00:00:00Z",
        },
        "suggested": SUGGESTED,
        "answers": answers,
    }
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(answers)} recorded answers to {OUT}")


if __name__ == "__main__":
    main()
