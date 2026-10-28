"""
Phase 7 Integration, Quality Assurance & Security Test Suite for SkillGraph.
Validates the complete end-to-end user lifecycle across authentication, profiling,
resume parsing, role matching, topological roadmaps, progress tracking, career readiness,
what-if simulations, cross-user isolation, file upload security, and database integrity.
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

# ---------------------------------------------------------
# Isolated Test Database Setup
# ---------------------------------------------------------
BACKUP_DB_PATH = REPO_ROOT / "data" / "processed" / "skillgraph_backup_phase7.db"
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

def create_user_and_get_token(email: str, password: str = "SecurePass123!", name: str = "Test User"):
    """Helper to register and login a test user, returning auth headers and user payload."""
    res = client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "full_name": name,
        "department": "Engineering"
    })
    assert res.status_code == 200, f"Registration failed: {res.text}"
    data = res.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}, data["user"]


# ---------------------------------------------------------
# 1. Complete End-to-End User Journey
# ---------------------------------------------------------
def test_complete_end_to_end_user_journey():
    """
    Validates complete lifecycle:
    Registration -> Profile Init -> Resume Upload & Staging -> Skill Confirmation ->
    Target Role Selection -> Skill Gap Analysis -> Learning Roadmap -> Progress Tracking ->
    Career Readiness -> What-If Simulation.
    """
    # 1. Register & Login
    headers, user = create_user_and_get_token("e2e.journey@skillgraph.internal", name="Journey Tester")
    assert user["email"] == "e2e.journey@skillgraph.internal"

    # 2. Check initial profile
    prof_res = client.get("/api/employees/profile", headers=headers)
    assert prof_res.status_code == 200
    initial_prof = prof_res.json()
    assert initial_prof["name"] == "Journey Tester"

    # 3. Upload resume text & extract skills
    resume_payload = {
        "text": (
            "Senior Systems Engineer with extensive hands-on experience in Python, "
            "Docker containerization, PostgreSQL relational databases, and Linux administration. "
            "Developed cloud microservices and automated CI/CD deployment pipelines."
        )
    }
    upload_res = client.post(
        "/api/employees/resume-upload",
        json=resume_payload,
        headers={**headers, "Content-Type": "application/json"}
    )
    assert upload_res.status_code == 200
    staged_data = upload_res.json()
    assert "extracted_skills" in staged_data
    assert len(staged_data["extracted_skills"]) > 0

    # 4. Review staged skills & confirm selection
    candidate_skills = staged_data["extracted_skills"]
    confirm_payload = {
        "skills": [
            {
                "skill_name": s["skill_name"],
                "proficiency": "Intermediate",
                "evidence": s.get("evidence", "Extracted from resume")
            }
            for s in candidate_skills[:4]
        ]
    }
    confirm_res = client.post("/api/employees/resume/confirm-skills", json=confirm_payload, headers=headers)
    assert confirm_res.status_code == 200
    confirm_result = confirm_res.json()
    assert confirm_result["confirmed_count"] >= 1

    # 5. Add a self-reported verified skill
    add_skill_res = client.post("/api/employees/skills", json={
        "skill_name": "Git",
        "proficiency": "Advanced",
        "source": "self_reported",
        "evidence": "Lead maintainer of internal repositories"
    }, headers=headers)
    assert add_skill_res.status_code == 200

    # Verify profile now reflects skills
    prof_res = client.get("/api/employees/profile", headers=headers)
    updated_prof = prof_res.json()
    skill_names = [s["skill_name"] for s in updated_prof["skills"]]
    assert "Git" in skill_names
    assert len(updated_prof["skills"]) >= 2

    # 6. Browse roles & designate target role
    target_role_id = "ROL-001"  # Cloud Engineer
    set_role_res = client.put("/api/employees/target-role", json={"target_role_id": target_role_id}, headers=headers)
    assert set_role_res.status_code == 200
    assert set_role_res.json()["target_role_id"] == target_role_id

    # 7. Perform Skill-Gap Analysis
    gap_res = client.get(f"/api/analysis/skill-gap/{target_role_id}", headers=headers)
    assert gap_res.status_code == 200
    gap_data = gap_res.json()
    assert "all_gaps" in gap_data
    assert "match_score" in gap_data
    assert "summary" in gap_data
    assert "met_count" in gap_data["summary"]
    assert "missing_count" in gap_data["summary"]

    # 8. Generate Personalized Learning Roadmap
    roadmap_res = client.get(f"/api/roadmap?role_id={target_role_id}", headers=headers)
    assert roadmap_res.status_code == 200
    roadmap_data = roadmap_res.json()
    assert roadmap_data["target_role_id"] == target_role_id
    assert len(roadmap_data["milestones"]) > 0

    first_course = roadmap_data["milestones"][0]
    course_id = first_course["course_id"]
    assert first_course["status"] == "not_started"

    # 9. Update Course Progress (in_progress -> completed)
    prog_res1 = client.put(
        f"/api/roadmap/courses/{course_id}/progress",
        json={"status": "in_progress", "progress_pct": 50},
        headers=headers
    )
    assert prog_res1.status_code == 200
    assert prog_res1.json()["course_status"] == "in_progress"
    assert prog_res1.json()["progress_pct"] == 50

    prog_res2 = client.put(
        f"/api/roadmap/courses/{course_id}/progress",
        json={"status": "completed", "progress_pct": 100},
        headers=headers
    )
    assert prog_res2.status_code == 200
    assert prog_res2.json()["course_status"] == "completed"
    assert prog_res2.json()["progress_pct"] == 100
    assert prog_res2.json()["roadmap_summary"]["completed_courses_count"] >= 1

    # 10. Evaluate Career Readiness Assessment
    readiness_res = client.get(f"/api/analysis/readiness/{target_role_id}", headers=headers)
    assert readiness_res.status_code == 200
    readiness = readiness_res.json()
    assert "readiness_score" in readiness
    assert "readiness_level" in readiness
    assert "contributing_factors" in readiness
    assert "limitations" in readiness
    assert readiness["readiness_score"] >= 0.0

    # 11. Run What-If Simulation
    # Pick a missing skill from gap analysis if any
    missing_gaps = [g for g in gap_data.get("all_gaps", []) if g["status"] == "missing"]
    hypothetical_skill = missing_gaps[0]["skill_name"] if missing_gaps else "Kubernetes"

    sim_res = client.post("/api/analysis/what-if", json={
        "target_role_id": target_role_id,
        "skills": [
            {"skill_name": hypothetical_skill, "proficiency": "Advanced"}
        ]
    }, headers=headers)
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert "baseline" in sim_data
    assert "simulated" in sim_data
    assert "deltas" in sim_data
    assert sim_data["simulated"]["match_score"] >= sim_data["baseline"]["match_score"]

    # Verify simulation caused zero permanent database changes
    after_prof = client.get("/api/employees/profile", headers=headers).json()
    after_skills = [s["skill_name"] for s in after_prof["skills"]]
    if hypothetical_skill not in skill_names:
        assert hypothetical_skill not in after_skills


# ---------------------------------------------------------
# 2. Strict Cross-User Isolation & Security
# ---------------------------------------------------------
def test_cross_user_isolation_and_privacy():
    """Verify strict multi-tenant user isolation. User A cannot access or manipulate User B's data."""
    headers_a, user_a = create_user_and_get_token("user.alpha@skillgraph.internal", name="User Alpha")
    headers_b, user_b = create_user_and_get_token("user.beta@skillgraph.internal", name="User Beta")

    # User A adds a private skill and sets target role
    client.post("/api/employees/skills", json={
        "skill_name": "TensorFlow",
        "proficiency": "Expert",
        "source": "project"
    }, headers=headers_a)
    client.put("/api/employees/target-role", json={"target_role_id": "ROL-095"}, headers=headers_a)

    # User B adds a distinct skill and different target role
    client.post("/api/employees/skills", json={
        "skill_name": "SQL",
        "proficiency": "Beginner",
        "source": "self_reported"
    }, headers=headers_b)
    client.put("/api/employees/target-role", json={"target_role_id": "ROL-001"}, headers=headers_b)

    # 1. Profile isolation
    prof_a = client.get("/api/employees/profile", headers=headers_a).json()
    prof_b = client.get("/api/employees/profile", headers=headers_b).json()

    skills_a = [s["skill_name"] for s in prof_a["skills"]]
    skills_b = [s["skill_name"] for s in prof_b["skills"]]

    assert "TensorFlow" in skills_a
    assert "TensorFlow" not in skills_b
    assert "SQL" in skills_b
    assert "SQL" not in skills_a
    assert prof_a["target_role_id"] == "ROL-095"
    assert prof_b["target_role_id"] == "ROL-001"

    # 2. Roadmap isolation
    roadmap_a = client.get("/api/roadmap?role_id=ROL-095", headers=headers_a).json()
    course_a = roadmap_a["milestones"][0]["course_id"]

    # User B attempts to manipulate User A's roadmap course progress
    # User B's roadmap does not contain course_a or if it doesn't belong to B's target roadmap
    b_attempt = client.put(
        f"/api/roadmap/courses/{course_a}/progress",
        json={"status": "completed", "progress_pct": 100},
        headers=headers_b
    )
    # Course is not in User B's active roadmap (ROL-001) or rejected
    assert b_attempt.status_code in (400, 404)

    # 3. User A's progress remains untouched
    roadmap_a_check = client.get("/api/roadmap?role_id=ROL-095", headers=headers_a).json()
    course_status_a = next(m["status"] for m in roadmap_a_check["milestones"] if m["course_id"] == course_a)
    assert course_status_a == "not_started"


