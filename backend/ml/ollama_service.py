"""
Ollama Qwen AI Service for SkillGraph.
Connects to local Ollama instance running Qwen (e.g. qwen2.5:1.5b / qwen2.5:0.5b)
to generate tailored executive career transition plans, weekly study guides, and milestone coaching.
"""

import os
import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_DEFAULT_MODEL", "qwen2.5:1.5b")

def get_ollama_status() -> Dict[str, Any]:
    """Checks if local Ollama daemon is reachable and lists installed models."""
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SkillGraph/1.0"})
        with urllib.request.urlopen(req, timeout=3) as res:
            if res.status == 200:
                data = json.loads(res.read().decode("utf-8"))
                models = [m.get("name") for m in data.get("models", [])]
                qwen_models = [m for m in models if "qwen" in m.lower()]
                active_model = qwen_models[0] if qwen_models else (models[0] if models else DEFAULT_MODEL)
                return {
                    "available": True,
                    "active_model": active_model,
                    "qwen_models": qwen_models,
                    "all_models": models,
                    "base_url": OLLAMA_BASE_URL
                }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
            "active_model": DEFAULT_MODEL,
            "qwen_models": [],
            "all_models": [],
            "base_url": OLLAMA_BASE_URL
        }

def build_qwen_plan_prompt(
    employee_name: str,
    current_role: str,
    exp_years: int,
    target_role_title: str,
    target_role_dept: str,
    target_role_exp: int,
    current_skills: List[str],
    milestones: List[Dict[str, Any]],
    gaps: List[Dict[str, Any]],
    unaddressed_gaps: List[Dict[str, Any]]
) -> str:
    """Builds a structured prompt optimized for Qwen 2.5 instruction tuning."""
    
    gaps_summary = []
    for g in gaps[:6]:
        sk = g.get("skill_name") or g.get("name") or "Skill"
        prio = g.get("priority", "Medium")
        cls = g.get("classification", "missing")
        gaps_summary.append(f"- {sk} ({cls}, {prio} priority)")
    
    courses_summary = []
    for m in milestones[:6]:
        order = m.get("step_order", 1)
        title = m.get("title", "Course")
        dur = m.get("duration_weeks", 4)
        skills = ", ".join(m.get("targeted_skills", m.get("skills_taught", []))[:3])
        courses_summary.append(f"{order}. {title} ({dur} wks) -> Targets: {skills or 'Core competencies'}")

    unaddressed_summary = [u.get("skill_name", "") for u in unaddressed_gaps[:4] if u.get("skill_name")]

    return f"""You are an elite Engineering Career Coach & Principal Systems Architect.
Generate a high-impact, professional career transition and personalized study plan for an engineer upskilling for an internal mobility promotion.

Candidate Profile:
- Name: {employee_name}
- Current Position: {current_role} ({exp_years} yrs professional experience)
- Target Position: {target_role_title} ({target_role_dept} Dept, requires {target_role_exp} yrs)
- Demonstrated Skills: {', '.join(current_skills[:8]) if current_skills else 'Baseline competencies'}

Key Skill Gaps Identified:
{chr(10).join(gaps_summary) if gaps_summary else '- None (Fully qualified)'}

Prerequisite-Ordered Course Milestones (Topological DAG):
{chr(10).join(courses_summary) if courses_summary else '- Self-guided curriculum'}

Skills Not Covered in Course Catalog (Independent Study):
{', '.join(unaddressed_summary) if unaddressed_summary else 'All key gaps covered by internal courses'}

Generate the plan formatted in clean GitHub Markdown using these exact 4 sections:
### 1. Executive Career Strategy & Transition Assessment
Provide a 2-3 sentence strategic evaluation of how feasible this career transition is, key leverage from current skills, and the target trajectory.

### 2. Phased Study Roadmap & Weekly Rhythm
Break down the sequence into 2-3 clear phases (Foundations -> Intermediate -> Production Readiness) aligned with the course milestones. Include suggested weekly study hours and focus areas.

### 3. Bridging Missing Gaps & Practical Labs
Give 2 actionable hands-on project ideas or lab exercises that prove competence in the target role, and how to address unaddressed gaps.

### 4. Senior Coach Advice & Pitfalls to Avoid
Highlight 2 critical engineering pitfalls candidates make when interviewing or transitioning into this specific role.

Keep it structured, realistic, and directly relevant to {target_role_title}. Do not generate unnecessary filler.
"""

