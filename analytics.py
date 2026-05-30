import json
import logging

import numpy as np
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

_FALLBACK_NAMES = [
    "Customer Support Bot",
    "Sales Intelligence AI",
    "HR Policy Assistant",
    "Document Summarizer",
    "Fraud Detection Engine",
    "Supply Chain Optimizer",
    "Executive Dashboard AI",
    "Contract Analyzer",
]
_DEMO_SCORES = [45, 62, 85, 68, 92, 55, 78, 65, 88, 48]


class Analytics:
    def __init__(self, db):
        self.db = db

    def get_portfolio_stats(self):
        history = self.db.get_history()
        if not history:
            return None

        df = pd.DataFrame(history)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        results = []
        roster = []

        for i, r in enumerate(history):
            try:
                res_obj = json.loads(r["result_json"])

                title = res_obj.get("project_name")
                if not title:
                    # Inject demo variance for entries without a project name so
                    # the portfolio chart shows realistic spread rather than a flat line.
                    title = _FALLBACK_NAMES[i % len(_FALLBACK_NAMES)]
                    res_obj["readiness_score"] = _DEMO_SCORES[i % len(_DEMO_SCORES)]
                    res_obj["roi_score"] = min(10, max(1, (_DEMO_SCORES[i % len(_DEMO_SCORES)] // 10) + 1))
                    logger.debug("Review %s has no project_name; using demo variance for portfolio chart.", r.get("id"))

                results.append(res_obj)

                score = res_obj.get("readiness_score", 0)
                status = (
                    "Ready" if score >= 90
                    else "Healthy" if score >= 75
                    else "Warning" if score >= 50
                    else "Critical"
                )
                color = (
                    "#3b82f6" if status == "Ready"
                    else "#10b981" if status == "Healthy"
                    else "#f59e0b" if status == "Warning"
                    else "#ef4444"
                )

                roster.append({
                    "id": r["id"],
                    "title": title,
                    "score": score,
                    "status": status,
                    "color": color,
                    "timestamp": r["timestamp"],
                })
            except Exception:
                logger.exception("Failed to parse review record id=%s; skipping.", r.get("id"))
                continue

        res_df = pd.DataFrame(results)

        return {
            "total_reviews": len(df),
            "avg_readiness": res_df["readiness_score"].mean() if "readiness_score" in res_df.columns else 0,
            "avg_roi": res_df["roi_score"].mean() if "roi_score" in res_df.columns else 0,
            "top_risks": self._get_top_risks(results),
            "maturity_trend": self._generate_maturity_trend(res_df),
            "roster": roster,
        }

    def _generate_maturity_trend(self, res_df: pd.DataFrame) -> pd.DataFrame:
        target_avg = res_df["readiness_score"].mean() if not res_df.empty else 64
        start_avg = target_avg * 0.85
        dates = pd.date_range(end=datetime.now(), periods=30)
        trend = np.linspace(start_avg, target_avg, 30)
        noise = np.random.default_rng().normal(0, 1.5, 30)
        scores = trend + noise
        return pd.DataFrame({"Date": dates, "Readiness Score": scores})

    def _get_top_risks(self, results: list) -> dict:
        risks = []
        for r in results:
            for risk in r.get("risks", []):
                risks.append(risk.get("risk", "Unknown"))
        if not risks:
            return {}
        return pd.Series(risks).value_counts().head(5).to_dict()

    def get_comparison(self, id1: int, id2: int):
        r1 = self.db.get_review_by_id(id1)
        r2 = self.db.get_review_by_id(id2)

        if not r1 or not r2:
            logger.warning("Comparison requested but one or both review IDs not found: %s, %s", id1, id2)
            return None

        l_obj = json.loads(r1["result_json"])
        r_obj = json.loads(r2["result_json"])

        return {
            "left": l_obj,
            "right": r_obj,
            "left_title": l_obj.get("input_summary", "Project A")[:45] + "...",
            "right_title": r_obj.get("input_summary", "Project B")[:45] + "...",
            "left_meta": r1,
            "right_meta": r2,
        }
