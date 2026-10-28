"""
Career Readiness Assessment Engine for SkillGraph Phase 6.
Provides transparent, explainable multi-factor readiness evaluation, distinguishing
operational transition readiness from keyword role-matching, accounting for core competency
coverage, proficiency depth, evidence verification, and experience alignment.
"""

import os
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.database.db import REPO_ROOT
from backend.ml.role_matching import calculate_role_match

MODEL_PATH = os.getenv("READINESS_MODEL_PATH", str(REPO_ROOT / "backend" / "ml" / "models" / "readiness_model.joblib"))

LIMITATIONS_NOTICE = (
    "This career readiness assessment is an interpretable, multi-factor heuristic baseline "
    "combining core competency coverage, proficiency depth, evidence provenance, and experience alignment. "
    "It is not empirically validated against historical employee transition cohorts and should be used "
    "as self-service career guidance alongside managerial and peer evaluations."
)

class ReadinessPredictor:
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.scaler = None
        self.model_path = model_path if model_path is not None else MODEL_PATH
        self._load_model()

    def _load_model(self):
        if self.model_path and os.path.exists(self.model_path):
            try:
                artifacts = joblib.load(self.model_path)
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
        """
        Legacy predictor method maintained for backward compatibility.
        Predicts readiness score [0.0 - 1.0] using trained ML model or transparent rule-based fallback.
        """
        if self.model and self.scaler:
            features = np.array([[
                skill_match_ratio,
                core_skill_coverage,
                exp_delta,
                education_alignment,
                prerequisite_readiness
            ]])
            try:
                scaled = self.scaler.transform(features)
                probs = self.model.predict_proba(scaled)
                pred_score = float(probs[0][1])
                blended = 0.65 * pred_score + 0.35 * (0.5 * skill_match_ratio + 0.3 * core_skill_coverage + 0.2 * prerequisite_readiness)
                return round(float(np.clip(blended, 0.05, 0.98)), 3)
            except Exception:
                pass

        # Transparent formula fallback
        score = (
            0.40 * skill_match_ratio +
            0.30 * core_skill_coverage +
            0.15 * max(0.4, min(1.0, 1.0 + exp_delta * 0.05)) +
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
        Legacy transition evaluation method.
        Removed arbitrary heuristic that previously forced (+15%) guaranteed improvement.
        Projected readiness now strictly reflects acquired skills and prerequisite closure.
        """
        curr_ratio = current_match_score / 100.0
        curr_readiness = self.predict_readiness(
            skill_match_ratio=curr_ratio,
            core_skill_coverage=curr_ratio * 0.9,
            exp_delta=exp_delta,
            prerequisite_readiness=completed_prereqs_ratio
        )
        curr_pct = round(curr_readiness * 100, 1)

        if missing_skills_count > 0 and total_skills_count > 0:
            skill_gain_ratio = (missing_skills_count / total_skills_count) * 0.85
            projected_ratio = min(1.0, curr_ratio + skill_gain_ratio)
            projected_readiness = self.predict_readiness(
                skill_match_ratio=projected_ratio,
                core_skill_coverage=1.0,
                exp_delta=exp_delta + 1,
                prerequisite_readiness=1.0
            )
            proj_pct = round(projected_readiness * 100, 1)
            # Ensure projected reflects computed value (no arbitrary flat +15)
            proj_pct = max(curr_pct, proj_pct)
        else:
            # If 0 skills missing, projected readiness matches current readiness (no artificial boost)
            proj_pct = curr_pct

        proj_pct = min(98.5, proj_pct)
        gain_pct = round(proj_pct - curr_pct, 1)

        return {
            "current_readiness_pct": curr_pct,
            "projected_readiness_pct": proj_pct,
            "readiness_gain_pct": gain_pct,
            "transition_verdict": (
                "High Feasibility" if proj_pct >= 85 else
                ("Moderate Feasibility" if proj_pct >= 70 else "Long-Term Upskilling")
            ),
            "contributing_factors": {
                "skill_coverage_weight": "40%",
                "prerequisite_fulfillment": f"{int(completed_prereqs_ratio * 100)}%",
                "experience_delta_years": exp_delta
            },
            "assessment_methodology": "transparent_rule_based_baseline",
            "limitations": LIMITATIONS_NOTICE
        }

    def assess_career_readiness(
        self,
        employee_skills: List[Dict[str, Any]],
        employee_exp_years: int,
        role_required_skills: List[str],
        role_exp_years: int,
        role_skill_weights: Optional[Dict[str, float]] = None,
        completed_courses_count: int = 0,
        total_roadmap_courses: int = 0
    ) -> Dict[str, Any]:
        """
        Phase 6 Multi-Factor Career Readiness Assessment:
        Evaluates operational transition readiness distinguishing it from lexical keyword role matching.
        Factors:
        1. Core Competency Coverage (40%): Penalty for critical & high priority gaps.
        2. Proficiency & Verification Depth (30%): Demonstrated vs benchmark levels and evidence verification.
        3. Prerequisite & Foundational Alignment (15%): Completed roadmap courses or foundational curriculum.
        4. Experience Alignment (15%): Tenure delta against role experience requirements.
        """
        # 1. Compute baseline role match
        match_result = calculate_role_match(
            employee_skills=employee_skills,
            employee_exp_years=employee_exp_years,
            role_required_skills=role_required_skills,
            role_exp_years=role_exp_years,
            role_skill_weights=role_skill_weights
        )

        match_score = match_result["match_score"]
        total_required = match_result["total_required"]
        gaps = match_result.get("gaps", [])
        met_skills = match_result.get("met_skills", [])
        partially_met = match_result.get("partially_met_skills", [])
        missing_skills = match_result.get("missing_skills", [])

        # Empty skill profile check
        if not employee_skills or total_required == 0:
            if total_required == 0:
                readiness_score = 100.0
                verdict = "High Readiness — Ready for Transition"
                reasoning = "Role has no listed skill requirements."
            else:
                readiness_score = 0.0
                verdict = "Low Readiness — Foundational Upskilling Needed"
                reasoning = "No personal skills have been reported or verified in profile yet."

            return {
                "readiness_score": readiness_score,
                "readiness_level": verdict,
                "role_match_score": match_score,
                "score_difference": round(readiness_score - match_score, 1),
                "distinction_explanation": (
                    "Role Match measures lexical skill keyword overlap against job requirements. "
                    "Career Readiness assesses holistic capability to perform in the role today, "
                    "accounting for competency priorities, verification provenance, and prerequisite foundations."
                ),
                "difference_explanation": reasoning,
                "contributing_factors": [
                    {
                        "factor": "Core Competency Coverage",
                        "weight_pct": 40,
                        "score_pct": 0.0 if employee_skills else 100.0,
                        "impact": "Negative" if not employee_skills else "Positive",
                        "explanation": "No demonstrated competencies" if not employee_skills else "No required competencies"
                    },
                    {
                        "factor": "Proficiency & Verification Depth",
                        "weight_pct": 30,
                        "score_pct": 0.0,
                        "impact": "Negative",
                        "explanation": "No skills to assess proficiency or verification"
                    },
                    {
                        "factor": "Prerequisite Foundations",
                        "weight_pct": 15,
                        "score_pct": 0.0 if not employee_skills else 100.0,
                        "impact": "Neutral",
                        "explanation": "Prerequisite readiness"
                    },
                    {
                        "factor": "Experience Alignment",
                        "weight_pct": 15,
                        "score_pct": max(40.0, min(100.0, (1.0 + (employee_exp_years - role_exp_years) * 0.1) * 100)),
                        "impact": "Positive" if employee_exp_years >= role_exp_years else "Negative",
                        "explanation": f"Experience delta: {employee_exp_years - role_exp_years:+d} years"
                    }
                ],
                "missing_competencies": missing_skills,
                "assessment_methodology": "transparent_rule_based_baseline",
                "limitations": LIMITATIONS_NOTICE
            }

        # Factor 1: Core Competency Coverage (40%)
        critical_count = sum(1 for g in gaps if g.get("priority") == "Critical")
        high_count = sum(1 for g in gaps if g.get("priority") == "High")
        med_count = sum(1 for g in gaps if g.get("priority") in ["Medium", "Low"])

        core_penalty = (1.0 * critical_count + 0.6 * high_count + 0.3 * med_count) / max(1, total_required)
        factor_core = max(0.0, 1.0 - core_penalty)

        # Factor 2: Proficiency & Verification Depth (30%)
        total_matched = len(met_skills) + len(partially_met)
        if total_matched > 0:
            met_ratio = len(met_skills) / max(1, total_required)
            # Count how many matched skills are verified
            emp_map = {s.get("name", "").lower(): s for s in employee_skills if s.get("name")}
            verified_count = 0
            for ms in met_skills:
                sk_name = ms.get("skill_name", "").lower()
                if emp_map.get(sk_name, {}).get("verified"):
                    verified_count += 1
            for ps in partially_met:
                sk_name = ps.get("skill_name", "").lower()
                if emp_map.get(sk_name, {}).get("verified"):
                    verified_count += 0.5

            verif_ratio = verified_count / max(1, total_matched)
            factor_prof = 0.6 * met_ratio + 0.4 * verif_ratio
        else:
            factor_prof = 0.0

        # Factor 3: Prerequisite & Foundational Alignment (15%)
        if total_roadmap_courses > 0:
            factor_prereq = min(1.0, completed_courses_count / total_roadmap_courses)
        else:
            # If no courses needed or not specified, use proportion of met skills
            factor_prereq = len(met_skills) / max(1, total_required)

        # Factor 4: Experience Alignment (15%)
        exp_delta = employee_exp_years - role_exp_years
        if exp_delta >= 0:
            factor_exp = 1.0
        else:
            factor_exp = max(0.4, 1.0 + (exp_delta * 0.12))

        # Composite Readiness Score (0 - 100)
        raw_readiness = (
            0.40 * factor_core +
            0.30 * factor_prof +
            0.15 * factor_prereq +
            0.15 * factor_exp
        ) * 100.0

        # Guardrail: If critical core competency is missing, candidate cannot exceed 65% readiness
        if critical_count > 0:
            raw_readiness = min(65.0, raw_readiness)

        readiness_score = round(max(0.0, min(100.0, raw_readiness)), 1)
        score_diff = round(readiness_score - match_score, 1)

        # Verdict
        if readiness_score >= 85.0:
            verdict = "High Readiness — Ready for Transition"
        elif readiness_score >= 70.0:
            verdict = "Moderate Readiness — Targeted Upskilling Required"
        elif readiness_score >= 50.0:
            verdict = "Developing Readiness — Substantial Upskilling Needed"
        else:
            verdict = "Low Readiness — Foundational Upskilling Needed"

        # Difference explanation
        positive_factors = []
        negative_factors = []

        if critical_count > 0:
            negative_factors.append(f"{critical_count} critical core requirement{'s' if critical_count > 1 else ''} missing")
        elif high_count > 0:
            negative_factors.append(f"{high_count} high-priority requirement{'s' if high_count > 1 else ''} missing")

        if exp_delta < 0:
            negative_factors.append(f"{abs(exp_delta)} year experience deficit")
        elif exp_delta >= 0:
            positive_factors.append(f"full experience tenure alignment ({employee_exp_years} yrs)")

        if factor_prof >= 0.6:
            positive_factors.append("verified proficiency depth in demonstrated competencies")
        elif factor_prof < 0.5:
            negative_factors.append("unverified evidence or proficiency gaps in matched skills")

        if score_diff < -3.0:
            reasons_str = ", and ".join(negative_factors) if negative_factors else "competency prioritization penalties"
            diff_text = f"Readiness is {abs(score_diff)}% lower than Role Match primarily due to {reasons_str}."
        elif score_diff > 3.0:
            reasons_str = ", and ".join(positive_factors) if positive_factors else "foundational competency and tenure alignment"
            diff_text = f"Readiness is {score_diff}% higher than Role Match primarily due to {reasons_str}."
        else:
            diff_text = "Readiness closely mirrors Role Match alignment across core competencies and experience tenure."

        contributing_factors = [
            {
                "factor": "Core Competency Coverage",
                "weight_pct": 40,
                "score_pct": round(factor_core * 100, 1),
                "impact": "Positive" if factor_core >= 0.75 else ("Neutral" if factor_core >= 0.50 else "Negative"),
                "explanation": (
                    f"Covering {total_required - len(gaps)} of {total_required} requirements; "
                    f"{critical_count} critical and {high_count} high priority gaps."
                )
            },
            {
                "factor": "Proficiency & Verification Depth",
                "weight_pct": 30,
                "score_pct": round(factor_prof * 100, 1),
                "impact": "Positive" if factor_prof >= 0.75 else ("Neutral" if factor_prof >= 0.50 else "Negative"),
                "explanation": (
                    f"{len(met_skills)} skills meet benchmark level; "
                    f"{len(partially_met)} have proficiency gaps."
                )
            },
            {
                "factor": "Prerequisite Foundations",
                "weight_pct": 15,
                "score_pct": round(factor_prereq * 100, 1),
                "impact": "Positive" if factor_prereq >= 0.75 else ("Neutral" if factor_prereq >= 0.50 else "Negative"),
                "explanation": (
                    f"{completed_courses_count} of {total_roadmap_courses} prerequisite roadmap courses completed."
                    if total_roadmap_courses > 0 else "Foundational requirements satisfied."
                )
            },
            {
                "factor": "Experience Alignment",
                "weight_pct": 15,
                "score_pct": round(factor_exp * 100, 1),
                "impact": "Positive" if exp_delta >= 0 else "Negative",
                "explanation": f"Candidate has {employee_exp_years} yrs exp vs {role_exp_years} yrs required ({exp_delta:+d} yrs)."
            }
        ]

        return {
            "readiness_score": readiness_score,
            "readiness_level": verdict,
            "role_match_score": match_score,
            "score_difference": score_diff,
            "distinction_explanation": (
                "Role Match measures lexical skill keyword overlap against job requirements. "
                "Career Readiness assesses holistic capability to perform in the role today, "
                "accounting for competency priorities, verification provenance, and prerequisite foundations."
            ),
            "difference_explanation": diff_text,
            "contributing_factors": contributing_factors,
            "missing_competencies": missing_skills,
            "assessment_methodology": "transparent_rule_based_baseline",
            "limitations": LIMITATIONS_NOTICE
        }

readiness_predictor = ReadinessPredictor()
