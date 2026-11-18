"""
LLM integration module for SkillGraph.
"""

from backend.ai.llm.base import (
    LLMProvider,
    LLMProviderError,
    LLMConfigurationError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMResponseError
)
from backend.ai.llm.client import OpenAICompatibleClient
from backend.ai.llm.factory import get_llm_client, get_llm_status
from backend.ai.llm.schemas import (
    ExtractedSkill,
    SkillEvidenceItem,
    OverallAssessment,
    ResumeAnalysisResponse,
    LearningPlanStep,
    LearningPlanResponse,
    SkillImprovementAnalysis,
    SkillImprovementResponse
)

__all__ = [
    "LLMProvider",
    "LLMProviderError",
    "LLMConfigurationError",
    "LLMTimeoutError",
    "LLMRateLimitError",
    "LLMResponseError",
    "OpenAICompatibleClient",
    "get_llm_client",
    "get_llm_status",
    "ExtractedSkill",
    "SkillEvidenceItem",
    "OverallAssessment",
    "ResumeAnalysisResponse",
    "LearningPlanStep",
    "LearningPlanResponse",
    "SkillImprovementAnalysis",
    "SkillImprovementResponse"
]