# ---------------------------------------------------------
# 3. Authentication & Boundary Security Edge Cases
# ---------------------------------------------------------
def test_authentication_boundaries_and_rejections():
    """Verify unauthorized requests and tampered tokens are rejected with 401 or 403."""
    # 1. No token (FastAPI HTTPBearer returns 403 when header is missing)
    assert client.get("/api/employees/profile").status_code in (401, 403)
    assert client.get("/api/roadmap").status_code in (401, 403)
    assert client.get("/api/analysis/readiness").status_code in (401, 403)
    assert client.post("/api/analysis/what-if", json={}).status_code in (401, 403)

    # 2. Invalid / malformed token
    bad_headers = {"Authorization": "Bearer not-a-valid-jwt-token"}
    assert client.get("/api/employees/profile", headers=bad_headers).status_code == 401
    assert client.get("/api/roadmap", headers=bad_headers).status_code == 401

    # 3. Forged JWT with incorrect signature
    forged_token = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiJhZG1pbkBoYWNrZXIuaW50ZXJuYWwiLCJleHAiOjk5OTk5OTk5OTl9."
        "badsignaturestring"
    )
    assert client.get("/api/employees/profile", headers={"Authorization": f"Bearer {forged_token}"}).status_code == 401


def test_password_change_security():
    """Verify password change enforces length requirements, current password verification, and updates hash."""
    headers, _ = create_user_and_get_token("pwd.security@skillgraph.internal", password="OldPassword123!")

    # 1. Wrong current password
    res_wrong = client.post("/api/auth/change-password", json={
        "current_password": "WrongPassword999!",
        "new_password": "NewSecurePassword456!"
    }, headers=headers)
    assert res_wrong.status_code == 400

    # 2. New password too short
    res_short = client.post("/api/auth/change-password", json={
        "current_password": "OldPassword123!",
        "new_password": "short"
    }, headers=headers)
    assert res_short.status_code == 400

    # 3. Valid password change
    res_valid = client.post("/api/auth/change-password", json={
        "current_password": "OldPassword123!",
        "new_password": "NewSecurePassword456!"
    }, headers=headers)
    assert res_valid.status_code == 200

    # 4. Old password can no longer login
    res_old_login = client.post("/api/auth/login", json={
        "email": "pwd.security@skillgraph.internal",
        "password": "OldPassword123!"
    })
    assert res_old_login.status_code == 401

    # 5. New password successfully logs in
    res_new_login = client.post("/api/auth/login", json={
        "email": "pwd.security@skillgraph.internal",
        "password": "NewSecurePassword456!"
    })
    assert res_new_login.status_code == 200


