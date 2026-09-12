"""
Multi-Factor Role Matching & Skill Gap Engine.
Compares employee profiles against organizational target roles to calculate
skill coverage, weighted compatibility, proficiency gaps, and talent mobility status.
"""

from typing import List, Dict, Any

PROFICIENCY_WEIGHTS = {
    "Expert": 1.0,
    "Advanced": 0.90,
    "Intermediate": 0.75,
    "Beginner": 0.50
}

def calculate_role_match(
    employee_skills: List[Dict[str, Any]],
    employee_exp_years: int,
    role_required_skills: List[str],
    role_exp_years: int,
    role_skill_weights: Dict[str, float] = None
) -> Dict[str, Any]:
    """
    Computes rigorous multi-factor match percentage and categorized skill gaps.
    """
    if not role_required_skills:
        return {
            "match_score": 100.0,
            "coverage_percentage": 100.0,
            "matched_skills": [],
            "missing_skills": [],
            "mobility_status": "Ready for Internal Transition"
        }

    emp_skill_map = {}
    for s in employee_skills:
        name = s.get("name") or s.get("skill_name")
        prof = s.get("proficiency", "Intermediate")
        if name:
            emp_skill_map[name.lower()] = prof

    total_weight = 0.0
    earned_weight = 0.0
    matched_skills = []
    missing_skills = []

    for req in role_required_skills:
        w = role_skill_weights.get(req, 1.0) if role_skill_weights else 1.0
        total_weight += w

        req_lower = req.lower()
        if req_lower in emp_skill_map:
            prof = emp_skill_map[req_lower]
            p_factor = PROFICIENCY_WEIGHTS.get(prof, 0.75)
            earned_weight += (w * p_factor)
            matched_skills.append({
                "skill_name": req,
                "proficiency": prof,
                "weight": w,
                "status": "Strong match" if p_factor >= 0.90 else "Partial match"
            })
        else:
            missing_skills.append({
                "skill_name": req,
                "weight": w,
                "status": "Missing"
            })

    coverage = (earned_weight / total_weight) if total_weight > 0 else 0.0

    # Experience compatibility factor (range 0.65 to 1.10)
    exp_delta = employee_exp_years - role_exp_years
    if exp_delta >= 0:
        exp_factor = min(1.05, 1.0 + (exp_delta * 0.02))
    else:
        exp_factor = max(0.70, 1.0 + (exp_delta * 0.08))

    composite_score = round(min(100.0, coverage * exp_factor * 100.0), 1)
    coverage_pct = round(coverage * 100.0, 1)

    if composite_score >= 80.0:
        status = "Ready for Internal Transition"
    elif composite_score >= 60.0:
        status = "Potential Internal Candidate"
    else:
        status = "Needs Upskilling"

    return {
        "match_score": composite_score,
        "coverage_percentage": coverage_pct,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "matched_count": len(matched_skills),
        "missing_count": len(missing_skills),
        "total_required": len(role_required_skills),
        "experience_delta": exp_delta,
        "mobility_status": status
    }
