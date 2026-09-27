import json

import pytest

from app.rag.prompts import build_context_string, QA_SYSTEM_PROMPT

# In a real environment with GPU/Ollama running, we would use:
# from ragas import evaluate
# from ragas.metrics import faithfulness, answer_relevancy


def load_golden_data():
    with open("tests/evaluation/golden_qa.json", "r") as f:
        return json.load(f)


def test_golden_data_is_valid():
    """Verify the golden QA dataset is well-formed."""
    golden_data = load_golden_data()
    assert len(golden_data) >= 2, "Golden dataset should contain at least 2 QA pairs"
    for item in golden_data:
        assert "question" in item, "Each item must have a 'question' field"
        assert "ground_truth" in item, "Each item must have a 'ground_truth' field"
        assert "context" in item, "Each item must have a 'context' field"
        assert len(item["question"]) > 0
        assert len(item["ground_truth"]) > 0
        assert len(item["context"]) > 0


def test_context_string_formatting():
    """Verify that retrieved chunks are formatted correctly for the LLM prompt."""
    chunks = [
        {"page": 1, "text": "The monthly rent is $2,500."},
        {"page": 3, "text": "No pets are allowed on the premises."},
    ]
    result = build_context_string(chunks)
    assert "[Page 1]" in result
    assert "[Page 3]" in result
    assert "The monthly rent is $2,500." in result
    assert "No pets are allowed on the premises." in result


def test_system_prompt_includes_context():
    """Verify the system prompt correctly interpolates the context string."""
    context = "[Page 1] The lease term is 12 months."
    prompt = QA_SYSTEM_PROMPT.format(context_string=context)
    assert context in prompt
    assert "RULES" in prompt
    assert "Do not use outside knowledge" in prompt


# To run full Ragas evaluation (requires Ollama running locally):
# @pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="Ollama not running")
# @pytest.mark.asyncio
# async def test_rag_pipeline_quality():
#     golden_data = load_golden_data()
#     dataset = Dataset.from_dict({...})
#     result = evaluate(dataset, metrics=[faithfulness, answer_relevancy])
#     assert result['faithfulness'] > 0.80
