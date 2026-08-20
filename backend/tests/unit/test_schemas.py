# backend/tests/unit/test_schemas.py
import uuid

import pytest
from pydantic import ValidationError

from app.rag.agent import QAState


def test_qa_state_validation():
    valid_uuid = uuid.uuid4()
    req = QAState(lease_id=valid_uuid, query="Who is the tenant?", status="processing")
    assert req.query == "Who is the tenant?"
    
    with pytest.raises(ValidationError):
        QAState(lease_id="not-a-uuid", query="Who is the tenant?")
