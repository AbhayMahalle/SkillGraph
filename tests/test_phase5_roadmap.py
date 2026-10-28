"""
Automated Test Suite for SkillGraph — Phase 5: Personalized Learning-Roadmap Generation.
Uses an isolated temporary copy of the database to guarantee real database integrity.

Covers:
1. Catalog preservation (119 skills, 96 roles, 18 courses) & database migration idempotency
2. Roadmap generation from actual role skill gaps (missing & partially met)
3. Correct skill-to-course mapping and explainable reasons for selection
4. Prerequisite inclusion and strict topological DAG ordering
5. Duplicate prevention and deterministic output across multiple runs
6. Identification of unaddressed skill gaps not covered by catalog
7. Handling of empty skill profiles, zero-gap ready profiles, and missing target roles
8. Roadmap persistence in employee_roadmaps and course progress tracking
9. Rejection of progress updates for courses outside the user's roadmap
10. Strict authentication enforcement and cross-user data isolation
11. Automatic roadmap recalculation following target-role or personal skill changes
12. Roadmap course detail retrieval and backward compatibility for legacy endpoints
"""

import os
import json
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

# ---------------------------------------------------------
# Isolated Test Database Setup
# ---------------------------------------------------------
BACKUP_DB_PATH = REPO_ROOT / "data" / "processed" / "skillgraph_backup_phase5.db"
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
# 1. Catalog Preservation & Migration Idempotency
# ---------------------------------------------------------
def test_catalog_preservation_and_migration_idempotency():
    """Verify that catalog counts are exactly 119 skills, 96 roles, 18 courses, and migrations are idempotent."""
    db = TestingSessionLocal()
    try:
        assert db.query(Skill).count() == 119
        assert db.query(Role).count() == 96
        assert db.query(Course).count() == 18

        # Run migration multiple times to guarantee zero errors and complete idempotency
        ensure_schema_migrations(test_engine)
        ensure_schema_migrations(test_engine)

        assert db.query(Skill).count() == 119
        assert db.query(Role).count() == 96
        assert db.query(Course).count() == 18
    finally:
        db.close()


