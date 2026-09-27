"""
Deterministic scoring helpers.

These decide correctness by string matching against recorded ground truth, with
no model in the loop, so the resulting numbers are reproducible and auditable.
"""

import re

REFUSAL_PATTERNS = [
    r"cannot find",
    r"can't find",
    r"not (?:stated|specified|mentioned|found|addressed|covered) in the lease",
    r"does not (?:state|specify|mention|address)",
    r"no information",
]


def is_money(key: str) -> bool:
    return key.strip().startswith("$")


def money_digits(key: str) -> str:
    """'$1,850.00' -> '1850'"""
    return re.sub(r"[^\d.]", "", key).split(".")[0]


def contains_money(answer: str, key: str) -> bool:
    value = money_digits(key)
    if not value:
        return False
    normalized = re.sub(r"[,$]", "", answer)
    return re.search(rf"(?<!\d){re.escape(value)}(?!\d)", normalized) is not None


def contains_text(answer: str, key: str) -> bool:
    return re.search(rf"\b{re.escape(key)}\b", answer, re.IGNORECASE) is not None


def matches_any_key(answer: str, keys: list[str]) -> bool:
    """answer_keys are ALTERNATIVES: any one of them counts as correct."""
    if not answer:
        return False
    for key in keys:
        if is_money(key):
            if contains_money(answer, key):
                return True
        elif contains_text(answer, key):
            return True
    return False


def is_refusal(answer: str) -> bool:
    if not answer:
        return False
    return any(re.search(p, answer, re.IGNORECASE) for p in REFUSAL_PATTERNS)


def score_item(item: dict, answer: str) -> dict:
    """
    Returns the deterministic verdicts for one answered question.

    unanswerable -> correct iff the model refuses
    answerable   -> correct iff a ground-truth key appears AND it did not refuse
    """
    refused = is_refusal(answer)
    unanswerable = item["category"] == "unanswerable"

    if unanswerable:
        correct = refused
        false_refusal = False
    else:
        correct = matches_any_key(answer, item["answer_keys"]) and not refused
        false_refusal = refused

    return {
        "correct": correct,
        "refused": refused,
        "false_refusal": false_refusal,
    }


def cited_pages(answer: str) -> list[int]:
    """Pull '(Page 4)' / '[Page 4]' style citations out of a generated answer."""
    return sorted({int(m) for m in re.findall(r"[Pp]age\s+(\d+)", answer)})


def citation_correct(answer: str, gold_pages: list[int]) -> bool | None:
    """
    True  - every page the model cited is a gold page
    False - it cited something else, or cited nothing at all
    None  - not applicable (unanswerable item)
    """
    if not gold_pages:
        return None
    cites = cited_pages(answer)
    if not cites:
        return False
    return all(p in gold_pages for p in cites)
