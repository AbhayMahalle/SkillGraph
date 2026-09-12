"""
Prerequisite-Aware Learning Path Generator.
Constructs ordered topological roadmaps over the course prerequisite DAG,
resolving all transitive dependencies for targeted skill gaps.
"""

import os
import json
import networkx as nx
from typing import List, Dict, Any

PROCESSED_DIR = "data/processed"

class LearningPathGenerator:
    def __init__(self):
        self.courses = {}
        self.skill_to_courses = {}
        self.dag = nx.DiGraph()
        self._load_courses()

    def _load_courses(self):
        courses_file = os.path.join(PROCESSED_DIR, "course_catalog.json")
        if os.path.exists(courses_file):
            with open(courses_file, "r") as f:
                data = json.load(f)
            for c in data:
                cid = c["course_id"]
                self.courses[cid] = c
                self.dag.add_node(cid)
                for pre in c.get("prerequisites", []):
                    self.dag.add_edge(pre, cid)

                for sk in c.get("skills_taught", []):
                    sk_lower = sk.lower()
                    if sk_lower not in self.skill_to_courses:
                        self.skill_to_courses[sk_lower] = []
                    self.skill_to_courses[sk_lower].append(cid)

    def generate_path(
        self,
        missing_skills: List[str],
        completed_course_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates an ordered learning path of courses needed to acquire the missing skills,
        expanding all prerequisite courses not yet completed.
        """
        completed = set(completed_course_ids or [])
        target_course_ids = set()

        # Find courses directly teaching missing skills
        for sk in missing_skills:
            sk_lower = sk.lower()
            c_candidates = self.skill_to_courses.get(sk_lower, [])
            for cid in c_candidates:
                if cid not in completed:
                    target_course_ids.add(cid)

        # Recursively expand prerequisites using ancestor traversal
        all_needed_courses = set(target_course_ids)
        for cid in list(target_course_ids):
            if cid in self.dag:
                ancestors = nx.ancestors(self.dag, cid)
                for anc in ancestors:
                    if anc not in completed:
                        all_needed_courses.add(anc)

        if not all_needed_courses:
            return {
                "total_courses": 0,
                "total_estimated_weeks": 0,
                "milestones": [],
                "target_skills": missing_skills
            }

        # Subgraph of needed courses
        subgraph = self.dag.subgraph(all_needed_courses)

        # Topological sort ensures prerequisites come first
        try:
            sorted_course_ids = list(nx.topological_sort(subgraph))
        except nx.NetworkXUnfeasible:
            # Fallback if any unexpected cycle
            sorted_course_ids = list(all_needed_courses)

        milestones = []
        cumulative_weeks = 0
        cumulative_skills = set()

        for step, cid in enumerate(sorted_course_ids, start=1):
            course_info = self.courses.get(cid, {})
            duration = course_info.get("duration_weeks", 4)
            cumulative_weeks += duration
            taught = course_info.get("skills_taught", [])
            cumulative_skills.update(taught)

            milestones.append({
                "step_order": step,
                "course_id": cid,
                "title": course_info.get("title", cid),
                "provider": course_info.get("provider", "SkillGraph Academy"),
                "duration_weeks": duration,
                "level": course_info.get("level", "Intermediate"),
                "skills_taught": taught,
                "cumulative_weeks": cumulative_weeks,
                "prerequisites": course_info.get("prerequisites", []),
                "description": course_info.get("description", "")
            })

        return {
            "total_courses": len(milestones),
            "total_estimated_weeks": cumulative_weeks,
            "skills_covered": list(cumulative_skills),
            "milestones": milestones
        }

learning_path_generator = LearningPathGenerator()