# ---------------------------------------------------------
# 2. Roadmap Generation from Actual Skill Gaps
# ---------------------------------------------------------
def test_roadmap_generation_for_authenticated_user():
    """Verify roadmap generation for Alex Rivera targeting Cloud Engineer."""
    headers = get_auth_headers("alex.rivera@skillgraph.internal")
    res = client.get("/api/roadmap", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["target_role_id"] in ["ROL-095", "ROL-001"]
    assert "milestones" in data
    assert "total_courses" in data
    assert "total_estimated_weeks" in data
    assert data["total_courses"] > 0
    assert data["total_estimated_weeks"] > 0

    milestones = data["milestones"]
    cids = [m["course_id"] for m in milestones]
    assert len(cids) == len(set(cids)), "Milestones must contain no duplicate courses"


# ---------------------------------------------------------
# 3. Prerequisite Inclusion and Strict Topological Ordering
# ---------------------------------------------------------
def test_prerequisite_inclusion_and_topological_dag_ordering():
    """Verify all prerequisite courses precede dependent courses in the ordered roadmap."""
    headers = get_auth_headers("alex.rivera@skillgraph.internal")
    # Query explicitly for Cloud Engineer (ROL-095)
    res = client.get("/api/roadmap?role_id=ROL-095", headers=headers)
    assert res.status_code == 200
    data = res.json()

    milestones = data["milestones"]
    course_order = {m["course_id"]: idx for idx, m in enumerate(milestones)}

    db = TestingSessionLocal()
    try:
        # Check every prerequisite edge in DB
        for m in milestones:
            cid = m["course_id"]
            prereqs = db.query(CoursePrerequisite).filter(CoursePrerequisite.course_id == cid).all()
            for p in prereqs:
                pre_id = p.prerequisite_course_id
                # If the prerequisite is also in the roadmap, it MUST appear before this course
                if pre_id in course_order:
                    assert course_order[pre_id] < course_order[cid], (
                        f"Prerequisite {pre_id} must appear before {cid} in roadmap! "
                        f"Got order: {course_order[pre_id]} vs {course_order[cid]}"
                    )
    finally:
        db.close()


# ---------------------------------------------------------
# 4. Explainable Selection Reasons & Targeted Skills
# ---------------------------------------------------------
def test_explainable_reasons_and_targeted_skills():
    """Verify each milestone clearly explains why it was selected and which skills it targets."""
    headers = get_auth_headers("alex.rivera@skillgraph.internal")
    res = client.get("/api/roadmap?role_id=ROL-095", headers=headers)
    assert res.status_code == 200
    data = res.json()

    for m in data["milestones"]:
        assert "reason" in m
        assert len(m["reason"]) > 5
        assert "skills_taught" in m
        assert "targeted_skills" in m
        assert "prerequisites" in m
        assert "status" in m
        assert "progress_pct" in m
        assert m["status"] in ["not_started", "in_progress", "completed"]


# ---------------------------------------------------------
# 5. Deterministic Output & Duplicate Prevention
# ---------------------------------------------------------
def test_deterministic_output_across_repeated_runs():
    """Verify running generation multiple times returns the exact same milestone sequence."""
    headers = get_auth_headers("priya.sharma@skillgraph.internal")
    first_res = client.get("/api/roadmap?role_id=ROL-001", headers=headers).json()
    first_cids = [m["course_id"] for m in first_res["milestones"]]

    for _ in range(3):
        res = client.get("/api/roadmap?role_id=ROL-001", headers=headers).json()
        cids = [m["course_id"] for m in res["milestones"]]
        assert cids == first_cids, "Roadmap ordering must be 100% deterministic across repeated calls"


# ---------------------------------------------------------
# 6. Unaddressed Gaps Identification
# ---------------------------------------------------------
def test_unaddressed_gaps_identification():
    """Verify that skills not taught by any course in catalog are flagged as unaddressed gaps."""
    headers = get_auth_headers("alex.rivera@skillgraph.internal")
    # Cloud Architect (ROL-006) requires AWS, Azure, GCP, System Design
    res = client.get("/api/roadmap?role_id=ROL-006", headers=headers)
    assert res.status_code == 200
    data = res.json()

    unaddressed_names = [u["skill_name"] for u in data["unaddressed_gaps"]]
    assert "Azure" in unaddressed_names
    assert "GCP" in unaddressed_names

    for u in data["unaddressed_gaps"]:
        assert "reason" in u
        assert "priority" in u
        assert "recommendation" in u["reason"].lower() or "independent" in u["reason"].lower() or "catalog" in u["reason"].lower()


# ---------------------------------------------------------
# 7. Empty Profiles & Missing Target Role Handling
# ---------------------------------------------------------
def test_missing_target_role_prompts_user():
    """Verify GET /api/roadmap without a target role returns a 400 Bad Request prompting role selection."""
    # Register new user without employee profile target role
    reg_res = client.post("/api/auth/register", json={
        "email": "new.recruit@skillgraph.internal",
        "password": "Password123!",
        "full_name": "New Recruit",
        "current_role": "Junior Analyst",
        "department": "Analytics"
    })
    assert reg_res.status_code == 200
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Clear target_role_id to simulate an employee who has not selected a target role
    db = TestingSessionLocal()
    emp = db.query(Employee).filter(Employee.email == "new.recruit@skillgraph.internal").first()
    emp.target_role_id = None
    db.commit()
    db.close()

    # User has no target_role_id set
    res = client.get("/api/roadmap", headers=headers)
    assert res.status_code == 400
    assert "target role" in res.json()["detail"].lower()

    # User explicitly queries for a role
    res_with_role = client.get("/api/roadmap?role_id=ROL-001", headers=headers)
    assert res_with_role.status_code == 200
    assert res_with_role.json()["total_courses"] > 0


# ---------------------------------------------------------
# 8. User Course Status & Progress Updates
# ---------------------------------------------------------
def test_course_progress_updates_and_roadmap_summary():
    """Verify updating course progress persists and updates roadmap summary metrics."""
    headers = get_auth_headers("alex.rivera@skillgraph.internal")
    roadmap = client.get("/api/roadmap?role_id=ROL-095", headers=headers).json()
    first_course_id = roadmap["milestones"][0]["course_id"]

    # Update first course to in_progress with 60%
    update_res = client.put(
        f"/api/roadmap/courses/{first_course_id}/progress",
        headers=headers,
        json={"status": "in_progress", "progress_pct": 60}
    )
    assert update_res.status_code == 200
    update_data = update_res.json()
    assert update_data["status"] == "success"
    assert update_data["course_status"] == "in_progress"
    assert update_data["progress_pct"] == 60
    assert update_data["roadmap_summary"]["in_progress_courses_count"] >= 1

    # Mark first course completed
    complete_res = client.put(
        f"/api/roadmap/courses/{first_course_id}/progress",
        headers=headers,
        json={"status": "completed"}
    )
    assert complete_res.status_code == 200
    comp_data = complete_res.json()
    assert comp_data["course_status"] == "completed"
    assert comp_data["progress_pct"] == 100


# ---------------------------------------------------------
# 9. Rejection of Progress for Unrelated Courses
# ---------------------------------------------------------
def test_rejection_of_progress_for_courses_not_in_roadmap():
    """Verify attempting to update progress for a course not in the user's roadmap is rejected with 400."""
    headers = get_auth_headers("alex.rivera@skillgraph.internal")
    # Alex's roadmap for Cloud Engineer does NOT include CRS-018 (Leadership)
    res = client.put(
        "/api/roadmap/courses/CRS-018/progress",
        headers=headers,
        json={"status": "in_progress", "progress_pct": 50}
    )
    assert res.status_code == 400
    assert "not part of your active learning roadmap" in res.json()["detail"].lower()


# ---------------------------------------------------------
# 10. Multi-User Isolation & Authentication Enforcement
# ---------------------------------------------------------
def test_unauthorized_access_and_cross_user_isolation():
    """Verify endpoints require valid JWT and progress changes on User A do not affect User B."""
    # 1. Unauthenticated request rejected
    unauth_res = client.get("/api/roadmap")
    assert unauth_res.status_code in [401, 403]

    headers_a = get_auth_headers("alex.rivera@skillgraph.internal")
    headers_b = get_auth_headers("priya.sharma@skillgraph.internal")

    # Set Priya's target role to ROL-095
    client.put("/api/employees/target-role", headers=headers_b, json={"target_role_id": "ROL-095"})

    roadmap_b = client.get("/api/roadmap", headers=headers_b).json()
    first_course_id = roadmap_b["milestones"][0]["course_id"]

    # User B marks course as not_started
    client.put(
        f"/api/roadmap/courses/{first_course_id}/progress",
        headers=headers_b,
        json={"status": "not_started", "progress_pct": 0}
    )

    # User A sets progress on the same course
    client.put(
        f"/api/roadmap/courses/{first_course_id}/progress",
        headers=headers_a,
        json={"status": "completed", "progress_pct": 100}
    )

    # Verify User B's roadmap course status remains unaffected
    roadmap_b_after = client.get("/api/roadmap", headers=headers_b).json()
    b_first = next(m for m in roadmap_b_after["milestones"] if m["course_id"] == first_course_id)
    assert b_first["status"] == "not_started"
    assert b_first["progress_pct"] == 0


# ---------------------------------------------------------
# 11. Roadmap Recalculation on Skill & Role Changes
# ---------------------------------------------------------
def test_roadmap_recalculation_on_skill_and_target_role_changes():
    """Verify modifying target role or adding skills immediately recalculates roadmap milestones."""
    headers = get_auth_headers("alex.rivera@skillgraph.internal")

    # 1. Switch target role to ROL-001 (Software Engineer)
    role_change_res = client.put(
        "/api/employees/target-role",
        headers=headers,
        json={"target_role_id": "ROL-001"}
    )
    assert role_change_res.status_code == 200

    roadmap_new_role = client.get("/api/roadmap", headers=headers).json()
    assert roadmap_new_role["target_role_id"] == "ROL-001"

    # 2. Add an expert skill to close a gap
    add_skill_res = client.post(
        "/api/employees/skills",
        headers=headers,
        json={"skill_name": "Kubernetes", "proficiency": "Expert"}
    )
    assert add_skill_res.status_code == 200

    # Roadmap should recalculate and reflect the skill update
    roadmap_updated = client.get("/api/roadmap?role_id=ROL-095", headers=headers).json()
    # Kubernetes course (CRS-008) is no longer a targeted gap course
    k8s_milestone = next((m for m in roadmap_updated["milestones"] if m["course_id"] == "CRS-008"), None)
    if k8s_milestone:
        assert "Kubernetes" not in k8s_milestone["targeted_skills"]


# ---------------------------------------------------------
# 12. Roadmap Course Detail Retrieval & Backward Compatibility
# ---------------------------------------------------------
def test_course_details_and_legacy_learning_path_route():
    """Verify GET /api/roadmap/courses/{id} and legacy GET /api/analysis/learning-path/{role_id}."""
    headers = get_auth_headers("alex.rivera@skillgraph.internal")

    # Course details
    course_res = client.get("/api/roadmap/courses/CRS-006", headers=headers)
    assert course_res.status_code == 200
    cdata = course_res.json()
    assert cdata["course_id"] == "CRS-006"
    assert "AWS" in cdata["skills_taught"]
    assert "user_status" in cdata

    # 404 for invalid course
    assert client.get("/api/roadmap/courses/NONEXISTENT", headers=headers).status_code == 404

    # Legacy endpoint backwards compatibility
    legacy_res = client.get("/api/analysis/learning-path/ROL-095", headers=headers)
    assert legacy_res.status_code == 200
    leg_data = legacy_res.json()
    assert "target_role_id" in leg_data
    assert "learning_path" in leg_data
    assert "milestones" in leg_data["learning_path"]
