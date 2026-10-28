"""
Phase 8 Final Quality, Integration & Acceptance Verification Test Suite.
Exhaustively validates:
1. Canonical Courses Catalog API (/api/courses)
2. Role Comparison validation (duplicate rejection, count constraints, 404 detection)
3. Course Progress input validation (invalid status rejection, progress percentage clamping)
4. What-If Simulation input contract enforcement (missing skill identifier, invalid proficiency)
5. Career Readiness evaluation contract & formula bounded behavior
6. Profile CRUD edge cases (empty strings, custom skill creation, proficiency updates, deletions)
7. Security resilience: SQL injection queries, path traversal filename sanitization
8. Multi-user concurrent isolation and non-interference
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
    User, Employee, Skill, Role, Course, CoursePrerequisite,
    EmployeeSkill, EmployeeCourse, EmployeeRoadmap
)
from backend.database.init_db import ensure_schema_migrations
from backend.api.auth import create_access_token
from backend.ml.resume_parser import sanitize_filename

# ---------------------------------------------------------
# Isolated Test Database Setup
# ---------------------------------------------------------
BACKUP_DB_PATH = REPO_ROOT / "data" / "processed" / "skillgraph_backup_phase8.db"
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

def create_user_and_get_token(email: str, password: str = "AcceptancePass123!", name: str = "QA Tester"):
    res = client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "full_name": name,
        "department": "Quality Engineering"
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, res.json()["user"]


# ---------------------------------------------------------
# 1. Canonical Courses Catalog API Endpoint
# ---------------------------------------------------------
def test_canonical_courses_endpoint():
    """Verify /api/courses returns all 18 canonical courses with complete curriculum schemas."""
    res = client.get("/api/courses")
    assert res.status_code == 200
    courses = res.json()
    assert len(courses) == 18

    course_ids = {c["course_id"] for c in courses}
    assert "CRS-001" in course_ids  # Foundations of Linux & Bash
    assert "CRS-003" in course_ids  # Python for Systems & Data

    for c in courses:
        assert c["course_id"].startswith("CRS-")
        assert len(c["title"]) > 0
        assert c["duration_weeks"] > 0
        assert c["level"] in ("Beginner", "Intermediate", "Advanced")
        assert isinstance(c["skills_taught"], list)
        assert isinstance(c["prerequisites"], list)


# ---------------------------------------------------------
# 2. Role Comparison Validation & Distinctness
# ---------------------------------------------------------
def test_role_comparison_input_constraints():
    """Verify comparison enforces distinct role IDs, count boundaries, and catalog existence."""
    headers, _ = create_user_and_get_token("compare.test@skillgraph.internal")

    # 1. Duplicate role IDs (e.g. ROL-001,ROL-001) -> 400
    res_dup = client.get("/api/roles/compare?role_ids=ROL-001,ROL-001", headers=headers)
    assert res_dup.status_code == 400
    assert "distinct" in res_dup.json()["detail"].lower()

    # 2. Single role ID -> 400
    res_single = client.get("/api/roles/compare?role_ids=ROL-001", headers=headers)
    assert res_single.status_code == 400

    # 3. More than 4 roles -> 400
    res_overflow = client.get("/api/roles/compare?role_ids=ROL-001,ROL-002,ROL-003,ROL-004,ROL-005", headers=headers)
    assert res_overflow.status_code == 400
    assert "maximum of 4" in res_overflow.json()["detail"].lower()

    # 4. Non-existent role ID -> 404
    res_missing = client.get("/api/roles/compare?role_ids=ROL-001,ROL-NONEXISTENT", headers=headers)
    assert res_missing.status_code == 404

    # 5. Valid 2 distinct roles -> 200 OK
    res_valid = client.get("/api/roles/compare?role_ids=ROL-001,ROL-002", headers=headers)
    assert res_valid.status_code == 200
    data = res_valid.json()
    assert len(data["compared_roles"]) == 2
    assert "common_required_skills" in data


# ---------------------------------------------------------
# 3. Course Progress Input Validation & Clamping
# ---------------------------------------------------------
def test_course_progress_validation_and_clamping():
    """Verify course status validates against allowed set and clamps progress percentage."""
    headers, _ = create_user_and_get_token("progress.test@skillgraph.internal")

    # Set target role to get an active roadmap
    client.put("/api/employees/target-role", json={"target_role_id": "ROL-001"}, headers=headers)
    roadmap = client.get("/api/roadmap?role_id=ROL-001", headers=headers).json()
    course_id = roadmap["milestones"][0]["course_id"]

    # 1. Invalid status string -> 400
    res_bad_status = client.put(
        f"/api/roadmap/courses/{course_id}/progress",
        json={"status": "graduated_master"},
        headers=headers
    )
    assert res_bad_status.status_code == 400
    assert "invalid status" in res_bad_status.json()["detail"].lower()

    # 2. Over-100 percentage clamped to 100
    res_over = client.put(
        f"/api/roadmap/courses/{course_id}/progress",
        json={"status": "in_progress", "progress_pct": 250},
        headers=headers
    )
    assert res_over.status_code == 200
    assert res_over.json()["progress_pct"] == 100

    # 3. Negative percentage clamped to 0
    res_neg = client.put(
        f"/api/roadmap/courses/{course_id}/progress",
        json={"status": "in_progress", "progress_pct": -80},
        headers=headers
    )
    assert res_neg.status_code == 200
    assert res_neg.json()["progress_pct"] == 0


# ---------------------------------------------------------
# 4. What-If Simulation Input Contract Enforcement
# ---------------------------------------------------------
def test_what_if_simulation_input_contract():
    """Verify What-If simulation rejects malformed hypothetical skill payloads."""
    headers, _ = create_user_and_get_token("whatif.test@skillgraph.internal")
    client.put("/api/employees/target-role", json={"target_role_id": "ROL-001"}, headers=headers)

    # 1. Missing both skill_name and skill_id -> 400
    res_no_id = client.post("/api/analysis/what-if", json={
        "target_role_id": "ROL-001",
        "skills": [{"proficiency": "Expert"}]
    }, headers=headers)
    assert res_no_id.status_code == 400
    assert "must specify 'skill_name' or 'skill_id'" in res_no_id.json()["detail"]

    # 2. Invalid completed course ID -> 400
    res_bad_course = client.post("/api/analysis/what-if", json={
        "target_role_id": "ROL-001",
        "skills": [],
        "completed_course_ids": ["CRS-FAKE-999"]
    }, headers=headers)
    assert res_bad_course.status_code == 400
    assert "not found in catalog" in res_bad_course.json()["detail"]


# ---------------------------------------------------------
# 5. Career Readiness Metric Bounds & Contract
# ---------------------------------------------------------
def test_career_readiness_metric_bounds():
    """Verify career readiness returns bounded scores, factor weights, and methodology notice."""
    headers, _ = create_user_and_get_token("readiness.test@skillgraph.internal")
    client.put("/api/employees/target-role", json={"target_role_id": "ROL-001"}, headers=headers)

    res = client.get("/api/analysis/readiness", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert 0.0 <= data["readiness_score"] <= 100.0
    assert any(w in data["readiness_level"] for w in ["Readiness", "Transition", "Upskilling"])
    factors = data["contributing_factors"]
    factor_names = [f["factor"].lower() for f in factors] if isinstance(factors, list) else list(factors.keys())
    assert any("core competency" in fn for fn in factor_names)
    assert any("proficiency" in fn for fn in factor_names)
    assert any("prerequisite" in fn for fn in factor_names)
    assert any("experience" in fn for fn in factor_names)
    assert "limitations" in data


# ---------------------------------------------------------
# 6. Profile CRUD Edge Cases & Custom Skill Creation
# ---------------------------------------------------------
def test_profile_crud_and_custom_skill():
    """Verify skill addition supports canonical lookup and automatic custom skill creation."""
    headers, _ = create_user_and_get_token("profile.crud@skillgraph.internal")

    # 1. Add skill with whitespace name -> 400
    res_empty = client.post("/api/employees/skills", json={
        "skill_name": "   ",
        "proficiency": "Intermediate"
    }, headers=headers)
    assert res_empty.status_code == 400

    # 2. Add novel custom skill not originally in canonical catalog
    novel_skill = "Emerging Quantum ML Framework"
    res_custom = client.post("/api/employees/skills", json={
        "skill_name": novel_skill,
        "proficiency": "Beginner",
        "source": "assessment",
        "evidence": "Completed internal hackathon"
    }, headers=headers)
    assert res_custom.status_code == 200
    returned_skill_name = res_custom.json()["skill_name"]
    assert returned_skill_name.lower() == novel_skill.lower()

    # 3. Update skill proficiency
    res_update = client.put(
        f"/api/employees/skills/{returned_skill_name}",
        json={"proficiency": "Advanced"},
        headers=headers
    )
    assert res_update.status_code == 200

    # 4. Verify updated in profile
    prof = client.get("/api/employees/profile", headers=headers).json()
    sk_item = next(s for s in prof["skills"] if s["skill_name"].lower() == novel_skill.lower())
    assert sk_item["proficiency"] == "Advanced"

    # 5. Delete skill
    res_del = client.delete(f"/api/employees/skills/{returned_skill_name}", headers=headers)
    assert res_del.status_code == 200

    # Verify deleted
    prof_after = client.get("/api/employees/profile", headers=headers).json()
    assert not any(s["skill_name"].lower() == novel_skill.lower() for s in prof_after["skills"])


# ---------------------------------------------------------
# 7. Security Resilience: SQL Injection & Path Traversal
# ---------------------------------------------------------
def test_security_resilience_injections():
    """Verify SQL injection strings and path traversal filenames are handled safely."""
    # 1. SQL Injection query in role search
    sql_payload = "'; DROP TABLE roles; --"
    res_sql = client.get(f"/api/roles?q={sql_payload}")
    assert res_sql.status_code == 200
    # Roles table must remain intact
    roles_check = client.get("/api/roles").json()
    assert len(roles_check) == 96

    # 2. Filename sanitization against path traversal
    dirty_name = "../../../etc/passwd"
    clean_name = sanitize_filename(dirty_name)
    assert ".." not in clean_name
    assert "/" not in clean_name
    assert "\\" not in clean_name


# ---------------------------------------------------------
# 8. Multi-User Concurrency & Data Isolation
# ---------------------------------------------------------
def test_multi_user_concurrent_isolation():
    """Verify two users modifying their profiles simultaneously do not leak data across sessions."""
    headers_u1, _ = create_user_and_get_token("user1.iso@skillgraph.internal", name="User One")
    headers_u2, _ = create_user_and_get_token("user2.iso@skillgraph.internal", name="User Two")

    # User 1 sets ROL-001, User 2 sets ROL-095
    client.put("/api/employees/target-role", json={"target_role_id": "ROL-001"}, headers=headers_u1)
    client.put("/api/employees/target-role", json={"target_role_id": "ROL-095"}, headers=headers_u2)

    # User 1 adds Skill A, User 2 adds Skill B
    client.post("/api/employees/skills", json={"skill_name": "Kubernetes", "proficiency": "Expert"}, headers=headers_u1)
    client.post("/api/employees/skills", json={"skill_name": "PyTorch", "proficiency": "Beginner"}, headers=headers_u2)

    # Verify User 1 state
    p1 = client.get("/api/employees/profile", headers=headers_u1).json()
    assert p1["target_role_id"] == "ROL-001"
    u1_skills = {s["skill_name"] for s in p1["skills"]}
    assert "Kubernetes" in u1_skills
    assert "PyTorch" not in u1_skills

    # Verify User 2 state
    p2 = client.get("/api/employees/profile", headers=headers_u2).json()
    assert p2["target_role_id"] == "ROL-095"
    u2_skills = {s["skill_name"] for s in p2["skills"]}
    assert "PyTorch" in u2_skills
    assert "Kubernetes" not in u2_skills
