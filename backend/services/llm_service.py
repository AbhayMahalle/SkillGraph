"""
LLM Service for SkillGraph.
Bridges business logic to external LLM providers, injecting authentic ontology catalogs,
formatting contextual prompts, and applying server-side validation and canonical normalization.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.database.db import REPO_ROOT
from backend.ai.llm.base import LLMProvider, LLMConfigurationError, LLMResponseError
from backend.ai.llm.factory import get_llm_client
from backend.ai.llm.prompts import load_prompt
from backend.ai.llm.schemas import (
    ResumeAnalysisResponse,
    ExtractedSkill,
    LearningPlanResponse,
    LearningPlanStep
)

PROCESSED_DIR = Path(os.getenv("PROCESSED_DIR", str(REPO_ROOT / "data" / "processed")))

class LLMService:
    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or get_llm_client()
        self.canonical_skills: Dict[str, Dict[str, Any]] = {}
        self.canonical_roles: Dict[str, Dict[str, Any]] = {}
        self.course_catalog: Dict[str, Dict[str, Any]] = {}
        self._load_catalogs()

    def _load_catalogs(self):
        """Loads canonical reference datasets from processed directory."""
        skills_path = PROCESSED_DIR / "canonical_skills.json"
        if skills_path.exists():
            with open(skills_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for s in data:
                    self.canonical_skills[s["name"].lower()] = s
                    for alias in s.get("aliases", []):
                        self.canonical_skills[alias.lower().strip()] = s

        roles_path = PROCESSED_DIR / "canonical_roles.json"
        if roles_path.exists():
            with open(roles_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for r in data:
                    self.canonical_roles[r["role_id"]] = r

        courses_path = PROCESSED_DIR / "course_catalog.json"
        if courses_path.exists():
            with open(courses_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for c in data:
                    self.course_catalog[c["course_id"]] = c

    def is_configured(self) -> bool:
        """Returns True if the underlying LLM provider is configured with credentials."""
        return self.provider.is_available()

    def analyze_resume(self, resume_text: str, filename: Optional[str] = None) -> ResumeAnalysisResponse:
        """
        Submits candidate resume text to the external LLM API for structured skill extraction.
        Injects canonical skill ontology for exact entity linking.
        """
        if not self.is_configured():
            raise LLMConfigurationError(
                "External LLM API is not configured. Please set LLM_API_KEY (and optionally LLM_PROVIDER / LLM_MODEL) "
                "in your environment to enable AI-powered resume intelligence."
            )

        system_prompt = load_prompt("resume_skill_extraction.txt")

        # Provide brief canonical ontology summary (first 50 skills)
        sample_skills = list({s["name"]: s["skill_id"] for s in self.canonical_skills.values()}.items())[:60]
        ontology_context = "\n".join([f"- {name} (ID: {sid})" for name, sid in sample_skills])

        user_prompt = f"""CANONICAL SKILLS ONTOLOGY REFERENCE (Map detected skills to these IDs where applicable):
{ontology_context}

---
CANDIDATE RESUME TEXT TO ANALYZE (Filename: {filename or 'resume.txt'}):
{resume_text}

