"""
SkillGraph REST API Endpoints.
Covers Auth, Employee Profiles, Resume NLP parsing, Role Matching, Skill Gap Analysis,
Prerequisite Learning Paths, What-If Simulation, Knowledge Graph, HR Workforce Planning,
and Research Dataset Summaries.
"""

import os
import json
import uuid
import re
from datetime import datetime
import pandas as pd
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.db import get_db, REPO_ROOT
from backend.models.models import (
    User, Employee, Skill, EmployeeSkill, Role, RoleSkill,
    Course, CourseSkill, CoursePrerequisite, EmployeeCourse, EmployeeRoadmap
)
from backend.api.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, revoke_token, security
)
from backend.ml.skill_extraction import skill_extractor, normalize_skill_name
from backend.ml.resume_parser import validate_and_extract_text, save_uploaded_resume, ResumeParsingError
from backend.ml.role_matching import calculate_role_match
from backend.ml.readiness import readiness_predictor
from backend.ml.learning_path import learning_path_generator
from backend.graph.skill_graph import skill_graph_manager

api_router = APIRouter()

PROCESSED_DIR = os.getenv("PROCESSED_DIR", str(REPO_ROOT / "data" / "processed"))
RAW_DIR = os.getenv("RAW_DIR", str(REPO_ROOT / "data" / "raw"))

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------
class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    department: Optional[str] = "Engineering"
    current_role: Optional[str] = "Software Engineer"

