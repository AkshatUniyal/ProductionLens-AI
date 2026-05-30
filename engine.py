import json
import logging
import os
from typing import List

import ollama
from pydantic import BaseModel

logger = logging.getLogger(__name__)

MAX_INPUT_CHARS = 5000
DEFAULT_MODEL = "llama3.2"
DEFAULT_HOST = "http://127.0.0.1:11434"
DEFAULT_TIMEOUT = 120


class Risk(BaseModel):
    risk: str
    severity: str  # High, Medium, Low
    why_it_matters: str
    mitigation: str

class Gap(BaseModel):
    feature: str
    in_demo: str
    in_production: str

class LensScore(BaseModel):
    lens: str
    score: int  # 1-10
    rationale: str

class ReviewOutput(BaseModel):
    input_summary: str
    readiness_score: int  # 0-100
    recommendation: str
    primary_risk: str
    suggested_next_step: str
    executive_summary: str
    lens_scores: List[LensScore]
    risks: List[Risk]
    gaps: List[Gap]
    missing_information: List[str]
    assumptions_made: List[str]
    pilot_plan: List[str]
    score_tagline: str
    recommendation_tagline: str
    risk_tagline: str
    step_tagline: str
    estimated_pilot_cost: str  # e.g. "$50k - $100k"
    roi_score: int  # 1-10


