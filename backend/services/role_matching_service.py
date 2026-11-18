"""
Role Matching & Compatibility Service for SkillGraph.
Coordinates multi-factor deterministic role matching and ML-assisted transition analysis.
"""

from typing import Dict, Any, List, Optional
from backend.ml.role_matching import calculate_role_match
from backend.models.models import Role, Employee

def evaluate_role_compatibility(
    emp: Employee,
    role: Role,
    hypothetical_skills: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Evaluates compatibility between employee and a target career role.
    Supports hypothetical what-if skills for career sandboxing.
    """
    emp_skills = [
        {
            "name": es.skill.name if es.skill else "",
            "proficiency": es.proficiency,
            "source": es.source or "self_reported",
            "verified": es.verified,
            "evidence": es.evidence
        }
        for es in emp.skills if es.skill
    ]

    # Incorporate hypothetical skills if supplied
    if hypothetical_skills:
        existing_names = {s["name"].lower() for s in emp_skills}
        for h in hypothetical_skills:
            h_name = h.get("name") or h.get("skill_name") or ""
            if h_name:
                h_clean = {
                    "name": h_name,
                    "proficiency": h.get("proficiency", "Intermediate"),
                    "source": "hypothetical",
                    "verified": True,
                    "evidence": "Hypothetical career simulation"
                }
                if h_name.lower() in existing_names:
                    # Update existing proficiency
                    for idx, s in enumerate(emp_skills):
                        if s["name"].lower() == h_name.lower():
                            emp_skills[idx] = h_clean
                else:
                    emp_skills.append(h_clean)

    req_skills = [rs.skill.name for rs in role.required_skills if rs.skill]
    weights = {rs.skill.name: rs.importance_weight for rs in role.required_skills if rs.skill}

    match_result = calculate_role_match(
        employee_skills=emp_skills,
        employee_exp_years=emp.experience_years,
        role_required_skills=req_skills,
        role_exp_years=role.experience_years,
        role_skill_weights=weights
    )

    return match_result
