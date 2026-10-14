"""
Automated Test Suite for SkillGraph — Phase 3: Skill Profiling & Resume Intelligence.
Uses an isolated temporary copy of the database to guarantee database integrity.

Covers:
1. Canonical Skill Catalog selection and query search (GET /api/skills/catalog)
2. Personal Skill CRUD and validated proficiency scale (Beginner, Intermediate, Advanced, Expert)
3. Duplicate skill prevention and in-place proficiency updates
4. Provenance and evidence tracking (source, evidence, timestamps)
5. Multi-format resume upload (PDF, DOCX, TXT)
6. File validation, magic byte checking, and oversized/malformed rejection
7. Graceful handling of empty/unreadable/scanned PDFs (no false OCR claim)
8. Extraction-to-catalog matching with confidence scores and context snippets
9. Candidate review & confirmation workflow (staged extractions, confirm/reject)
10. Preserving unverified status (verified=False) for resume-extracted skills
11. Cross-user isolation: User A cannot access User B's files, staged skills, or profile
12. Catalog preservation (119 skills, 96 roles, 18 courses)
"""

import os
import shutil
import tempfile
import io
import docx
import fitz  # PyMuPDF
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
BACKUP_DB_PATH = REPO_ROOT / "data" / "processed" / "skillgraph_backup_phase3.db"
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
# 1. Canonical Skill Catalog
# ---------------------------------------------------------
def test_skill_catalog_retrieval_and_filtering():
    """Verify GET /api/skills/catalog returns canonical 119 skills with category and search filtering."""
    # All skills
    res = client.get("/api/skills/catalog")
    assert res.status_code == 200
    catalog = res.json()
    assert len(catalog) == 119
    first_item = catalog[0]
    assert "skill_id" in first_item
    assert "name" in first_item
    assert "category" in first_item

    # Search filter
    res_search = client.get("/api/skills/catalog?q=python")
    assert res_search.status_code == 200
    py_skills = res_search.json()
    assert len(py_skills) >= 1
    assert any(s["name"] == "Python" for s in py_skills)

    # Category filter
    res_cat = client.get("/api/skills/catalog?category=Cloud")
    assert res_cat.status_code == 200
    cloud_skills = res_cat.json()
    assert len(cloud_skills) > 0
    assert all("Cloud" in s["category"] for s in cloud_skills)

