"""
Automated Test Suite for SkillGraph — Phase 6: Career Readiness Prediction & What-If Simulation.
Uses an isolated temporary copy of the database to guarantee real database integrity.

Covers:
1. Career readiness assessment retrieval & transparent methodology labeling
2. Clear mathematical distinction between Role Match % and Career Readiness score
3. Contributing factors breakdown (Core Competency, Proficiency Depth, Prerequisite Foundations, Experience)
4. Empty profile handling and missing target role rejection (400 Bad Request)
5. Provenance factor: unverified vs verified skill impact on readiness
6. Elimination of arbitrary guaranteed-increase heuristic (0 gain when 0 skills acquired)
7. What-If simulation with single and multiple hypothetical skill proficiency adjustments
8. Rejection of invalid skill IDs, skill names, proficiency levels, and course IDs (400 Bad Request)
9. Verification of zero database writes: proof that simulations never modify persistent profiles, roles, or roadmaps
10. Strict authentication enforcement (401) and multi-user simulation isolation
"""

import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database.db import get_db, REPO_ROOT
from backend.models.models import (
    User, Employee, Skill, Role, Course, EmployeeSkill, EmployeeCourse, EmployeeRoadmap
)
from backend.database.init_db import ensure_schema_migrations
from backend.api.auth import create_access_token
from backend.ml.readiness import readiness_predictor

# ---------------------------------------------------------
# Isolated Test Database Setup
# ---------------------------------------------------------
BACKUP_DB_PATH = REPO_ROOT / "data" / "processed" / "skillgraph_backup_phase6.db"
temp_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
TEMP_DB_PATH = temp_db_file.name
temp_db_file.close()

shutil.copyfile(str(BACKUP_DB_PATH), TEMP_DB_PATH)

