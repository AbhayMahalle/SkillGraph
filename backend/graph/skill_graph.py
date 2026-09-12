"""
Knowledge Graph Engine for SkillGraph.
Maintains an in-memory multi-relational graph using NetworkX for sub-millisecond
graph queries, visualization data export, and Neo4j Cypher generation.
"""

import os
import json
import networkx as nx
from typing import Dict, Any, List, Optional

PROCESSED_DIR = "data/processed"

NODE_COLORS = {
    "employee": "#3b82f6",  # Blue
    "skill": "#10b981",     # Emerald
    "role": "#8b5cf6",      # Purple
    "course": "#f59e0b"     # Amber
}

class SkillGraphManager:
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self._build_graph()

    def _build_graph(self):
        # 1. Add Skills
        skills_file = os.path.join(PROCESSED_DIR, "canonical_skills.json")
        if os.path.exists(skills_file):
            with open(skills_file, "r") as f:
                for s in json.load(f):
                    nid = f"SKILL_{s['skill_id']}"
                    self.graph.add_node(
                        nid,
                        id=nid,
                        label=s["name"],
                        type="skill",
                        category=s.get("category", "General"),
                        color=NODE_COLORS["skill"],
                        val=14
                    )

        # 2. Add Roles & REQUIRES edges
        roles_file = os.path.join(PROCESSED_DIR, "canonical_roles.json")
        if os.path.exists(roles_file):
            with open(roles_file, "r") as f:
                for r in json.load(f):
                    rid = f"ROLE_{r['role_id']}"
                    self.graph.add_node(
                        rid,
                        id=rid,
                        label=r["title"],
                        type="role",
                        category=r.get("category", "Technology"),
                        department=r.get("department", "Engineering"),
                        color=NODE_COLORS["role"],
                        val=20
                    )
                    # Link required skills
                    for req in r.get("required_skills", []):
                        # Find skill node
                        for node, data in self.graph.nodes(data=True):
                            if data.get("type") == "skill" and data.get("label", "").lower() == req.lower():
                                self.graph.add_edge(rid, node, relationship="REQUIRES", color="#a78bfa")
                                break

        # 3. Add Courses & TEACHES / PREREQUISITE edges
        courses_file = os.path.join(PROCESSED_DIR, "course_catalog.json")
        if os.path.exists(courses_file):
            with open(courses_file, "r") as f:
                for c in json.load(f):
                    cid = f"COURSE_{c['course_id']}"
                    self.graph.add_node(
                        cid,
                        id=cid,
                        label=c["title"],
                        type="course",
                        level=c.get("level", "Intermediate"),
                        color=NODE_COLORS["course"],
                        val=16
                    )
                    for sk in c.get("skills_taught", []):
                        for node, data in self.graph.nodes(data=True):
                            if data.get("type") == "skill" and data.get("label", "").lower() == sk.lower():
                                self.graph.add_edge(cid, node, relationship="TEACHES", color="#fbbf24")
                                break
                    for pre in c.get("prerequisites", []):
                        pre_nid = f"COURSE_{pre}"
                        self.graph.add_edge(pre_nid, cid, relationship="PREREQUISITE_FOR", color="#f87171")

        # 4. Add Employees & HAS_SKILL / TARGETS_ROLE edges
        emp_file = os.path.join(PROCESSED_DIR, "employees_seed.json")
        if os.path.exists(emp_file):
            with open(emp_file, "r") as f:
                for e in json.load(f):
                    eid = f"EMP_{e['employee_id']}"
                    self.graph.add_node(
                        eid,
                        id=eid,
                        label=e["name"],
                        type="employee",
                        current_role=e["current_role"],
                        department=e["department"],
                        color=NODE_COLORS["employee"],
                        val=22
                    )
                    # Skills
                    for sk in e.get("skills", []):
                        sk_name = sk["name"]
                        for node, data in self.graph.nodes(data=True):
                            if data.get("type") == "skill" and data.get("label", "").lower() == sk_name.lower():
                                self.graph.add_edge(eid, node, relationship="HAS_SKILL", proficiency=sk.get("proficiency"), color="#60a5fa")
                                break
                    # Target Role
                    tgt_title = e.get("target_role")
                    if tgt_title:
                        for node, data in self.graph.nodes(data=True):
                            if data.get("type") == "role" and data.get("label", "").lower() == tgt_title.lower():
                                self.graph.add_edge(eid, node, relationship="TARGETS_ROLE", color="#c084fc")
                                break

    def get_graph_data(
        self,
        node_type: Optional[str] = None,
        search: Optional[str] = None,
        focus_id: Optional[str] = None,
        max_nodes: int = 150
    ) -> Dict[str, Any]:
        """
        Extracts visualization-ready JSON graph payload of nodes and links.
        Can filter by node type, search query, or neighborhood of a focus node.
        """
        selected_nodes = set()

        if focus_id and focus_id in self.graph:
            # 1-hop neighborhood of focus node
            selected_nodes.add(focus_id)
            selected_nodes.update(self.graph.predecessors(focus_id))
            selected_nodes.update(self.graph.successors(focus_id))
        else:
            for n, d in self.graph.nodes(data=True):
                if node_type and d.get("type") != node_type:
                    continue
                if search and search.lower() not in d.get("label", "").lower():
                    continue
                selected_nodes.add(n)
                if len(selected_nodes) >= max_nodes:
                    break

        # Fallback if empty
        if not selected_nodes:
            selected_nodes = set(list(self.graph.nodes())[:max_nodes])

        nodes_payload = []
        for n in selected_nodes:
            data = self.graph.nodes[n].copy()
            nodes_payload.append(data)

        edges_payload = []
        for u, v, k, data in self.graph.edges(keys=True, data=True):
            if u in selected_nodes and v in selected_nodes:
                edge_dict = data.copy()
                edge_dict["source"] = u
                edge_dict["target"] = v
                edges_payload.append(edge_dict)

        return {
            "summary": {
                "total_nodes": len(nodes_payload),
                "total_edges": len(edges_payload),
                "types": {
                    "employee": sum(1 for n in nodes_payload if n.get("type") == "employee"),
                    "skill": sum(1 for n in nodes_payload if n.get("type") == "skill"),
                    "role": sum(1 for n in nodes_payload if n.get("type") == "role"),
                    "course": sum(1 for n in nodes_payload if n.get("type") == "course")
                }
            },
            "nodes": nodes_payload,
            "edges": edges_payload
        }

    def export_to_cypher(self, output_file: str = "backend/graph/neo4j_export.cypher"):
        """
        Generates production-grade Neo4j Cypher ingestion statements.
        """
        statements = [
            "// SkillGraph Neo4j Ingestion Cypher Script",
            "// Creates unique constraints",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Employee) REQUIRE e.id IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Skill) REQUIRE s.id IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Role) REQUIRE r.id IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Course) REQUIRE c.id IS UNIQUE;\n"
        ]

        # Nodes
        for n, d in self.graph.nodes(data=True):
            ntype = d.get("type", "").capitalize()
            label = d.get("label", "").replace("'", "\\'")
            nid = d.get("id")
            statements.append(f"MERGE (:{ntype} {{id: '{nid}', name: '{label}'}});")

        # Relationships
        statements.append("\n// Relationships")
        for u, v, data in self.graph.edges(data=True):
            rel = data.get("relationship", "CONNECTED_TO")
            statements.append(f"MATCH (a {{id: '{u}'}}), (b {{id: '{v}'}}) MERGE (a)-[:{rel}]->(b);")

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w") as f:
            f.write("\n".join(statements))
        print(f"[GRAPH] Exported {len(statements)} Cypher statements to {output_file}")
        return output_file

skill_graph_manager = SkillGraphManager()
