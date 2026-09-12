"""
Database Initialization & Seeding Script for SkillGraph.
Reads processed JSON datasets and populates the SQLite/PostgreSQL database tables.
"""

import os
import json
import hashlib
from backend.database.db import engine, Base, SessionLocal
from backend.models.models import (
    User, Employee, Skill, EmployeeSkill, Role, RoleSkill,
    Course, CourseSkill, CoursePrerequisite, EmployeeCourse
)

PROCESSED_DIR = "data/processed"

def hash_pw(pw: str) -> str:
    """Simple deterministic hash for demo authentication."""
    return hashlib.sha256(pw.encode()).hexdigest()

def seed_database():
    print("[DB INIT] Creating database tables...")
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    try:
        # Check if already seeded
        if session.query(Skill).count() > 0:
            print("[DB INIT] Database already populated. Skipping re-seed.")
            return

        print("[DB INIT] Loading processed datasets...")

        # 1. Skills
        skills_file = os.path.join(PROCESSED_DIR, "canonical_skills.json")
        skill_name_to_id = {}
        if os.path.exists(skills_file):
            with open(skills_file, "r") as f:
                skills_data = json.load(f)
            for s in skills_data:
                skill_obj = Skill(
                    skill_id=s["skill_id"],
                    name=s["name"],
                    category=s.get("category", "General"),
                    importance_weight=s.get("importance_weight", 1.0),
                    aliases=json.dumps(s.get("aliases", []))
                )
                session.add(skill_obj)
                skill_name_to_id[s["name"]] = s["skill_id"]
            session.commit()
            print(f"  -> Seeded {len(skills_data)} skills")

        # 2. Roles
        roles_file = os.path.join(PROCESSED_DIR, "canonical_roles.json")
        role_title_to_id = {}
        if os.path.exists(roles_file):
            with open(roles_file, "r") as f:
                roles_data = json.load(f)
            for r in roles_data:
                role_obj = Role(
                    role_id=r["role_id"],
                    title=r["title"],
                    category=r.get("category", "Technology"),
                    department=r.get("department", "Engineering"),
                    experience_years=r.get("experience_years", 2),
                    education=r.get("education", "Bachelor's Degree"),
                    salary_range=r.get("salary_range", "80-140K"),
                    description=r.get("description", ""),
                    openings=r.get("openings", 2)
                )
                session.add(role_obj)
                role_title_to_id[r["title"]] = r["role_id"]

                for sk_name in r.get("required_skills", []):
                    sk_id = skill_name_to_id.get(sk_name)
                    if sk_id:
                        rs = RoleSkill(
                            role_id=r["role_id"],
                            skill_id=sk_id,
                            importance_weight=1.0
                        )
                        session.add(rs)
            session.commit()
            print(f"  -> Seeded {len(roles_data)} roles and skill requirements")

        # 3. Courses
        courses_file = os.path.join(PROCESSED_DIR, "course_catalog.json")
        if os.path.exists(courses_file):
            with open(courses_file, "r") as f:
                courses_data = json.load(f)
            for c in courses_data:
                course_obj = Course(
                    course_id=c["course_id"],
                    title=c["title"],
                    provider=c.get("provider", "SkillGraph Academy"),
                    duration_weeks=c.get("duration_weeks", 4),
                    level=c.get("level", "Intermediate"),
                    description=c.get("description", "")
                )
                session.add(course_obj)

                for sk_name in c.get("skills_taught", []):
                    sk_id = skill_name_to_id.get(sk_name)
                    if sk_id:
                        cs = CourseSkill(course_id=c["course_id"], skill_id=sk_id)
                        session.add(cs)

                for pre_id in c.get("prerequisites", []):
                    cp = CoursePrerequisite(course_id=c["course_id"], prerequisite_course_id=pre_id)
                    session.add(cp)
            session.commit()
            print(f"  -> Seeded {len(courses_data)} courses and prerequisite DAG")

        # 4. Employees
        emp_file = os.path.join(PROCESSED_DIR, "employees_seed.json")
        if os.path.exists(emp_file):
            with open(emp_file, "r") as f:
                emp_data = json.load(f)
            for e in emp_data:
                target_role_id = role_title_to_id.get(e.get("target_role", "Cloud Engineer"), "ROL-001")
                emp_obj = Employee(
                    employee_id=e["employee_id"],
                    name=e["name"],
                    email=e["email"],
                    current_role=e["current_role"],
                    department=e["department"],
                    experience_years=e["experience_years"],
                    qualification=e["qualification"],
                    target_role_id=target_role_id,
                    bio=e.get("bio", ""),
                    resume_text=e.get("bio", "")
                )
                session.add(emp_obj)

                for sk in e.get("skills", []):
                    sk_id = skill_name_to_id.get(sk["name"])
                    if sk_id:
                        es = EmployeeSkill(
                            employee_id=e["employee_id"],
                            skill_id=sk_id,
                            proficiency=sk.get("proficiency", "Intermediate"),
                            verified=sk.get("verified", True)
                        )
                        session.add(es)

                for c_id in e.get("completed_courses", []):
                    ec = EmployeeCourse(
                        employee_id=e["employee_id"],
                        course_id=c_id,
                        status="completed"
                    )
                    session.add(ec)

                # Create User Account for authentication
                is_hr = "HR" in e["current_role"] or "sarah" in e["email"].lower()
                user_obj = User(
                    email=e["email"],
                    hashed_password=hash_pw("admin123" if is_hr else "employee123"),
                    full_name=e["name"],
                    role="HR" if is_hr else "EMPLOYEE",
                    employee_id=e["employee_id"]
                )
                session.add(user_obj)

            session.commit()
            print(f"  -> Seeded {len(emp_data)} employees and login accounts")

        print("[DB INIT] Database initialization completed successfully!")
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()
