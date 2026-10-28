"""
Prerequisite-Aware Personalized Learning Path Generator for SkillGraph Phase 5.
Constructs ordered, deterministic topological roadmaps over the course prerequisite DAG,
resolving transitive dependencies for targeted skill gaps, prioritizing critical skills,
identifying unaddressed gaps, and providing explainable rationale for every milestone.
"""

import os
import json
import networkx as nx
from typing import List, Dict, Any, Optional, Set
from backend.database.db import REPO_ROOT
from backend.ml.role_matching import calculate_role_match

PROCESSED_DIR = os.getenv("PROCESSED_DIR", str(REPO_ROOT / "data" / "processed"))

LEVEL_ORDER = {
    "Beginner": 1,
    "Intermediate": 2,
    "Advanced": 3,
    "Expert": 4
}

PRIORITY_WEIGHTS = {
    "Critical": 4.0,
    "High": 3.0,
    "Medium": 2.0,
    "Low": 1.0
}

class LearningPathGenerator:
    def __init__(self):
        self.courses: Dict[str, Dict[str, Any]] = {}
        self.skill_to_courses: Dict[str, List[str]] = {}
        self.dag: nx.DiGraph = nx.DiGraph()
        self._load_courses()

    def _load_courses(self):
        courses_file = os.path.join(PROCESSED_DIR, "course_catalog.json")
        if os.path.exists(courses_file):
            with open(courses_file, "r") as f:
                data = json.load(f)
            self.courses = {}
            self.skill_to_courses = {}
            self.dag = nx.DiGraph()

            for c in data:
                cid = c["course_id"]
                self.courses[cid] = c
                self.dag.add_node(cid)

                for pre in c.get("prerequisites", []):
                    # Directed edge: prerequisite -> course (must finish pre before course)
                    self.dag.add_edge(pre, cid)

                for sk in c.get("skills_taught", []):
                    sk_lower = sk.lower().strip()
                    if sk_lower not in self.skill_to_courses:
                        self.skill_to_courses[sk_lower] = []
                    if cid not in self.skill_to_courses[sk_lower]:
                        self.skill_to_courses[sk_lower].append(cid)

    def reload_catalog(self):
        """Forces reloading the course catalog from disk."""
        self._load_courses()

    def generate_path(
        self,
        missing_skills: List[str],
        completed_course_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Legacy backward-compatible path generation method.
        Constructs an ordered learning path of courses needed to acquire missing skills.
        """
        completed = set(completed_course_ids or [])
        target_course_ids = set()

        for sk in missing_skills:
            sk_lower = sk.lower().strip()
            candidates = self.skill_to_courses.get(sk_lower, [])
            for cid in candidates:
                if cid not in completed:
                    target_course_ids.add(cid)

        all_needed_courses = set(target_course_ids)
        for cid in list(target_course_ids):
            if cid in self.dag:
                for anc in nx.ancestors(self.dag, cid):
                    if anc not in completed:
                        all_needed_courses.add(anc)

        if not all_needed_courses:
            return {
                "total_courses": 0,
                "total_estimated_weeks": 0,
                "milestones": [],
                "target_skills": missing_skills,
                "skills_covered": []
            }

        subgraph = self.dag.subgraph(all_needed_courses)
        sorted_course_ids = self._topological_sort_deterministic(subgraph)

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
            "skills_covered": sorted(list(cumulative_skills)),
            "milestones": milestones
        }

    def generate_personalized_roadmap(
        self,
        employee_skills: List[Dict[str, Any]],
        employee_exp_years: int,
        role_required_skills: List[str],
        role_exp_years: int,
        role_skill_weights: Optional[Dict[str, float]] = None,
        target_role_id: Optional[str] = None,
        target_role_title: Optional[str] = None,
        target_role_department: Optional[str] = "Engineering",
        completed_course_ids: Optional[List[str]] = None,
        course_progress_map: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Phase 5 Personalized Learning Roadmap Generator:
        1. Compares employee skills against role requirements to obtain classified gaps (Missing & Partially Met).
        2. Identifies unaddressed gaps not taught by any course in the catalog.
        3. Selects optimal courses covering actual skill gaps prioritizing critical needs.
        4. Transively expands prerequisite courses.
        5. Performs deterministic topological sort respecting every DAG prerequisite edge.
        6. Explains why each course was selected and which skills it addresses.
        7. Incorporates user course status and progress.
        """
        completed = set(completed_course_ids or [])
        progress_map = course_progress_map or {}

        # 1. Skill Gap Analysis via Phase 4 Role Matching Engine
        match_result = calculate_role_match(
            employee_skills=employee_skills,
            employee_exp_years=employee_exp_years,
            role_required_skills=role_required_skills,
            role_exp_years=role_exp_years,
            role_skill_weights=role_skill_weights
        )

        all_gaps: List[Dict[str, Any]] = match_result.get("gaps", [])

        # If role has no gaps at all, user is 100% ready
        if not all_gaps:
            return {
                "target_role_id": target_role_id,
                "target_role_title": target_role_title or "Target Role",
                "target_role_department": target_role_department,
                "match_score": match_result["match_score"],
                "coverage_percentage": match_result["coverage_percentage"],
                "total_courses": 0,
                "total_estimated_weeks": 0,
                "completed_courses_count": 0,
                "in_progress_courses_count": 0,
                "not_started_courses_count": 0,
                "overall_progress_pct": 100,
                "milestones": [],
                "unaddressed_gaps": [],
                "skills_covered": [],
                "targeted_skills_covered": [],
                "message": "All required skills for this role are already met! You are fully qualified for internal transition."
            }

        # 2. Partition gaps into Teachable vs Unaddressed
        teachable_gaps: Dict[str, Dict[str, Any]] = {}
        unaddressed_gaps: List[Dict[str, Any]] = []

        for g in all_gaps:
            sk_name = g["skill_name"]
            sk_lower = sk_name.lower().strip()
            candidate_cids = self.skill_to_courses.get(sk_lower, [])
            if candidate_cids:
                teachable_gaps[sk_lower] = g
            else:
                unaddressed_gaps.append({
                    "skill_name": sk_name,
                    "classification": g.get("classification", "missing"),
                    "priority": g.get("priority", "Medium"),
                    "importance_weight": g.get("importance_weight", 1.0),
                    "required_proficiency": g.get("required_proficiency", "Intermediate"),
                    "demonstrated_proficiency": g.get("demonstrated_proficiency", "None"),
                    "reason": f"No course currently in the catalog teaches '{sk_name}'. Independent study or external certification recommended."
                })

        # 3. Determine skills already covered by already completed courses
        skills_covered_by_completed = set()
        for cid in completed:
            if cid in self.courses:
                for taught in self.courses[cid].get("skills_taught", []):
                    skills_covered_by_completed.add(taught.lower().strip())

        remaining_uncovered_skills: Set[str] = {
            sk for sk in teachable_gaps.keys()
            if sk not in skills_covered_by_completed
        }

        # 4. Greedy Course Selection with Deterministic Tie-Breaking
        selected_course_ids: Set[str] = set()

        while remaining_uncovered_skills:
            best_candidate = None
            best_key = None

            for cid, cinfo in self.courses.items():
                if cid in completed or cid in selected_course_ids:
                    continue

                taught_lower = {s.lower().strip() for s in cinfo.get("skills_taught", [])}
                covers = taught_lower.intersection(remaining_uncovered_skills)
                if not covers:
                    continue

                # Priority score for covered skills
                priority_score = 0.0
                for sk in covers:
                    gap_info = teachable_gaps[sk]
                    p_weight = PRIORITY_WEIGHTS.get(gap_info.get("priority", "Medium"), 2.0)
                    imp_weight = gap_info.get("importance_weight", 1.0)
                    priority_score += (p_weight * imp_weight)

                # Count new prerequisites needed that are not yet in selected or completed
                ancestors = nx.ancestors(self.dag, cid) if cid in self.dag else set()
                new_prereqs = len(ancestors - completed - selected_course_ids)

                duration = cinfo.get("duration_weeks", 4)
                level_rank = LEVEL_ORDER.get(cinfo.get("level", "Intermediate"), 2)

                # Tie-breaking key:
                # 1. Highest priority score
                # 2. Most gap skills covered directly
                # 3. Fewest new prerequisites needed
                # 4. Shortest duration
                # 5. Beginner level before advanced
                # 6. Lexicographical course_id (descending negative string / ascending string)
                candidate_key = (
                    priority_score,
                    len(covers),
                    -new_prereqs,
                    -duration,
                    -level_rank,
                    cid
                )

                if best_key is None or candidate_key > best_key:
                    best_key = candidate_key
                    best_candidate = cid

            if not best_candidate:
                # No more candidates can cover remaining skills
                break

            selected_course_ids.add(best_candidate)
            taught_by_best = {s.lower().strip() for s in self.courses[best_candidate].get("skills_taught", [])}
            remaining_uncovered_skills -= taught_by_best

        # 5. Recursively Expand Prerequisites
        needed_course_ids: Set[str] = set(selected_course_ids)
        for cid in list(selected_course_ids):
            if cid in self.dag:
                for anc in nx.ancestors(self.dag, cid):
                    if anc not in completed:
                        needed_course_ids.add(anc)

        # Preserve curriculum courses in progress_map that address role gaps or serve as prerequisites
        for cid in progress_map.keys():
            if cid in self.courses:
                taught = {s.lower().strip() for s in self.courses[cid].get("skills_taught", [])}
                if taught.intersection(teachable_gaps.keys()) or any(
                    cid in nx.ancestors(self.dag, nid) for nid in selected_course_ids if nid in self.dag
                ):
                    needed_course_ids.add(cid)

        # 6. Redundancy Elimination
        # If a course was chosen as a target course, but ALL its gap skills are also
        # covered by other courses in needed_course_ids (e.g. via an ancestor),
        # and it is NOT a prerequisite for any course in needed_course_ids, remove it.
        for cid in list(selected_course_ids):
            # Check if cid is a prerequisite for any course in needed_course_ids
            has_dependents = any(
                cid in nx.ancestors(self.dag, other_id)
                for other_id in needed_course_ids if other_id != cid
            )
            if not has_dependents:
                taught_here = {s.lower().strip() for s in self.courses[cid].get("skills_taught", [])}
                gap_taught_here = taught_here.intersection(teachable_gaps.keys())
                # Check if other courses in needed_course_ids cover all gap_taught_here
                other_covered = set()
                for other_cid in needed_course_ids:
                    if other_cid != cid:
                        other_covered.update(
                            s.lower().strip() for s in self.courses[other_cid].get("skills_taught", [])
                        )
                if gap_taught_here and gap_taught_here.issubset(other_covered):
                    needed_course_ids.remove(cid)

        if not needed_course_ids:
            return {
                "target_role_id": target_role_id,
                "target_role_title": target_role_title or "Target Role",
                "target_role_department": target_role_department,
                "match_score": match_result["match_score"],
                "coverage_percentage": match_result["coverage_percentage"],
                "total_courses": 0,
                "total_estimated_weeks": 0,
                "completed_courses_count": 0,
                "in_progress_courses_count": 0,
                "not_started_courses_count": 0,
                "overall_progress_pct": 0,
                "milestones": [],
                "unaddressed_gaps": unaddressed_gaps,
                "skills_covered": [],
                "targeted_skills_covered": [],
                "message": "No courses currently in the catalog address the remaining skill gaps."
            }

        # 7. Deterministic Topological Sort Respecting Every Prerequisite Edge
        subgraph = self.dag.subgraph(needed_course_ids)
        sorted_course_ids = self._topological_sort_deterministic(subgraph)

        # 8. Construct Explainable Milestones with Prerequisites & Progress
        milestones = []
        cumulative_weeks = 0
        all_skills_covered = set()
        targeted_skills_covered = set()

        completed_count = 0
        in_progress_count = 0
        not_started_count = 0
        total_progress_pct_sum = 0

        for step, cid in enumerate(sorted_course_ids, start=1):
            cinfo = self.courses.get(cid, {})
            duration = cinfo.get("duration_weeks", 4)
            cumulative_weeks += duration
            taught = cinfo.get("skills_taught", [])
            all_skills_covered.update(taught)

            # Check which role skill gaps this course directly targets
            course_targeted_skills = [
                sk for sk in taught
                if sk.lower().strip() in teachable_gaps
            ]
            targeted_skills_covered.update(course_targeted_skills)

            # Determine which courses in this roadmap depend on cid
            dependent_courses = [
                dep for dep in sorted_course_ids
                if dep != cid and cid in nx.ancestors(self.dag, dep)
            ]

            # Construct explainable rationale
            reasons = []
            if course_targeted_skills:
                gap_labels = []
                for s in course_targeted_skills:
                    gap_priority = teachable_gaps.get(s.lower().strip(), {}).get("priority", "Medium")
                    gap_labels.append(f"{s} ({gap_priority} priority)")
                reasons.append(f"Directly addresses skill gaps: {', '.join(gap_labels)}")

            if dependent_courses:
                dep_titles = [self.courses.get(d, {}).get("title", d) for d in dependent_courses]
                reasons.append(f"Required prerequisite for: {', '.join(dep_titles)}")

            if not reasons:
                reasons.append("Foundational course recommended for curriculum completeness")

            full_reason = ". ".join(reasons) + "."

            # Course Status & Progress
            user_progress = progress_map.get(cid, {})
            if cid in completed:
                status = "completed"
                progress_pct = 100
            elif user_progress:
                status = user_progress.get("status", "in_progress")
                progress_pct = user_progress.get("progress_pct", 0)
                if status == "completed":
                    progress_pct = 100
            else:
                status = "not_started"
                progress_pct = 0

            if status == "completed":
                completed_count += 1
            elif status == "in_progress":
                in_progress_count += 1
            else:
                not_started_count += 1

            total_progress_pct_sum += progress_pct

            # Prerequisite details with status
            prereqs_status = []
            for pre_id in cinfo.get("prerequisites", []):
                pre_info = self.courses.get(pre_id, {})
                prereqs_status.append({
                    "course_id": pre_id,
                    "title": pre_info.get("title", pre_id),
                    "is_completed": pre_id in completed,
                    "is_in_roadmap": pre_id in needed_course_ids
                })

            milestones.append({
                "step_order": step,
                "course_id": cid,
                "title": cinfo.get("title", cid),
                "provider": cinfo.get("provider", "SkillGraph Academy"),
                "duration_weeks": duration,
                "level": cinfo.get("level", "Intermediate"),
                "description": cinfo.get("description", ""),
                "skills_taught": taught,
                "targeted_skills": course_targeted_skills,
                "prerequisites": cinfo.get("prerequisites", []),
                "prerequisites_detail": prereqs_status,
                "prerequisite_for": dependent_courses,
                "reason": full_reason,
                "cumulative_weeks": cumulative_weeks,
                "status": status,
                "progress_pct": progress_pct
            })

        overall_progress = round(total_progress_pct_sum / max(1, len(milestones)))

        return {
            "target_role_id": target_role_id,
            "target_role_title": target_role_title or "Target Role",
            "target_role_department": target_role_department,
            "match_score": match_result["match_score"],
            "coverage_percentage": match_result["coverage_percentage"],
            "mobility_status": match_result["mobility_status"],
            "total_courses": len(milestones),
            "total_estimated_weeks": cumulative_weeks,
            "completed_courses_count": completed_count,
            "in_progress_courses_count": in_progress_count,
            "not_started_courses_count": not_started_count,
            "overall_progress_pct": overall_progress,
            "skills_covered": sorted(list(all_skills_covered)),
            "targeted_skills_covered": sorted(list(targeted_skills_covered)),
            "unaddressed_gaps": unaddressed_gaps,
            "milestones": milestones
        }

    def _topological_sort_deterministic(self, subgraph: nx.DiGraph) -> List[str]:
        """
        Executes Kahn's algorithm over the DAG with a strict, explainable tie-breaking rule:
        When multiple courses have in-degree 0:
        1. Beginner courses before Intermediate before Advanced (foundation first).
        2. Higher out-degree in subgraph (courses that unblock more downstream courses first).
        3. Shorter duration in weeks (faster early wins).
        4. Course ID ascending (absolute determinism).
        """
        in_degree = {u: subgraph.in_degree(u) for u in subgraph.nodes()}
        zero_in_degree = [u for u, deg in in_degree.items() if deg == 0]

        def tie_break_key(cid: str):
            cinfo = self.courses.get(cid, {})
            level_rank = LEVEL_ORDER.get(cinfo.get("level", "Intermediate"), 2)
            out_deg = subgraph.out_degree(cid)
            duration = cinfo.get("duration_weeks", 4)
            return (level_rank, -out_deg, duration, cid)

        zero_in_degree.sort(key=tie_break_key)

        result = []
        while zero_in_degree:
            curr = zero_in_degree.pop(0)
            result.append(curr)

            for neighbor in subgraph.successors(curr):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    zero_in_degree.append(neighbor)
                    zero_in_degree.sort(key=tie_break_key)

        if len(result) < len(subgraph):
            # In case of an unexpected cycle (catalog integrity safeguard), fallback safely
            for node in subgraph.nodes():
                if node not in result:
                    result.append(node)

        return result

learning_path_generator = LearningPathGenerator()
