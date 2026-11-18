"""
Role Classifier Inference Service for SkillGraph.
Loads the trained production Random Forest classifier and scores candidate skill profiles
against occupational categories with probability estimation and feature attribution.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

from backend.database.db import REPO_ROOT

MODEL_DIR = REPO_ROOT / "backend" / "ml" / "models" / "role_matching"
MODEL_PATH = MODEL_DIR / "role_classifier.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata.json"

class RoleClassifierPredictor:
    def __init__(self):
        self.model = None
        self.metadata = None
        self.feature_names = []
        self.classes = []
        self._load()

    def _load(self):
        if MODEL_PATH.exists():
            try:
                self.model = joblib.load(MODEL_PATH)
            except Exception as e:
                print(f"[WARN] Could not load role classifier: {e}")

        if METADATA_PATH.exists():
            try:
                with open(METADATA_PATH, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                    self.feature_names = self.metadata.get("feature_names", [])
                    self.classes = self.metadata.get("target_classes", [])
            except Exception as e:
                print(f"[WARN] Could not load model metadata: {e}")

    def is_available(self) -> bool:
        return self.model is not None and len(self.feature_names) > 0

    def predict_roles(
        self,
        candidate_skills: List[str],
        experience_level: str = "Mid",
        qualification: str = "Bachelor's in Computer Science",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Constructs candidate feature vector and predicts top-K compatible roles with probabilities.
        """
        if not self.is_available():
            return []

        # 1. Map experience level
        exp_map = {"entry": 1, "mid": 2, "senior": 3}
        tier = exp_map.get(experience_level.lower().strip(), 2)

        # 2. Approximate qualification encoding
        qual_encoded = 0

        # 3. Build multi-hot feature vector
        cand_skills_clean = {s.lower().strip() for s in candidate_skills}
        feat_vector = np.zeros(len(self.feature_names), dtype=float)

        for i, fname in enumerate(self.feature_names):
            if fname == "experience_tier_num":
                feat_vector[i] = tier
            elif fname == "qual_encoded":
                feat_vector[i] = qual_encoded
            elif fname == "total_skills":
                feat_vector[i] = len(candidate_skills)
            elif fname.startswith("skill_"):
                skill_name_clean = fname[6:].replace("_", " ")
                if skill_name_clean in cand_skills_clean:
                    feat_vector[i] = 1.0

        # 4. Model inference
        df_input = pd.DataFrame([feat_vector], columns=self.feature_names)
        proba = self.model.predict_proba(df_input)[0]
        sorted_indices = np.argsort(proba)[::-1][:top_k]

        results = []
        for idx in sorted_indices:
            role_name = self.classes[idx]
            confidence = float(proba[idx])
            if confidence > 0.01:
                # Identify which matching skills contributed
                contributing_skills = [s for s in candidate_skills if f"skill_{s.lower().replace(' ', '_')}" in self.feature_names]
                results.append({
                    "role_title": role_name,
                    "model_confidence": round(confidence * 100, 1),
                    "probability": round(confidence, 4),
                    "contributing_skills": contributing_skills[:6]
                })

        return results