class ReviewEngine:
    def __init__(self, model: str | None = None, host: str | None = None, timeout: int | None = None):
        self.model = model or os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)
        self.host = host or os.getenv("OLLAMA_HOST", DEFAULT_HOST)
        try:
            self.timeout = int(os.getenv("OLLAMA_TIMEOUT", str(DEFAULT_TIMEOUT)))
        except ValueError:
            self.timeout = DEFAULT_TIMEOUT
        if timeout is not None:
            self.timeout = timeout
        self._client = ollama.Client(host=self.host, timeout=self.timeout)

    def _check_ollama(self) -> None:
        """Raise a clear RuntimeError if Ollama is unreachable or model is missing."""
        try:
            tags = self._client.list()
            available = {m.model for m in tags.models}
            if self.model not in available:
                raise RuntimeError(
                    f"Model '{self.model}' is not available in Ollama. "
                    f"Run: ollama pull {self.model}\n"
                    f"Available models: {', '.join(sorted(available)) or 'none'}"
                )
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError(
                f"Cannot reach Ollama at {self.host}. "
                "Make sure Ollama is running: ollama serve"
            ) from exc

    def get_review(
        self,
        idea_text: str,
        mode: str = "Full Production Review",
        depth: str = "Standard",
        include_pilot: bool = True,
        include_checklist: bool = True,
    ) -> ReviewOutput:
        if not idea_text or not idea_text.strip():
            raise ValueError("Project description cannot be empty.")
        if len(idea_text) > MAX_INPUT_CHARS:
            raise ValueError(
                f"Project description is too long ({len(idea_text)} chars). "
                f"Please keep it under {MAX_INPUT_CHARS} characters."
            )

        self._check_ollama()

        mode_focus = {
            "Full Production Review": "Provide a balanced, comprehensive review across all 8 lenses.",
            "Executive Review": "Focus primarily on business value, executive risks, ROI, and high-level strategic alignment. Use non-technical language where possible.",
            "RAG Readiness": "Focus deeply on data retrieval, grounding, hallucination risks, and chunking strategy. Be highly critical of data freshness.",
            "Architecture Review": "Focus on infrastructure, scalability, latency, modularity, and integration complexity. Use technical terminology."
        }

        depth_instr = {
            "Standard": "Provide a thorough analysis with 3-4 specific risks and gaps.",
            "Deep Dive": "Provide an EXHAUSTIVE, CRITICAL analysis. Identify 6+ critical risks and 6+ detailed production gaps. Be extremely skeptical and look for edge cases.",
            "Concise": "Provide a HIGH-LEVEL executive summary. Focus only on the single most critical 'make-or-break' risk and gap. Keep all rationals extremely brief."
        }

        system_prompt = f"You are a senior AI Review Board. Your current mission is: {mode_focus.get(mode, '')} {depth_instr.get(depth, '')}"
        if include_pilot:
            system_prompt += " Pay extra attention to the pilot_plan, ensuring it is actionable and specific."
        if include_checklist:
            system_prompt += " Ensure the risks and gaps form a comprehensive technical checklist for production readiness."
        system_prompt += " You MUST provide short, punchy taglines for the score, recommendation, risk, and next step."
        system_prompt += " You MUST return a valid JSON object."

        user_prompt = f"""
        CRITICAL: YOU ARE A SENIOR ARCHITECT. DO NOT COPY THE SAMPLE VALUES.
        EVERY FIELD MUST BE UNIQUE TO THE PROVIDED PROJECT DESCRIPTION.

        PROJECT DESCRIPTION FOR REVIEW:
        ---
        {idea_text}
        ---

        AUDIT CONTEXT:
        - Mode: {mode} (Focus: {mode_focus.get(mode, '')})
        - Depth: {depth} (Intensity: {depth_instr.get(depth, '')})

        REQUIRED OUTPUT JSON STRUCTURE:
        {{
            "project_name": "Short 2-3 word professional title",
            "input_summary": "One sentence summary of the input above.",
            "readiness_score": (int between 0-100 based on your audit),
            "score_tagline": "A 2-3 word technical status phrase",
            "recommendation": "Short 2-3 word core action",
            "recommendation_tagline": "One short sentence justification",
            "primary_risk": "Short 2-4 word technical risk name",
            "risk_tagline": "One short sentence explaining the danger",
            "suggested_next_step": "Short 2-4 word immediate task",
            "step_tagline": "One short sentence on how to start",
            "executive_summary": "3-5 sentences of high-level strategic analysis.",
            "lens_scores": [
                {{"lens": "Architecture", "score": 1-10, "rationale": "One short sentence rationale"}},
                {{"lens": "Data", "score": 1-10, "rationale": "One short sentence rationale"}},
                {{"lens": "RAG", "score": 1-10, "rationale": "One short sentence rationale"}},
                {{"lens": "Security", "score": 1-10, "rationale": "One short sentence rationale"}},
                {{"lens": "Observability", "score": 1-10, "rationale": "One short sentence rationale"}},
                {{"lens": "Evaluation", "score": 1-10, "rationale": "One short sentence rationale"}},
                {{"lens": "Adoption", "score": 1-10, "rationale": "One short sentence rationale"}},
                {{"lens": "Executive", "score": 1-10, "rationale": "One short sentence rationale"}}
            ],
            "risks": [
                {{
                    "risk": "Name of specific technical risk",
                    "severity": "High/Medium/Low",
                    "why_it_matters": "Business or technical impact",
                    "mitigation": "Concrete technical fix"
                }}
            ],
            "gaps": [
                {{
                    "feature": "Name of missing or weak feature",
                    "in_demo": "Current state/prototype limitation",
                    "in_production": "Required enterprise-grade state"
                }}
            ],
            "missing_information": ["List of strings"],
            "assumptions_made": ["List of strings"],
            "pilot_plan": ["List of strings"],
            "estimated_pilot_cost": "USD Range (string)",
            "roi_score": "Integer (1-10)"
        }}

        INSTRUCTIONS:
        1. "input_summary" must summarize the user's specific text.
        2. "lens_scores" must reflect the technical maturity of the input. Every lens MUST have a unique, specific rationale.
        3. "risks" and "gaps" must be relevant to the specific domain.
        4. "pilot_plan" must be a strictly 3-phase, 90-day concrete validation roadmap (exactly 3 string elements).
        5. "estimated_pilot_cost" must be a PRACTICAL range for a 3-month validation pilot.
        6. "roi_score" should be higher if the idea has clear business value and manageable technical complexity.
        """

        logger.info("Starting Ollama review (model=%s, mode=%s, depth=%s)", self.model, mode, depth)
        try:
            response = self._client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                format="json",
                options={"temperature": float(os.getenv("OLLAMA_TEMPERATURE", "0.2"))},
            )
        except ollama.ResponseError as exc:
            logger.error("Ollama model error: %s", exc)
            raise RuntimeError(
                f"Ollama returned an error for model '{self.model}': {exc}. "
                f"Try: ollama pull {self.model}"
            ) from exc
        except Exception as exc:
            logger.error("Ollama request failed: %s", exc)
            raise RuntimeError(
                f"Ollama request failed: {exc}. "
                "Check that Ollama is running and the model is available."
            ) from exc

        logger.info("Ollama response received.")
        content = response["message"]["content"]

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse LLM JSON output: %s", content[:500])
            raise RuntimeError(
                "The LLM returned a response that could not be parsed as JSON. "
                "Try running the review again."
            ) from exc

        # Fill in missing / malformed fields defensively
        keys = [
            "input_summary", "readiness_score", "recommendation", "primary_risk",
            "suggested_next_step", "executive_summary", "lens_scores", "risks", "gaps",
            "missing_information", "assumptions_made", "pilot_plan", "score_tagline",
            "recommendation_tagline", "risk_tagline", "step_tagline",
            "estimated_pilot_cost", "roi_score",
        ]
        defaults_taglines = {
            "score_tagline": "Assessment Complete",
            "recommendation_tagline": "Proceed with findings",
            "risk_tagline": "Review priority items",
            "step_tagline": "Start validation phase",
            "roi_score": 5,
            "estimated_pilot_cost": "TBD",
        }
        for key, default in defaults_taglines.items():
            if key not in data:
                data[key] = default

        list_keys = {"lens_scores", "risks", "gaps", "missing_information", "assumptions_made", "pilot_plan"}
        for key in keys:
            if key not in data:
                data[key] = [] if key in list_keys else "N/A"

        # Coerce string fields that LLM occasionally wraps in dicts or lists
        string_fields = [
            "input_summary", "readiness_score", "recommendation", "primary_risk",
            "suggested_next_step", "executive_summary", "score_tagline",
            "recommendation_tagline", "risk_tagline", "step_tagline", "estimated_pilot_cost",
        ]
        for field in string_fields:
            val = data.get(field)
            if isinstance(val, dict):
                data[field] = (
                    val.get("summary") or val.get("description") or val.get("text")
                    or val.get("risk") or val.get("value") or str(val)
                )
            elif isinstance(val, list):
                data[field] = " ".join(map(str, val))

        try:
            data["readiness_score"] = int(data["readiness_score"])
        except (ValueError, TypeError):
            logger.warning("Could not parse readiness_score; defaulting to 50")
            data["readiness_score"] = 50

        try:
            data["roi_score"] = max(1, min(10, int(data["roi_score"])))
        except (ValueError, TypeError):
            logger.warning("Could not parse roi_score; defaulting to 5")
            data["roi_score"] = 5

        if isinstance(data.get("lens_scores"), list):
            for lens in data["lens_scores"]:
                if isinstance(lens, dict) and "score" in lens:
                    try:
                        s = int(lens["score"])
                        if s > 10:
                            s = round(s / 10)
                        lens["score"] = max(1, min(10, s))
                    except (ValueError, TypeError):
                        lens["score"] = 5

        if isinstance(data.get("gaps"), list):
            for gap in data["gaps"]:
                if isinstance(gap, dict):
                    for k, v in gap.items():
                        if not isinstance(v, str):
                            gap[k] = "Yes" if v is True else "No" if v is False else str(v)

        if isinstance(data.get("risks"), list):
            for risk in data["risks"]:
                if isinstance(risk, dict):
                    for k, v in risk.items():
                        if not isinstance(v, str):
                            risk[k] = str(v)

        if isinstance(data.get("pilot_plan"), list):
            new_pilot = []
            for item in data["pilot_plan"]:
                if isinstance(item, dict):
                    step_str = f"{item.get('phase', item.get('step', 'Step'))}: {item.get('description', item.get('action', ''))}"
                    new_pilot.append(step_str)
                else:
                    new_pilot.append(str(item))
            data["pilot_plan"] = new_pilot

        try:
            return ReviewOutput(**data)
        except Exception as exc:
            logger.error("Pydantic validation failed after normalization: %s", exc)
            raise RuntimeError(
                f"LLM output could not be validated after normalization: {exc}"
            ) from exc


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    engine = ReviewEngine()
    test_idea = "We want to build an AI assistant that searches internal product data and recommends products to sales teams."
    result = engine.get_review(test_idea)
    print(result.model_dump_json(indent=2))
