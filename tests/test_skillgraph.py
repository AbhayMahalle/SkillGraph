"""
Automated Test Suite for SkillGraph.
Tests skill normalization, role matching, topological learning path DAGs,
ML transition readiness prediction, and NLP resume skill parsing.
"""

import pytest
import networkx as nx
from backend.ml.skill_extraction import skill_extractor, normalize_skill_name
from backend.ml.role_matching import calculate_role_match
from backend.ml.readiness import readiness_predictor
from backend.ml.learning_path import learning_path_generator

def test_skill_normalization():
    assert normalize_skill_name("python 3") == "Python"
    assert normalize_skill_name("python programming") == "Python"
    assert normalize_skill_name("react.js") == "React"
    assert normalize_skill_name("reactjs") == "React"
    assert normalize_skill_name("k8s") == "Kubernetes"
    assert normalize_skill_name("aws") == "AWS"
    assert normalize_skill_name("postgres") == "PostgreSQL"
    assert normalize_skill_name("ml") == "Machine Learning"

def test_nlp_skill_extraction():
    text = "Full stack engineer experienced in Python, React, Docker, and AWS cloud infrastructure."
    skills = skill_extractor.extract_skills_from_text(text)
    extracted_names = [s["skill_name"] for s in skills]
    assert "Python" in extracted_names
    assert "React" in extracted_names
    assert "Docker" in extracted_names
    assert "AWS" in extracted_names

def test_role_matching_calculation():
    emp_skills = [
        {"name": "Python", "proficiency": "Advanced"},
        {"name": "SQL", "proficiency": "Intermediate"}
    ]
    req_skills = ["Python", "SQL", "AWS", "Kubernetes"]
    
    result = calculate_role_match(
        employee_skills=emp_skills,
        employee_exp_years=3,
        role_required_skills=req_skills,
        role_exp_years=3
    )

    assert 0.0 <= result["match_score"] <= 100.0
    assert result["matched_count"] == 2
    assert result["missing_count"] == 2
    assert result["mobility_status"] in ["Ready for Internal Transition", "Potential Internal Candidate", "Needs Upskilling"]

def test_topological_dag_properties():
    assert nx.is_directed_acyclic_graph(learning_path_generator.dag), "Course prerequisite graph must be a strict DAG"
    
    path = learning_path_generator.generate_path(
        missing_skills=["Kubernetes", "AWS"],
        completed_course_ids=[]
    )
    milestones = path["milestones"]
    course_order = [m["course_id"] for m in milestones]
    
    # If Docker (CRS-007) and Kubernetes (CRS-008) are both in roadmap, CRS-007 must precede CRS-008
    if "CRS-007" in course_order and "CRS-008" in course_order:
        assert course_order.index("CRS-007") < course_order.index("CRS-008")

def test_readiness_prediction_monotonicity():
    res = readiness_predictor.evaluate_transition(
        current_match_score=40.0,
        missing_skills_count=4,
        total_skills_count=8,
        exp_delta=0
    )
    assert 0.0 <= res["current_readiness_pct"] <= 100.0
    assert 0.0 <= res["projected_readiness_pct"] <= 100.0
    assert res["projected_readiness_pct"] >= res["current_readiness_pct"]
    assert "transition_verdict" in res
