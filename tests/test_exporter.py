from __future__ import annotations

import pytest
from exporter import Exporter


def _minimal_result(score: int = 72) -> dict:
    return {
        "project_name": "Test AI",
        "input_summary": "A test project.",
        "readiness_score": score,
        "recommendation": "Proceed",
        "executive_summary": "This is a test executive summary.",
        "roi_score": 7,
        "estimated_pilot_cost": "$40,000 - $80,000",
        "lens_scores": [
            {"lens": name, "score": 7, "rationale": f"Rationale for {name}."}
            for name in ["Architecture", "Data", "RAG", "Security"]
        ],
        "gaps": [{"feature": "Logging", "in_demo": "None", "in_production": "Full stack"}],
        "pilot_plan": ["Month 1: Setup", "Month 2: Test", "Month 3: Evaluate"],
        "risks": [],
    }


def test_generate_pdf_returns_bytes():
    result = Exporter().generate_pdf(_minimal_result())
    assert isinstance(result, (bytes, bytearray))
    assert len(result) > 1000


def test_generate_pdf_high_score():
    result = Exporter().generate_pdf(_minimal_result(score=95))
    assert len(result) > 0


def test_generate_pdf_low_score():
    result = Exporter().generate_pdf(_minimal_result(score=20))
    assert len(result) > 0


def test_generate_pdf_empty_sections():
    data = _minimal_result()
    data["gaps"] = []
    data["pilot_plan"] = []
    data["lens_scores"] = []
    result = Exporter().generate_pdf(data)
    assert len(result) > 0


def test_generate_pdf_missing_project_name():
    data = _minimal_result()
    del data["project_name"]
    result = Exporter().generate_pdf(data)
    assert len(result) > 0


def test_generate_pdf_raises_runtime_on_bad_input():
    with pytest.raises(RuntimeError, match="PDF export failed"):
        Exporter().generate_pdf(None)
