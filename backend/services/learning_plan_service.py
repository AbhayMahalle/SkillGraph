"""
Learning Plan Service for SkillGraph.
Coordinates prerequisite-aware personalized curriculum generation using
deterministic topological sorting and optional external LLM coaching enrichment.
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.ml.learning_path import LearningPathGenerator
from backend.ml.role_matching import calculate_role_match
from backend.services.llm_service import LLMService
from backend.models.models import Employee, Role, AILearningPlan, EmployeeCourse

learning_path_generator = LearningPathGenerator()
llm_service = LLMService()

def generate_learning_roadmap_for_employee(
    emp: Employee,
    role: Role,
    db: Session,
    use_ai: bool = False
) -> Dict[str, Any]:
    """
    Generates a personalized, prerequisite-respecting roadmap for an employee targeting a role.
    If use_ai=True and LLM credentials are configured, enhances the roadmap with an AI coaching plan.
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
    req_skills = [rs.skill.name for rs in role.required_skills if rs.skill]
    weights = {rs.skill.name: rs.importance_weight for rs in role.required_skills if rs.skill}

    db_courses = db.query(EmployeeCourse).filter(EmployeeCourse.employee_id == emp.employee_id).all()
    completed_courses = [c.course_id for c in db_courses if c.status == "completed"]
    course_progress_map = {
        c.course_id: {"status": c.status, "progress_pct": c.progress_pct or 0}
        for c in db_courses
    }

    # 1. Generate core deterministic topological roadmap
    roadmap = learning_path_generator.generate_personalized_roadmap(
        employee_skills=emp_skills,
        employee_exp_years=emp.experience_years,
        role_required_skills=req_skills,
        role_exp_years=role.experience_years,
        role_skill_weights=weights,
        target_role_id=role.role_id,
        target_role_title=role.title,
        target_role_department=role.department,
        completed_course_ids=completed_courses,
        course_progress_map=course_progress_map
    )

    ai_plan_data = None
    # 2. If AI plan requested and LLM is configured, generate LLM coaching roadmap
    if use_ai and llm_service.is_configured():
        match_result = calculate_role_match(
            employee_skills=emp_skills,
            employee_exp_years=emp.experience_years,
            role_required_skills=req_skills,
            role_exp_years=role.experience_years,
            role_skill_weights=weights
        )
        try:
            ai_plan = llm_service.generate_personalized_learning_plan(
                employee_name=emp.name,
                current_role=emp.current_role,
                exp_years=emp.experience_years,
                target_role_id=role.role_id,
                current_skills=emp_skills,
                skill_gaps=match_result.get("gaps", []),
                completed_course_ids=completed_courses
            )
            ai_plan_data = ai_plan.model_dump()
            model_info = llm_service.provider.get_model_info()

            # Persist in ai_learning_plans table
            plan_record = AILearningPlan(
                employee_id=emp.employee_id,
                target_role_id=role.role_id,
                plan_json=json.dumps(ai_plan_data),
                provider=model_info.get("provider"),
                model=model_info.get("model"),
                created_at=datetime.utcnow().isoformat()
            )
            db.add(plan_record)
            db.commit()
        except Exception as e:
            ai_plan_data = {"error": str(e), "fallback": "Deterministic DAG roadmap provided."}

    roadmap["ai_plan"] = ai_plan_data
    roadmap["ai_available"] = llm_service.is_configured()
    return roadmap

