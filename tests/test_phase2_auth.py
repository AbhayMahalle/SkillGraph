"""
Automated Test Suite for SkillGraph — Phase 2: Authentication & Personal Profiles.
Uses an isolated temporary copy of the verified database to protect real database integrity.

Covers:
1. Registration (validation, PBKDF2 hashing, duplicate rejection, employee profile linkage)
2. Login (success, legacy hash upgrade, invalid credentials, nonexistent account)
3. Token verification (valid, invalid, expired, revoked)
4. Logout & immediate server-side token revocation
5. Current user retrieval (GET /api/users/me)
6. Profile update (PATCH /api/users/me, protected field immutability, role validation)
7. Password change (POST /api/auth/change-password, verification, rejection of old password)
8. Multi-user private data isolation (two independent accounts, no cross-user leakage)
9. Catalog preservation (skills, roles, courses remain intact)
"""

import os
import shutil
import tempfile
import atexit
import jwt
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database.db import get_db, REPO_ROOT
from backend.models.models import User, Employee, Skill, Role, Course, EmployeeSkill
from backend.api.auth import JWT_SECRET, JWT_ALGORITHM, hash_password, verify_password

# ---------------------------------------------------------
# Isolated Test Database Setup
# ---------------------------------------------------------
BACKUP_DB_PATH = REPO_ROOT / "data" / "processed" / "skillgraph_backup_phase2.db"
temp_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
TEMP_DB_PATH = temp_db_file.name
temp_db_file.close()

# Copy baseline seed data to isolated test database
shutil.copyfile(str(BACKUP_DB_PATH), TEMP_DB_PATH)

test_engine = create_engine(
    f"sqlite:///{TEMP_DB_PATH}",
    connect_args={"check_same_thread": False}
)
from backend.database.init_db import ensure_schema_migrations
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

def cleanup_temp_db():
    if os.path.exists(TEMP_DB_PATH):
        try:
            os.remove(TEMP_DB_PATH)
        except Exception:
            pass

atexit.register(cleanup_temp_db)

client = TestClient(app)

# ---------------------------------------------------------
# Test Fixtures & Helpers
# ---------------------------------------------------------
def unique_email(prefix="test"):
    import uuid
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"

