from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock

from database import Database


@pytest.fixture
def db(tmp_path):
    return Database(db_path=str(tmp_path / "test_reviews.db"))


def _mock_result(title: str = "Test Project") -> MagicMock:
    obj = MagicMock()
    obj.model_dump_json.return_value = json.dumps({
        "project_name": title,
        "readiness_score": 75,
        "roi_score": 7,
        "lens_scores": [],
        "risks": [],
        "gaps": [],
    })
    return obj


def test_empty_history(db):
    assert db.get_history() == []


def test_save_and_retrieve(db):
    result = _mock_result("Sales AI")
    db.save_review("idea text", "Full Production Review", "Standard", result)
    history = db.get_history()
    assert len(history) == 1
    assert history[0]["mode"] == "Full Production Review"
    assert history[0]["idea_text"] == "idea text"


def test_multiple_reviews_ordered_desc(db):
    db.save_review("idea 1", "Full Production Review", "Standard", _mock_result("First"))
    db.save_review("idea 2", "Executive Review", "Concise", _mock_result("Second"))
    history = db.get_history()
    assert len(history) == 2
    assert history[0]["mode"] == "Executive Review"  # most recent first


def test_get_review_by_id(db):
    db.save_review("idea", "Full Production Review", "Standard", _mock_result())
    history = db.get_history()
    review_id = history[0]["id"]
    row = db.get_review_by_id(review_id)
    assert row is not None
    assert row["id"] == review_id


def test_get_review_by_id_missing(db):
    assert db.get_review_by_id(9999) is None


def test_result_json_is_valid(db):
    db.save_review("idea", "Full Production Review", "Standard", _mock_result("My Bot"))
    history = db.get_history()
    data = json.loads(history[0]["result_json"])
    assert data["project_name"] == "My Bot"


def test_db_path_from_env(tmp_path, monkeypatch):
    custom_path = str(tmp_path / "custom.db")
    monkeypatch.setenv("DB_PATH", custom_path)
    db = Database()
    assert db.db_path == custom_path
