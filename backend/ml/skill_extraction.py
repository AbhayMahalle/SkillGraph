"""
NLP Skill Extraction & Canonicalization Engine.
Extracts technical and professional skills from resume text, PDF streams, or job descriptions,
resolving aliases to canonical ontology skills.
"""

import re
import json
import os
from typing import List, Dict, Any

PROCESSED_DIR = "data/processed"

CANONICAL_ALIASES = {
    "python": "Python", "python3": "Python", "python 3": "Python",
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
                for alias in s.get("aliases", []):
                    self.alias_to_canonical[alias.lower().strip()] = canon
        else:
            # Fallback basic list
            fallbacks = ["Python", "JavaScript", "React", "Docker", "AWS", "Kubernetes", "SQL", "Linux", "FastAPI"]
            for f in fallbacks:
                self.skills_lookup[f.lower()] = f
                self.alias_to_canonical[f.lower()] = f

    def extract_skills_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Scans input text for known canonical skills and aliases using token matching
        and n-gram window inspection (up to 3 words).
        """
        if not text:
            return []

        clean_text = text.lower()
        # Normalize punctuation for token boundaries
        tokens = re.findall(r"[\w\+\#\/\.\-]+", clean_text)
        found_canonical = {}

        # 1. Check multi-word aliases (trigrams and bigrams)
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

        # Structure response with estimated proficiency based on frequency and context
        results = []
        for canon_name, count in found_canonical.items():
            proficiency = "Expert" if count >= 4 else ("Advanced" if count >= 2 else "Intermediate")
            results.append({
                "skill_name": canon_name,
                "frequency": count,
                "confidence": min(1.0, 0.70 + (count * 0.1)),
                "estimated_proficiency": proficiency
            })

        # Sort by frequency descending
        results.sort(key=lambda x: x["frequency"], reverse=True)
        return results

skill_extractor = SkillExtractor()
