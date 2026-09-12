"""
Transition Readiness Prediction Engine.
Uses the pre-trained Machine Learning model to evaluate current and post-upskilling readiness
for internal talent mobility transitions.
"""

import os
import joblib
import numpy as np
from typing import Dict, Any, List

MODEL_PATH = "backend/ml/models/readiness_model.joblib"

class ReadinessPredictor:
    def __init__(self):
        self.model = None
        self.scaler = None
        self._load_model()

    def _load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                artifacts = joblib.load(MODEL_PATH)
                self.model = artifacts.get("model")
                self.scaler = artifacts.get("scaler")
            except Exception as e:
                print(f"[WARN] Could not load ML model: {e}")

    def predict_readiness(
        self,
        skill_match_ratio: float,
        core_skill_coverage: float,
        exp_delta: int,
        education_alignment: float = 0.85,
        prerequisite_readiness: float = 0.80
    ) -> float:
        """Predicts readiness score [0.0 - 1.0] using trained ML model or probabilistic fallback."""
        if self.model and self.scaler:
            features = np.array([[
                skill_match_ratio,
                core_skill_coverage,
                exp_delta,
                education_alignment,
                prerequisite_readiness
            ]])
            scaled = self.scaler.transform(features)
            # Use predict_proba for smooth probability score
            probs = self.model.predict_proba(scaled)
            pred_score = float(probs[0][1])
            # Calibrate with raw features to maintain monotonic consistency
            blended = 0.65 * pred_score + 0.35 * (0.5 * skill_match_ratio + 0.3 * core_skill_coverage + 0.2 * prerequisite_readiness)
            return round(float(np.clip(blended, 0.05, 0.98)), 3)
        else:
            # Formula fallback
            score = (
                0.40 * skill_match_ratio +
                0.30 * core_skill_coverage +
                0.15 * max(0.5, min(1.0, 1.0 + exp_delta * 0.05)) +
                0.15 * prerequisite_readiness
            )
            return round(float(np.clip(score, 0.05, 0.98)), 3)

    def evaluate_transition(
        self,
        current_match_score: float,
        missing_skills_count: int,
        total_skills_count: int,
        exp_delta: int,
        completed_prereqs_ratio: float = 0.75
    ) -> Dict[str, Any]:
        """
        Computes current readiness and projected readiness after completing upskilling.
        """
        curr_ratio = current_match_score / 100.0
        curr_readiness = self.predict_readiness(
            skill_match_ratio=curr_ratio,
            core_skill_coverage=curr_ratio * 0.9,
            exp_delta=exp_delta,
            prerequisite_readiness=completed_prereqs_ratio
        )

        # Projected readiness assuming missing skills acquired
        projected_ratio = min(1.0, curr_ratio + (missing_skills_count / max(1, total_skills_count)) * 0.85)
        projected_readiness = self.predict_readiness(
            skill_match_ratio=projected_ratio,
            core_skill_coverage=1.0,
            exp_delta=exp_delta + 1,  # after training timeline
            prerequisite_readiness=1.0
        )

        curr_pct = round(curr_readiness * 100, 1)
        proj_pct = round(max(curr_pct + 15, projected_readiness * 100), 1)
        proj_pct = min(98.5, proj_pct)

        return {
            "current_readiness_pct": curr_pct,
            "projected_readiness_pct": proj_pct,
            "readiness_gain_pct": round(proj_pct - curr_pct, 1),
            "transition_verdict": "High Feasibility" if proj_pct >= 85 else ("Moderate Feasibility" if proj_pct >= 70 else "Long-Term Upskilling"),
            "contributing_factors": {
                "skill_coverage_weight": "40%",
                "prerequisite_fulfillment": f"{int(completed_prereqs_ratio * 100)}%",
                "experience_delta_years": exp_delta
            }
        }

readiness_predictor = ReadinessPredictor()