# ---------------------------------------------------------
# 4. Resume File Upload Security & Validation
# ---------------------------------------------------------
def test_resume_upload_security_and_format_validation():
    """Verify resume upload rejects unsafe formats, empty files, and handles supported formats securely."""
    headers, _ = create_user_and_get_token("upload.security@skillgraph.internal")

    # 1. Disallowed file extension (.exe)
    res_exe = client.post(
        "/api/employees/resume-upload",
        files={"file": ("malware.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/octet-stream")},
        headers=headers
    )
    assert res_exe.status_code == 400
    assert "Unsupported file extension" in res_exe.text or "format" in res_exe.text.lower()

    # 2. Empty file
    res_empty = client.post(
        "/api/employees/resume-upload",
        files={"file": ("empty.txt", b"", "text/plain")},
        headers=headers
    )
    assert res_empty.status_code == 400

    # 3. Valid plain text file
    txt_content = b"Experienced Data Analyst proficient in SQL, Python, Tableau, and Statistics."
    res_txt = client.post(
        "/api/employees/resume-upload",
        files={"file": ("resume.txt", txt_content, "text/plain")},
        headers=headers
    )
    assert res_txt.status_code == 200
    data = res_txt.json()
    assert data["file_type"] in ("TEXT", "TXT")
    assert len(data["extracted_skills"]) > 0


