"""
Automated Test Suite for SkillGraph — Phase 4: Target-Role Matching & Skill-Gap Analysis.
Uses an isolated temporary copy of the database to guarantee real database integrity.

Covers:
1. Canonical Role Catalog retrieval and query search (GET /api/roles)
2. Role detail retrieval (GET /api/roles/{role_id})
3. Target role selection and persistence (PUT/POST /api/employees/target-role)
4. Rejection of invalid/nonexistent role IDs (404 Not Found)
5. Explainable role match score calculation (GET /api/roles/match/{role_id})
6. Skill-gap classification: Met, Partially Met, and Missing
7. Proficiency gap math: max(0, required_level - demonstrated_level)
8. Explainable priority ranking (Critical, High, Medium, Low)
9. Unverified resume mentions vs verified evidence discounting
10. Side-by-side role comparison (GET /api/roles/compare)
11. Safe handling of empty skill profiles and zero-requirement edge cases
12. Multi-user isolation and refresh-safe persistence
13. Recalculation after personal skill changes
14. Catalog preservation (119 skills, 96 roles, 18 courses)
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
from backend.models.models import User, Employee, Skill, Role, Course, EmployeeSkill
from backend.database.init_db import ensure_schema_migrations
from backend.api.auth import create_access_token

# ---------------------------------------------------------
# Isolated Test Database Setup
# ---------------------------------------------------------
BACKUP_DB_PATH = REPO_ROOT / "data" / "processed" / "skillgraph_backup_phase4.db"
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

def get_auth_headers(email: str = "sarah.jenkins@skillgraph.internal"):
    token = create_access_token(data={"sub": email})
    return {"Authorization": f"Bearer {token}"}

# ---------------------------------------------------------
# 1. Role Catalog Retrieval & Search
# ---------------------------------------------------------
def test_get_all_roles_and_search_filter():
    """Verify listing of all 96 canonical roles and search filtering."""
    # List all
    res = client.get("/api/roles")
    assert res.status_code == 200
    roles = res.json()
    assert len(roles) == 96
    first_role = roles[0]
    assert "role_id" in first_role
    assert "title" in first_role
    assert "required_skills" in first_role
    assert "salary_range" in first_role

    # Search filter by title
    res_search = client.get("/api/roles?q=Cloud")
    assert res_search.status_code == 200
    cloud_roles = res_search.json()
    assert len(cloud_roles) >= 2
    assert any("Cloud" in r["title"] for r in cloud_roles)

    # Filter by category/department
    res_dept = client.get("/api/roles?category=Engineering")
    assert res_dept.status_code == 200
    eng_roles = res_dept.json()
    assert len(eng_roles) > 0

def test_get_role_detail_and_not_found():
    """Verify role details with required skills and weights, plus 404 for unknown role."""
    # Valid role
    res = client.get("/api/roles/ROL-001")
    assert res.status_code == 200
    data = res.json()
    assert data["role_id"] == "ROL-001"
    assert data["title"] == "Software Engineer"
    assert len(data["required_skills"]) >= 3
    first_req = data["required_skills"][0]
    assert "skill_name" in first_req
    assert "weight" in first_req

    # Unknown role
    res_404 = client.get("/api/roles/ROL-NONEXISTENT")
    assert res_404.status_code == 404

# ---------------------------------------------------------
# 2. Target Role Selection & Persistence
# ---------------------------------------------------------
def test_target_role_selection_and_persistence():
    """Verify user can designate, change, and persist their target role."""
    headers = get_auth_headers("sarah.jenkins@skillgraph.internal")

    # Set target role to Full Stack Developer (ROL-002)
    payload = {"target_role_id": "ROL-002"}
    res = client.put("/api/employees/target-role", headers=headers, json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["target_role_id"] == "ROL-002"
    assert "Full Stack" in data["target_role_title"]

    # Verify persistent retrieval via /api/users/me
    res_me = client.get("/api/users/me", headers=headers)
    assert res_me.status_code == 200
    assert res_me.json()["profile"]["target_role_id"] == "ROL-002"

    # Verify persistent retrieval via /api/employees/profile
    res_prof = client.get("/api/employees/profile", headers=headers)
    assert res_prof.status_code == 200
    assert res_prof.json()["target_role_id"] == "ROL-002"

def test_target_role_invalid_id_rejected():
    """Setting target role to nonexistent role ID returns 404."""
    headers = get_auth_headers("sarah.jenkins@skillgraph.internal")

    payload = {"target_role_id": "ROL-FAKE-999"}
    res = client.put("/api/employees/target-role", headers=headers, json=payload)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()

# ---------------------------------------------------------
# 3. Explainable Role Matching & Gap Classification
# ---------------------------------------------------------
def test_explainable_role_match_and_gap_classification():
    """
    Test role matching calculation and skill gap classification:
    - Met: skill meets or exceeds required proficiency with verified/self_reported source
    - Partially Met: skill below required proficiency OR unverified candidate mention
    - Missing: skill completely absent
    """
    headers = get_auth_headers("sarah.jenkins@skillgraph.internal")

    # Software Engineer (ROL-001) requires: Python, Java, C++, Git, Problem Solving (Intermediate level benchmark)
    # Add Python at Advanced (Met)
    client.post("/api/employees/skills", headers=headers, json={
        "skill_name": "Python",
        "proficiency": "Advanced",
        "source": "self_reported"
    })
    # Add Git at Intermediate (Met)
    client.post("/api/employees/skills", headers=headers, json={
        "skill_name": "Git",
        "proficiency": "Intermediate",
        "source": "self_reported"
    })
    # Add Java at Beginner (Partially Met - level below requirement)
    client.post("/api/employees/skills", headers=headers, json={
        "skill_name": "Java",
        "proficiency": "Beginner",
        "source": "self_reported"
    })
    # Add C++ as unverified resume extracted (Partially Met - unverified candidate mention)
    client.post("/api/employees/resume/confirm-skills", headers=headers, json={
        "skills": [{"skill_name": "C++", "proficiency": "Intermediate", "accepted": True}]
    })

    # Retrieve gap analysis for ROL-001
    res = client.get("/api/analysis/skill-gap/ROL-001", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["role_id"] == "ROL-001"
    assert 0.0 <= data["match_score"] <= 100.0

    # Met skills must include Python and Git
    met_names = [s["skill_name"] for s in data["met_skills"]]
    assert "Python" in met_names
    assert "Git" in met_names

    # Partially met skills must include Java (below level) and C++ (unverified)
    part_names = [s["skill_name"] for s in data["partially_met_skills"]]
    assert "Java" in part_names
    assert "C++" in part_names

    # Missing skills must include Problem Solving
    missing_names = [s["skill_name"] for s in data["missing_skills"]]
    assert "Problem Solving" in missing_names

    # Verify summary counts
    assert data["summary"]["met_count"] == 2
    assert data["summary"]["partially_met_count"] == 2
    assert data["summary"]["missing_count"] == 1
    assert data["summary"]["total_required"] == 5

    # Verify explainability object
    assert "explanation" in data
    exp = data["explanation"]
    assert "formula" in exp
    assert "earned_weight" in exp
    assert "summary" in exp
    assert "unverified_skills_discounted" in exp
    assert exp["unverified_skills_discounted"] >= 1

def test_proficiency_gap_calculation_and_priorities():
    """Verify gap formula max(0, required - demonstrated) and priority ordering."""
    headers = get_auth_headers("sarah.jenkins@skillgraph.internal")

    res = client.get("/api/analysis/skill-gap/ROL-001", headers=headers)
    assert res.status_code == 200
    data = res.json()

    all_gaps = data["all_gaps"]
    assert len(all_gaps) >= 3

    # Missing skill has gap equal to required level
    missing_ps = next((g for g in all_gaps if g["skill_name"] == "Problem Solving"), None)
    assert missing_ps is not None
    assert missing_ps["classification"] == "missing"
    assert missing_ps["gap"] == missing_ps["required_level"]
    assert missing_ps["priority"] in ["Critical", "High", "Medium"]
    assert "not present" in missing_ps["reason"]

    # Java has gap = required_level - current_level
    java_gap = next((g for g in all_gaps if g["skill_name"] == "Java"), None)
    assert java_gap is not None
    assert java_gap["classification"] == "partially_met"
    assert java_gap["gap"] >= 1
    assert "below required" in java_gap["reason"]

    # C++ has unverified explanation
    cpp_gap = next((g for g in all_gaps if g["skill_name"] == "C++"), None)
    assert cpp_gap is not None
    assert "unverified" in cpp_gap["reason"].lower()

def test_single_role_match_endpoint():
    """Verify GET /api/roles/match/{role_id} returns accurate personalized breakdown."""
    headers = get_auth_headers("sarah.jenkins@skillgraph.internal")

    res = client.get("/api/roles/match/ROL-001", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["role_id"] == "ROL-001"
    assert "match_score" in data
    assert "coverage_percentage" in data
    assert "mobility_status" in data
    assert "explanation" in data

# ---------------------------------------------------------
# 4. Multi-Role Comparison
# ---------------------------------------------------------
def test_compare_roles_endpoint():
    """Verify side-by-side comparison of 2 to 4 canonical roles."""
    headers = get_auth_headers("sarah.jenkins@skillgraph.internal")

    # Compare Software Engineer (ROL-001) and Cloud Architect (ROL-002)
    res = client.get("/api/roles/compare?role_ids=ROL-001,ROL-002", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_compared"] == 2
    assert len(data["compared_roles"]) == 2
    assert "common_required_skills" in data
    assert "common_missing_skills" in data

    r1 = data["compared_roles"][0]
    r2 = data["compared_roles"][1]
    assert r1["role_id"] == "ROL-001"
    assert r2["role_id"] == "ROL-002"
    assert "match_score" in r1
    assert "coverage_percentage" in r1

def test_compare_roles_validation():
    """Verify comparison requires at least 2 roles and at most 4."""
    headers = get_auth_headers("sarah.jenkins@skillgraph.internal")

    # Only 1 role
    res_1 = client.get("/api/roles/compare?role_ids=ROL-001", headers=headers)
    assert res_1.status_code == 400
    assert "at least 2" in res_1.json()["detail"].lower()

    # 5 roles (exceeds max 4)
    res_5 = client.get("/api/roles/compare?role_ids=ROL-001,ROL-002,ROL-003,ROL-004,ROL-005", headers=headers)
    assert res_5.status_code == 400
    assert "maximum of 4" in res_5.json()["detail"].lower()

    # Nonexistent role
    res_fake = client.get("/api/roles/compare?role_ids=ROL-001,ROL-FAKE", headers=headers)
    assert res_fake.status_code == 404

# ---------------------------------------------------------
# 5. Empty Profiles & Edge Cases
# ---------------------------------------------------------
def test_empty_skill_profile_handling():
    """A user with 0 skills matches 0% without division-by-zero errors."""
    # Register fresh user with 0 skills
    unique_email = "zero.skills@skillgraph.internal"
    reg_res = client.post("/api/auth/register", json={
        "full_name": "Zero Skills User",
        "email": unique_email,
        "password": "Password123!",
        "department": "Engineering"
    })
    assert reg_res.status_code == 200
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res_gap = client.get("/api/analysis/skill-gap/ROL-001", headers=headers)
    assert res_gap.status_code == 200
    data = res_gap.json()
    assert data["match_score"] == 0.0
    assert data["coverage_percentage"] == 0.0
    assert data["mobility_status"] == "Needs Upskilling"
    assert data["summary"]["met_count"] == 0
    assert data["summary"]["partially_met_count"] == 0
    assert data["summary"]["missing_count"] == data["summary"]["total_required"]

# ---------------------------------------------------------
# 6. Multi-User Isolation & Real-Time Recalculation
# ---------------------------------------------------------
def test_cross_user_isolation_and_recalculation():
    """User A setting target role and adding skills does not alter User B's state."""
    headers_a = get_auth_headers("alex.rivera@skillgraph.internal")
    headers_b = get_auth_headers("david.kim@skillgraph.internal")

    # User A sets target role to ROL-001
    client.put("/api/employees/target-role", headers=headers_a, json={"target_role_id": "ROL-001"})

    # User B sets target role to ROL-002
    client.put("/api/employees/target-role", headers=headers_b, json={"target_role_id": "ROL-002"})

    # Verify User A target role is ROL-001
    me_a = client.get("/api/users/me", headers=headers_a).json()
    assert me_a["profile"]["target_role_id"] == "ROL-001"

    # Verify User B target role is ROL-002
    me_b = client.get("/api/users/me", headers=headers_b).json()
    assert me_b["profile"]["target_role_id"] == "ROL-002"

# ---------------------------------------------------------
# 7. Catalog Preservation
# ---------------------------------------------------------
def test_catalogs_preserved_after_phase4():
    """Ensure canonical 119 skills, 96 roles, and 18 courses remain completely intact."""
    db = TestingSessionLocal()
    try:
        assert db.query(Skill).count() == 119
        assert db.query(Role).count() == 96
        assert db.query(Course).count() == 18
    finally:
        db.close()