# ---------------------------------------------------------
# 1. Registration Tests
# ---------------------------------------------------------
def test_successful_registration():
    email = unique_email("alice")
    payload = {
        "full_name": "Alice Engineer",
        "email": email,
        "password": "SecurePassword123!",
        "department": "Engineering",
        "current_role": "Backend Developer"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == email.lower()
    assert data["user"]["full_name"] == "Alice Engineer"
    assert data["user"]["role"] == "EMPLOYEE"
    assert data["user"]["employee_id"].startswith("EMP-")

    # Verify password hash in isolated test database is PBKDF2, not plaintext
    session = TestingSessionLocal()
    try:
        user = session.query(User).filter(User.email == email.lower()).first()
        assert user is not None
        assert user.hashed_password.startswith("pbkdf2_sha256$100000$")
        assert user.hashed_password != payload["password"]
        assert verify_password(payload["password"], user.hashed_password)

        # Verify linked employee profile was created
        emp = session.query(Employee).filter(Employee.employee_id == user.employee_id).first()
        assert emp is not None
        assert emp.name == "Alice Engineer"
        assert emp.email == email.lower()
        assert emp.department == "Engineering"
        assert emp.current_role == "Backend Developer"
    finally:
        session.close()

def test_duplicate_email_registration_rejected():
    email = unique_email("dup")
    payload = {
        "full_name": "Duplicate User",
        "email": email,
        "password": "Password123!",
        "department": "Product",
        "current_role": "Product Manager"
    }
    # First registration succeeds
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 200

    # Second registration with same email (even with different case/spaces) must fail
    dup_payload = payload.copy()
    dup_payload["email"] = f"  {email.upper()}  "
    res2 = client.post("/api/auth/register", json=dup_payload)
    assert res2.status_code == 400
    assert "already registered" in res2.json()["detail"].lower()

def test_registration_validation_rules():
    # Invalid email format
    res_bad_email = client.post("/api/auth/register", json={
        "full_name": "Bad Email",
        "email": "not-an-email",
        "password": "Password123!"
    })
    assert res_bad_email.status_code == 400

    # Short password (< 8 chars)
    res_short_pwd = client.post("/api/auth/register", json={
        "full_name": "Short Pwd",
        "email": unique_email("short"),
        "password": "short"
    })
    assert res_short_pwd.status_code == 400
    assert "8 characters" in res_short_pwd.json()["detail"]

    # Empty full name
    res_empty_name = client.post("/api/auth/register", json={
        "full_name": "   ",
        "email": unique_email("noname"),
        "password": "Password123!"
    })
    assert res_empty_name.status_code == 400

# ---------------------------------------------------------
# 2. Login Tests
# ---------------------------------------------------------
def test_successful_login_and_hash_upgrade():
    email = unique_email("bob")
    pwd = "BobStrongPassword99!"
    # Register Bob
    reg_res = client.post("/api/auth/register", json={
        "full_name": "Bob Architect",
        "email": email,
        "password": pwd
    })
    assert reg_res.status_code == 200

    # Login Bob
    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": pwd
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    assert login_data["user"]["email"] == email

def test_legacy_seeded_user_login_and_auto_upgrade():
    # Alex Rivera is a seeded Phase 1 user with legacy sha256 hash of 'employee123'
    login_res = client.post("/api/auth/login", json={
        "email": "alex.rivera@skillgraph.internal",
        "password": "employee123"
    })
    assert login_res.status_code == 200, login_res.text
    assert "access_token" in login_res.json()

    # Verify that Alex's password hash in the DB was upgraded to PBKDF2
    session = TestingSessionLocal()
    try:
        alex = session.query(User).filter(User.email == "alex.rivera@skillgraph.internal").first()
        assert alex is not None
        assert alex.hashed_password.startswith("pbkdf2_sha256$100000$")
    finally:
        session.close()

def test_failed_login_invalid_password():
    email = unique_email("failpwd")
    client.post("/api/auth/register", json={
        "full_name": "Fail Pwd",
        "email": email,
        "password": "CorrectPassword123!"
    })
    res = client.post("/api/auth/login", json={
        "email": email,
        "password": "WrongPassword!"
    })
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]

def test_failed_login_nonexistent_email():
    res = client.post("/api/auth/login", json={
        "email": "definitely_does_not_exist_9999@example.com",
        "password": "AnyPassword123!"
    })
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]

# ---------------------------------------------------------
# 3. Token Verification, Expired Tokens, and Logout Revocation
# ---------------------------------------------------------
def test_unauthenticated_requests_rejected():
    res = client.get("/api/users/me")
    assert res.status_code in [401, 403]

    res_invalid_token = client.get("/api/users/me", headers={"Authorization": "Bearer invalid.token.payload"})
    assert res_invalid_token.status_code == 401