def generate_plan_with_qwen(
    employee_name: str,
    current_role: str,
    exp_years: int,
    target_role_title: str,
    target_role_dept: str,
    target_role_exp: int,
    current_skills: List[str],
    milestones: List[Dict[str, Any]],
    gaps: List[Dict[str, Any]],
    unaddressed_gaps: List[Dict[str, Any]],
    model_name: Optional[str] = None
) -> Dict[str, Any]:
    """Queries local Ollama Qwen model to generate a custom career transition plan."""
    start_time = time.time()
    
    # 1. Determine model
    status_info = get_ollama_status()
    selected_model = model_name or status_info.get("active_model") or DEFAULT_MODEL
    
    # 2. Build prompt
    prompt = build_qwen_plan_prompt(
        employee_name=employee_name,
        current_role=current_role,
        exp_years=exp_years,
        target_role_title=target_role_title,
        target_role_dept=target_role_dept,
        target_role_exp=target_role_exp,
        current_skills=current_skills,
        milestones=milestones,
        gaps=gaps,
        unaddressed_gaps=unaddressed_gaps
    )

    if not status_info.get("available"):
        # Graceful fallback plan if Ollama is not running
        fallback_plan = f"""### 1. Executive Career Strategy & Transition Assessment
{employee_name} has a solid foundation as a {current_role} with {exp_years} years of experience. Transitioning to **{target_role_title}** in the {target_role_dept} department requires mastering critical infrastructure and domain competencies. With {len(milestones)} structured courses mapped out, the transition is realistic within the projected timeline.

### 2. Phased Study Roadmap & Weekly Rhythm
- **Phase 1: Foundations**: Focus on the early prerequisite courses ({milestones[0].get('title', 'Fundamental coursework') if milestones else 'Initial coursework'}). Dedicate 5-7 hours per week to core theory and basic syntax.
- **Phase 2: Core Engineering**: Work through containerization, cloud systems, and service integration. Build reproducible environments for each module.
- **Phase 3: Production Readiness**: Complete advanced capstones and mock deployments under simulated production constraints.

### 3. Bridging Missing Gaps & Practical Labs
- **Lab 1**: Build and deploy an automated end-to-end multi-tier application using the target role's core toolchain.
- **Lab 2**: Document a disaster-recovery and monitoring playbook demonstrating operational readiness.

### 4. Senior Coach Advice & Pitfalls to Avoid
- **Pitfall 1**: Memorizing tools instead of understanding underlying architecture and failure modes.
- **Pitfall 2**: Neglecting security boundaries and compliance practices during transition practice.
"""
        return {
            "status": "fallback",
            "model_used": "deterministic-fallback",
            "plan_markdown": fallback_plan,
            "execution_time_seconds": round(time.time() - start_time, 2),
            "message": "Ollama service was not reachable; generated deterministic engineering plan."
        }

    # 3. Call Ollama API
    generate_url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate"
    payload = {
        "model": selected_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.35,
            "num_predict": 550,
            "top_p": 0.9
        }
    }

    try:
        req = urllib.request.Request(
            generate_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=90) as res:
            if res.status == 200:
                raw_data = json.loads(res.read().decode("utf-8"))
                plan_text = raw_data.get("response", "").strip()
                elapsed = round(time.time() - start_time, 2)
                return {
                    "status": "success",
                    "model_used": selected_model,
                    "plan_markdown": plan_text,
                    "execution_time_seconds": elapsed,
                    "message": f"Successfully generated customized career plan using local {selected_model} in {elapsed}s."
                }
            else:
                raise Exception(f"Ollama returned HTTP status {res.status}")
    except Exception as e:
        elapsed = round(time.time() - start_time, 2)
        return {
            "status": "error",
            "model_used": selected_model,
            "plan_markdown": None,
            "execution_time_seconds": elapsed,
            "error": str(e),
            "message": f"Failed to generate plan via Ollama {selected_model}: {str(e)}"
        }

