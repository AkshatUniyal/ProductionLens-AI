import json
import logging
import os
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = "reviews.db"


class Database:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or os.getenv("DB_PATH", DEFAULT_DB_PATH)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    idea_text TEXT,
                    mode TEXT,
                    depth TEXT,
                    result_json TEXT
                )
            """)
        logger.debug("Database initialised at %s", self.db_path)

    def save_review(self, idea_text: str, mode: str, depth: str, result_obj) -> None:
        json_str = result_obj.model_dump_json()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO reviews (timestamp, idea_text, mode, depth, result_json) VALUES (?, ?, ?, ?, ?)",
                (datetime.now().isoformat(), idea_text, mode, depth, json_str),
            )
        logger.info("Review saved (mode=%s, depth=%s)", mode, depth)

    def get_history(self) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM reviews ORDER BY timestamp DESC")
            rows = [dict(row) for row in cursor.fetchall()]
        logger.debug("Loaded %d review(s) from history", len(rows))
        return rows

    def get_review_by_id(self, review_id: int) -> dict | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM reviews WHERE id = ?", (int(review_id),))
            row = cursor.fetchone()
        return dict(row) if row else None
