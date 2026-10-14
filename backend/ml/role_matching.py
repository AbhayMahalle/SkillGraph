"""
Multi-Factor Role Matching & Skill Gap Engine.
Compares employee profiles against organizational target roles to calculate
skill coverage, weighted compatibility, proficiency gaps, provenance factors,
and talent mobility status with rigorous explainability.
"""

from typing import List, Dict, Any, Optional

PROFICIENCY_LEVELS: Dict[str, int] = {
    "Beginner": 1,
    "Intermediate": 2,
    "Advanced": 3,
    "Expert": 4
}

LEVEL_TO_PROFICIENCY: Dict[int, str] = {
    1: "Beginner",
    2: "Intermediate",
    3: "Advanced",
    4: "Expert"
}

PROFICIENCY_WEIGHTS: Dict[str, float] = {
    "Expert": 1.0,
    "Advanced": 0.90,
    "Intermediate": 0.75,
    "Beginner": 0.50
}

def get_role_benchmark_level(role_exp_years: int) -> int:
    """
    Derives required skill proficiency benchmark based on role experience requirements:
    - 5+ years experience: Advanced (Level 3)
    - 2-4 years experience: Intermediate (Level 2)
    - <2 years experience: Beginner (Level 1)
    """
    if role_exp_years >= 5:
        return 3
    elif role_exp_years >= 2:
        return 2
    else:
        return 1

def classify_gap_priority(gap: int, importance_weight: float) -> str:
    """
    Computes explainable gap priority based on proficiency distance and role importance weight:
    - priority_metric = gap * weight
    - >= 3.0 or gap >= 3: Critical
    - >= 2.0 or gap == 2: High
    - >= 1.0 or gap == 1: Medium
    - < 1.0: Low
    """
    metric = gap * importance_weight
    if metric >= 3.0 or gap >= 3:
        return "Critical"
    elif metric >= 2.0 or gap == 2:
        return "High"
    elif metric >= 1.0 or gap == 1:
        return "Medium"
    else:
        return "Low"

