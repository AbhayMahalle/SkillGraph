"""
NLP Skill Extraction & Canonicalization Engine.
Extracts technical and professional skills from resume text, PDF streams, or job descriptions,
resolving aliases to canonical ontology skills.
"""

import re
import json
import os
from typing import List, Dict, Any
from backend.database.db import REPO_ROOT

PROCESSED_DIR = os.getenv("PROCESSED_DIR", str(REPO_ROOT / "data" / "processed"))

CANONICAL_ALIASES = {
    "python": "Python", "python3": "Python", "python 3": "Python", "python programming": "Python",
    "javascript": "JavaScript", "js": "JavaScript", "typescript": "TypeScript", "ts": "TypeScript",
    "react": "React", "react.js": "React", "reactjs": "React", "react native": "React Native",
    "vue": "Vue.js", "vue.js": "Vue.js", "angular": "Angular",
    "node": "Node.js", "node.js": "Node.js", "nodejs": "Node.js", "fastapi": "FastAPI",
    "html": "HTML/CSS", "css": "HTML/CSS", "html/css": "HTML/CSS",
    "sql": "SQL", "postgresql": "PostgreSQL", "postgres": "PostgreSQL", "mongodb": "MongoDB",
    "aws": "AWS", "azure": "Azure", "gcp": "GCP",
    "docker": "Docker", "kubernetes": "Kubernetes", "k8s": "Kubernetes", "ci/cd": "CI/CD",
    "git": "Git", "github": "Git", "linux": "Linux",
    "machine learning": "Machine Learning", "ml": "Machine Learning", "deep learning": "Deep Learning",
    "nlp": "Natural Language Processing", "scikit-learn": "Scikit-Learn", "sklearn": "Scikit-Learn",
    "pandas": "Pandas", "numpy": "NumPy", "data analysis": "Data Analysis",
    "rest apis": "REST APIs", "rest api": "REST APIs", "microservices": "Microservices"
}

def normalize_skill_name(raw_name: str) -> str:
    clean = re.sub(r"[^\w\s\+\#\/\.\-]", "", raw_name.strip().lower())
    clean = re.sub(r"\s+", " ", clean).strip()
    if clean in CANONICAL_ALIASES:
        return CANONICAL_ALIASES[clean]
    return raw_name.strip().title()


class SkillExtractor:
    def __init__(self):
        self.skills_lookup = {}
        self.alias_to_canonical = {}
        self.canonical_categories = {}
        self.canonical_ids = {}
        self._load_skills()

    def _load_skills(self):
        skills_file = os.path.join(PROCESSED_DIR, "canonical_skills.json")
        if os.path.exists(skills_file):
            with open(skills_file, "r") as f:
                skills_data = json.load(f)
            for s in skills_data:
                canon = s["name"]
                self.skills_lookup[canon.lower()] = canon
                self.alias_to_canonical[canon.lower()] = canon
                self.canonical_categories[canon] = s.get("category", "General")
                self.canonical_ids[canon] = s.get("skill_id", f"SKL-{len(self.canonical_ids)+1:03d}")
                for alias in s.get("aliases", []):
                    self.alias_to_canonical[alias.lower().strip()] = canon
        else:
            # Fallback basic list
            fallbacks = ["Python", "JavaScript", "React", "Docker", "AWS", "Kubernetes", "SQL", "Linux", "FastAPI"]
            for f in fallbacks:
                self.skills_lookup[f.lower()] = f
                self.alias_to_canonical[f.lower()] = f
                self.canonical_categories[f] = "Technology"
                self.canonical_ids[f] = f"SKL-{len(self.canonical_ids)+1:03d}"

    def extract_evidence_snippet(self, text: str, skill_name: str) -> str:
        """Extracts a compact surrounding text window containing the skill for provenance audit."""
        # Search for skill or aliases
        pattern = r"(?i)\b" + re.escape(skill_name) + r"\b"
        match = re.search(pattern, text)
        if not match:
            # Fallback to case-insensitive substring
            idx = text.lower().find(skill_name.lower())
            if idx == -1:
                return f"Mentioned in resume context for {skill_name}."
            start = max(0, idx - 45)
            end = min(len(text), idx + len(skill_name) + 45)
        else:
            start = max(0, match.start() - 45)
            end = min(len(text), match.end() + 45)

        snippet = text[start:end].strip()
        snippet = re.sub(r"\s+", " ", snippet)
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        return snippet

    def extract_skills_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Scans input text for known canonical skills and aliases using token matching,
        regex boundary checks, and n-gram window inspection.
        Returns detected skills with frequency, confidence, evidence snippets, and proficiency.
        """
        if not text:
            return []

        clean_text = text.lower()
        tokens = re.findall(r"[\w\+\#\/\.\-]+", clean_text)
        found_canonical = {}

        # 1. Check multi-word aliases (trigrams, bigrams, single words)
        n = len(tokens)
        for window_size in [3, 2, 1]:
            for i in range(n - window_size + 1):
                phrase = " ".join(tokens[i : i + window_size])
                if phrase in self.alias_to_canonical:
                    canon = self.alias_to_canonical[phrase]
                    found_canonical[canon] = found_canonical.get(canon, 0) + 1

        # 2. Check direct canonical regex matches with word boundaries
        for canon_lower, canon_title in self.skills_lookup.items():
            pattern = r"\b" + re.escape(canon_lower) + r"\b"
            matches = len(re.findall(pattern, clean_text))
            if matches > 0:
                found_canonical[canon_title] = found_canonical.get(canon_title, 0) + matches

        # Structure response with evidence snippet, confidence, and proficiency
        results = []
        for canon_name, count in found_canonical.items():
            # Check context for level keywords
            snippet = self.extract_evidence_snippet(text, canon_name)
            snip_lower = snippet.lower()
            if any(k in snip_lower for k in ["expert", "lead", "architect", "senior", "mastery"]):
                proficiency = "Expert"
            elif any(k in snip_lower for k in ["advanced", "proficient", "extensively", "deep"]):
                proficiency = "Advanced"
            elif any(k in snip_lower for k in ["basic", "familiar", "beginner", "learning"]):
                proficiency = "Beginner"
            else:
                proficiency = "Expert" if count >= 4 else ("Advanced" if count >= 2 else "Intermediate")

            confidence = min(0.98, round(0.72 + (min(count, 5) * 0.05), 2))

            results.append({
                "skill_id": self.canonical_ids.get(canon_name, "SKL-000"),
                "skill_name": canon_name,
                "category": self.canonical_categories.get(canon_name, "General"),
                "frequency": count,
                "confidence": confidence,
                "estimated_proficiency": proficiency,
                "evidence": snippet,
                "source": "resume_extracted",
                "verified": False
            })

        # Sort by frequency and confidence descending
        results.sort(key=lambda x: (x["frequency"], x["confidence"]), reverse=True)
        return results

skill_extractor = SkillExtractor()
