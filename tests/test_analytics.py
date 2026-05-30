from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock

from analytics import Analytics


def _make_review(title: str, score: int, roi: int = 6) -> dict:
    return {
        "id": 1,
        "timestamp": "2026-05-01T10:00:00",
        "idea_text": "Some idea",
        "mode": "Full Production Review",
        "depth": "Standard",
        "result_json": json.dumps({
            "project_name": title,
            "readiness_score": score,
            "roi_score": roi,
            "risks": [{"risk": "Data risk", "severity": "High", "why_it_matters": "x", "mitigation": "y"}],
            "lens_scores": [],
            "gaps": [],
        }),
    }


def _make_analytics(reviews: list) -> Analytics:
    db = MagicMock()
    db.get_history.return_value = reviews
    return Analytics(db)


def test_returns_none_when_no_history():
    analytics = _make_analytics([])
    assert analytics.get_portfolio_stats() is None


def test_total_reviews_count():
    analytics = _make_analytics([
        _make_review("Bot A", 80),
        _make_review("Bot B", 60),
    ])
    stats = analytics.get_portfolio_stats()
    assert stats["total_reviews"] == 2


def test_avg_readiness_computed():
    analytics = _make_analytics([
        _make_review("Bot A", 80),
        _make_review("Bot B", 60),
    ])
    stats = analytics.get_portfolio_stats()
    assert abs(stats["avg_readiness"] - 70.0) < 0.1


def test_roster_contains_correct_titles():
    analytics = _make_analytics([_make_review("Sales AI", 90)])
    stats = analytics.get_portfolio_stats()
    assert stats["roster"][0]["title"] == "Sales AI"


def test_roster_status_ready():
    analytics = _make_analytics([_make_review("Sales AI", 92)])
    stats = analytics.get_portfolio_stats()
    assert stats["roster"][0]["status"] == "Ready"


def test_roster_status_critical():
    analytics = _make_analytics([_make_review("Broken AI", 30)])
    stats = analytics.get_portfolio_stats()
    assert stats["roster"][0]["status"] == "Critical"


def test_maturity_trend_has_30_rows():
    analytics = _make_analytics([_make_review("AI", 70)])
    stats = analytics.get_portfolio_stats()
    assert len(stats["maturity_trend"]) == 30


def test_top_risks_extracted():
    analytics = _make_analytics([_make_review("AI", 70)])
    stats = analytics.get_portfolio_stats()
    assert "Data risk" in stats["top_risks"]


def test_corrupt_record_skipped():
    good = _make_review("Good AI", 75)
    bad = {**good, "result_json": "not-json"}
    analytics = _make_analytics([good, bad])
    stats = analytics.get_portfolio_stats()
    assert stats["total_reviews"] == 2
    assert len(stats["roster"]) == 1  # bad record skipped


def test_get_comparison_returns_both():
    db = MagicMock()
    r1 = {**_make_review("AI One", 80), "id": 1}
    r2 = {**_make_review("AI Two", 60), "id": 2}
    db.get_review_by_id.side_effect = lambda x: r1 if x == 1 else r2
    analytics = Analytics(db)
    comp = analytics.get_comparison(1, 2)
    assert comp["left"]["project_name"] == "AI One"
    assert comp["right"]["project_name"] == "AI Two"


def test_get_comparison_returns_none_when_missing():
    db = MagicMock()
    db.get_review_by_id.return_value = None
    analytics = Analytics(db)
    assert analytics.get_comparison(1, 2) is None