Extract all demonstrated technical and professional skills, estimate practical proficiency (Beginner, Intermediate, Advanced, Expert) and proficiency percentage (0-100), extract supporting context citations, evaluate limitations, and output strictly valid JSON.
"""

        response = self.provider.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=True,
            temperature=0.15
        )

        raw_json = response.get("content")
        if not isinstance(raw_json, dict):
            raise LLMResponseError("LLM response did not parse into a dictionary.")

        # Validate with Pydantic
        parsed = ResumeAnalysisResponse.model_validate(raw_json)

        # Canonical normalization & guardrail enforcement
        normalized_skills = []
        for sk in parsed.skills:
            sk_lower = sk.skill_name.lower().strip()
            if sk_lower in self.canonical_skills:
                canonical_meta = self.canonical_skills[sk_lower]
                sk.skill_name = canonical_meta["name"]
                sk.canonical_skill_id = canonical_meta["skill_id"]
                if not sk.category or sk.category == "General Technology":
                    sk.category = canonical_meta.get("category", "General Technology")
            sk.verified = False
            sk.requires_review = True
            normalized_skills.append(sk)

        parsed.skills = normalized_skills
        return parsed

    def generate_personalized_learning_plan(
        self,
        employee_name: str,
        current_role: str,
        exp_years: int,
        target_role_id: str,
        current_skills: List[Dict[str, Any]],
        skill_gaps: List[Dict[str, Any]],
        completed_course_ids: Optional[List[str]] = None
    ) -> LearningPlanResponse:
        """
        Sends structured profile, gap breakdown, and internal course catalog to external LLM
        to formulate a prerequisite-aware personalized learning plan.
        """
        if not self.is_configured():
            raise LLMConfigurationError(
                "External LLM API is not configured. Please set LLM_API_KEY in your environment."
            )

        role_info = self.canonical_roles.get(target_role_id)
        if not role_info:
            raise ValueError(f"Target role '{target_role_id}' not found in canonical role catalog.")

        system_prompt = load_prompt("learning_plan_generation.txt")

        # Format Course Catalog Context
        catalog_lines = []
        for cid, c in self.course_catalog.items():
            pre_str = ", ".join(c.get("prerequisites", [])) or "None"
            skills_str = ", ".join(c.get("skills_taught", []))
            catalog_lines.append(
                f"- Course ID: {cid} | Title: {c['title']} | Duration: {c['duration_weeks']} wks | "
                f"Level: {c['level']} | Teaches: {skills_str} | Prerequisites: [{pre_str}]"
            )
        catalog_context = "\n".join(catalog_lines)

        # Format Skills and Gaps Context
        skills_summary = ", ".join([f"{s.get('name', s.get('skill_name'))} ({s.get('proficiency', 'Intermediate')})" for s in current_skills[:12]])
        gaps_summary = "\n".join([
            f"- {g.get('skill_name')}: {g.get('classification', 'missing')} | Priority: {g.get('priority', 'Medium')} | Required: {g.get('required_proficiency', 'Intermediate')}"
            for g in skill_gaps[:10]
        ])

        user_prompt = f"""INTERNAL COURSE CATALOG (You MUST recommend ONLY courses from this list):
{catalog_context}

---
EMPLOYEE CANDIDATE PROFILE:
- Name: {employee_name}
- Current Position: {current_role} ({exp_years} years experience)
- Demonstrated Skills: {skills_summary or 'None registered'}
- Already Completed Courses: {', '.join(completed_course_ids or []) or 'None'}

---
TARGET CAREER ROLE:
- Role Title: {role_info['title']} (ID: {role_info['role_id']})
- Department: {role_info.get('department', 'Engineering')}
- Benchmark Experience: {role_info.get('experience_years', 2)} years
- Required Skills: {', '.join(role_info.get('required_skills', []))}

---
IDENTIFIED SKILL GAPS:
{gaps_summary or 'No missing gaps identified.'}

Formulate a sequenced learning plan using only internal courses, respecting prerequisite DAG order, prioritizing critical gaps, with portfolio projects and clear outcomes. Output strictly valid JSON.
"""

        response = self.provider.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=True,
            temperature=0.2
        )

        raw_json = response.get("content")
        if not isinstance(raw_json, dict):
            raise LLMResponseError("LLM learning plan response did not parse into a dictionary.")

        parsed = LearningPlanResponse.model_validate(raw_json)

        # Post-process: Validate all recommended courses exist in authentic course catalog
        validated_milestones = []
        for step in parsed.milestones:
            if step.recommended_course_id and step.recommended_course_id not in self.course_catalog:
                # Attempt to find matching course by title or taught skill
                matched_cid = None
                for cid, cinfo in self.course_catalog.items():
                    if step.skill_name.lower() in [s.lower() for s in cinfo.get("skills_taught", [])]:
                        matched_cid = cid
                        step.recommended_course_id = cid
                        step.recommended_course_title = cinfo["title"]
                        step.prerequisites = cinfo.get("prerequisites", [])
                        break
                if not matched_cid:
                    step.recommended_course_id = None
            elif step.recommended_course_id in self.course_catalog:
                cinfo = self.course_catalog[step.recommended_course_id]
                step.recommended_course_title = cinfo["title"]
                step.prerequisites = cinfo.get("prerequisites", [])

            validated_milestones.append(step)

        parsed.milestones = validated_milestones
        parsed.total_estimated_weeks = sum(m.estimated_duration_weeks for m in validated_milestones)
        return parsed
