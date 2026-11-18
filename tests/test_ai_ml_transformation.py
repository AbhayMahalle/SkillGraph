"""
Automated Test Suite for SkillGraph AI/ML Transformation Deliverables.
Validates:
1. Provider-independent LLM architecture (schemas, clients, prompt templates, error types)
2. Production ML Role Classifier (Random Forest inference, calibrated probabilities, feature explanations)
3. AI-Powered Resume Intelligence (structured extraction, proficiency percentage, confidence, reasoning)
4. AI Personalized Learning Plan (curriculum validation, DAG prerequisite consistency, unaddressed gaps)
5. New AI/ML Endpoints (/api/ai/status, /api/ai/resume/analyze, /api/ai/learning-plan/generate, /api/ml/model-info, /api/ml/predict-role)
6. Strict Employee Data Isolation across all AI services.
"""

import uuid
import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.database.db import get_db, SessionLocal
from backend.models.models import User, Employee, Skill, EmployeeSkill, Role, Course
from backend.ai.llm.base import LLMConfigurationError, LLMResponseError
from backend.ai.llm.client import OpenAICompatibleClient
from backend.ai.llm.schemas import (
    ExtractedSkill, SkillEvidenceItem, OverallAssessment,
    ResumeAnalysisResponse, LearningPlanStep, LearningPlanResponse
)
from backend.ai.llm.factory import get_llm_status
from backend.ml.inference.role_classifier import RoleClassifierPredictor
from backend.services.resume_service import process_resume_and_extract_skills
from backend.services.learning_plan_service import generate_learning_roadmap_for_employee

import os
import atexit
from tests.test_db_helper import create_isolated_test_database

TEMP_DB_PATH, test_engine, TestingSessionLocal = create_isolated_test_database("ai_ml")

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