# ---------------------------------------------------------
# 5. Learning Roadmap DAG & Topological Order Verification
# ---------------------------------------------------------
def test_roadmap_dag_topological_consistency():
    """
    Verifies that generated roadmaps strictly satisfy prerequisite ordering:
    For any course milestone in the roadmap, all of its required prerequisite courses
    must appear earlier in the milestone sequence.
    """
    headers, _ = create_user_and_get_token("dag.tester@skillgraph.internal")

    # Test across multiple canonical roles
    test_role_ids = ["ROL-001", "ROL-002", "ROL-095"]

    for role_id in test_role_ids:
        res = client.get(f"/api/roadmap?role_id={role_id}", headers=headers)
        assert res.status_code == 200
        data = res.json()
        milestones = data.get("milestones", [])
        if not milestones:
            continue

        course_order = [m["course_id"] for m in milestones]
        course_index = {cid: idx for idx, cid in enumerate(course_order)}

        # Check every prerequisite relationship in milestone list
        for m in milestones:
            cid = m["course_id"]
            prereqs = m.get("prerequisites", [])
            for p in prereqs:
                p_id = p if isinstance(p, str) else p.get("course_id")
                if p_id in course_index:
                    assert course_index[p_id] < course_index[cid], (
                        f"Topological violation in role {role_id}: Prerequisite {p_id} "
                        f"(idx {course_index[p_id]}) appears after dependent course {cid} "
                        f"(idx {course_index[cid]})."
                    )


# ---------------------------------------------------------
# 6. What-If Simulation Validation & Zero-Side-Effect Guarantee
# ---------------------------------------------------------
def test_what_if_simulation_zero_side_effects():
    """Verify What-If simulation validates inputs, accurately measures delta, and produces zero side effects."""
    headers, _ = create_user_and_get_token("simulation.tester@skillgraph.internal")

    # Set target role
    client.put("/api/employees/target-role", json={"target_role_id": "ROL-001"}, headers=headers)

    # Snapshot user profile before simulation
    prof_before = client.get("/api/employees/profile", headers=headers).json()
    skills_before = prof_before["skills"]

    # 1. Invalid role ID -> 404
    bad_role_res = client.post("/api/analysis/what-if", json={
        "target_role_id": "NON_EXISTENT_ROLE_999",
        "skills": [{"skill_name": "Python", "proficiency": "Expert"}]
    }, headers=headers)
    assert bad_role_res.status_code == 404

    # 2. Invalid proficiency string -> 400
    bad_prof_res = client.post("/api/analysis/what-if", json={
        "target_role_id": "ROL-001",
        "skills": [{"skill_name": "Python", "proficiency": "SuperExpert"}]
    }, headers=headers)
    assert bad_prof_res.status_code == 400

    # 3. Zero hypothetical changes -> delta == 0.0
    zero_res = client.post("/api/analysis/what-if", json={
        "target_role_id": "ROL-001",
        "skills": []
    }, headers=headers)
    assert zero_res.status_code == 200
    zero_data = zero_res.json()
    assert zero_data["deltas"]["match_gain"] == 0.0
    assert zero_data["deltas"]["readiness_gain"] == 0.0

    # 4. Realistic simulation
    valid_res = client.post("/api/analysis/what-if", json={
        "target_role_id": "ROL-001",
        "skills": [
            {"skill_name": "Docker", "proficiency": "Advanced"},
            {"skill_name": "Kubernetes", "proficiency": "Expert"}
        ]
    }, headers=headers)
    assert valid_res.status_code == 200
    valid_data = valid_res.json()
    assert valid_data["simulated"]["match_score"] >= valid_data["baseline"]["match_score"]

    # Snapshot user profile after simulation -> Must be completely identical
    prof_after = client.get("/api/employees/profile", headers=headers).json()
    assert prof_after["skills"] == skills_before
    assert prof_after["target_role_id"] == prof_before["target_role_id"]


# ---------------------------------------------------------
# 7. Canonical Catalog & Database Integrity
# ---------------------------------------------------------
def test_canonical_catalog_integrity():
    """Verify canonical catalogs remain preserved (119 skills, 96 roles, 18 courses, 20 prerequisite edges)."""
    db = TestingSessionLocal()
    try:
        skill_count = db.query(Skill).count()
        role_count = db.query(Role).count()
        course_count = db.query(Course).count()
        prereq_count = db.query(CoursePrerequisite).count()

        assert skill_count == 119, f"Expected 119 skills, found {skill_count}"
        assert role_count == 96, f"Expected 96 roles, found {role_count}"
        assert course_count == 18, f"Expected 18 courses, found {course_count}"
        assert prereq_count == 20, f"Expected 20 prerequisite edges, found {prereq_count}"

        # Verify no cycle in prerequisite graph
        prereqs = db.query(CoursePrerequisite).all()
        adj = {}
        for p in prereqs:
            adj.setdefault(p.prerequisite_course_id, []).append(p.course_id)

        visited = set()
        rec_stack = set()

        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
            return False

        for node in list(adj.keys()):
            if node not in visited:
                assert not has_cycle(node), f"Cycle detected in prerequisite DAG at node {node}"
    finally:
        db.close()
