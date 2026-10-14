"""
Automated Test Suite for SkillGraph — Phase 1: Foundation & Audit Verification.
Tests skill normalization, NLP extraction, role matching, topological DAGs,
readiness prediction, health check, router registrations, database integrity,
catalog counts, database initialization idempotency, and missing model fallback.
"""

import os
import json
import pytest
import sqlite3
import networkx as nx
from fastapi.testclient import TestClient

from backend.main import app
from backend.database.db import REPO_ROOT, DEFAULT_DB_PATH, engine, SessionLocal
from backend.database.init_db import seed_database
from backend.models.models import Skill, Role, Course
from backend.ml.skill_extraction import skill_extractor, normalize_skill_name
from backend.ml.role_matching import calculate_role_match
from backend.ml.readiness import readiness_predictor, ReadinessPredictor
from backend.ml.learning_path import learning_path_generator

client = TestClient(app)

# ---------------------------------------------------------
# 1. Existing Preserved ML & Algorithm Tests
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# 2. Phase 1 Foundation & System Verification Tests
# ---------------------------------------------------------
def test_health_endpoint():
    """Verify health endpoint responds successfully with service info."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["service"] == "SkillGraph API"
    assert data["version"] == "1.0.0"

def test_router_registration_and_no_hr_endpoints():
    """Verify intended self-service endpoints exist and HR endpoints are removed."""
    paths = set(app.openapi().get("paths", {}).keys())
    
    # Self-service career development endpoints must exist
    assert "/api/health" in paths
    assert "/api/auth/demo-login" in paths
    assert "/api/roles" in paths
    assert "/api/roles/recommendations" in paths
    assert "/api/roles/{role_id}" in paths
    assert "/api/employees/profile" in paths
    assert "/api/analysis/skill-gap/{role_id}" in paths
    assert "/api/analysis/learning-path/{role_id}" in paths
    assert "/api/analysis/what-if" in paths
    assert "/api/graph/data" in paths
    assert "/api/datasets/summary" in paths

    # HR administrative endpoints must be removed
    assert "/api/hr/analytics" not in paths
    assert "/api/hr/talent-pool" not in paths
    assert "/api/hr/candidates-for-role/{role_id}" not in paths

def test_database_configuration_and_path():
    """Verify database configuration resolves reliably to the existing SQLite database."""
    assert DEFAULT_DB_PATH.exists(), f"Database file does not exist at {DEFAULT_DB_PATH}"
    assert DEFAULT_DB_PATH.is_file()
    
    # Verify tables can be queried
    conn = sqlite3.connect(str(DEFAULT_DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall()]
    conn.close()

    assert "skills" in tables
    assert "roles" in tables
    assert "courses" in tables
    assert "users" in tables

def test_catalog_integrity():
    """Verify catalogs match expected numbers: 119 skills, 96 roles, 18 courses."""
    session = SessionLocal()
    try:
        skill_count = session.query(Skill).count()
        role_count = session.query(Role).count()
        course_count = session.query(Course).count()

        assert skill_count == 119, f"Expected 119 skills, found {skill_count}"
        assert role_count == 96, f"Expected 96 roles, found {role_count}"
        assert course_count == 18, f"Expected 18 courses, found {course_count}"
    finally:
        session.close()

    # Also verify source JSON catalog counts
    skills_json = REPO_ROOT / "data" / "processed" / "canonical_skills.json"
    roles_json = REPO_ROOT / "data" / "processed" / "canonical_roles.json"
    courses_json = REPO_ROOT / "data" / "processed" / "course_catalog.json"

    with open(skills_json, "r", encoding="utf-8") as f:
        assert len(json.load(f)) == 119

    with open(roles_json, "r", encoding="utf-8") as f:
        assert len(json.load(f)) == 96

    with open(courses_json, "r", encoding="utf-8") as f:
        assert len(json.load(f)) == 18

def test_database_initialization_idempotency():
    """Verify seed_database() is non-destructive and preserves existing records."""
    session = SessionLocal()
    try:
        skills_before = session.query(Skill).count()
        roles_before = session.query(Role).count()
        courses_before = session.query(Course).count()
    finally:
        session.close()

    # Run seeder again
    seed_database()

    session = SessionLocal()
    try:
        assert session.query(Skill).count() == skills_before
        assert session.query(Role).count() == roles_before
        assert session.query(Course).count() == courses_before
    finally:
        session.close()

def test_missing_model_graceful_fallback():
    """Verify ReadinessPredictor gracefully falls back to formula when model file is missing."""
    dummy_predictor = ReadinessPredictor(model_path="non_existent_model_artifact.joblib")
    assert dummy_predictor.model is None
    assert dummy_predictor.scaler is None

    score = dummy_predictor.predict_readiness(
        skill_match_ratio=0.75,
        core_skill_coverage=0.70,
        exp_delta=1,
        education_alignment=0.85,
        prerequisite_readiness=0.80
    )
    assert 0.05 <= score <= 0.98

    transition = dummy_predictor.evaluate_transition(
        current_match_score=60.0,
        missing_skills_count=2,
        total_skills_count=6,
        exp_delta=0
    )
    assert 0.0 <= transition["current_readiness_pct"] <= 100.0
    assert 0.0 <= transition["projected_readiness_pct"] <= 100.0
    assert "transition_verdict" in transition