class LoginRequest(BaseModel):
    email: str
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class UpdateUserMeRequest(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    department: Optional[str] = None
    target_role_id: Optional[str] = None
    experience_years: Optional[int] = None
    qualification: Optional[str] = None

class DemoLoginRequest(BaseModel):
    employee_id: Optional[str] = None

VALID_PROFICIENCIES = {"Beginner", "Intermediate", "Advanced", "Expert"}
VALID_SOURCES = {"self_reported", "resume_extracted", "project", "assessment"}

class SkillAddRequest(BaseModel):
    skill_name: str
    proficiency: str = "Intermediate"  # Beginner, Intermediate, Advanced, Expert
    source: Optional[str] = "self_reported"
    evidence: Optional[str] = None

class SkillUpdateRequest(BaseModel):
    proficiency: str
    evidence: Optional[str] = None
    source: Optional[str] = None

class SkillConfirmItem(BaseModel):
    skill_name: str
    proficiency: str = "Intermediate"
    evidence: Optional[str] = None
    accepted: bool = True

class ConfirmSkillsRequest(BaseModel):
    skills: List[SkillConfirmItem]

# In-memory staging for extracted skills pending user review (keyed by user_id)
STAGED_RESUME_EXTRACTIONS: Dict[int, Dict[str, Any]] = {}

class TargetRoleRequest(BaseModel):
    target_role_id: Optional[str] = None
    role_id: Optional[str] = None

class ProfileUpdateRequest(BaseModel):
    target_role_id: Optional[str] = None
    bio: Optional[str] = None
    department: Optional[str] = None

class ResumeTextRequest(BaseModel):
    text: str

class CourseProgressUpdate(BaseModel):
    status: str
    progress_pct: Optional[int] = None

class RoadmapRefreshRequest(BaseModel):
    target_role_id: Optional[str] = None

class HypotheticalSkill(BaseModel):
    skill_name: Optional[str] = None
    skill_id: Optional[str] = None
    proficiency: str = "Intermediate"

class WhatIfRequest(BaseModel):
    target_role_id: str
    skills: List[HypotheticalSkill] = []
    additional_skills: List[str] = []
    completed_course_ids: List[str] = []

# ---------------------------------------------------------
# Auth & User Endpoints
# ---------------------------------------------------------
@api_router.post("/auth/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Registers a new personal account with an isolated profile and PBKDF2-hashed credentials."""
    # 1. Normalize and validate email
    email = req.email.strip().lower()
    if not email or not EMAIL_REGEX.match(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid email address is required"
        )

    # 2. Validate full_name
    full_name = req.full_name.strip()
    if not full_name or len(full_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Full name must be at least 2 characters long"
        )

    # 3. Validate password
    if not req.password or len(req.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    # 4. Check uniqueness in users and employees
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    existing_emp = db.query(Employee).filter(Employee.email == email).first()
    if existing_emp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An employee account with this email already exists"
        )

    # 5. Generate unique employee_id
    new_emp_id = f"EMP-{uuid.uuid4().hex[:8].upper()}"
    while db.query(Employee).filter(Employee.employee_id == new_emp_id).first():
        new_emp_id = f"EMP-{uuid.uuid4().hex[:8].upper()}"

    # 6. Create Employee profile
    new_emp = Employee(
        employee_id=new_emp_id,
        name=full_name,
        email=email,
        current_role=req.current_role.strip() if req.current_role else "Software Engineer",
        department=req.department.strip() if req.department else "Engineering",
        experience_years=1,
        qualification="Bachelor's Degree",
        target_role_id="ROL-001",
        bio="",
        resume_text=""
    )
    db.add(new_emp)
    db.flush()

    # 7. Create User
    new_user = User(
        email=email,
        hashed_password=hash_password(req.password),
        full_name=full_name,
        role="EMPLOYEE",
        employee_id=new_emp_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 8. Issue token
    token = create_access_token({"sub": new_user.email, "role": new_user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role": new_user.role,
            "employee_id": new_user.employee_id
        }
    }

@api_router.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Verifies credentials, upgrades legacy hashes, and returns HS256 JWT access token."""
    email = req.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Seamlessly upgrade legacy Phase 1 SHA-256 hash to PBKDF2
    if not user.hashed_password.startswith("pbkdf2_sha256$"):
        user.hashed_password = hash_password(req.password)
        db.commit()

    token = create_access_token({"sub": user.email, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "employee_id": user.employee_id
        }
    }

@api_router.post("/auth/logout")
def logout(
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Terminates active session by revoking the JWT token on the server."""
    revoke_token(credentials.credentials)
    return {"status": "success", "message": "Successfully logged out"}

@api_router.post("/auth/change-password")
def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Securely updates password after verifying existing credentials."""
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    if len(req.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )
    if req.current_password == req.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as current password"
        )

    current_user.hashed_password = hash_password(req.new_password)
    db.commit()
    return {"status": "success", "message": "Password changed successfully"}

@api_router.get("/users/me")
def get_user_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves authenticated user details and strictly linked private employee profile."""
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "employee_id": current_user.employee_id,
        "profile": {
            "employee_id": emp.employee_id,
            "name": emp.name,
            "email": emp.email,
            "current_role": emp.current_role,
            "department": emp.department,
            "experience_years": emp.experience_years,
            "qualification": emp.qualification,
            "target_role_id": emp.target_role_id,
            "bio": emp.bio
        } if emp else None
    }

@api_router.patch("/users/me")
def update_user_me(
    req: UpdateUserMeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Safely updates personal profile while prohibiting tampering with protected fields."""
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()

    if req.full_name is not None:
        name_val = req.full_name.strip()
        if not name_val:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Full name cannot be empty")
        current_user.full_name = name_val
        if emp:
            emp.name = name_val

    if emp:
        if req.target_role_id is not None:
            role_obj = db.query(Role).filter(Role.role_id == req.target_role_id).first()
            if not role_obj:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Target role '{req.target_role_id}' not found")
            emp.target_role_id = req.target_role_id

        if req.bio is not None:
            emp.bio = req.bio

        if req.department is not None:
            emp.department = req.department.strip()

        if req.experience_years is not None:
            if req.experience_years < 0 or req.experience_years > 60:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Experience years must be between 0 and 60")
            emp.experience_years = req.experience_years

        if req.qualification is not None:
            emp.qualification = req.qualification.strip()

    db.commit()
    db.refresh(current_user)
    if emp:
        db.refresh(emp)

    return {
        "status": "success",
        "message": "Profile updated successfully",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "employee_id": current_user.employee_id,
            "profile": {
                "employee_id": emp.employee_id,
                "name": emp.name,
                "email": emp.email,
                "current_role": emp.current_role,
                "department": emp.department,
                "experience_years": emp.experience_years,
                "qualification": emp.qualification,
                "target_role_id": emp.target_role_id,
                "bio": emp.bio
            } if emp else None
        }
    }

@api_router.post("/auth/demo-login")
def demo_login(req: DemoLoginRequest = DemoLoginRequest(), db: Session = Depends(get_db)):
    """Preserved demo login for compatibility testing."""
    if req.employee_id:
        user = db.query(User).filter(User.employee_id == req.employee_id).first()
    else:
        user = db.query(User).filter(User.role == "EMPLOYEE").first()

    if not user:
        user = db.query(User).first()

    if not user:
        raise HTTPException(status_code=404, detail="Demo account not found")

    token = create_access_token({"sub": user.email, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "employee_id": user.employee_id
        }
    }

@api_router.get("/auth/me")
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Legacy endpoint adapter mapping to current authenticated user."""
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "employee_id": current_user.employee_id,
        "employee_details": {
            "name": emp.name if emp else current_user.full_name,
            "current_role": emp.current_role if emp else "Employee",
            "department": emp.department if emp else "Engineering",
            "target_role_id": emp.target_role_id if emp else "ROL-001"
        } if emp else None
    }

# ---------------------------------------------------------
# Employee Endpoints
# ---------------------------------------------------------
@api_router.get("/employees/profile")
def get_employee_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    # Load skills
    skills_data = []
    for es in emp.skills:
        skills_data.append({
            "id": es.id,
            "skill_id": es.skill_id,
            "skill_name": es.skill.name if es.skill else es.skill_id,
            "category": es.skill.category if es.skill else "General",
            "proficiency": es.proficiency,
            "verified": es.verified,
            "source": es.source or "self_reported",
            "evidence": es.evidence,
            "created_at": es.created_at,
            "updated_at": es.updated_at
        })

    # Completed courses
    completed_courses = [c.course_id for c in emp.courses if c.status == "completed"]

    target_role = db.query(Role).filter(Role.role_id == emp.target_role_id).first()

    return {
        "employee_id": emp.employee_id,
        "name": emp.name,
        "email": emp.email,
        "current_role": emp.current_role,
        "department": emp.department,
        "experience_years": emp.experience_years,
        "qualification": emp.qualification,
        "bio": emp.bio,
        "target_role_id": emp.target_role_id,
        "target_role_title": target_role.title if target_role else None,
        "skills": skills_data,
        "completed_courses": completed_courses
    }

@api_router.put("/employees/profile")
def update_employee_profile(
    req: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    if req.target_role_id is not None:
        emp.target_role_id = req.target_role_id
    if req.bio is not None:
        emp.bio = req.bio
    if req.department is not None:
        emp.department = req.department

    db.commit()
    db.refresh(emp)
    return {"status": "success", "message": "Profile updated successfully"}

# ---------------------------------------------------------
# Phase 3: Personal Skill Profiling & Resume Intelligence Endpoints
# ---------------------------------------------------------
@api_router.get("/skills/catalog")
def get_skills_catalog(
    q: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieves canonical 119 skills with category and alias information for selection."""
    query = db.query(Skill)
    if category:
        query = query.filter(Skill.category.ilike(f"%{category}%"))
    if q:
        query = query.filter(Skill.name.ilike(f"%{q}%"))
    skills = query.order_by(Skill.name).all()
    return [
        {
            "skill_id": s.skill_id,
            "name": s.name,
            "category": s.category,
            "importance_weight": s.importance_weight,
            "aliases": json.loads(s.aliases) if s.aliases else []
        }
        for s in skills
    ]

@api_router.get("/employees/skills")
def get_user_skills(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists current authenticated user's skills with validated proficiency, source, and evidence."""
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    skills_data = []
    for es in emp.skills:
        skills_data.append({
            "id": es.id,
            "skill_id": es.skill_id,
            "skill_name": es.skill.name if es.skill else es.skill_id,
            "category": es.skill.category if es.skill else "General",
            "proficiency": es.proficiency,
            "verified": es.verified,
            "source": es.source or "self_reported",
            "evidence": es.evidence,
            "created_at": es.created_at,
            "updated_at": es.updated_at
        })
    return skills_data

@api_router.post("/employees/skills")
def add_employee_skill(
    req: SkillAddRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Adds or updates a personal skill with proficiency validation and provenance tracking."""
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    if not req.skill_name or not req.skill_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill name cannot be empty or whitespace"
        )

    if req.proficiency not in VALID_PROFICIENCIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid proficiency '{req.proficiency}'. Allowed levels: {', '.join(sorted(VALID_PROFICIENCIES))}"
        )

    norm_name = normalize_skill_name(req.skill_name)
    if not norm_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill name is invalid or cannot be normalized"
        )
    skill = db.query(Skill).filter(Skill.name.ilike(norm_name)).first()
    if not skill:
        skill = Skill(
            skill_id=f"SKL-{db.query(Skill).count()+1:03d}",
            name=norm_name,
            category="General",
            importance_weight=1.0,
            aliases="[]"
        )
        db.add(skill)
        db.commit()
        db.refresh(skill)

    now_iso = datetime.utcnow().isoformat()
    source_val = req.source if req.source in VALID_SOURCES else "self_reported"
    verified_val = True if source_val != "resume_extracted" else False

    existing = db.query(EmployeeSkill).filter(
        EmployeeSkill.employee_id == emp.employee_id,
        EmployeeSkill.skill_id == skill.skill_id
    ).first()

    if existing:
        existing.proficiency = req.proficiency
        existing.updated_at = now_iso
        if req.evidence:
            existing.evidence = req.evidence
        if req.source:
            existing.source = source_val
    else:
        new_es = EmployeeSkill(
            employee_id=emp.employee_id,
            skill_id=skill.skill_id,
            proficiency=req.proficiency,
            verified=verified_val,
            source=source_val,
            evidence=req.evidence,
            created_at=now_iso,
            updated_at=now_iso
        )
        db.add(new_es)
    if emp.roadmap:
        db.delete(emp.roadmap)
    db.commit()
    return {
        "status": "success",
        "skill_name": skill.name,
        "skill_id": skill.skill_id,
        "proficiency": req.proficiency,
        "source": source_val,
        "verified": verified_val
    }

@api_router.put("/employees/skills/{skill_name}")
def update_employee_skill(
    skill_name: str,
    req: SkillUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates proficiency and evidence for an existing skill in the user's profile."""
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    if req.proficiency not in VALID_PROFICIENCIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid proficiency '{req.proficiency}'. Allowed levels: {', '.join(sorted(VALID_PROFICIENCIES))}"
        )

    norm_name = normalize_skill_name(skill_name)
    skill = db.query(Skill).filter(Skill.name.ilike(norm_name)).first()
    if not skill:
        skill = db.query(Skill).filter(Skill.name.ilike(skill_name)).first()
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")

    existing = db.query(EmployeeSkill).filter(
        EmployeeSkill.employee_id == emp.employee_id,
        EmployeeSkill.skill_id == skill.skill_id
    ).first()
    if not existing:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found in profile")

    existing.proficiency = req.proficiency
    existing.updated_at = datetime.utcnow().isoformat()
    if req.evidence is not None:
        existing.evidence = req.evidence
    if req.source and req.source in VALID_SOURCES:
        existing.source = req.source

    db.commit()
    return {
        "status": "success",
        "skill_name": skill.name,
        "proficiency": existing.proficiency,
        "source": existing.source,
        "evidence": existing.evidence
    }

@api_router.delete("/employees/skills/{skill_name}")
def delete_employee_skill(
    skill_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Removes a skill from the authenticated user's personal profile."""
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    norm_name = normalize_skill_name(skill_name)
    skill = db.query(Skill).filter(Skill.name.ilike(norm_name)).first()
    if not skill:
        skill = db.query(Skill).filter(Skill.name.ilike(skill_name)).first()
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")

    deleted = db.query(EmployeeSkill).filter(
        EmployeeSkill.employee_id == emp.employee_id,
        EmployeeSkill.skill_id == skill.skill_id
    ).delete()

    if deleted == 0:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found in user profile")

    db.commit()
    return {"status": "success", "message": f"Skill {skill_name} removed"}

@api_router.post("/employees/resume-upload")
async def upload_resume(
    request: Request,
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Uploads and processes a resume file (PDF, DOCX, TXT) or raw text.
    Extracts candidate skills with evidence and confidence.
    Candidate skills are staged for user review and NOT automatically saved as verified expertise.
    """
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    extracted_text = ""
    file_info = {"file_type": "TEXT", "filename": "pasted_text.txt"}
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict) and "text" in body and body["text"].strip():
                extracted_text = body["text"].strip()
        except Exception:
            pass
    elif file and file.filename:
        try:
            content = await file.read()
            extracted_text, detected_type = validate_and_extract_text(file.filename, content)
            stored_rel_path = save_uploaded_resume(current_user.id, file.filename, content)
            file_info["file_type"] = detected_type
            file_info["filename"] = file.filename
            file_info["stored_path"] = stored_rel_path
        except ResumeParsingError as rpe:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(rpe))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to process file: {str(e)}")
    elif text and text.strip():
        extracted_text = text.strip()

    if not extracted_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either a valid resume file (.pdf, .docx, .txt) or non-empty resume text must be provided."
        )



    emp.resume_text = extracted_text
    db.commit()

    # Extract candidate skills with supporting text evidence and confidence
    extracted_skills = skill_extractor.extract_skills_from_text(extracted_text)

    # Store in staging cache for user review (keyed by current_user.id)
    STAGED_RESUME_EXTRACTIONS[current_user.id] = {
        "filename": file_info["filename"],
        "file_type": file_info["file_type"],
        "extracted_skills": extracted_skills,
        "timestamp": datetime.utcnow().isoformat()
    }

    return {
        "status": "success",
        "filename": file_info["filename"],
        "file_type": file_info["file_type"],
        "text_length": len(extracted_text),
        "extracted_skills": extracted_skills,
        "total_extracted": len(extracted_skills),
        "message": "Resume analyzed successfully. Please review and confirm detected skills."
    }

@api_router.get("/employees/resume/extracted")
def get_extracted_skills(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves staged resume extraction results awaiting user review."""
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    staged = STAGED_RESUME_EXTRACTIONS.get(current_user.id)
    if staged:
        return staged

    # If staging is empty but user previously uploaded resume text, re-extract on demand
    if emp.resume_text:
        skills = skill_extractor.extract_skills_from_text(emp.resume_text)
        return {
            "filename": "saved_resume.txt",
            "file_type": "TEXT",
            "extracted_skills": skills,
            "timestamp": datetime.utcnow().isoformat()
        }

    return {
        "filename": None,
        "file_type": None,
        "extracted_skills": [],
        "timestamp": None
    }

@api_router.post("/employees/resume/confirm-skills")
def confirm_extracted_skills(
    req: ConfirmSkillsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Saves user-reviewed and approved candidate skills to their personal profile.
    Saves with source 'resume_extracted' and verified=False (unverified candidate skill).
    """
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    confirmed_count = 0
    now_iso = datetime.utcnow().isoformat()

    for item in req.skills:
        if not item.accepted:
            continue

        prof = item.proficiency if item.proficiency in VALID_PROFICIENCIES else "Intermediate"
        norm_name = normalize_skill_name(item.skill_name)

        skill = db.query(Skill).filter(Skill.name.ilike(norm_name)).first()
        if not skill:
            skill = Skill(
                skill_id=f"SKL-{db.query(Skill).count()+1:03d}",
                name=norm_name,
                category="General",
                importance_weight=1.0,
                aliases="[]"
            )
            db.add(skill)
            db.flush()

        existing = db.query(EmployeeSkill).filter(
            EmployeeSkill.employee_id == emp.employee_id,
            EmployeeSkill.skill_id == skill.skill_id
        ).first()

        if existing:
            existing.proficiency = prof
            existing.evidence = item.evidence or existing.evidence
            existing.source = "resume_extracted"
            existing.verified = False
            existing.updated_at = now_iso
        else:
            new_es = EmployeeSkill(
                employee_id=emp.employee_id,
                skill_id=skill.skill_id,
                proficiency=prof,
                verified=False,
                source="resume_extracted",
                evidence=item.evidence,
                created_at=now_iso,
                updated_at=now_iso
            )
            db.add(new_es)
        confirmed_count += 1

    db.commit()
    # Clear staging for user
    STAGED_RESUME_EXTRACTIONS.pop(current_user.id, None)

    return {
        "status": "success",
        "confirmed_count": confirmed_count,
        "message": f"Successfully saved {confirmed_count} confirmed skills to your personal profile."
    }

# ---------------------------------------------------------
# Roles & Recommendations Endpoints
# ---------------------------------------------------------
# ---------------------------------------------------------
# Roles & Recommendations Endpoints
# ---------------------------------------------------------
@api_router.get("/roles")
def get_all_roles(
    q: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Lists canonical roles with optional query search and category filtering."""
    query = db.query(Role)
    if category and category.lower() != "all":
        query = query.filter(Role.category.ilike(f"%{category}%") | Role.department.ilike(f"%{category}%"))
    if q:
        query = query.filter(
            Role.title.ilike(f"%{q}%") |
            Role.department.ilike(f"%{q}%") |
            Role.description.ilike(f"%{q}%")
        )
    roles = query.order_by(Role.title).all()

    result = []
    for r in roles:
        req_skills = [rs.skill.name for rs in r.required_skills if rs.skill]
        result.append({
            "role_id": r.role_id,
            "title": r.title,
            "category": r.category,
            "department": r.department,
            "experience_years": r.experience_years,
            "education": r.education,
            "salary_range": r.salary_range,
            "description": r.description,
            "openings": r.openings,
            "required_skills": req_skills,
            "skill_count": len(req_skills)
        })
    return result

@api_router.put("/employees/target-role")
@api_router.post("/employees/target-role")
def set_employee_target_role(
    req: TargetRoleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sets and persists the authenticated user's designated target career role."""
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    target_id = (req.target_role_id or req.role_id or "").strip()
    if not target_id:
        raise HTTPException(status_code=400, detail="Missing required 'target_role_id' or 'role_id'")

    role = db.query(Role).filter(Role.role_id == target_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target role '{target_id}' not found in canonical catalog"
        )

    emp.target_role_id = role.role_id
    if emp.roadmap:
        db.delete(emp.roadmap)
    db.commit()
    db.refresh(emp)
    return {
        "status": "success",
        "target_role_id": role.role_id,
        "target_role_title": role.title,
        "department": role.department,
        "message": f"Target role successfully set to '{role.title}'."
    }

@api_router.get("/roles/compare")
def compare_roles(
    role_ids: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compares multiple canonical roles side-by-side against the authenticated user's verified profile."""
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    ids = [rid.strip() for rid in role_ids.split(",") if rid.strip()]
    unique_ids = list(dict.fromkeys(ids))
    if len(unique_ids) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 distinct role IDs to compare (e.g. ?role_ids=ROL-001,ROL-002)")
    if len(unique_ids) > 4:
        raise HTTPException(status_code=400, detail="A maximum of 4 roles can be compared simultaneously")

    emp_skills = [
        {
            "name": es.skill.name,
            "proficiency": es.proficiency,
            "source": es.source or "self_reported",
            "verified": es.verified,
            "evidence": es.evidence
        }
        for es in emp.skills if es.skill
    ]

    compared = []
    all_req_sets = []
    all_missing_sets = []

    for rid in unique_ids:
        r = db.query(Role).filter(Role.role_id == rid).first()
        if not r:
            raise HTTPException(status_code=404, detail=f"Role '{rid}' not found in canonical catalog")

        req_skills = [rs.skill.name for rs in r.required_skills if rs.skill]
        weights = {rs.skill.name: rs.importance_weight for rs in r.required_skills if rs.skill}

        match = calculate_role_match(
            employee_skills=emp_skills,
            employee_exp_years=emp.experience_years,
            role_required_skills=req_skills,
            role_exp_years=r.experience_years,
            role_skill_weights=weights
        )

        all_req_sets.append(set(req_skills))
        missing_names = {m["skill_name"] for m in match["missing_skills"]}
        all_missing_sets.append(missing_names)

        compared.append({
            "role_id": r.role_id,
            "title": r.title,
            "department": r.department,
            "category": r.category,
            "salary_range": r.salary_range,
            "openings": r.openings,
            "experience_years": r.experience_years,
            "match_score": match["match_score"],
            "coverage_percentage": match["coverage_percentage"],
            "mobility_status": match["mobility_status"],
            "met_count": match.get("met_count", 0),
            "partially_met_count": match.get("partially_met_count", 0),
            "missing_count": match.get("missing_count", 0),
            "met_skills": [m["skill_name"] for m in match.get("met_skills", [])],
            "partially_met_skills": [m["skill_name"] for m in match.get("partially_met_skills", [])],
            "missing_skills": [m["skill_name"] for m in match["missing_skills"]],
            "gaps": match.get("gaps", []),
            "explanation": match.get("explanation")
        })

    common_req = list(set.intersection(*all_req_sets)) if all_req_sets else []
    common_miss = list(set.intersection(*all_missing_sets)) if all_missing_sets else []

    return {
        "compared_roles": compared,
        "common_required_skills": sorted(common_req),
        "common_missing_skills": sorted(common_miss),
        "total_compared": len(compared)
    }

@api_router.get("/roles/recommendations")
def get_role_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Computes personalized multi-factor match scores across all roles with provenance awareness."""
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    emp_skills = [
        {
            "name": es.skill.name,
            "proficiency": es.proficiency,
            "source": es.source or "self_reported",
            "verified": es.verified,
            "evidence": es.evidence
        }
        for es in emp.skills if es.skill
    ]
    all_roles = db.query(Role).all()

    recommendations = []
    for r in all_roles:
        req_skills = [rs.skill.name for rs in r.required_skills if rs.skill]
        weights = {rs.skill.name: rs.importance_weight for rs in r.required_skills if rs.skill}

        match = calculate_role_match(
            employee_skills=emp_skills,
            employee_exp_years=emp.experience_years,
            role_required_skills=req_skills,
            role_exp_years=r.experience_years,
            role_skill_weights=weights
        )

        readiness = readiness_predictor.evaluate_transition(
            current_match_score=match["match_score"],
            missing_skills_count=match["missing_count"],
            total_skills_count=match["total_required"],
            exp_delta=match["experience_delta"]
        )

        recommendations.append({
            "role_id": r.role_id,
            "title": r.title,
            "department": r.department,
            "category": r.category,
            "match_score": match["match_score"],
            "coverage_percentage": match["coverage_percentage"],
            "mobility_status": match["mobility_status"],
            "projected_readiness_pct": readiness["projected_readiness_pct"],
            "matched_count": match["matched_count"],
            "missing_count": match["missing_count"],
            "met_count": match.get("met_count", 0),
            "partially_met_count": match.get("partially_met_count", 0),
            "matched_skills": [m["skill_name"] for m in match["matched_skills"]],
            "missing_skills": [m["skill_name"] for m in match["missing_skills"]],
            "met_skills": [m["skill_name"] for m in match.get("met_skills", [])],
            "partially_met_skills": [m["skill_name"] for m in match.get("partially_met_skills", [])],
            "openings": r.openings,
            "salary_range": r.salary_range,
            "explanation": match.get("explanation")
        })

    # Sort descending by match score
    recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    return recommendations

@api_router.get("/roles/match/{role_id}")
def get_single_role_match(
    role_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns detailed personalized match calculation and explainable breakdown for a specific role."""
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    r = db.query(Role).filter(Role.role_id == role_id).first()
    if not r:
        raise HTTPException(status_code=404, detail=f"Role '{role_id}' not found in canonical catalog")

    emp_skills = [
        {
            "name": es.skill.name,
            "proficiency": es.proficiency,
            "source": es.source or "self_reported",
            "verified": es.verified,
            "evidence": es.evidence
        }
        for es in emp.skills if es.skill
    ]

    req_skills = [rs.skill.name for rs in r.required_skills if rs.skill]
    weights = {rs.skill.name: rs.importance_weight for rs in r.required_skills if rs.skill}

    match = calculate_role_match(
        employee_skills=emp_skills,
        employee_exp_years=emp.experience_years,
        role_required_skills=req_skills,
        role_exp_years=r.experience_years,
        role_skill_weights=weights
    )

    readiness = readiness_predictor.evaluate_transition(
        current_match_score=match["match_score"],
        missing_skills_count=match["missing_count"],
        total_skills_count=match["total_required"],
        exp_delta=match["experience_delta"]
    )

    return {
        "role_id": r.role_id,
        "title": r.title,
        "department": r.department,
        "category": r.category,
        "salary_range": r.salary_range,
        "openings": r.openings,
        "experience_years": r.experience_years,
        "match_score": match["match_score"],
        "coverage_percentage": match["coverage_percentage"],
        "mobility_status": match["mobility_status"],
        "met_skills": match.get("met_skills", []),
        "partially_met_skills": match.get("partially_met_skills", []),
        "missing_skills": match["missing_skills"],
        "all_gaps": match.get("gaps", []),
        "matched_count": match["matched_count"],
        "missing_count": match["missing_count"],
        "met_count": match.get("met_count", 0),
        "partially_met_count": match.get("partially_met_count", 0),
        "total_required": match["total_required"],
        "experience_delta": match["experience_delta"],
        "projected_readiness_pct": readiness["projected_readiness_pct"],
        "readiness_verdict": readiness["transition_verdict"],
        "explanation": match.get("explanation")
    }

@api_router.get("/roles/{role_id}")
def get_role_detail(role_id: str, db: Session = Depends(get_db)):
    """Retrieves full canonical details, requirements, and weights for a designated role."""
    r = db.query(Role).filter(Role.role_id == role_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Role not found")

    req_skills = [
        {
            "skill_name": rs.skill.name,
            "category": rs.skill.category,
            "weight": rs.importance_weight
        }
        for rs in r.required_skills if rs.skill
    ]
    return {
        "role_id": r.role_id,
        "title": r.title,
        "category": r.category,
        "department": r.department,
        "experience_years": r.experience_years,
        "education": r.education,
        "salary_range": r.salary_range,
        "description": r.description,
        "openings": r.openings,
        "required_skills": req_skills
    }

# ---------------------------------------------------------
# Skill Gap Analysis & Learning Path Endpoints
# ---------------------------------------------------------
@api_router.get("/analysis/skill-gap/{role_id}")
def get_skill_gap_analysis(
    role_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Performs rigorous skill gap analysis classifying requirements into Met, Partially Met, and Missing."""
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    role = db.query(Role).filter(Role.role_id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail=f"Target role '{role_id}' not found in canonical catalog")

    emp_skills = [
        {
            "name": es.skill.name,
            "proficiency": es.proficiency,
            "source": es.source or "self_reported",
            "verified": es.verified,
            "evidence": es.evidence
        }
        for es in emp.skills if es.skill
    ]
    req_skills = [rs.skill.name for rs in role.required_skills if rs.skill]
    weights = {rs.skill.name: rs.importance_weight for rs in role.required_skills if rs.skill}

    match_result = calculate_role_match(
        employee_skills=emp_skills,
        employee_exp_years=emp.experience_years,
        role_required_skills=req_skills,
        role_exp_years=role.experience_years,
        role_skill_weights=weights
    )

    readiness = readiness_predictor.evaluate_transition(
        current_match_score=match_result["match_score"],
        missing_skills_count=match_result["missing_count"],
        total_skills_count=match_result["total_required"],
        exp_delta=match_result["experience_delta"]
    )

    # Prepare Radar Chart data
    radar_data = []
    emp_skill_dict = {s["name"].lower(): s["proficiency"] for s in emp_skills}
    proficiency_numeric = {"Expert": 100, "Advanced": 80, "Intermediate": 55, "Beginner": 30}
    benchmark_num = 80 if role.experience_years >= 5 else 60 if role.experience_years >= 2 else 40

    for rs in req_skills:
        rs_lower = rs.lower()
        curr_val = proficiency_numeric.get(emp_skill_dict.get(rs_lower, ""), 0)
        radar_data.append({
            "skill": rs,
            "required_level": benchmark_num,
            "current_level": curr_val
        })

    return {
        "role_id": role.role_id,
        "role_title": role.title,
        "department": role.department,
        "category": role.category,
        "experience_years": role.experience_years,
        "education": role.education,
        "salary_range": role.salary_range,
        "description": role.description,
        "openings": role.openings,
        "employee_name": emp.name,
        "current_role": emp.current_role,
        "match_score": match_result["match_score"],
        "coverage_percentage": match_result["coverage_percentage"],
        "mobility_status": match_result["mobility_status"],
        "matched_skills": match_result["matched_skills"],
        "missing_skills": match_result["missing_skills"],
        "met_skills": match_result.get("met_skills", []),
        "partially_met_skills": match_result.get("partially_met_skills", []),
        "all_gaps": match_result.get("gaps", []),
        "summary": {
            "met_count": match_result.get("met_count", 0),
            "partially_met_count": match_result.get("partially_met_count", 0),
            "missing_count": match_result.get("missing_count", 0),
            "total_required": match_result["total_required"]
        },
        "explanation": match_result.get("explanation"),
        "radar_data": radar_data,
        "readiness_prediction": readiness
    }

def compute_and_save_employee_roadmap(emp: Employee, role: Role, db: Session) -> Dict[str, Any]:
    """Helper that generates personalized roadmap for an employee against a role and persists it."""
    emp_skills = [
        {
            "name": es.skill.name,
            "proficiency": es.proficiency,
            "source": es.source or "self_reported",
            "verified": es.verified,
            "evidence": es.evidence
        }
        for es in emp.skills if es.skill
    ]
    req_skills = [rs.skill.name for rs in role.required_skills if rs.skill]
    weights = {rs.skill.name: rs.importance_weight for rs in role.required_skills if rs.skill}

    db_courses = db.query(EmployeeCourse).filter(EmployeeCourse.employee_id == emp.employee_id).all()
    completed_courses = [c.course_id for c in db_courses if c.status == "completed"]
    course_progress_map = {
        c.course_id: {"status": c.status, "progress_pct": c.progress_pct or 0}
        for c in db_courses
    }

    roadmap = learning_path_generator.generate_personalized_roadmap(
        employee_skills=emp_skills,
        employee_exp_years=emp.experience_years,
        role_required_skills=req_skills,
        role_exp_years=role.experience_years,
        role_skill_weights=weights,
        target_role_id=role.role_id,
        target_role_title=role.title,
        target_role_department=role.department,
        completed_course_ids=completed_courses,
        course_progress_map=course_progress_map
    )

    now_str = datetime.utcnow().isoformat()
    emp_roadmap = db.query(EmployeeRoadmap).filter(EmployeeRoadmap.employee_id == emp.employee_id).first()
    if not emp_roadmap:
        emp_roadmap = EmployeeRoadmap(
            employee_id=emp.employee_id,
            target_role_id=role.role_id,
            roadmap_data=json.dumps(roadmap),
            created_at=now_str,
            updated_at=now_str
        )
        db.add(emp_roadmap)
    else:
        emp_roadmap.target_role_id = role.role_id
        emp_roadmap.roadmap_data = json.dumps(roadmap)
        emp_roadmap.updated_at = now_str
    db.commit()

    return roadmap

@api_router.get("/roadmap")
def get_current_user_roadmap(
    role_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the authenticated user's personalized learning roadmap for their designated target role
    (or an explicitly queried role_id).
    """
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    target_id = (role_id or emp.target_role_id or "").strip()
    if not target_id:
        raise HTTPException(
            status_code=400,
            detail="No target role selected. Please select a target role to generate your personalized learning roadmap."
        )

    role = db.query(Role).filter(Role.role_id == target_id).first()
    if not role:
        raise HTTPException(status_code=404, detail=f"Target role '{target_id}' not found in canonical catalog")

    roadmap = compute_and_save_employee_roadmap(emp, role, db)
    return roadmap

@api_router.post("/roadmap/generate")
@api_router.post("/roadmap/refresh")
def refresh_current_user_roadmap(
    req: Optional[RoadmapRefreshRequest] = None,
    role_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Forces recalculation of the personalized learning roadmap using current skills and target role.
    """
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    target_id = (req.target_role_id if req and req.target_role_id else None) or role_id or emp.target_role_id or ""
    target_id = target_id.strip()
    if not target_id:
        raise HTTPException(
            status_code=400,
            detail="No target role selected. Please select a target role to generate your personalized learning roadmap."
        )

    role = db.query(Role).filter(Role.role_id == target_id).first()
    if not role:
        raise HTTPException(status_code=404, detail=f"Target role '{target_id}' not found in canonical catalog")

    roadmap = compute_and_save_employee_roadmap(emp, role, db)
    return roadmap

@api_router.get("/analysis/learning-path/{role_id}")
def get_learning_path(
    role_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Backward-compatible learning path endpoint returning the full Phase 5 personalized roadmap.
    """
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    role = db.query(Role).filter(Role.role_id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Target role not found")

    roadmap = compute_and_save_employee_roadmap(emp, role, db)

    emp_skill_names = {es.skill.name.lower() for es in emp.skills if es.skill}
    missing_skills = [rs.skill.name for rs in role.required_skills if rs.skill and rs.skill.name.lower() not in emp_skill_names]

    return {
        "target_role_id": role.role_id,
        "target_role_title": role.title,
        "missing_skills": missing_skills,
        "learning_path": roadmap,
        **roadmap
    }

@api_router.get("/courses")
def get_canonical_courses(db: Session = Depends(get_db)):
    """Retrieves all 18 canonical curriculum courses with skills taught and prerequisites."""
    courses = db.query(Course).order_by(Course.course_id).all()
    result = []
    for c in courses:
        prereqs = [p.prerequisite_course_id for p in c.prerequisites]
        skills_taught = [cs.skill.name for cs in c.skills_taught if cs.skill]
        result.append({
            "course_id": c.course_id,
            "title": c.title,
            "provider": c.provider,
            "duration_weeks": c.duration_weeks,
            "level": c.level,
            "description": c.description,
            "skills_taught": skills_taught,
            "prerequisites": prereqs
        })
    return result

@api_router.get("/roadmap/courses/{course_id}")
def get_roadmap_course_details(
    course_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves detailed curriculum, prerequisite, targeted skill, and authenticated user progress
    for a specific course.
    """
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    course = db.query(Course).filter(Course.course_id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail=f"Course '{course_id}' not found in catalog")

    ec = db.query(EmployeeCourse).filter(
        EmployeeCourse.employee_id == emp.employee_id,
        EmployeeCourse.course_id == course_id
    ).first()

    prereqs = [cp.prerequisite_course_id for cp in course.prerequisites]
    cinfo = learning_path_generator.courses.get(course_id, {})
    skills_taught = cinfo.get("skills_taught", [])
    if not skills_taught:
        skills_taught = [cs.skill.name for cs in course.skills_taught if cs.skill]

    status_val = ec.status if ec else "not_started"
    progress_pct = ec.progress_pct if ec else 0

    return {
        "course_id": course.course_id,
        "title": course.title,
        "provider": course.provider,
        "duration_weeks": course.duration_weeks,
        "level": course.level,
        "description": course.description,
        "skills_taught": skills_taught,
        "prerequisites": prereqs,
        "user_status": status_val,
        "user_progress_pct": progress_pct
    }

@api_router.put("/roadmap/courses/{course_id}/progress")
@api_router.patch("/roadmap/courses/{course_id}/progress")
def update_roadmap_course_progress(
    course_id: str,
    req: CourseProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates status and progress percentage strictly for a course belonging to the authenticated user's active roadmap.
    """
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    valid_statuses = {"not_started", "in_progress", "completed"}
    if req.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{req.status}'. Must be one of: {', '.join(sorted(valid_statuses))}"
        )

    if not emp.target_role_id:
        raise HTTPException(status_code=400, detail="No target role selected for employee.")

    role = db.query(Role).filter(Role.role_id == emp.target_role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Target role not found")

    emp_roadmap = db.query(EmployeeRoadmap).filter(EmployeeRoadmap.employee_id == emp.employee_id).first()
    if not emp_roadmap or emp_roadmap.target_role_id != role.role_id:
        roadmap_data = compute_and_save_employee_roadmap(emp, role, db)
    else:
        roadmap_data = json.loads(emp_roadmap.roadmap_data)

    milestone_cids = {m["course_id"] for m in roadmap_data.get("milestones", [])}
    if course_id not in milestone_cids:
        raise HTTPException(
            status_code=400,
            detail=f"Course '{course_id}' is not part of your active learning roadmap."
        )

    VALID_COURSE_STATUSES = {"not_started", "in_progress", "completed"}
    if req.status not in VALID_COURSE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid course status '{req.status}'. Allowed statuses: {', '.join(sorted(VALID_COURSE_STATUSES))}"
        )

    ec = db.query(EmployeeCourse).filter(
        EmployeeCourse.employee_id == emp.employee_id,
        EmployeeCourse.course_id == course_id
    ).first()
    now_iso = datetime.utcnow().isoformat()
    if not ec:
        init_progress = (
            100 if req.status == "completed" else (
                max(0, min(100, req.progress_pct)) if req.progress_pct is not None else (
                    50 if req.status == "in_progress" else 0
                )
            )
        )
        ec = EmployeeCourse(
            employee_id=emp.employee_id,
            course_id=course_id,
            status=req.status,
            progress_pct=init_progress,
            updated_at=now_iso
        )
        db.add(ec)
    else:
        ec.status = req.status
        if req.status == "completed":
            ec.progress_pct = 100
        elif req.progress_pct is not None:
            ec.progress_pct = max(0, min(100, req.progress_pct))
        elif req.status == "not_started":
            ec.progress_pct = 0
        ec.updated_at = now_iso

    db.commit()

    updated_roadmap = compute_and_save_employee_roadmap(emp, role, db)
    updated_milestone = next((m for m in updated_roadmap["milestones"] if m["course_id"] == course_id), None)

    return {
        "status": "success",
        "course_id": course_id,
        "course_status": ec.status,
        "progress_pct": ec.progress_pct,
        "milestone": updated_milestone,
        "roadmap_summary": {
            "overall_progress_pct": updated_roadmap["overall_progress_pct"],
            "completed_courses_count": updated_roadmap["completed_courses_count"],
            "in_progress_courses_count": updated_roadmap["in_progress_courses_count"],
            "not_started_courses_count": updated_roadmap["not_started_courses_count"],
            "total_courses": updated_roadmap["total_courses"],
            "total_estimated_weeks": updated_roadmap["total_estimated_weeks"]
        }
    }

@api_router.get("/analysis/readiness/{role_id}")
@api_router.get("/analysis/readiness")
def get_career_readiness_assessment(
    role_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves transparent, multi-factor career readiness assessment for the user against their target role.
    Distinguishes operational readiness from lexical role-matching.
    """
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    target_id = (role_id or emp.target_role_id or "").strip()
    if not target_id:
        raise HTTPException(
            status_code=400,
            detail="No target role selected. Please designate a target role to assess career readiness."
        )

    role = db.query(Role).filter(Role.role_id == target_id).first()
    if not role:
        raise HTTPException(status_code=404, detail=f"Target role '{target_id}' not found in canonical catalog")

    emp_skills = [
        {
            "name": es.skill.name,
            "proficiency": es.proficiency,
            "source": es.source or "self_reported",
            "verified": es.verified,
            "evidence": es.evidence
        }
        for es in emp.skills if es.skill
    ]
    req_skills = [rs.skill.name for rs in role.required_skills if rs.skill]
    weights = {rs.skill.name: rs.importance_weight for rs in role.required_skills if rs.skill}

    completed_courses = [c.course_id for c in emp.courses if c.status == "completed"]

    assessment = readiness_predictor.assess_career_readiness(
        employee_skills=emp_skills,
        employee_exp_years=emp.experience_years,
        role_required_skills=req_skills,
        role_exp_years=role.experience_years,
        role_skill_weights=weights,
        completed_courses_count=len(completed_courses),
        total_roadmap_courses=len(completed_courses) + 3
    )

    return {
        "target_role_id": role.role_id,
        "target_role_title": role.title,
        "department": role.department,
        "experience_years_required": role.experience_years,
        "employee_experience_years": emp.experience_years,
        **assessment
    }

@api_router.post("/analysis/what-if")
def simulate_what_if(
    req: WhatIfRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Runs hypothetical career transition simulations without modifying saved user profiles.
    Allows adjusting proficiency levels on missing or partially met skills.
    Returns explainable before-and-after match and readiness metrics.
    """
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    role = db.query(Role).filter(Role.role_id == req.target_role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail=f"Target role '{req.target_role_id}' not found in canonical catalog")

    req_skills = [rs.skill.name for rs in role.required_skills if rs.skill]
    weights = {rs.skill.name: rs.importance_weight for rs in role.required_skills if rs.skill}

    # 1. Base skills
    base_skills = [
        {
            "name": es.skill.name,
            "proficiency": es.proficiency,
            "source": es.source or "self_reported",
            "verified": es.verified,
            "evidence": es.evidence
        }
        for es in emp.skills if es.skill
    ]

    # 2. Build simulated skills dictionary (case-insensitive name key)
    sim_skills_dict = {
        s["name"].lower(): {
            "name": s["name"],
            "proficiency": s["proficiency"],
            "source": s.get("source", "self_reported"),
            "verified": s.get("verified", False),
            "evidence": s.get("evidence")
        }
        for s in base_skills
    }

    assumptions = []

    # 3. Apply structured hypothetical skills
    for h_sk in req.skills:
        if not h_sk.skill_id and not (h_sk.skill_name and h_sk.skill_name.strip()):
            raise HTTPException(
                status_code=400,
                detail="Each hypothetical skill must specify 'skill_name' or 'skill_id'"
            )
        if h_sk.proficiency not in VALID_PROFICIENCIES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid proficiency '{h_sk.proficiency}'. Allowed levels: {', '.join(sorted(VALID_PROFICIENCIES))}"
            )

        skill_obj = None
        if h_sk.skill_id:
            skill_obj = db.query(Skill).filter(Skill.skill_id == h_sk.skill_id).first()
            if not skill_obj:
                raise HTTPException(status_code=400, detail=f"Skill ID '{h_sk.skill_id}' not found in catalog")
        elif h_sk.skill_name:
            norm_name = normalize_skill_name(h_sk.skill_name)
            skill_obj = db.query(Skill).filter(Skill.name.ilike(norm_name)).first()
            if not skill_obj:
                raise HTTPException(status_code=400, detail=f"Skill '{h_sk.skill_name}' not found in catalog")

        if skill_obj:
            canonical_name = skill_obj.name
            key = canonical_name.lower()
            prev_prof = sim_skills_dict.get(key, {}).get("proficiency")
            sim_skills_dict[key] = {
                "name": canonical_name,
                "proficiency": h_sk.proficiency,
                "source": "simulated_hypothetical",
                "verified": True,
                "evidence": "Hypothetical what-if simulation"
            }
            if prev_prof:
                assumptions.append(f"Adjusted '{canonical_name}' proficiency from {prev_prof} to {h_sk.proficiency}.")
            else:
                assumptions.append(f"Hypothetically acquired '{canonical_name}' at {h_sk.proficiency} level.")

    # 4. Backward compatibility: apply string additional_skills
    for add_sk_name in req.additional_skills:
        norm_name = normalize_skill_name(add_sk_name)
        skill_obj = db.query(Skill).filter(Skill.name.ilike(norm_name)).first()
        if not skill_obj:
            raise HTTPException(status_code=400, detail=f"Skill '{add_sk_name}' not found in catalog")
        canonical_name = skill_obj.name
        key = canonical_name.lower()
        if key not in sim_skills_dict or sim_skills_dict[key]["proficiency"] == "Beginner":
            sim_skills_dict[key] = {
                "name": canonical_name,
                "proficiency": "Advanced",
                "source": "simulated_hypothetical",
                "verified": True,
                "evidence": "Hypothetical what-if simulation"
            }
            assumptions.append(f"Hypothetically acquired '{canonical_name}' at Advanced level.")

    # 5. Apply hypothetical completed courses
    if req.completed_course_ids:
        for cid in req.completed_course_ids:
            course = db.query(Course).filter(Course.course_id == cid).first()
            if not course:
                raise HTTPException(status_code=400, detail=f"Course ID '{cid}' not found in catalog")
            cinfo = learning_path_generator.courses.get(cid, {})
            skills_taught = cinfo.get("skills_taught", [cs.skill.name for cs in course.skills_taught if cs.skill])
            for taught in skills_taught:
                key = taught.lower()
                if key not in sim_skills_dict:
                    sim_skills_dict[key] = {
                        "name": taught,
                        "proficiency": "Intermediate",
                        "source": "simulated_course_completion",
                        "verified": True,
                        "evidence": f"Simulated completion of {cid}"
                    }
            assumptions.append(f"Completed '{course.title}' ({cid}), learning: {', '.join(skills_taught)}.")

    simulated_skills = list(sim_skills_dict.values())

    # 6. Calculate baseline match and readiness
    base_match = calculate_role_match(
        employee_skills=base_skills,
        employee_exp_years=emp.experience_years,
        role_required_skills=req_skills,
        role_exp_years=role.experience_years,
        role_skill_weights=weights
    )

    completed_courses = [c.course_id for c in emp.courses if c.status == "completed"]
    shared_total_courses = max(len(completed_courses) + 3, 5)

    base_readiness = readiness_predictor.assess_career_readiness(
        employee_skills=base_skills,
        employee_exp_years=emp.experience_years,
        role_required_skills=req_skills,
        role_exp_years=role.experience_years,
        role_skill_weights=weights,
        completed_courses_count=len(completed_courses),
        total_roadmap_courses=shared_total_courses
    )

    # 7. Calculate simulated match and readiness
    sim_match = calculate_role_match(
        employee_skills=simulated_skills,
        employee_exp_years=emp.experience_years,
        role_required_skills=req_skills,
        role_exp_years=role.experience_years,
        role_skill_weights=weights
    )

    sim_completed_courses = set(completed_courses).union(req.completed_course_ids)

    if not req.skills and not req.additional_skills and not req.completed_course_ids:
        # Exact identity when no hypothetical inputs are supplied
        sim_readiness = base_readiness
    else:
        sim_readiness = readiness_predictor.assess_career_readiness(
            employee_skills=simulated_skills,
            employee_exp_years=emp.experience_years,
            role_required_skills=req_skills,
            role_exp_years=role.experience_years,
            role_skill_weights=weights,
            completed_courses_count=len(sim_completed_courses),
            total_roadmap_courses=shared_total_courses
        )

    match_gain = round(sim_match["match_score"] - base_match["match_score"], 1)
    readiness_gain = round(sim_readiness["readiness_score"] - base_readiness["readiness_score"], 1)
    skills_closed = base_match["missing_count"] - sim_match["missing_count"]

    if not assumptions:
        assumptions.append("No hypothetical modifications selected; simulated profile identical to baseline.")

    summary_text = (
        f"Simulating this scenario yields a +{match_gain}% match gain and a "
        f"{'+' if readiness_gain >= 0 else ''}{readiness_gain}% readiness adjustment, "
        f"closing {skills_closed} missing skill gap(s)."
    )

    return {
        "target_role": role.title,
        "target_role_id": role.role_id,
        "is_hypothetical": True,
        "assumptions": assumptions,
        "baseline": {
            "match_score": base_match["match_score"],
            "coverage_percentage": base_match["coverage_percentage"],
            "mobility_status": base_match["mobility_status"],
            "readiness_score": base_readiness["readiness_score"],
            "readiness_level": base_readiness["readiness_level"],
            "missing_count": base_match["missing_count"],
            "partially_met_count": base_match.get("partially_met_count", 0),
            "met_count": base_match.get("met_count", 0),
            "gaps": base_match.get("gaps", []),
            "contributing_factors": base_readiness["contributing_factors"]
        },
        "simulated": {
            "match_score": sim_match["match_score"],
            "coverage_percentage": sim_match["coverage_percentage"],
            "mobility_status": sim_match["mobility_status"],
            "readiness_score": sim_readiness["readiness_score"],
            "readiness_level": sim_readiness["readiness_level"],
            "missing_count": sim_match["missing_count"],
            "partially_met_count": sim_match.get("partially_met_count", 0),
            "met_count": sim_match.get("met_count", 0),
            "gaps": sim_match.get("gaps", []),
            "matched_skills": [m["skill_name"] for m in sim_match.get("matched_skills", [])],
            "missing_skills": [m["skill_name"] for m in sim_match.get("missing_skills", [])],
            "contributing_factors": sim_readiness["contributing_factors"],
            "projected_readiness_pct": sim_readiness["readiness_score"],
            "readiness_verdict": sim_readiness["readiness_level"]
        },
        "deltas": {
            "match_gain": match_gain,
            "readiness_gain": readiness_gain,
            "skills_closed": skills_closed
        },
        "explanation": {
            "distinction": (
                "Role Match evaluates lexical skill keyword overlap against role requirements. "
                "Career Readiness measures practical day-to-day transition capability, "
                "incorporating competency criticality, verified proficiency depth, and experience tenure."
            ),
            "summary": summary_text
        },
        "limitations": "Deterministic heuristic baseline. Real-world transition success requires ongoing managerial feedback, practical execution, and empirical validation."
    }

# ---------------------------------------------------------
# Knowledge Graph Endpoints
# ---------------------------------------------------------
@api_router.get("/graph/data")
def get_graph_data(
    node_type: Optional[str] = None,
    search: Optional[str] = None,
    focus_id: Optional[str] = None,
    max_nodes: int = 120
):
    return skill_graph_manager.get_graph_data(
        node_type=node_type,
        search=search,
        focus_id=focus_id,
        max_nodes=max_nodes
    )

# ---------------------------------------------------------
# Research & Raw Datasets Summary (Viva / Presentation Explorer)
# ---------------------------------------------------------
@api_router.get("/datasets/summary")
def get_datasets_summary():
    """Returns live verification metrics and schema metadata for the 4 raw Kaggle/O*NET datasets."""
    summary = {}

    # 1. Job Skill Set
    job_csv = os.path.join(RAW_DIR, "job_skill_set", "all_job_post.csv")
    if os.path.exists(job_csv):
        df_jobs = pd.read_csv(job_csv, nrows=10)
        summary["job_skill_set"] = {
            "name": "Job Skill Set Dataset",
            "file": "all_job_post.csv",
            "columns": list(df_jobs.columns),
            "approx_rows": 1167,
            "categories": ["INFORMATION-TECHNOLOGY", "BUSINESS-DEVELOPMENT", "FINANCE", "SALES", "HR"]
        }

    # 2. Resume Dataset
    roles_csv = os.path.join(RAW_DIR, "resume_dataset", "job_roles.csv")
    if os.path.exists(roles_csv):
        df_r = pd.read_csv(roles_csv, nrows=5)
        summary["resume_dataset"] = {
            "name": "Resume Dataset & Role Profiles",
            "file": "job_roles.csv & training_data.csv",
            "columns": list(df_r.columns),
            "role_definitions_count": 324
        }

    # 3. Candidate Job Role Dataset
    cand_csv = os.path.join(RAW_DIR, "candidate_job_role", "candidate_job_role_dataset.csv")
    if os.path.exists(cand_csv):
        df_c = pd.read_csv(cand_csv, nrows=5)
        summary["candidate_job_role"] = {
            "name": "Candidate–Job Role Dataset",
            "file": "candidate_job_role_dataset.csv",
            "columns": list(df_c.columns),
            "candidate_profiles_count": 1000
        }

    # 4. O*NET Database 29.0
    onet_file = os.path.join(RAW_DIR, "onet_29_0_database", "db_29_0_text", "Occupation Data.txt")
    if os.path.exists(onet_file):
        summary["onet_29_0_database"] = {
            "name": "O*NET 29.0 Database",
            "source": "US Department of Labor / O*NET Resource Center",
            "key_files": [
                "Occupation Data.txt",
                "Skills.txt",
                "Technology Skills.txt",
                "Related Occupations.txt",
                "Task Statements.txt"
            ],
            "occupations_indexed": 1016
        }

    return summary
