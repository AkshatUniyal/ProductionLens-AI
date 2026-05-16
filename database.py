import sqlite3
import json
from datetime import datetime
import os

class Database:
    def __init__(self, db_path="reviews.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
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

    def save_review(self, idea_text, mode, depth, result_obj):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO reviews (timestamp, idea_text, mode, depth, result_json) VALUES (?, ?, ?, ?, ?)",
                (datetime.now().isoformat(), idea_text, mode, depth, result_obj.json())
            )

    def get_history(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM reviews ORDER BY timestamp DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_review_by_id(self, review_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
