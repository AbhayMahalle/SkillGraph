"""
Resume Processing Service for SkillGraph.
Orchestrates secure file validation, text extraction, text normalization,
and AI-powered skill extraction with transparent deterministic fallback.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.ml.resume_parser import validate_and_extract_text, save_uploaded_resume, ResumeParsingError
from backend.ml.skill_extraction import SkillExtractor
from backend.services.llm_service import LLMService
from backend.ai.llm.base import LLMConfigurationError
from backend.models.models import Employee, ResumeAnalysis

skill_extractor = SkillExtractor()
llm_service = LLMService()

def process_resume_and_extract_skills(
    user_id: int,
    emp: Employee,
    filename: str,
    content: bytes,
    use_ai: bool = True,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Validates resume file, extracts text, and performs structured skill extraction.
    If use_ai=True and LLM credentials are configured, leverages external LLM.
    Otherwise, applies deterministic rule-based ontology matching.
    """
    # 1. Format validation & text extraction
    extracted_text, detected_type = validate_and_extract_text(filename, content)
    
    # 2. Save file safely in user-segregated directory
    rel_path = save_uploaded_resume(user_id, filename, content)

    # 3. Update employee record with raw text
    emp.resume_text = extracted_text

    ai_analysis_performed = False
    ai_metadata = {}
    extracted_skills_list = []
    overall_assessment = {
        "summary": "Extracted skills using deterministic ontology keyword parser.",
        "primary_domain": "General Engineering",
        "limitations": ["Rule-based extraction only; configure LLM_API_KEY for deep semantic reasoning."]
    }

    # 4. Attempt AI/LLM extraction if requested and configured
    if use_ai and llm_service.is_configured():
        try:
            analysis_resp = llm_service.analyze_resume(extracted_text, filename=filename)
            ai_analysis_performed = True
            model_info = llm_service.provider.get_model_info()
            ai_metadata = {
                "provider": model_info.get("provider"),
                "model": model_info.get("model")
            }

            # Convert Pydantic models to dicts
            for sk in analysis_resp.skills:
                extracted_skills_list.append({
                    "skill_name": sk.skill_name,
                    "canonical_skill_id": sk.canonical_skill_id,
                    "category": sk.category,
                    "proficiency": sk.proficiency_level,
                    "proficiency_percentage": sk.proficiency_percentage,
                    "confidence": round(sk.confidence, 2),
                    "evidence": [ev.model_dump() for ev in sk.evidence],
                    "evidence_text": " | ".join([ev.text for ev in sk.evidence]) if sk.evidence else "",
                    "reasoning": sk.reasoning,
                    "verified": False,
                    "source": "resume_extracted"
                })

            for unk in analysis_resp.unmatched_skills:
                extracted_skills_list.append({
                    "skill_name": unk.skill_name,
                    "canonical_skill_id": None,
                    "category": unk.category or "Candidate Skills",
                    "proficiency": unk.proficiency_level,
                    "proficiency_percentage": unk.proficiency_percentage,
                    "confidence": round(unk.confidence, 2),
                    "evidence": [ev.model_dump() for ev in unk.evidence],
                    "evidence_text": " | ".join([ev.text for ev in unk.evidence]) if unk.evidence else "",
                    "reasoning": unk.reasoning,
                    "verified": False,
                    "source": "resume_extracted"
                })

            overall_assessment = analysis_resp.overall_assessment.model_dump()

            # Record in database if session available
            if db:
                analysis_record = ResumeAnalysis(
                    employee_id=emp.employee_id,
                    filename=filename,
                    extracted_text_snippet=extracted_text[:1000],
                    analysis_json=json.dumps(analysis_resp.model_dump()),
                    provider=model_info.get("provider"),
                    model=model_info.get("model"),
                    created_at=datetime.utcnow().isoformat()
                )
                db.add(analysis_record)

        except Exception as e:
            # Fall back gracefully to deterministic extractor if LLM call fails
            ai_analysis_performed = False
            ai_metadata = {"error": str(e)}

    # Fallback to deterministic NLP if AI was not performed
    if not ai_analysis_performed:
        deterministic_skills = skill_extractor.extract_skills_from_text(extracted_text)
        for ds in deterministic_skills:
            prof_level = "Intermediate"
            prof_pct = int(ds.get("confidence", 0.85) * 60)
            extracted_skills_list.append({
                "skill_name": ds["skill_name"],
                "canonical_skill_id": ds.get("canonical_skill_id"),
                "category": ds.get("category", "General Technology"),
                "proficiency": prof_level,
                "proficiency_percentage": prof_pct,
                "confidence": round(ds.get("confidence", 0.85), 2),
                "evidence": [{"text": ds.get("snippet", ""), "section": "Extracted Text"}],
                "evidence_text": ds.get("snippet", ""),
                "reasoning": "Detected via canonical alias matching and keyword boundary recognition.",
                "verified": False,
                "source": "resume_extracted"
            })

    if db:
        db.commit()

    return {
        "status": "success",
        "file_type": detected_type,
        "filename": filename,
        "saved_path": rel_path,
        "text_length": len(extracted_text),
        "ai_powered": ai_analysis_performed,
        "ai_metadata": ai_metadata,
        "extracted_skills": extracted_skills_list,
        "total_extracted": len(extracted_skills_list),
        "overall_assessment": overall_assessment
    }