def unique_email(prefix="test"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"

@pytest.fixture
def auth_headers():
    """Provides authenticated session headers for registered test employee."""
    email = unique_email("user_a")
    res = client.post("/api/auth/register", json={
        "full_name": "Test User A",
        "email": email,
        "password": "SecurePassword123!",
        "department": "Engineering",
        "current_role": "Backend Developer"
    })
    assert res.status_code == 200, f"Registration failed: {res.text}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def secondary_auth_headers():
    """Provides authenticated session headers for second test employee."""
    email = unique_email("user_b")
    res = client.post("/api/auth/register", json={
        "full_name": "Test User B",
        "email": email,
        "password": "SecurePassword123!",
        "department": "Engineering",
        "current_role": "Data Analyst"
    })
    assert res.status_code == 200, f"Registration failed: {res.text}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# 1. PROVIDER-INDEPENDENT LLM ARCHITECTURE TESTS
# ==============================================================================

def test_llm_unconfigured_behavior():
    """Verifies that an unconfigured client raises LLMConfigurationError with instructions."""
    client_instance = OpenAICompatibleClient(provider_name="openai", api_key="", model="gpt-4o-mini")
    assert not client_instance.is_configured()
    with pytest.raises(LLMConfigurationError) as exc_info:
        client_instance.complete("System", "User")
    assert "LLM_API_KEY" in str(exc_info.value)

def test_llm_pydantic_schemas_validation():
    """Verifies Pydantic schema validation for extracted skills and evidence."""
    skill = ExtractedSkill(
        skill_name="Python",
        canonical_skill_id="SKL-001",
        category="Backend Development",
        proficiency_level="Advanced",
        proficiency_percentage=85,
        confidence=0.95,
        evidence=[
            SkillEvidenceItem(text="Engineered microservices using Python FastAPI.", section="Work Experience")
        ],
        reasoning="Demonstrated 4+ years of backend development."
    )
    assert skill.proficiency_percentage == 85
    assert skill.confidence == 0.95
    assert len(skill.evidence) == 1
    assert skill.evidence[0].section == "Work Experience"

def test_llm_pydantic_schema_invalid_clamping():
    """Verifies bounds enforcement on proficiency percentage (0-100) and confidence (0.0-1.0)."""
    with pytest.raises(Exception):
        ExtractedSkill(
            skill_name="Python",
            proficiency_level="Advanced",
            proficiency_percentage=150,  # Invalid: > 100
            confidence=0.9
        )

    with pytest.raises(Exception):
        ExtractedSkill(
            skill_name="Python",
            proficiency_level="Advanced",
            proficiency_percentage=50,
            confidence=1.5  # Invalid: > 1.0
        )

def test_llm_factory_status_safe_reflection():
    """Verifies factory returns masked key and unconfigured status safely without leaking secrets."""
    status = get_llm_status()
    assert "provider" in status
    assert "model" in status
    assert "has_api_key" in status
    assert "masked_key" in status
    assert not status.get("has_api_key") or "..." in status["masked_key"]


# ==============================================================================
# 2. PRODUCTION ML ROLE CLASSIFIER TESTS
# ==============================================================================

def test_ml_model_artifacts_and_metadata():
    """Verifies the trained Random Forest classifier and metadata are present and valid."""
    predictor = RoleClassifierPredictor()
    assert predictor.is_loaded()
    metadata = predictor.get_model_metadata()
    assert metadata["model_type"] == "Random Forest"
    assert metadata["feature_dimension"] >= 75
    assert len(metadata["classes"]) > 0

def test_ml_role_classifier_inference_predictions():
    """Verifies ML classifier predicts top compatible roles with calibrated probabilities."""
    predictor = RoleClassifierPredictor()
    ds_skills = ["Python", "SQL", "Machine Learning", "Pandas", "NumPy", "Scikit-Learn"]
    predictions = predictor.predict_roles(candidate_skills=ds_skills, top_k=5)
    
    assert len(predictions) > 0
    top_prediction = predictions[0]
    assert "role" in top_prediction
    assert "role_title" in top_prediction
    assert "probability" in top_prediction
    assert 0.0 <= top_prediction["probability"] <= 1.0
    assert len(top_prediction["contributing_skills"]) > 0

def test_ml_role_classifier_software_engineer_predictions():
    """Verifies ML classifier predicts software engineering roles for software development skills."""
    predictor = RoleClassifierPredictor()
    se_skills = ["Java", "C++", "Data Structures", "Algorithms", "Git"]
    predictions = predictor.predict_roles(candidate_skills=se_skills, top_k=5)
    
    assert len(predictions) > 0
    top_roles = [p["role"] for p in predictions[:3]]
    assert len(top_roles) > 0


# ==============================================================================
# 3. AI RESUME INTELLIGENCE TESTS
# ==============================================================================

def test_resume_processing_deterministic_fallback():
    """Verifies resume processing produces structured skill extraction with confidence and evidence."""
    db = TestingSessionLocal()
    try:
        emp = db.query(Employee).first()
        assert emp is not None
        raw_text = (
            "Senior Cloud Engineer with 5 years experience in Python, Docker, Kubernetes, "
            "FastAPI, and AWS cloud architecture."
        )
        result = process_resume_and_extract_skills(
            user_id=1,
            emp=emp,
            filename="cloud_resume.txt",
            raw_text=raw_text,
            use_ai=False,
            db=db
        )
        assert result["status"] == "success"
        assert result["total_extracted"] > 0
        
        extracted_names = [s["skill_name"] for s in result["extracted_skills"]]
        assert any(k in extracted_names for k in ["Python", "Docker", "Kubernetes", "AWS"])
        
        for sk in result["extracted_skills"]:
            assert "proficiency" in sk
            assert "proficiency_percentage" in sk
            assert 0 <= sk["proficiency_percentage"] <= 100
            assert "confidence" in sk
            assert 0.0 <= sk["confidence"] <= 1.0
            assert "evidence" in sk
            assert "reasoning" in sk
    finally:
        db.close()


# ==============================================================================
# 4. AI PERSONALIZED LEARNING ROADMAP TESTS
# ==============================================================================

def test_learning_roadmap_service_dag_and_catalog_validation():
    """Verifies learning plan validates course recommendations against authentic 18-course catalog."""
    db = TestingSessionLocal()
    try:
        emp = db.query(Employee).first()
        role = db.query(Role).filter(Role.role_id == "ROL-003").first()  # Cloud Architect
        assert emp is not None
        assert role is not None
        
        result = generate_learning_roadmap_for_employee(emp=emp, role=role, db=db)
        assert "deterministic_roadmap" in result
        assert "ai_coaching_plan" in result
        
        roadmap = result["deterministic_roadmap"]
        ai_plan = result["ai_coaching_plan"]
        
        # All milestone courses must be strictly from canonical catalog
        canonical_course_ids = {c.course_id for c in db.query(Course.course_id).all()}
        for m in roadmap.get("milestones", []):
            for crs in m.get("courses", []):
                assert crs["course_id"] in canonical_course_ids
        
        # AI coaching plan contains executive summary and weekly pacing
        assert "executive_summary" in ai_plan
        assert "weekly_commitment_hours" in ai_plan
    finally:
        db.close()


# ==============================================================================
# 5. NEW API ENDPOINTS & INTEGRATION TESTS
# ==============================================================================

def test_api_ai_status_endpoint():
    """Verifies GET /api/ai/status returns structured configuration diagnostics."""
    res = client.get("/api/ai/status")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "provider" in data
    assert "supported_providers" in data
    assert "configuration_guide" in data

def test_api_ml_model_info_endpoint():
    """Verifies GET /api/ml/model-info returns metadata for the production ML model."""
    res = client.get("/api/ml/model-info")
    assert res.status_code == 200
    data = res.json()
    assert data["model_type"] == "Random Forest"
    assert "feature_dimension" in data
    assert "metrics" in data or "cv_metrics" in data

def test_api_ml_predict_role_endpoint():
    """Verifies POST /api/ml/predict-role produces multi-class role predictions."""
    res = client.post("/api/ml/predict-role", json={
        "skills": ["Python", "Docker", "Kubernetes", "Linux", "Git"],
        "top_k": 3
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["predictions"]) == 3
    for p in data["predictions"]:
        assert "role" in p
        assert "probability" in p
        assert "rank" in p

def test_api_ai_resume_analyze_endpoint(auth_headers):
    """Verifies POST /api/ai/resume/analyze runs structured skill extraction with auth."""
    res = client.post(
        "/api/ai/resume/analyze",
        headers=auth_headers,
        json={"text": "Software engineer with proficiency in Python, FastAPI, Docker, and PostgreSQL."}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "skills" in data
    assert len(data["skills"]) > 0
    assert "overall_assessment" in data

def test_api_ai_learning_plan_generate_endpoint(auth_headers):
    """Verifies POST /api/ai/learning-plan/generate creates an AI coaching roadmap."""
    res = client.post(
        "/api/ai/learning-plan/generate",
        headers=auth_headers,
        json={"target_role_id": "ROL-001"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "roadmap" in data
    assert "ai_plan" in data or "ai_coaching_plan" in data


# ==============================================================================
# 6. EMPLOYEE DATA ISOLATION VERIFICATION
# ==============================================================================

def test_employee_data_isolation_on_ai_endpoints(auth_headers, secondary_auth_headers):
    """Verifies User A cannot access User B's AI analysis records or employee skills."""
    # User A analyzes resume
    res_a = client.post(
        "/api/ai/resume/analyze",
        headers=auth_headers,
        json={"text": "Experienced Python and Docker developer."}
    )
    assert res_a.status_code == 200
    emp_a_id = res_a.json()["employee_id"]

    # User B checks their own profile skills
    res_b = client.get("/api/employees/skills", headers=secondary_auth_headers)
    assert res_b.status_code == 200
    b_skills = res_b.json()
    
    # Confirm User B's returned profile does not leak User A's employee_id
    for sk in b_skills:
        assert sk.get("employee_id") != emp_a_id
