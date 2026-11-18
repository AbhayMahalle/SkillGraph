"""
Pydantic Schemas for Structured External LLM Responses in SkillGraph.
Enforces rigorous server-side validation on all LLM outputs.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator

VALID_PROFICIENCY_LEVELS = {"Beginner", "Intermediate", "Advanced", "Expert"}

class SkillEvidenceItem(BaseModel):
    """Specific contextual evidence extracted from resume or experience text."""
    text: str = Field(..., description="Verbatim or summarized evidence snippet")
    section: Optional[str] = Field("Experience", description="Resume section (e.g., Work Experience, Projects, Education)")

class ExtractedSkill(BaseModel):
    """An individual skill identified and assessed by the LLM."""
    skill_name: str = Field(..., min_length=1, description="Standardized name of the skill")
    canonical_skill_id: Optional[str] = Field(None, description="Mapped canonical ID (e.g., SKL-001) if present in catalog")
    category: Optional[str] = Field("General Technology", description="Skill domain category")
    proficiency_level: str = Field("Intermediate", description="Beginner, Intermediate, Advanced, or Expert")
    proficiency_percentage: int = Field(50, ge=0, le=100, description="Estimated competency percentage (0-100)")
    confidence: float = Field(0.85, ge=0.0, le=1.0, description="Model confidence in detection (0.0-1.0)")
    evidence: List[SkillEvidenceItem] = Field(default_factory=list, description="Supporting evidence items")
    reasoning: str = Field("", description="Explainable justification for the proficiency assessment")
    verified: bool = Field(False, description="Whether this skill has undergone formal verification")
    requires_review: bool = Field(True, description="Human-in-the-loop review requirement flag")

    @field_validator("proficiency_level")
    @classmethod
    def validate_proficiency(cls, v: str) -> str:
        formatted = v.strip().title()
        if formatted not in VALID_PROFICIENCY_LEVELS:
            # Gracefully map common variants
            mapping = {
                "Novice": "Beginner",
                "Entry": "Beginner",
                "Junior": "Beginner",
                "Mid": "Intermediate",
                "Proficient": "Advanced",
                "Senior": "Advanced",
                "Master": "Expert",
                "Lead": "Expert"
            }
            if formatted in mapping:
                return mapping[formatted]
            return "Intermediate"
        return formatted

class OverallAssessment(BaseModel):
    """High-level summary of candidate strengths and limitations based on resume evidence."""
    summary: str = Field(..., description="Executive summary of technical strengths")
    primary_domain: Optional[str] = Field(None, description="Inferred core domain")
    estimated_experience_years: Optional[int] = Field(None, ge=0, description="Experience years inferred from timeline")
    limitations: List[str] = Field(default_factory=list, description="Identified resume gaps or areas lacking verifiable evidence")

class ResumeAnalysisResponse(BaseModel):
    """Complete structured response from LLM resume intelligence processing."""
    skills: List[ExtractedSkill] = Field(default_factory=list, description="Skills mapped or matching canonical ontology")
    unmatched_skills: List[ExtractedSkill] = Field(default_factory=list, description="Unmatched candidate skills for user review")
    overall_assessment: OverallAssessment = Field(..., description="Synthesized profile assessment")

class LearningPlanStep(BaseModel):
    """A milestone in an AI-generated personalized career upskilling roadmap."""
    step_order: int = Field(..., ge=1, description="Sequential execution index")
    skill_name: str = Field(..., description="Target skill to acquire or deepen")
    current_proficiency: str = Field("None", description="Current demonstrated level")
    target_proficiency: str = Field("Intermediate", description="Required proficiency level for target role")
    gap_explanation: str = Field(..., description="Why this gap matters for role transition")
    learning_objective: str = Field(..., description="Measurable outcome upon completion")
    recommended_course_id: Optional[str] = Field(None, description="Course ID from catalog if matched")
    recommended_course_title: Optional[str] = Field(None, description="Title of course from catalog")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisite courses or skills")
    learning_activities: List[str] = Field(default_factory=list, description="Specific weekly study exercises")
    practical_project: Optional[str] = Field(None, description="Hands-on portfolio project to validate learning")
    assessment_method: Optional[str] = Field(None, description="How mastery should be demonstrated")
    estimated_duration_weeks: int = Field(4, ge=1, le=52, description="Estimated study duration in weeks")
    expected_outcome: str = Field("", description="Deliverable or milestone artifact")

class LearningPlanResponse(BaseModel):
    """Complete personalized learning plan generated by external LLM."""
    target_role_id: str = Field(..., description="Canonical ID of target career role")
    target_role_title: str = Field(..., description="Title of target career role")
    overall_objective: str = Field(..., description="High-level transition strategy")
    skill_gap_summary: str = Field(..., description="Summary of key gaps addressed")
    milestones: List[LearningPlanStep] = Field(default_factory=list, description="Topologically ordered learning steps")
    practical_projects: List[Dict[str, str]] = Field(default_factory=list, description="Portfolio capstone projects")
    pitfalls_to_avoid: List[str] = Field(default_factory=list, description="Common mistakes candidates make in this transition")
    total_estimated_weeks: int = Field(0, ge=0, description="Sum of milestone durations")

class SkillImprovementAnalysis(BaseModel):
    """Detailed improvement recommendation for a specific skill."""
    skill_name: str
    current_level: str
    target_level: str
    learning_actions: List[str] = Field(default_factory=list)
    hands_on_project: Optional[str] = None
    expected_impact: str = ""

class SkillImprovementResponse(BaseModel):
    """Response containing suggestions for improving specific skills."""
    target_role_title: str
    improvements: List[SkillImprovementAnalysis] = Field(default_factory=list)