def calculate_role_match(
    employee_skills: List[Dict[str, Any]],
    employee_exp_years: int,
    role_required_skills: List[str],
    role_exp_years: int,
    role_skill_weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Computes explainable multi-factor match score, classified skill gaps (Met, Partially Met, Missing),
    and provenance-aware talent mobility status.
    """
    if not role_required_skills:
        return {
            "match_score": 100.0,
            "coverage_percentage": 100.0,
            "matched_skills": [],
            "missing_skills": [],
            "met_skills": [],
            "partially_met_skills": [],
            "matched_count": 0,
            "missing_count": 0,
            "met_count": 0,
            "partially_met_count": 0,
            "total_required": 0,
            "experience_delta": employee_exp_years - role_exp_years,
            "mobility_status": "Ready for Internal Transition",
            "gaps": [],
            "explanation": {
                "formula": "Empty role requirements default to 100% compatibility.",
                "raw_coverage_pct": 100.0,
                "experience_factor": 1.0,
                "summary": "This role has no specific skill requirements listed."
            }
        }

    # Map employee skills with case-insensitive normalization and provenance awareness
    emp_skill_map: Dict[str, Dict[str, Any]] = {}
    for s in employee_skills:
        name = s.get("name") or s.get("skill_name")
        if not name:
            continue
        prof = s.get("proficiency", "Intermediate")
        user_lvl = PROFICIENCY_LEVELS.get(prof, 2)
        source = s.get("source", "self_reported")
        verified = s.get("verified", True if source != "resume_extracted" else False)
        
        # Provenance rule: unverified candidate resume mentions are discounted by 1 level
        is_unverified = (source == "resume_extracted" and not verified)
        demonstrated_lvl = max(1, user_lvl - 1) if is_unverified else user_lvl

        emp_skill_map[name.lower()] = {
            "skill_name": name,
            "proficiency": prof,
            "user_level": user_lvl,
            "demonstrated_level": demonstrated_lvl,
            "source": source,
            "verified": verified,
            "is_unverified": is_unverified,
            "evidence": s.get("evidence")
        }

    required_level = get_role_benchmark_level(role_exp_years)
    req_level_label = LEVEL_TO_PROFICIENCY[required_level]

    total_weight = 0.0
    earned_weight = 0.0
    met_skills = []
    partially_met_skills = []
    missing_skills = []
    all_gaps = []

    for req in role_required_skills:
        w = role_skill_weights.get(req, 1.0) if role_skill_weights else 1.0
        total_weight += w
        req_lower = req.lower()

        if req_lower not in emp_skill_map:
            # Classification 1: Missing
            gap = required_level
            priority = classify_gap_priority(gap, w)
            gap_item = {
                "skill_name": req,
                "classification": "missing",
                "status": "Missing",
                "weight": w,
                "importance_weight": w,
                "required_proficiency": req_level_label,
                "required_level": required_level,
                "current_proficiency": None,
                "current_level": 0,
                "gap": gap,
                "priority": priority,
                "source": None,
                "verified": None,
                "evidence": None,
                "reason": "Skill is not present in employee profile."
            }
            missing_skills.append(gap_item)
            all_gaps.append(gap_item)
        else:
            item = emp_skill_map[req_lower]
            demonstrated = item["demonstrated_level"]

            if not item["is_unverified"] and demonstrated >= required_level:
                # Classification 2: Met
                earned_weight += w * 1.0
                met_item = {
                    "skill_name": req,
                    "classification": "met",
                    "status": "Strong match",
                    "weight": w,
                    "importance_weight": w,
                    "required_proficiency": req_level_label,
                    "required_level": required_level,
                    "current_proficiency": item["proficiency"],
                    "current_level": item["user_level"],
                    "demonstrated_level": demonstrated,
                    "gap": 0,
                    "priority": "None",
                    "source": item["source"],
                    "verified": item["verified"],
                    "evidence": item["evidence"],
                    "reason": f"Demonstrated {item['proficiency']} proficiency meets role requirement ({req_level_label})."
                }
                met_skills.append(met_item)
            else:
                # Classification 3: Partially Met
                p_ratio = min(1.0, demonstrated / required_level)
                verification_mult = 0.85 if item["is_unverified"] else 1.0
                earned_contribution = w * p_ratio * verification_mult
                earned_weight += earned_contribution

                gap = max(1, required_level - demonstrated) if demonstrated < required_level else 1
                priority = classify_gap_priority(gap, w)

                reason_clauses = []
                if demonstrated < required_level:
                    reason_clauses.append(
                        f"Current proficiency '{item['proficiency']}' (Level {item['user_level']}) is below required '{req_level_label}' (Level {required_level})"
                    )
                if item["is_unverified"]:
                    reason_clauses.append("Candidate skill mention from resume is unverified")

                partial_item = {
                    "skill_name": req,
                    "classification": "partially_met",
                    "status": "Partial match",
                    "weight": w,
                    "importance_weight": w,
                    "required_proficiency": req_level_label,
                    "required_level": required_level,
                    "current_proficiency": item["proficiency"],
                    "current_level": item["user_level"],
                    "demonstrated_level": demonstrated,
                    "gap": gap,
                    "priority": priority,
                    "source": item["source"],
                    "verified": item["verified"],
                    "evidence": item["evidence"],
                    "reason": ". ".join(reason_clauses) + "."
                }
                partially_met_skills.append(partial_item)
                all_gaps.append(partial_item)

    # Calculate skill coverage ratio
    coverage = (earned_weight / total_weight) if total_weight > 0 else 0.0

    # Experience alignment factor (bounded between 0.70 and 1.05)
    exp_delta = employee_exp_years - role_exp_years
    if exp_delta >= 0:
        exp_factor = min(1.05, 1.0 + (exp_delta * 0.015))
    else:
        exp_factor = max(0.70, 1.0 + (exp_delta * 0.06))

    composite_score = round(min(100.0, coverage * exp_factor * 100.0), 1)
    coverage_pct = round(coverage * 100.0, 1)

    # Mobility status
    if composite_score >= 80.0:
        mobility_status = "Ready for Internal Transition"
    elif composite_score >= 60.0:
        mobility_status = "Potential Internal Candidate"
    else:
        mobility_status = "Needs Upskilling"

    # Sort gaps by priority: Critical -> High -> Medium -> Low
    priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "None": 4}
    all_gaps.sort(key=lambda g: (priority_order.get(g["priority"], 99), -g["weight"], g["skill_name"]))

    # Legacy compatibility list of matched skills
    matched_skills = met_skills + partially_met_skills

    # Explainability breakdown narrative
    unverified_count = sum(1 for m in partially_met_skills if m.get("source") == "resume_extracted" and not m.get("verified"))
    explanation = {
        "formula": "Score = min(100.0, (Earned_Weight / Total_Weight) * Exp_Factor * 100.0)",
        "scoring_formula": "Score = min(100.0, (Earned_Weight / Total_Weight) * Exp_Factor * 100.0)",
        "earned_weight": round(earned_weight, 2),
        "total_weight": round(total_weight, 2),
        "raw_coverage_pct": coverage_pct,
        "experience_delta_years": exp_delta,
        "experience_factor": round(exp_factor, 3),
        "met_skills_count": len(met_skills),
        "partially_met_skills_count": len(partially_met_skills),
        "missing_skills_count": len(missing_skills),
        "unverified_skills_discounted": unverified_count,
        "summary": (
            f"Match score of {composite_score}% derived from {len(met_skills)} fully met skills, "
            f"{len(partially_met_skills)} partially met skills, and {len(missing_skills)} missing skills. "
            f"Experience alignment ({'+' if exp_delta >= 0 else ''}{exp_delta} yrs) adjusted score by {round(exp_factor, 2)}x."
            + (f" Note: {unverified_count} unverified resume mentions received a 15% discount until verified." if unverified_count > 0 else "")
        )
    }

    return {
        "match_score": composite_score,
        "coverage_percentage": coverage_pct,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "met_skills": met_skills,
        "partially_met_skills": partially_met_skills,
        "matched_count": len(matched_skills),
        "missing_count": len(missing_skills),
        "met_count": len(met_skills),
        "partially_met_count": len(partially_met_skills),
        "total_required": len(role_required_skills),
        "experience_delta": exp_delta,
        "mobility_status": mobility_status,
        "gaps": all_gaps,
        "explanation": explanation
    }
