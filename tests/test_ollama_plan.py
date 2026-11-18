"""
Tests for Ollama Qwen AI Learning Plan Generation.
Verifies service detection, fallback behavior, prompt formatting, and API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.ml.ollama_service import get_ollama_status, build_qwen_plan_prompt, generate_plan_with_qwen
from backend.api.auth import create_access_token

client = TestClient(app)

def test_ollama_status():
    status = get_ollama_status()
    assert isinstance(status, dict)
    assert "available" in status
    assert "active_model" in status
    assert "base_url" in status

def test_build_qwen_plan_prompt():
    prompt = build_qwen_plan_prompt(
        employee_name="Alex Rivera",
        current_role="Software Engineer",
        exp_years=3,
        target_role_title="Cloud Engineer",
        target_role_dept="Platform",
        target_role_exp=2,
        current_skills=["Python", "Docker"],
        milestones=[{"step_order": 1, "title": "Kubernetes Mastery", "duration_weeks": 4, "targeted_skills": ["Kubernetes"]}],
        gaps=[{"skill_name": "Kubernetes", "priority": "Critical", "classification": "missing"}],
        unaddressed_gaps=[{"skill_name": "Linux", "priority": "Medium"}]
    )
    assert "Alex Rivera" in prompt
    assert "Cloud Engineer" in prompt
    assert "Kubernetes" in prompt
    assert "Linux" in prompt

def test_generate_plan_fallback_or_success():
    res = generate_plan_with_qwen(
        employee_name="Alex Rivera",
        current_role="Software Engineer",
        exp_years=3,
        target_role_title="Cloud Engineer",
        target_role_dept="Platform",
        target_role_exp=2,
        current_skills=["Python", "Docker"],
        milestones=[{"step_order": 1, "title": "Kubernetes Mastery", "duration_weeks": 4}],
        gaps=[{"skill_name": "Kubernetes", "priority": "Critical"}],
        unaddressed_gaps=[]
    )
    assert res["status"] in ("success", "fallback")
    assert res["plan_markdown"] is not None
    assert len(res["plan_markdown"]) > 50

def test_api_llm_status_endpoint():
    res = client.get("/api/llm/status")
    assert res.status_code == 200
    data = res.json()
    assert "available" in data
    assert "active_model" in data

def test_api_roadmap_ai_plan_requires_auth():
    res = client.post("/api/roadmap/ai-plan", json={"target_role_id": "ROL-001"})
    assert res.status_code in (401, 403)

def test_api_roadmap_ai_plan_with_auth():
    token = create_access_token({"sub": "alex.rivera@skillgraph.internal", "role": "EMPLOYEE", "employee_id": "EMP-001"})
    res = client.post(
        "/api/roadmap/ai-plan",
        json={"target_role_id": "ROL-001", "model_name": "qwen2.5:0.5b"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "ai_plan" in data
    assert "roadmap" in data
    assert data["ai_plan"]["status"] in ("success", "fallback")

