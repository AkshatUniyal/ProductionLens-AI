import json
import ollama
from pydantic import BaseModel, Field
from typing import List, Optional

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
    def __init__(self, model="llama3.2"):
        self.model = model

    def get_review(self, idea_text: str, mode: str = "Full Production Review", depth: str = "Standard", include_pilot: bool = True, include_checklist: bool = True) -> ReviewOutput:

        # Define mode-specific instructions
        mode_focus = {
            "Full Production Review": "Provide a balanced, comprehensive review across all 8 lenses.",
            "Executive Review": "Focus primarily on business value, executive risks, ROI, and high-level strategic alignment. Use non-technical language where possible.",
            "RAG Readiness": "Focus deeply on data retrieval, grounding, hallucination risks, and chunking strategy. Be highly critical of data freshness.",
            "Architecture Review": "Focus on infrastructure, scalability, latency, modularity, and integration complexity. Use technical terminology."
        }
        
        # Define depth-specific instructions
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
        
        # Add dynamic taglines
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
            "executive_summary": "3-5 sentences of high-level strategic analysis. Must read like a consultant's insight (e.g., 'Project X has stronger security posture (9/10) but significant data readiness gap (4/10)...')",
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
        2. "lens_scores" must reflect the technical maturity of the input. **CRITICAL: Every single lens MUST have a completely unique, specific rationale. Do NOT duplicate or reuse text across different lenses.**
        3. "risks" and "gaps" must be relevant to the specific domain.
        4. "pilot_plan" must be a strictly 3-phase, 90-day concrete validation roadmap for THIS specific project (e.g. Month 1, Month 2, Month 3). Must contain exactly 3 string elements.
        5. "estimated_pilot_cost" must be a PRACTICAL range for a 3-month validation pilot (e.g., $50,000 - $120,000). Avoid $200k+ unless the idea is massive scale.
        6. "roi_score" should be higher if the idea has clear business value and manageable technical complexity.
        """
        
        print(f"Engine: Starting Ollama chat (model={self.model})...")
        response = ollama.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            format="json",
            options={"temperature": 0.2}

        )
        print("Engine: Ollama response received.")
        
        content = response['message']['content']
        try:
            data = json.loads(content)
            # Ensure all keys exist to avoid Pydantic errors
            keys = ["input_summary", "readiness_score", "recommendation", "primary_risk", "suggested_next_step", "executive_summary", "lens_scores", "risks", "gaps", "missing_information", "assumptions_made", "pilot_plan", "score_tagline", "recommendation_tagline", "risk_tagline", "step_tagline", "estimated_pilot_cost", "roi_score"]
            
            # Default taglines if missing
            if 'score_tagline' not in data: data['score_tagline'] = "Assessment Complete"
            if 'recommendation_tagline' not in data: data['recommendation_tagline'] = "Proceed with findings"
            if 'risk_tagline' not in data: data['risk_tagline'] = "Review priority items"
            if 'step_tagline' not in data: data['step_tagline'] = "Start validation phase"
            if 'roi_score' not in data: data['roi_score'] = 5
            if 'estimated_pilot_cost' not in data: data['estimated_pilot_cost'] = "TBD"

            for key in keys:
                if key not in data:
                    if key in ["lens_scores", "risks", "gaps", "missing_information", "assumptions_made", "pilot_plan"]:
                        data[key] = []
                    else:
                        data[key] = "N/A"
            
            # Universal normalization for all potential string fields
            string_fields = ["input_summary", "readiness_score", "recommendation", "primary_risk", "suggested_next_step", "executive_summary", "score_tagline", "recommendation_tagline", "risk_tagline", "step_tagline", "estimated_pilot_cost"]
            for field in string_fields:
                val = data.get(field)
                if isinstance(val, dict):
                    # Flatten the dict into a string
                    data[field] = val.get("summary") or val.get("description") or val.get("text") or val.get("risk") or val.get("value") or str(val)
                elif isinstance(val, list):
                    data[field] = " ".join(map(str, val))
                
            # Ensure readiness_score and roi_score are ints
            try:
                data["readiness_score"] = int(data["readiness_score"])
            except:
                data["readiness_score"] = 50
            
            try:
                data["roi_score"] = max(1, min(10, int(data["roi_score"])))
            except:
                data["roi_score"] = 5

            # Normalize individual lens scores (0-10)
            if isinstance(data.get("lens_scores"), list):
                for lens in data["lens_scores"]:
                    if isinstance(lens, dict) and "score" in lens:
                        try:
                            s = int(lens["score"])
                            # Fix common hallucination where model gives 0-100 instead of 0-10
                            if s > 10:
                                s = round(s / 10)
                            # Clamp between 1 and 10
                            lens["score"] = max(1, min(10, s))
                        except:
                            lens["score"] = 5

            # Normalization for list fields (Gaps and Risks)
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
                        # Convert dict to a readable string
                        step_str = f"{item.get('phase', item.get('step', 'Step'))}: {item.get('description', item.get('action', ''))}"
                        new_pilot.append(step_str)
                    else:
                        new_pilot.append(str(item))
                data["pilot_plan"] = new_pilot

            return ReviewOutput(**data)
        except Exception as e:
            print(f"Failed to parse or validate LLM output: {content}")
            raise e

if __name__ == "__main__":
    # Test
    engine = ReviewEngine()
    test_idea = "We want to build an AI assistant that searches internal product data and recommends products to sales teams."
    result = engine.get_review(test_idea)
    print(result.model_dump_json(indent=2))
