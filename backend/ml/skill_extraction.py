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