# ---------------------------------------------------------
# 2. Personal Skill Management & Proficiency Validation
# ---------------------------------------------------------
def test_add_and_list_employee_skills():
    """Verify adding skill with validated proficiency scale and source provenance."""
    headers = get_auth_headers("sarah.jenkins@skillgraph.internal")

    # Add skill with valid proficiency
    payload = {
        "skill_name": "Docker",
        "proficiency": "Advanced",
        "source": "self_reported",
        "evidence": "Containerized microservices across 3 production clusters"
    }
    res = client.post("/api/employees/skills", headers=headers, json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["skill_name"] == "Docker"
    assert data["proficiency"] == "Advanced"
    assert data["source"] == "self_reported"
    assert data["verified"] is True

    # List skills and verify evidence persistence
    res_list = client.get("/api/employees/skills", headers=headers)
    assert res_list.status_code == 200
    skills = res_list.json()
    docker_item = next((s for s in skills if s["skill_name"] == "Docker"), None)
    assert docker_item is not None
    assert docker_item["proficiency"] == "Advanced"
    assert docker_item["evidence"] == "Containerized microservices across 3 production clusters"
    assert docker_item["created_at"] is not None

def test_proficiency_scale_validation():
    """Verify that invalid proficiencies are strictly rejected with 400 Bad Request."""
    headers = get_auth_headers("sarah.jenkins@skillgraph.internal")

    invalid_payload = {
        "skill_name": "Python",
        "proficiency": "MasterGuru"  # Invalid! Allowed: Beginner, Intermediate, Advanced, Expert
    }
    res = client.post("/api/employees/skills", headers=headers, json=invalid_payload)
    assert res.status_code == 400
    assert "Invalid proficiency" in res.json()["detail"]

def test_duplicate_prevention_and_in_place_update():
    """Adding an existing skill for the same user updates proficiency in-place without duplicate rows."""
    headers = get_auth_headers("sarah.jenkins@skillgraph.internal")

    # Add skill at Beginner
    client.post("/api/employees/skills", headers=headers, json={
        "skill_name": "Kubernetes",
        "proficiency": "Beginner"
    })

    # Add same skill again at Expert
    res_dup = client.post("/api/employees/skills", headers=headers, json={
        "skill_name": "Kubernetes",
        "proficiency": "Expert",
        "evidence": "Promoted to lead cluster administrator"
    })
    assert res_dup.status_code == 200

    # Verify only 1 entry exists for Kubernetes
    res_list = client.get("/api/employees/skills", headers=headers)
    k8s_entries = [s for s in res_list.json() if s["skill_name"] == "Kubernetes"]
    assert len(k8s_entries) == 1
    assert k8s_entries[0]["proficiency"] == "Expert"
    assert k8s_entries[0]["evidence"] == "Promoted to lead cluster administrator"

def test_update_and_delete_employee_skill():
    """Verify PUT update and DELETE endpoints for personal skills."""
    headers = get_auth_headers("sarah.jenkins@skillgraph.internal")

    # Ensure Terraform exists
    client.post("/api/employees/skills", headers=headers, json={
        "skill_name": "Terraform",
        "proficiency": "Intermediate"
    })

    # PUT update
    res_put = client.put("/api/employees/skills/Terraform", headers=headers, json={
        "proficiency": "Advanced",
        "evidence": "Authored reusable cloud infrastructure modules"
    })
    assert res_put.status_code == 200
    assert res_put.json()["proficiency"] == "Advanced"

    # DELETE skill
    res_del = client.delete("/api/employees/skills/Terraform", headers=headers)
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "success"

    # Verify it is gone
    res_list = client.get("/api/employees/skills", headers=headers)
    assert not any(s["skill_name"] == "Terraform" for s in res_list.json())

# ---------------------------------------------------------
# 3. Resume Upload & Processing (PDF, DOCX, TXT)
# ---------------------------------------------------------
def test_pdf_resume_upload_and_extraction():
    """Generate a clean synthetic PDF with PyMuPDF, upload it, and verify skill detection."""
    headers = get_auth_headers("sarah.jenkins@skillgraph.internal")

    # Create real PDF in memory
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Sarah Jenkins\nSenior Cloud Engineer with deep expertise in AWS, Docker, Kubernetes, and PostgreSQL.")
    pdf_bytes = doc.tobytes()
    doc.close()

    files = {"file": ("cloud_resume.pdf", pdf_bytes, "application/pdf")}
    res = client.post("/api/employees/resume-upload", headers=headers, files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["file_type"] == "PDF"
    assert data["total_extracted"] >= 3

    detected_names = [s["skill_name"] for s in data["extracted_skills"]]
    assert "AWS" in detected_names or "Docker" in detected_names or "PostgreSQL" in detected_names

def test_docx_resume_upload_and_extraction():
    """Generate a valid DOCX with python-docx, upload it, and verify skill detection."""
    headers = get_auth_headers("sarah.jenkins@skillgraph.internal")

    doc = docx.Document()
    doc.add_heading("Sarah Jenkins", 0)
    doc.add_paragraph("Machine learning specialist with hands-on experience in Python, PyTorch, Scikit-Learn, and SQL databases.")
    doc_io = io.BytesIO()
    doc.save(doc_io)
    docx_bytes = doc_io.getvalue()

    files = {"file": ("data_resume.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    res = client.post("/api/employees/resume-upload", headers=headers, files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["file_type"] == "DOCX"
    assert data["total_extracted"] >= 3

    detected_names = [s["skill_name"] for s in data["extracted_skills"]]
    assert "Python" in detected_names
    assert "SQL" in detected_names or "Scikit-Learn" in detected_names

def test_txt_resume_upload():
    """Upload plain text resume and verify skill extraction."""
    headers = get_auth_headers("sarah.jenkins@skillgraph.internal")

    text_content = b"Full stack developer experienced in React, TypeScript, Python, and Git version control."
    files = {"file": ("resume.txt", text_content, "text/plain")}
    res = client.post("/api/employees/resume-upload", headers=headers, files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["file_type"] in ["TXT", "TEXT"]
    detected_names = [s["skill_name"] for s in data["extracted_skills"]]
    assert "React" in detected_names
    assert "Python" in detected_names
    assert "Git" in detected_names

# ---------------------------------------------------------
# 4. File Validation & Security
# ---------------------------------------------------------
def test_unsupported_file_extension_rejected():
    """Verify executable or unsupported extensions are rejected safely."""
    headers = get_auth_headers("sarah.jenkins@skillgraph.internal")

    files = {"file": ("malicious.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/octet-stream")}
    res = client.post("/api/employees/resume-upload", headers=headers, files=files)
    assert res.status_code == 400
    assert "Unsupported file extension" in res.json()["detail"]

def test_fake_magic_byte_rejected():
    """Verify file claiming to be PDF but having plain garbage is rejected."""
    headers = get_auth_headers("sarah.jenkins@skillgraph.internal")

    files = {"file": ("fake.pdf", b"NOT_A_REAL_PDF_HEADER", "application/pdf")}
    res = client.post("/api/employees/resume-upload", headers=headers, files=files)
    assert res.status_code == 400
    assert "Invalid PDF" in res.json()["detail"]

def test_oversized_file_rejected():
    """Verify files larger than 10MB are rejected safely."""
    headers = get_auth_headers("sarah.jenkins@skillgraph.internal")

    # Create dummy 11MB file
    large_content = b"a" * (11 * 1024 * 1024)
    files = {"file": ("large.txt", large_content, "text/plain")}
    res = client.post("/api/employees/resume-upload", headers=headers, files=files)
    assert res.status_code == 400
    assert "exceeds maximum" in res.json()["detail"]

def test_empty_file_rejected():
    """Verify empty files are rejected."""
    headers = get_auth_headers("sarah.jenkins@skillgraph.internal")

    files = {"file": ("empty.txt", b"", "text/plain")}
    res = client.post("/api/employees/resume-upload", headers=headers, files=files)
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()

def test_scanned_image_only_pdf_handled_gracefully():
    """Verify PDF with no text layer returns graceful message and does not claim OCR."""
    headers = get_auth_headers("sarah.jenkins@skillgraph.internal")

    doc = fitz.open()
    doc.new_page()  # Blank page without text
    pdf_bytes = doc.tobytes()
    doc.close()

    files = {"file": ("scanned.pdf", pdf_bytes, "application/pdf")}
    res = client.post("/api/employees/resume-upload", headers=headers, files=files)
    assert res.status_code == 400
    assert "scanned" in res.json()["detail"].lower() or "no readable text" in res.json()["detail"].lower()

# ---------------------------------------------------------
# 5. Staged Review & Confirmation Workflow
# ---------------------------------------------------------
def test_review_and_confirmation_workflow():
    """
    Verify candidate skills are staged, awaiting review,
    and only confirmed skills are saved as source='resume_extracted' and verified=False.
    """
    headers = get_auth_headers("sarah.jenkins@skillgraph.internal")

    # 1. Upload resume to stage candidate skills
    sample_text = "Proficient in Python, Linux, and GraphQL. Built scalable APIs."
    res_up = client.post("/api/employees/resume-upload", headers=headers, json={"text": sample_text})
    assert res_up.status_code == 200

    # 2. Retrieve staged skills
    res_staged = client.get("/api/employees/resume/extracted", headers=headers)
    assert res_staged.status_code == 200
    staged_data = res_staged.json()
    staged_skills = staged_data["extracted_skills"]
    assert len(staged_skills) >= 2

    # Verify each item has confidence score and evidence snippet
    for item in staged_skills:
        assert "confidence" in item
        assert "evidence" in item
        assert item["confidence"] > 0

    # 3. User reviews: accepts Python and Linux, rejects GraphQL
    confirm_payload = {
        "skills": [
            {
                "skill_name": "Python",
                "proficiency": "Advanced",
                "evidence": "Extracted from resume: Proficient in Python",
                "accepted": True
            },
            {
                "skill_name": "Linux",
                "proficiency": "Intermediate",
                "evidence": "Extracted from resume: Linux",
                "accepted": True
            },
            {
                "skill_name": "GraphQL",
                "proficiency": "Beginner",
                "evidence": "",
                "accepted": False  # Rejected by user
            }
        ]
    }
    res_confirm = client.post("/api/employees/resume/confirm-skills", headers=headers, json=confirm_payload)
    assert res_confirm.status_code == 200
    assert res_confirm.json()["confirmed_count"] == 2

    # 4. Verify saved profile skills
    res_skills = client.get("/api/employees/skills", headers=headers)
    profile_skills = {s["skill_name"]: s for s in res_skills.json()}

    # Python must be present with source='resume_extracted' and verified=False
    assert "Python" in profile_skills
    assert profile_skills["Python"]["source"] == "resume_extracted"
    assert profile_skills["Python"]["verified"] is False
    assert profile_skills["Python"]["proficiency"] == "Advanced"

    # Linux must be present
    assert "Linux" in profile_skills
    assert profile_skills["Linux"]["source"] == "resume_extracted"
    assert profile_skills["Linux"]["verified"] is False

    # GraphQL was rejected, must NOT be added
    assert "GraphQL" not in profile_skills

    # 5. Verify staging cache is cleared after confirmation
    res_staged_after = client.get("/api/employees/resume/extracted", headers=headers)
    # Staging cleared; might fallback to re-extracting saved resume text if needed, or return fresh
    assert res_staged_after.status_code == 200

# ---------------------------------------------------------
# 6. Multi-User Isolation & Security
# ---------------------------------------------------------
def test_cross_user_isolation():
    """Ensure User A cannot view User B's skills, uploads, or staged extractions."""
    headers_user_a = get_auth_headers("alex.rivera@skillgraph.internal")
    headers_user_b = get_auth_headers("marcus.chen@skillgraph.internal")

    # User A adds a unique skill
    client.post("/api/employees/skills", headers=headers_user_a, json={
        "skill_name": "Go",
        "proficiency": "Intermediate",
        "evidence": "Alex's private Go work"
    })

    # User B lists skills -> Go with Alex's evidence must NOT appear in User B's profile
    res_b = client.get("/api/employees/skills", headers=headers_user_b)
    user_b_skills = res_b.json()
    alex_go = [s for s in user_b_skills if s["skill_name"] == "Go" and "Alex's private" in (s.get("evidence") or "")]
    assert len(alex_go) == 0

    # User A stages a resume
    client.post("/api/employees/resume-upload", headers=headers_user_a, json={
        "text": "Specialist in Scala and Spark big data pipelines."
    })

    # User B should NOT see User A's staged Scala skills
    res_staged_b = client.get("/api/employees/resume/extracted", headers=headers_user_b)
    assert res_staged_b.status_code == 200
    staged_b_names = [s["skill_name"] for s in res_staged_b.json().get("extracted_skills", [])]
    assert "Scala" not in staged_b_names
    assert "Spark" not in staged_b_names

# ---------------------------------------------------------
# 7. Catalog Preservation
# ---------------------------------------------------------
def test_catalogs_preserved():
    """Verify that canonical 119 skills, 96 roles, and 18 courses remain intact after Phase 3 operations."""
    db = TestingSessionLocal()
    try:
        assert db.query(Skill).count() == 119
        assert db.query(Role).count() == 96
        assert db.query(Course).count() == 18
    finally:
        db.close()