def test_expired_token_rejected():
    # Craft an expired token with HS256 and past expiration
    past_time = datetime.utcnow() - timedelta(hours=2)
    expired_token = jwt.encode(
        {"sub": "alex.rivera@skillgraph.internal", "exp": past_time, "iat": past_time - timedelta(hours=1)},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )
    res = client.get("/api/users/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401
    assert "Could not validate credentials" in res.json()["detail"]

def test_logout_and_token_revocation():
    email = unique_email("logout_test")
    reg_res = client.post("/api/auth/register", json={
        "full_name": "Logout Tester",
        "email": email,
        "password": "LogoutPassword123!"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify token works before logout
    check_before = client.get("/api/users/me", headers=headers)
    assert check_before.status_code == 200

    # Call logout
    logout_res = client.post("/api/auth/logout", headers=headers)
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "success"

    # Immediately verify that the revoked token is rejected
    check_after = client.get("/api/users/me", headers=headers)
    assert check_after.status_code == 401
    assert "terminated" in check_after.json()["detail"].lower() or "credentials" in check_after.json()["detail"].lower()

# ---------------------------------------------------------
# 4. User Retrieval and Profile Update (GET & PATCH /api/users/me)
# ---------------------------------------------------------
def test_get_users_me():
    email = unique_email("getme")
    reg_res = client.post("/api/auth/register", json={
        "full_name": "Get Me User",
        "email": email,
        "password": "GetMePassword123!",
        "department": "Platform",
        "current_role": "DevOps Engineer"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/users/me", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == email
    assert data["full_name"] == "Get Me User"
    assert data["profile"]["department"] == "Platform"
    assert data["profile"]["current_role"] == "DevOps Engineer"

def test_patch_users_me_success():
    email = unique_email("patchuser")
    reg_res = client.post("/api/auth/register", json={
        "full_name": "Original Name",
        "email": email,
        "password": "PatchPassword123!",
        "department": "QA",
        "current_role": "QA Engineer"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    patch_payload = {
        "full_name": "Updated Name",
        "bio": "Experienced cloud automation tester.",
        "department": "Core Infrastructure",
        "target_role_id": "ROL-002",
        "experience_years": 5,
        "qualification": "Master of Computer Science"
    }
    patch_res = client.patch("/api/users/me", json=patch_payload, headers=headers)
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["user"]["full_name"] == "Updated Name"
    assert data["user"]["profile"]["bio"] == "Experienced cloud automation tester."
    assert data["user"]["profile"]["department"] == "Core Infrastructure"
    assert data["user"]["profile"]["target_role_id"] == "ROL-002"
    assert data["user"]["profile"]["experience_years"] == 5

    # Verify persistence via fresh GET request
    get_res = client.get("/api/users/me", headers=headers)
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["full_name"] == "Updated Name"
    assert get_data["profile"]["bio"] == "Experienced cloud automation tester."

def test_patch_users_me_protected_field_tampering_prevented():
    email = unique_email("tamper")
    reg_res = client.post("/api/auth/register", json={
        "full_name": "Tamper Test",
        "email": email,
        "password": "TamperPassword123!"
    })
    token = reg_res.json()["access_token"]
    original_id = reg_res.json()["user"]["id"]
    original_emp_id = reg_res.json()["user"]["employee_id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to tamper with protected fields
    tamper_payload = {
        "id": 99999,
        "email": "hacked@company.internal",
        "role": "ADMIN",
        "employee_id": "EMP-99999",
        "hashed_password": "plaintextpassword",
        "full_name": "Legitimate Update"
    }
    patch_res = client.patch("/api/users/me", json=tamper_payload, headers=headers)
    assert patch_res.status_code == 200

    # Verify protected fields were NOT modified
    verify_res = client.get("/api/users/me", headers=headers)
    data = verify_res.json()
    assert data["id"] == original_id
    assert data["email"] == email
    assert data["role"] == "EMPLOYEE"
    assert data["employee_id"] == original_emp_id
    assert data["full_name"] == "Legitimate Update"

# ---------------------------------------------------------
# 5. Password Change (POST /api/auth/change-password)
# ---------------------------------------------------------
def test_change_password_flow():
    email = unique_email("pwdchange")
    old_pwd = "OldPassword123!"
    new_pwd = "BrandNewSecurePassword456!"

    reg_res = client.post("/api/auth/register", json={
        "full_name": "Password Changer",
        "email": email,
        "password": old_pwd
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Attempt with incorrect old password -> must fail
    res_wrong = client.post("/api/auth/change-password", json={
        "current_password": "IncorrectPassword!",
        "new_password": new_pwd
    }, headers=headers)
    assert res_wrong.status_code == 400
    assert "Current password is incorrect" in res_wrong.json()["detail"]

    # 2. Attempt with short new password (< 8 chars) -> must fail
    res_short = client.post("/api/auth/change-password", json={
        "current_password": old_pwd,
        "new_password": "short"
    }, headers=headers)
    assert res_short.status_code == 400
    assert "8 characters" in res_short.json()["detail"]

    # 3. Attempt with same password -> must fail
    res_same = client.post("/api/auth/change-password", json={
        "current_password": old_pwd,
        "new_password": old_pwd
    }, headers=headers)
    assert res_same.status_code == 400
    assert "cannot be the same" in res_same.json()["detail"]

    # 4. Successful password change
    res_ok = client.post("/api/auth/change-password", json={
        "current_password": old_pwd,
        "new_password": new_pwd
    }, headers=headers)
    assert res_ok.status_code == 200
    assert res_ok.json()["status"] == "success"

    # 5. Old password must now be rejected at login
    res_old_login = client.post("/api/auth/login", json={
        "email": email,
        "password": old_pwd
    })
    assert res_old_login.status_code == 401

    # 6. New password must succeed
    res_new_login = client.post("/api/auth/login", json={
        "email": email,
        "password": new_pwd
    })
    assert res_new_login.status_code == 200
    assert "access_token" in res_new_login.json()

# ---------------------------------------------------------
# 6. Multi-User Private Data Isolation Tests
# ---------------------------------------------------------
def test_multi_user_data_isolation():
    """
    Ensure complete data isolation between two independently registered users.
    User 1 and User 2 should never leak profile details, skills, or private records to each other.
    """
    email1 = unique_email("user1")
    email2 = unique_email("user2")

    # Register User 1
    u1_reg = client.post("/api/auth/register", json={
        "full_name": "User One",
        "email": email1,
        "password": "User1Password123!",
        "department": "Security",
        "current_role": "Security Specialist"
    })
    token1 = u1_reg.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # Register User 2
    u2_reg = client.post("/api/auth/register", json={
        "full_name": "User Two",
        "email": email2,
        "password": "User2Password123!",
        "department": "Design",
        "current_role": "UI/UX Designer"
    })
    token2 = u2_reg.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # User 1 adds a skill: Docker
    add_skill_res = client.post("/api/employees/skills", json={
        "skill_name": "Docker",
        "proficiency": "Expert"
    }, headers=headers1)
    assert add_skill_res.status_code == 200

    # User 1 sets bio and target role
    client.patch("/api/users/me", json={
        "bio": "User 1 Private Cyber Bio",
        "target_role_id": "ROL-003"
    }, headers=headers1)

    # User 2 reads their profile via /api/users/me
    u2_me = client.get("/api/users/me", headers=headers2).json()
    assert u2_me["email"] == email2
    assert u2_me["full_name"] == "User Two"
    assert u2_me["profile"]["bio"] != "User 1 Private Cyber Bio"
    assert u2_me["profile"]["department"] == "Design"

    # User 2 reads employee profile via /api/employees/profile
    u2_profile = client.get("/api/employees/profile", headers=headers2).json()
    assert u2_profile["name"] == "User Two"
    assert u2_profile["email"] == email2

    # Verify User 2 DOES NOT have User 1's added Docker skill
    u2_skills = [s["skill_name"] for s in u2_profile.get("skills", [])]
    assert "Docker" not in u2_skills

    # User 1 reads their profile and DOES have Docker skill and their own bio
    u1_profile = client.get("/api/employees/profile", headers=headers1).json()
    assert u1_profile["name"] == "User One"
    assert u1_profile["bio"] == "User 1 Private Cyber Bio"
    assert u1_profile["target_role_id"] == "ROL-003"
    u1_skills = [s["skill_name"] for s in u1_profile.get("skills", [])]
    assert "Docker" in u1_skills

# ---------------------------------------------------------
# 7. Catalog Preservation & Service Regressions
# ---------------------------------------------------------
def test_catalogs_remain_preserved_during_phase2():
    session = TestingSessionLocal()
    try:
        skill_count = session.query(Skill).count()
        role_count = session.query(Role).count()
        course_count = session.query(Course).count()
        # Canonical catalogs must remain intact (skills >= 119, roles 96, courses 18)
        assert skill_count >= 119
        assert role_count == 96
        assert course_count == 18
    finally:
        session.close()
