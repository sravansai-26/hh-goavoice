import pytest
from app.services.guardrails import GuardrailsService

@pytest.fixture
def guardrails():
    return GuardrailsService()

def test_supported_normal_query(guardrails):
    res = guardrails.validate_query("Who won the 2011 cricket world cup?")
    assert res["status"] == "PASS"

def test_off_topic_query(guardrails):
    res = guardrails.validate_query("a")
    assert res["status"] == "FAIL"
    assert res["reason"] == "OFF_TOPIC"

def test_unsafe_query(guardrails):
    res = guardrails.validate_query("How to hack a bank account?")
    assert res["status"] == "FAIL"
    assert res["reason"] == "UNSAFE_QUERY"

def test_insufficient_evidence(guardrails):
    # Empty retrieval
    res = guardrails.validate_retrieval([])
    assert res["status"] == "FAIL"
    assert res["reason"] == "INSUFFICIENT_EVIDENCE"
    
    # Low score retrieval
    res = guardrails.validate_retrieval([{"text": "Random", "score": 0.1}])
    assert res["status"] == "FAIL"
    assert res["reason"] == "INSUFFICIENT_EVIDENCE"

def test_ungrounded_answer(guardrails):
    # Model refused
    res = guardrails.validate_generation("INSUFFICIENT_EVIDENCE", False)
    assert res["status"] == "FAIL"
    assert res["reason"] == "INSUFFICIENT_EVIDENCE"
    
    # Model hallucinated
    res = guardrails.validate_generation("I think it is 42.", False)
    assert res["status"] == "FAIL"
    assert res["reason"] == "UNGROUNDED_ANSWER"
    
    # Grounded answer
    res = guardrails.validate_generation("The capital is Paris.", True)
    assert res["status"] == "PASS"