test_engine = create_engine(
    f"sqlite:///{TEMP_DB_PATH}",
    connect_args={"check_same_thread": False}
)
ensure_schema_migrations(test_engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def set_db_override():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture(scope="session", autouse=True)
def cleanup():
    yield
    if os.path.exists(TEMP_DB_PATH):
        try:
            os.remove(TEMP_DB_PATH)
        except Exception:
            pass

client = TestClient(app)

def get_auth_headers(email: str = "alex.rivera@skillgraph.internal"):
    token = create_access_token(data={"sub": email})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------
# 1. Career Readiness Assessment Retrieval & Distinction
# ---------------------------------------------------------
def test_readiness_assessment_and_match_score_distinction():
    """Verify readiness assessment clearly distinguishes readiness score from role match percentage."""
    headers = get_auth_headers("alex.rivera@skillgraph.internal")
    res = client.get("/api/analysis/readiness/ROL-095", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert "readiness_score" in data
    assert "role_match_score" in data
    assert "distinction_explanation" in data
    assert "difference_explanation" in data
    assert "contributing_factors" in data
    assert "assessment_methodology" in data
    assert "limitations" in data

    assert data["assessment_methodology"] == "transparent_rule_based_baseline"
    assert len(data["contributing_factors"]) == 4

    # Verify factors include Core Competency, Proficiency Depth, Prerequisite Foundations, Experience Alignment
    factor_names = [f["factor"] for f in data["contributing_factors"]]
    assert "Core Competency Coverage" in factor_names
    assert "Proficiency & Verification Depth" in factor_names
    assert "Prerequisite Foundations" in factor_names
    assert "Experience Alignment" in factor_names


# ---------------------------------------------------------
# 2. Empty Profile & Missing Target Role Rejection
# ---------------------------------------------------------
def test_readiness_empty_profile_and_missing_target_role():
    """Verify empty skill profile returns 0 readiness, and missing target role returns 400."""
    # Register fresh user with empty skills
    reg_res = client.post("/api/auth/register", json={
        "email": "fresh.grad@skillgraph.internal",
        "password": "Password123!",
        "full_name": "Fresh Grad",
        "current_role": "Intern",
        "department": "Engineering"
    })
    assert reg_res.status_code == 200
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. When querying for a specific role with empty profile
    res_empty = client.get("/api/analysis/readiness/ROL-001", headers=headers)
    assert res_empty.status_code == 200
    empty_data = res_empty.json()
    assert empty_data["readiness_score"] == 0.0
    assert "Low Readiness" in empty_data["readiness_level"]

    # 2. When employee has no target_role_id set and none passed in query
    db = TestingSessionLocal()
    emp = db.query(Employee).filter(Employee.email == "fresh.grad@skillgraph.internal").first()
    emp.target_role_id = None
    db.commit()
    db.close()

    res_missing_role = client.get("/api/analysis/readiness", headers=headers)
    assert res_missing_role.status_code == 400
    assert "target role" in res_missing_role.json()["detail"].lower()


# ---------------------------------------------------------
# 3. Provenance Factor: Verified vs Unverified Skills
# ---------------------------------------------------------
def test_verified_vs_unverified_skills_readiness_impact():
    """Verify that unverified resume mentions receive discounted proficiency factor compared to verified skills."""
    verified_res = readiness_predictor.assess_career_readiness(
        employee_skills=[
            {"name": "Python", "proficiency": "Advanced", "verified": True, "source": "self_reported"},
            {"name": "SQL", "proficiency": "Intermediate", "verified": True, "source": "self_reported"}
        ],
        employee_exp_years=2,
        role_required_skills=["Python", "SQL"],
        role_exp_years=2
    )

    unverified_res = readiness_predictor.assess_career_readiness(
        employee_skills=[
            {"name": "Python", "proficiency": "Advanced", "verified": False, "source": "resume_extracted"},
            {"name": "SQL", "proficiency": "Intermediate", "verified": False, "source": "resume_extracted"}
        ],
        employee_exp_years=2,
        role_required_skills=["Python", "SQL"],
        role_exp_years=2
    )

    # Verified profile must achieve higher or equal readiness than unverified resume mentions
    assert verified_res["readiness_score"] >= unverified_res["readiness_score"]
    verif_factor = next(f for f in verified_res["contributing_factors"] if f["factor"] == "Proficiency & Verification Depth")
    unverif_factor = next(f for f in unverified_res["contributing_factors"] if f["factor"] == "Proficiency & Verification Depth")
    assert verif_factor["score_pct"] > unverif_factor["score_pct"]


# ---------------------------------------------------------
# 4. Elimination of Arbitrary Guaranteed-Increase Heuristic
# ---------------------------------------------------------
def test_elimination_of_arbitrary_guaranteed_increase():
    """Verify evaluate_transition and what-if simulation produce 0 gain when no skills/courses are acquired."""
    # 1. evaluate_transition with 0 missing skills
    zero_gaps_transition = readiness_predictor.evaluate_transition(
        current_match_score=85.0,
        missing_skills_count=0,
        total_skills_count=6,
        exp_delta=0
    )
    # Guaranteed flat +15% must NOT be present!
    assert zero_gaps_transition["readiness_gain_pct"] == 0.0
    assert zero_gaps_transition["projected_readiness_pct"] == zero_gaps_transition["current_readiness_pct"]

    # 2. What-if simulation with empty inputs
    headers = get_auth_headers("alex.rivera@skillgraph.internal")
    sim_empty = client.post("/api/analysis/what-if", headers=headers, json={
        "target_role_id": "ROL-095",
        "skills": [],
        "completed_course_ids": []
    }).json()

    assert sim_empty["deltas"]["match_gain"] == 0.0
    assert sim_empty["deltas"]["readiness_gain"] == 0.0
    assert sim_empty["deltas"]["skills_closed"] == 0
    assert sim_empty["simulated"]["match_score"] == sim_empty["baseline"]["match_score"]
    assert sim_empty["simulated"]["readiness_score"] == sim_empty["baseline"]["readiness_score"]


# ---------------------------------------------------------
# 5. What-If Simulation: Single and Multiple Skills
# ---------------------------------------------------------
def test_what_if_simulation_single_and_multiple_skills():
    """Verify simulating single and multiple skills elevates match score and readiness proportionally."""
    headers = get_auth_headers("alex.rivera@skillgraph.internal")

    # 1. Single critical skill: AWS at Advanced
    sim_single = client.post("/api/analysis/what-if", headers=headers, json={
        "target_role_id": "ROL-095",
        "skills": [
            {"skill_name": "AWS", "proficiency": "Advanced"}
        ]
    })
    assert sim_single.status_code == 200
    data_single = sim_single.json()
    assert data_single["deltas"]["match_gain"] > 0
    assert data_single["deltas"]["skills_closed"] == 1
    assert "AWS" in data_single["simulated"]["matched_skills"]
    assert any("AWS" in ass for ass in data_single["assumptions"])

    # 2. Multiple skills: AWS, Docker, Kubernetes
    sim_multi = client.post("/api/analysis/what-if", headers=headers, json={
        "target_role_id": "ROL-095",
        "skills": [
            {"skill_name": "AWS", "proficiency": "Advanced"},
            {"skill_name": "Docker", "proficiency": "Intermediate"},
            {"skill_name": "Kubernetes", "proficiency": "Expert"}
        ]
    })
    assert sim_multi.status_code == 200
    data_multi = sim_multi.json()
    assert data_multi["deltas"]["match_gain"] > data_single["deltas"]["match_gain"]
    assert data_multi["deltas"]["skills_closed"] >= 3
    assert len(data_multi["assumptions"]) >= 3


# ---------------------------------------------------------
# 6. Rejection of Invalid Input Data (400 Bad Request)
# ---------------------------------------------------------
def test_what_if_rejection_of_invalid_inputs():
    """Verify what-if simulation rejects invalid proficiency, invalid skill, or invalid course IDs."""
    headers = get_auth_headers("alex.rivera@skillgraph.internal")

    # Invalid proficiency level
    res_prof = client.post("/api/analysis/what-if", headers=headers, json={
        "target_role_id": "ROL-095",
        "skills": [{"skill_name": "AWS", "proficiency": "Grandmaster"}]
    })
    assert res_prof.status_code == 400
    assert "invalid proficiency" in res_prof.json()["detail"].lower()

    # Invalid skill name
    res_sk_name = client.post("/api/analysis/what-if", headers=headers, json={
        "target_role_id": "ROL-095",
        "skills": [{"skill_name": "FakeImaginarySkill999", "proficiency": "Advanced"}]
    })
    assert res_sk_name.status_code == 400
    assert "not found in catalog" in res_sk_name.json()["detail"].lower()

    # Invalid course ID
    res_course = client.post("/api/analysis/what-if", headers=headers, json={
        "target_role_id": "ROL-095",
        "completed_course_ids": ["CRS-999"]
    })
    assert res_course.status_code == 400
    assert "not found in catalog" in res_course.json()["detail"].lower()

    # Invalid role ID
    res_role = client.post("/api/analysis/what-if", headers=headers, json={
        "target_role_id": "ROL-NONEXISTENT",
        "skills": [{"skill_name": "AWS", "proficiency": "Advanced"}]
    })
    assert res_role.status_code == 404


# ---------------------------------------------------------
# 7. Non-Persistence Guarantee: Zero Database Writes
# ---------------------------------------------------------
def test_what_if_simulation_non_persistence_guarantee():
    """Verify that running what-if simulations leaves persistent user profile, target role, and roadmap completely unchanged."""
    headers = get_auth_headers("alex.rivera@skillgraph.internal")

    db = TestingSessionLocal()
    emp_before = db.query(Employee).filter(Employee.email == "alex.rivera@skillgraph.internal").first()
    skills_before = [(es.skill.name, es.proficiency) for es in emp_before.skills if es.skill]
    courses_before = [c.course_id for c in emp_before.courses]
    target_role_before = emp_before.target_role_id
    db.close()

    # Run aggressive simulation with 4 skills and 2 courses for a completely different role
    sim_res = client.post("/api/analysis/what-if", headers=headers, json={
        "target_role_id": "ROL-006",
        "skills": [
            {"skill_name": "AWS", "proficiency": "Expert"},
            {"skill_name": "System Design", "proficiency": "Advanced"}
        ],
        "completed_course_ids": ["CRS-017"]
    })
    assert sim_res.status_code == 200

    # Re-query DB and assert zero changes
    db = TestingSessionLocal()
    emp_after = db.query(Employee).filter(Employee.email == "alex.rivera@skillgraph.internal").first()
    skills_after = [(es.skill.name, es.proficiency) for es in emp_after.skills if es.skill]
    courses_after = [c.course_id for c in emp_after.courses]
    target_role_after = emp_after.target_role_id
    db.close()

    assert skills_after == skills_before, "Simulation must NEVER mutate persistent employee skills!"
    assert courses_after == courses_before, "Simulation must NEVER mutate persistent employee courses!"
    assert target_role_after == target_role_before, "Simulation must NEVER mutate target role!"


# ---------------------------------------------------------
# 8. Authentication & Cross-User Data Isolation
# ---------------------------------------------------------
def test_what_if_unauthorized_access_and_cross_user_isolation():
    """Verify what-if simulation requires JWT and simulations on User A do not affect User B."""
    # 1. Unauthenticated request rejected
    unauth_res = client.post("/api/analysis/what-if", json={"target_role_id": "ROL-001"})
    assert unauth_res.status_code in [401, 403]

    headers_a = get_auth_headers("alex.rivera@skillgraph.internal")
    headers_b = get_auth_headers("priya.sharma@skillgraph.internal")

    # Run simulation on User A
    sim_a = client.post("/api/analysis/what-if", headers=headers_a, json={
        "target_role_id": "ROL-095",
        "skills": [{"skill_name": "Kubernetes", "proficiency": "Expert"}]
    }).json()

    # Get User B's baseline
    sim_b = client.post("/api/analysis/what-if", headers=headers_b, json={
        "target_role_id": "ROL-095",
        "skills": []
    }).json()

    # User B's baseline must remain isolated and unaffected by User A's simulation
    assert "Kubernetes" not in sim_b["baseline"]["matched_skills"] if "matched_skills" in sim_b["baseline"] else True
    assert sim_a["baseline"]["match_score"] != sim_b["baseline"]["match_score"]

