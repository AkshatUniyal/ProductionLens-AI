from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock, patch

from engine import ReviewEngine, ReviewOutput, MAX_INPUT_CHARS


def _make_valid_response() -> str:
    return json.dumps({
        "project_name": "Test Project",
        "input_summary": "A test AI project.",
        "readiness_score": 72,
        "score_tagline": "Promising",
        "recommendation": "Proceed",
        "recommendation_tagline": "Low risk approach.",
        "primary_risk": "Data quality",
        "risk_tagline": "Incomplete training data.",
        "suggested_next_step": "Run pilot",
        "step_tagline": "Start with 30-day trial.",
        "executive_summary": "This project has solid fundamentals.",
        "lens_scores": [
            {"lens": lname, "score": 7, "rationale": f"Rationale for {lname}."}
            for lname in ["Architecture", "Data", "RAG", "Security", "Observability", "Evaluation", "Adoption", "Executive"]
        ],
        "risks": [{"risk": "Data drift", "severity": "High", "why_it_matters": "Model degrades.", "mitigation": "Monitor."}],
        "gaps": [{"feature": "Logging", "in_demo": "None", "in_production": "Full observability"}],
        "missing_information": ["Data volume"],
        "assumptions_made": ["Data is available"],
        "pilot_plan": ["Month 1: Setup", "Month 2: Test", "Month 3: Evaluate"],
        "estimated_pilot_cost": "$40,000 - $80,000",
        "roi_score": 7,
    })


def _make_engine_with_mock(response_content: str) -> ReviewEngine:
    engine = ReviewEngine.__new__(ReviewEngine)
    engine.model = "llama3.2"
    engine.host = "http://127.0.0.1:11434"
    engine.timeout = 120

    mock_client = MagicMock()
    mock_client.list.return_value = MagicMock(models=[MagicMock(model="llama3.2")])
    mock_client.chat.return_value = {"message": {"content": response_content}}
    engine._client = mock_client
    return engine


def test_get_review_returns_review_output():
    engine = _make_engine_with_mock(_make_valid_response())
    result = engine.get_review("We want to build a sales AI assistant.")
    assert isinstance(result, ReviewOutput)
    assert result.readiness_score == 72
    assert len(result.lens_scores) == 8


def test_get_review_empty_input_raises():
    engine = _make_engine_with_mock(_make_valid_response())
    with pytest.raises(ValueError, match="empty"):
        engine.get_review("")


def test_get_review_too_long_input_raises():
    engine = _make_engine_with_mock(_make_valid_response())
    with pytest.raises(ValueError, match="too long"):
        engine.get_review("x" * (MAX_INPUT_CHARS + 1))


def test_get_review_invalid_json_raises():
    engine = _make_engine_with_mock("not valid json")
    with pytest.raises(RuntimeError, match="parsed as JSON"):
        engine.get_review("A valid description.")


def test_get_review_normalises_high_lens_score():
    data = json.loads(_make_valid_response())
    data["lens_scores"][0]["score"] = 70  # LLM hallucinated 0-100 scale
    engine = _make_engine_with_mock(json.dumps(data))
    result = engine.get_review("A valid description.")
    assert result.lens_scores[0].score <= 10


def test_get_review_clamps_readiness_score_default_on_bad_value():
    data = json.loads(_make_valid_response())
    data["readiness_score"] = "not-a-number"
    engine = _make_engine_with_mock(json.dumps(data))
    result = engine.get_review("A valid description.")
    assert result.readiness_score == 50


def test_get_review_clamps_roi_score():
    data = json.loads(_make_valid_response())
    data["roi_score"] = 999
    engine = _make_engine_with_mock(json.dumps(data))
    result = engine.get_review("A valid description.")
    assert result.roi_score == 10


def test_check_ollama_raises_when_model_missing():
    engine = ReviewEngine.__new__(ReviewEngine)
    engine.model = "missing-model"
    engine.host = "http://127.0.0.1:11434"
    engine.timeout = 120
    mock_client = MagicMock()
    mock_client.list.return_value = MagicMock(models=[MagicMock(model="llama3.2")])
    engine._client = mock_client
    with pytest.raises(RuntimeError, match="not available"):
        engine._check_ollama()


def test_check_ollama_raises_when_unreachable():
    engine = ReviewEngine.__new__(ReviewEngine)
    engine.model = "llama3.2"
    engine.host = "http://127.0.0.1:11434"
    engine.timeout = 120
    mock_client = MagicMock()
    mock_client.list.side_effect = ConnectionError("refused")
    engine._client = mock_client
    with pytest.raises(RuntimeError, match="Cannot reach Ollama"):
        engine._check_ollama()
