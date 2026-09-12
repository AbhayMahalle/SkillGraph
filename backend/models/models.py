"""
SQLAlchemy ORM models for SkillGraph.
Entities: User, Employee, Skill, EmployeeSkill, Role, RoleSkill, Course, CourseSkill, CoursePrerequisite.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from backend.database.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(120), nullable=False)
    role = Column(String(20), default="EMPLOYEE", nullable=False)  # "EMPLOYEE" or "HR"
    employee_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=True)

    employee = relationship("Employee", back_populates="user", uselist=False)

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    current_role = Column(String(120), nullable=False)
    department = Column(String(100), nullable=False)
    experience_years = Column(Integer, default=1)
    qualification = Column(String(200), default="Bachelor's Degree")
    target_role_id = Column(String(50), nullable=True)
    bio = Column(Text, nullable=True)
    resume_text = Column(Text, nullable=True)

    user = relationship("User", back_populates="employee", uselist=False)
    skills = relationship("EmployeeSkill", back_populates="employee", cascade="all, delete-orphan")
    courses = relationship("EmployeeCourse", back_populates="employee", cascade="all, delete-orphan")

class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(120), unique=True, index=True, nullable=False)
    category = Column(String(100), default="General Technology")
    importance_weight = Column(Float, default=1.0)
    aliases = Column(Text, default="[]")  # JSON encoded list of alias strings

    employee_skills = relationship("EmployeeSkill", back_populates="skill")
    role_skills = relationship("RoleSkill", back_populates="skill")

class EmployeeSkill(Base):
    __tablename__ = "employee_skills"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=False)
    skill_id = Column(String(50), ForeignKey("skills.skill_id"), nullable=False)
    proficiency = Column(String(50), default="Intermediate")  # Beginner, Intermediate, Advanced, Expert
    verified = Column(Boolean, default=True)

    employee = relationship("Employee", back_populates="skills")
    skill = relationship("Skill", back_populates="employee_skills")

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(150), unique=True, index=True, nullable=False)
    category = Column(String(100), default="Technology")
    department = Column(String(100), default="Engineering")
    experience_years = Column(Integer, default=2)
    education = Column(String(250), default="Bachelor's Degree")
    salary_range = Column(String(100), default="80-140K")
    description = Column(Text, nullable=True)
    openings = Column(Integer, default=2)

    required_skills = relationship("RoleSkill", back_populates="role", cascade="all, delete-orphan")

class RoleSkill(Base):
    __tablename__ = "role_skills"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(String(50), ForeignKey("roles.role_id"), nullable=False)
    skill_id = Column(String(50), ForeignKey("skills.skill_id"), nullable=False)
    importance_weight = Column(Float, default=1.0)

    role = relationship("Role", back_populates="required_skills")
    skill = relationship("Skill", back_populates="role_skills")

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    provider = Column(String(150), default="SkillGraph Academy")
    duration_weeks = Column(Integer, default=4)
    level = Column(String(50), default="Intermediate")  # Beginner, Intermediate, Advanced
    description = Column(Text, nullable=True)

    skills_taught = relationship("CourseSkill", back_populates="course", cascade="all, delete-orphan")
    prerequisites = relationship(
        "CoursePrerequisite",
        foreign_keys="CoursePrerequisite.course_id",
        back_populates="course",
        cascade="all, delete-orphan"
    )

class CourseSkill(Base):
    __tablename__ = "course_skills"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String(50), ForeignKey("courses.course_id"), nullable=False)
    skill_id = Column(String(50), ForeignKey("skills.skill_id"), nullable=False)

    course = relationship("Course", back_populates="skills_taught")

class CoursePrerequisite(Base):
    __tablename__ = "course_prerequisites"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String(50), ForeignKey("courses.course_id"), nullable=False)
    prerequisite_course_id = Column(String(50), ForeignKey("courses.course_id"), nullable=False)

    course = relationship("Course", foreign_keys=[course_id], back_populates="prerequisites")

class EmployeeCourse(Base):
    __tablename__ = "employee_courses"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=False)
    course_id = Column(String(50), ForeignKey("courses.course_id"), nullable=False)
    status = Column(String(50), default="completed")  # "completed", "in_progress"

    employee = relationship("Employee", back_populates="courses")
