"""
SkillGraph Data Preprocessing Pipeline
Ingests raw Kaggle & O*NET datasets, normalizes skills, builds role profiles,
constructs a validated course prerequisite DAG, generates seed employees, and
pre-trains the transition readiness ML model.
"""

import os
import re
import json
import joblib
import numpy as np
import pandas as pd
import networkx as nx
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
MODELS_DIR = "backend/ml/models"

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# ---------------------------------------------------------
# 1. Canonical Skill Normalization & Aliases
# ---------------------------------------------------------
CANONICAL_ALIASES = {
    "python": "Python",
    "python3": "Python",
    "python 3": "Python",
    "python programming": "Python",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "es6": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "react": "React",
    "react.js": "React",
    "reactjs": "React",
    "react native": "React Native",
    "vue": "Vue.js",
    "vue.js": "Vue.js",
    "vuejs": "Vue.js",
    "angular": "Angular",
    "angularjs": "Angular",
    "node": "Node.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "express": "Express.js",
    "express.js": "Express.js",
    "html": "HTML/CSS",
    "css": "HTML/CSS",
    "html/css": "HTML/CSS",
    "html5": "HTML/CSS",
    "css3": "HTML/CSS",
    "java": "Java",
    "core java": "Java",
    "c++": "C++",
    "cpp": "C++",
    "c#": "C#",
    "c sharp": "C#",
    ".net": ".NET",
    "dotnet": ".NET",
    "go": "Go",
    "golang": "Go",
    "rust": "Rust",
    "php": "PHP",
    "ruby": "Ruby",
    "ruby on rails": "Ruby on Rails",
    "rails": "Ruby on Rails",
    "sql": "SQL",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "redis": "Redis",
    "aws": "AWS",
    "amazon web services": "AWS",
    "azure": "Azure",
    "microsoft azure": "Azure",
    "gcp": "GCP",
    "google cloud platform": "GCP",
    "google cloud": "GCP",
    "docker": "Docker",
    "docker containers": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "terraform": "Terraform",
    "ansible": "Ansible",
    "jenkins": "Jenkins",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "continuous integration": "CI/CD",
    "git": "Git",
    "github": "Git",
    "gitlab": "Git",
    "linux": "Linux",
    "unix": "Linux",
    "bash": "Bash/Shell",
    "shell scripting": "Bash/Shell",
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "deep learning": "Deep Learning",
    "dl": "Deep Learning",
    "nlp": "Natural Language Processing",
    "natural language processing": "Natural Language Processing",
    "computer vision": "Computer Vision",
    "cv": "Computer Vision",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "scikit-learn": "Scikit-Learn",
    "sklearn": "Scikit-Learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "data analysis": "Data Analysis",
    "data analytics": "Data Analysis",
    "data visualization": "Data Visualization",
    "tableau": "Tableau",
    "power bi": "Power BI",
    "powerbi": "Power BI",
    "spark": "Apache Spark",
    "apache spark": "Apache Spark",
    "kafka": "Apache Kafka",
    "apache kafka": "Apache Kafka",
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "spring": "Spring Boot",
    "spring boot": "Spring Boot",
    "graphql": "GraphQL",
    "rest apis": "REST APIs",
    "rest api": "REST APIs",
    "restful api": "REST APIs",
    "rest": "REST APIs",
    "microservices": "Microservices",
    "system design": "System Design",
    "distributed systems": "Distributed Systems",
    "agile": "Agile Methodologies",
    "scrum": "Agile Methodologies",
    "agile methodologies": "Agile Methodologies",
    "problem solving": "Problem Solving",
    "communication": "Communication",
    "teamwork": "Teamwork",
    "leadership": "Leadership",
    "critical thinking": "Critical Thinking",
    "cybersecurity": "Cybersecurity",
    "network security": "Network Security",
    "penetration testing": "Penetration Testing",
    "ui/ux design": "UI/UX Design",
    "figma": "Figma",
}

def normalize_skill_name(raw_name: str) -> str:
    """Normalize raw skill name or alias into standard canonical title."""
    clean = re.sub(r"[^\w\s\+\#\/\.\-]", "", raw_name.strip().lower())
    clean = re.sub(r"\s+", " ", clean).strip()
    if clean in CANONICAL_ALIASES:
        return CANONICAL_ALIASES[clean]
    # Fallback to Title Case
    return raw_name.strip().title()

def build_skills_catalog():
    print("[1/6] Ingesting skills from raw datasets...")
    skills_map = {}

    # 1. From resume_dataset/skills_list.csv
    skills_csv = os.path.join(RAW_DIR, "resume_dataset", "skills_list.csv")
    if os.path.exists(skills_csv):
        df_skl = pd.read_csv(skills_csv)
        for _, row in df_skl.iterrows():
            name = str(row["Skill Name"]).strip()
            cat = str(row["Category"]).strip()
            norm = normalize_skill_name(name)
            if norm not in skills_map:
                skills_map[norm] = {
                    "skill_id": f"SKL-{len(skills_map)+1:03d}",
                    "name": norm,
                    "category": cat or "General Technology",
                    "importance_weight": 1.2 if cat in ["Programming", "Cloud & DevOps", "Database", "Data Science & Analytics"] else 1.0,
                    "aliases": [name.lower()] if name.lower() != norm.lower() else []
                }

    # 2. From resume_dataset/skills_database.json
    sdb_json = os.path.join(RAW_DIR, "resume_dataset", "skills_database.json")
    if os.path.exists(sdb_json):
        with open(sdb_json, "r") as f:
            sdb = json.load(f)
        for cat, items in sdb.items():
            for it in items:
                norm = normalize_skill_name(it)
                if norm not in skills_map:
                    skills_map[norm] = {
                        "skill_id": f"SKL-{len(skills_map)+1:03d}",
                        "name": norm,
                        "category": cat,
                        "importance_weight": 1.2 if cat in ["Programming", "Cloud & DevOps", "Database", "Data Science & Analytics"] else 1.0,
                        "aliases": [it.lower()] if it.lower() != norm.lower() else []
                    }
                elif it.lower() not in skills_map[norm]["aliases"] and it.lower() != norm.lower():
                    skills_map[norm]["aliases"].append(it.lower())

    # 3. Add core canonical aliases mapping
    for alias, canon in CANONICAL_ALIASES.items():
        if canon in skills_map and alias not in skills_map[canon]["aliases"] and alias != canon.lower():
            skills_map[canon]["aliases"].append(alias)

    # Ensure key tech skills exist
    essential_skills = [
        ("Python", "Programming"), ("Java", "Programming"), ("JavaScript", "Programming"),
        ("TypeScript", "Programming"), ("C++", "Programming"), ("Go", "Programming"),
        ("React", "Web Development"), ("Node.js", "Web Development"), ("FastAPI", "Web Development"),
        ("HTML/CSS", "Web Development"), ("SQL", "Database"), ("PostgreSQL", "Database"),
        ("MongoDB", "Database"), ("Redis", "Database"), ("Docker", "Cloud & DevOps"),
        ("Kubernetes", "Cloud & DevOps"), ("AWS", "Cloud & DevOps"), ("Azure", "Cloud & DevOps"),
        ("GCP", "Cloud & DevOps"), ("CI/CD", "Cloud & DevOps"), ("Terraform", "Cloud & DevOps"),
        ("Linux", "Systems"), ("Bash/Shell", "Systems"), ("Git", "Tools"),
        ("Machine Learning", "Data Science & AI"), ("Deep Learning", "Data Science & AI"),
        ("Natural Language Processing", "Data Science & AI"), ("Scikit-Learn", "Data Science & AI"),
        ("TensorFlow", "Data Science & AI"), ("PyTorch", "Data Science & AI"),
        ("Pandas", "Data Science & AI"), ("NumPy", "Data Science & AI"),
        ("Cybersecurity", "Cybersecurity"), ("Network Security", "Cybersecurity"),
        ("System Design", "Architecture"), ("Microservices", "Architecture"),
        ("REST APIs", "Backend"), ("GraphQL", "Backend"),
        ("Communication", "Soft Skills"), ("Problem Solving", "Soft Skills"),
        ("Teamwork", "Soft Skills"), ("Leadership", "Soft Skills"), ("Agile Methodologies", "Management")
    ]
    for name, cat in essential_skills:
        if name not in skills_map:
            skills_map[name] = {
                "skill_id": f"SKL-{len(skills_map)+1:03d}",
                "name": name,
                "category": cat,
                "importance_weight": 1.3 if cat in ["Cloud & DevOps", "Data Science & AI", "Architecture"] else 1.1,
                "aliases": []
            }

    skills_list = list(skills_map.values())
    skills_out = os.path.join(PROCESSED_DIR, "canonical_skills.json")
    with open(skills_out, "w") as f:
        json.dump(skills_list, f, indent=2)
    print(f"  -> Generated {len(skills_list)} canonical skills into {skills_out}")
    return skills_map

# ---------------------------------------------------------
# 2. Canonical Roles & Role Profiles
# ---------------------------------------------------------
def build_roles_catalog(skills_map):
    print("[2/6] Building canonical role profiles...")
    roles_map = {}

    roles_csv = os.path.join(RAW_DIR, "resume_dataset", "job_roles.csv")
    if os.path.exists(roles_csv):
        df_roles = pd.read_csv(roles_csv)
        for _, row in df_roles.iterrows():
            title = str(row["Job Title"]).strip()
            cat = str(row.get("Category", "Technology")).strip()
            exp_years = int(row["Experience Years"]) if pd.notna(row.get("Experience Years")) else 2
            edu = str(row.get("Education Requirement", "Bachelor's in Computer Science")).replace("|", " or ")
            salary = str(row.get("Salary Range", "80-130K")).strip()

            raw_req = str(row.get("Required Skills", "")).split("|")
            norm_req = []
            for s in raw_req:
                if s.strip():
                    ns = normalize_skill_name(s.strip())
                    if ns in skills_map and ns not in norm_req:
                        norm_req.append(ns)

            if len(norm_req) < 3:
                continue

            role_id = f"ROL-{len(roles_map)+1:03d}"
            roles_map[title] = {
                "role_id": role_id,
                "title": title,
                "category": cat,
                "department": "Engineering" if cat in ["Technology", "Data"] else "Operations",
                "experience_years": exp_years,
                "education": edu,
                "salary_range": salary,
                "required_skills": norm_req,
                "description": f"Responsible for designing, delivering, and maintaining enterprise solutions as a {title}.",
                "openings": 2 + (len(norm_req) % 4)
            }

    # Ensure hallmark organizational benchmark roles exist with rich profiles
    hallmark_roles = [
        {
            "title": "Cloud Engineer",
            "category": "Cloud Operations",
            "department": "Infrastructure",
            "experience_years": 3,
            "education": "Bachelor's in Computer Science or Engineering",
            "salary_range": "105-160K",
            "required_skills": ["AWS", "Docker", "Kubernetes", "Linux", "Terraform", "CI/CD", "Python"],
            "description": "Architects, provisions, and maintains highly available enterprise cloud infrastructure.",
            "openings": 5
        },
        {
            "title": "Data Scientist",
            "category": "Data & AI",
            "department": "Data Science",
            "experience_years": 3,
            "education": "Master's in Data Science or Computer Science",
            "salary_range": "110-165K",
            "required_skills": ["Python", "SQL", "Pandas", "Scikit-Learn", "Machine Learning", "Data Visualization", "Communication"],
            "description": "Extracts insights from large-scale data, builds predictive ML models, and communicates value to stakeholders.",
            "openings": 4
        },
        {
            "title": "Machine Learning Engineer",
            "category": "Data & AI",
            "department": "AI Engineering",
            "experience_years": 4,
            "education": "Master's in Computer Science or AI",
            "salary_range": "125-180K",
            "required_skills": ["Python", "Machine Learning", "Deep Learning", "PyTorch", "Docker", "FastAPI", "MLOps"],
            "description": "Designs, optimizes, and deploys scalable production deep learning and machine learning models.",
            "openings": 3
        },
        {
            "title": "Full Stack Developer",
            "category": "Technology",
            "department": "Engineering",
            "experience_years": 2,
            "education": "Bachelor's in Computer Science or Software Engineering",
            "salary_range": "85-140K",
            "required_skills": ["JavaScript", "TypeScript", "React", "Node.js", "FastAPI", "SQL", "Git", "REST APIs"],
            "description": "Builds end-to-end responsive web applications across frontend clients and backend microservices.",
            "openings": 6
        },
        {
            "title": "DevOps Engineer",
            "category": "Cloud Operations",
            "department": "Infrastructure",
            "experience_years": 3,
            "education": "Bachelor's in Computer Science",
            "salary_range": "100-155K",
            "required_skills": ["Linux", "Docker", "Kubernetes", "CI/CD", "AWS", "Git", "Bash/Shell"],
            "description": "Streamlines software deployment lifecycles, automates CI/CD pipelines, and manages container clusters.",
            "openings": 4
        },
        {
            "title": "Frontend Developer",
            "category": "Technology",
            "department": "Engineering",
            "experience_years": 2,
            "education": "Bachelor's in Computer Science or IT",
            "salary_range": "75-130K",
            "required_skills": ["JavaScript", "TypeScript", "React", "HTML/CSS", "Git", "UI/UX Design"],
            "description": "Builds accessible, visually stunning, high-performance web frontends and interactive component systems.",
            "openings": 4
        },
        {
            "title": "Backend Developer",
            "category": "Technology",
            "department": "Engineering",
            "experience_years": 2,
            "education": "Bachelor's in Software Engineering",
            "salary_range": "85-140K",
            "required_skills": ["Python", "FastAPI", "SQL", "PostgreSQL", "Docker", "REST APIs", "Git"],
            "description": "Develops resilient high-throughput backend APIs, databases, and microservices.",
            "openings": 5
        },
        {
            "title": "Security Analyst",
            "category": "Cybersecurity",
            "department": "Information Security",
            "experience_years": 3,
            "education": "Bachelor's in Cybersecurity or Computer Science",
            "salary_range": "95-150K",
            "required_skills": ["Cybersecurity", "Network Security", "Linux", "Python", "Problem Solving"],
            "description": "Protects digital assets, identifies vulnerabilities, responds to security incidents, and audits compliance.",
            "openings": 2
        }
    ]

    for hr in hallmark_roles:
        t = hr["title"]
        if t in roles_map:
            roles_map[t].update(hr)
        else:
            hr["role_id"] = f"ROL-{len(roles_map)+1:03d}"
            roles_map[t] = hr

    roles_list = list(roles_map.values())
    roles_out = os.path.join(PROCESSED_DIR, "canonical_roles.json")
    with open(roles_out, "w") as f:
        json.dump(roles_list, f, indent=2)
    print(f"  -> Generated {len(roles_list)} canonical roles into {roles_out}")
    return roles_map

# ---------------------------------------------------------
# 3. Course Catalog & Prerequisite DAG
# ---------------------------------------------------------
def build_course_catalog():
    print("[3/6] Constructing validated course catalog and prerequisite DAG...")
    courses = [
        {
            "course_id": "CRS-001",
            "title": "Python Programming Foundations",
            "provider": "SkillGraph Academy",
            "duration_weeks": 4,
            "level": "Beginner",
            "skills_taught": ["Python"],
            "prerequisites": [],
            "description": "Master core Python syntax, OOP concepts, data structures, and standard libraries."
        },
        {
            "course_id": "CRS-002",
            "title": "Modern JavaScript & TypeScript Mastery",
            "provider": "SkillGraph Academy",
            "duration_weeks": 4,
            "level": "Beginner",
            "skills_taught": ["JavaScript", "TypeScript"],
            "prerequisites": [],
            "description": "Learn ES6+, asynchronous JavaScript, typing systems, and DOM manipulation."
        },
        {
            "course_id": "CRS-003",
            "title": "Linux System Administration & Shell Scripting",
            "provider": "CloudOps Institute",
            "duration_weeks": 3,
            "level": "Beginner",
            "skills_taught": ["Linux", "Bash/Shell"],
            "prerequisites": [],
            "description": "Command line mastery, file permissions, process management, and shell automation."
        },
        {
            "course_id": "CRS-004",
            "title": "Relational Databases & SQL Optimization",
            "provider": "DataTech Labs",
            "duration_weeks": 4,
            "level": "Beginner",
            "skills_taught": ["SQL", "PostgreSQL"],
            "prerequisites": [],
            "description": "Complex joins, indexing, query optimization, and schema normalization."
        },
        {
            "course_id": "CRS-005",
            "title": "Computer Networking & Web Protocols",
            "provider": "CloudOps Institute",
            "duration_weeks": 3,
            "level": "Intermediate",
            "skills_taught": ["Network Security", "REST APIs"],
            "prerequisites": ["CRS-003"],
            "description": "TCP/IP stack, DNS, HTTP/HTTPS, SSL/TLS certificates, and load balancing."
        },
        {
            "course_id": "CRS-006",
            "title": "Cloud Computing Foundations with AWS",
            "provider": "CloudOps Institute",
            "duration_weeks": 5,
            "level": "Intermediate",
            "skills_taught": ["AWS"],
            "prerequisites": ["CRS-003", "CRS-005"],
            "description": "EC2, S3, RDS, VPCs, IAM policies, and cloud cost management on AWS."
        },
        {
            "course_id": "CRS-007",
            "title": "Docker Containers & Microservices Essentials",
            "provider": "DevOps Training Hub",
            "duration_weeks": 4,
            "level": "Intermediate",
            "skills_taught": ["Docker", "Microservices"],
            "prerequisites": ["CRS-003"],
            "description": "Container architecture, multi-stage Dockerfiles, Docker Compose, and networking."
        },
        {
            "course_id": "CRS-008",
            "title": "Kubernetes Container Orchestration at Scale",
            "provider": "DevOps Training Hub",
            "duration_weeks": 5,
            "level": "Advanced",
            "skills_taught": ["Kubernetes"],
            "prerequisites": ["CRS-006", "CRS-007"],
            "description": "Pods, Deployments, Services, Ingress, Helm charts, and cluster auto-scaling."
        },
        {
            "course_id": "CRS-009",
            "title": "CI/CD Automation & Infrastructure as Code (Terraform)",
            "provider": "DevOps Training Hub",
            "duration_weeks": 4,
            "level": "Advanced",
            "skills_taught": ["CI/CD", "Terraform"],
            "prerequisites": ["CRS-006", "CRS-007"],
            "description": "GitHub Actions, automated test pipelines, and declarative cloud provisioning with Terraform."
        },
        {
            "course_id": "CRS-010",
            "title": "Modern Frontend Development with React",
            "provider": "SkillGraph Academy",
            "duration_weeks": 5,
            "level": "Intermediate",
            "skills_taught": ["React", "HTML/CSS", "UI/UX Design"],
            "prerequisites": ["CRS-002"],
            "description": "React hooks, state management, component architecture, and responsive styling."
        },
        {
            "course_id": "CRS-011",
            "title": "Backend Engineering with FastAPI & Microservices",
            "provider": "SkillGraph Academy",
            "duration_weeks": 4,
            "level": "Intermediate",
            "skills_taught": ["FastAPI", "REST APIs", "Microservices"],
            "prerequisites": ["CRS-001", "CRS-004"],
            "description": "Asynchronous APIs with FastAPI, Pydantic validation, JWT security, and ORMs."
        },
        {
            "course_id": "CRS-012",
            "title": "Applied Data Analysis with Pandas & NumPy",
            "provider": "DataTech Labs",
            "duration_weeks": 4,
            "level": "Intermediate",
            "skills_taught": ["Pandas", "NumPy", "Data Analysis", "Data Visualization"],
            "prerequisites": ["CRS-001", "CRS-004"],
            "description": "Data wrangling, exploratory data analysis, time series manipulation, and Matplotlib."
        },
        {
            "course_id": "CRS-013",
            "title": "Machine Learning Algorithms with Scikit-Learn",
            "provider": "DataTech Labs",
            "duration_weeks": 6,
            "level": "Advanced",
            "skills_taught": ["Machine Learning", "Scikit-Learn"],
            "prerequisites": ["CRS-012"],
            "description": "Supervised/unsupervised algorithms, cross-validation, feature engineering, and metrics."
        },
        {
            "course_id": "CRS-014",
            "title": "Deep Learning & NLP with PyTorch",
            "provider": "DataTech Labs",
            "duration_weeks": 6,
            "level": "Advanced",
            "skills_taught": ["Deep Learning", "Natural Language Processing", "PyTorch"],
            "prerequisites": ["CRS-013"],
            "description": "Neural network architectures, transformers, embeddings, and NLP pipelines."
        },
        {
            "course_id": "CRS-015",
            "title": "Production MLOps & Model Deployment",
            "provider": "DataTech Labs",
            "duration_weeks": 4,
            "level": "Advanced",
            "skills_taught": ["Machine Learning", "Docker"],
            "prerequisites": ["CRS-007", "CRS-013"],
            "description": "Model serving, experiment tracking, pipeline automation, and monitoring model drift."
        },
        {
            "course_id": "CRS-016",
            "title": "Enterprise Cybersecurity & Network Defense",
            "provider": "CloudOps Institute",
            "duration_weeks": 4,
            "level": "Intermediate",
            "skills_taught": ["Cybersecurity", "Network Security"],
            "prerequisites": ["CRS-005"],
            "description": "Threat modeling, vulnerability scanning, security incident management, and hardening."
        },
        {
            "course_id": "CRS-017",
            "title": "System Design & Distributed Architecture",
            "provider": "SkillGraph Academy",
            "duration_weeks": 5,
            "level": "Advanced",
            "skills_taught": ["System Design", "Microservices"],
            "prerequisites": ["CRS-006", "CRS-011"],
            "description": "Scalability, CAP theorem, caching strategies, rate limiting, and fault tolerance."
        },
        {
            "course_id": "CRS-018",
            "title": "Agile Leadership & Cross-Functional Teamwork",
            "provider": "SkillGraph Leadership",
            "duration_weeks": 2,
            "level": "Beginner",
            "skills_taught": ["Communication", "Teamwork", "Agile Methodologies", "Leadership"],
            "prerequisites": [],
            "description": "Sprint planning, stakeholder management, code review culture, and effective collaboration."
        }
    ]

    # Verify DAG mathematical property
    G = nx.DiGraph()
    for c in courses:
        G.add_node(c["course_id"])
        for pre in c["prerequisites"]:
            G.add_edge(pre, c["course_id"])

    assert nx.is_directed_acyclic_graph(G), "CRITICAL: Course prerequisites contain a cycle!"
    print("  -> Course Prerequisite DAG mathematically validated (No cycles).")

    courses_out = os.path.join(PROCESSED_DIR, "course_catalog.json")
    with open(courses_out, "w") as f:
        json.dump(courses, f, indent=2)
    print(f"  -> Generated {len(courses)} courses into {courses_out}")
    return courses

# ---------------------------------------------------------
# 4. Seed Representative Organizational Employees
# ---------------------------------------------------------
def build_seed_employees():
    print("[4/6] Creating realistic employee profiles...")
    employees = [
        {
            "employee_id": "EMP-001",
            "name": "Alex Rivera",
            "email": "alex.rivera@skillgraph.internal",
            "current_role": "Software Developer",
            "department": "Engineering",
            "experience_years": 3,
            "qualification": "Bachelor's in Computer Science",
            "target_role": "Cloud Engineer",
            "skills": [
                {"name": "Python", "proficiency": "Advanced", "verified": True},
                {"name": "SQL", "proficiency": "Intermediate", "verified": True},
                {"name": "Git", "proficiency": "Advanced", "verified": True},
                {"name": "Linux", "proficiency": "Intermediate", "verified": True},
                {"name": "REST APIs", "proficiency": "Intermediate", "verified": True},
                {"name": "Problem Solving", "proficiency": "Advanced", "verified": True}
            ],
            "completed_courses": ["CRS-001", "CRS-003", "CRS-004"],
            "bio": "Full-stack software developer with 3 years building web services. Eager to transition into Cloud Engineering and infrastructure automation."
        },
        {
            "employee_id": "EMP-002",
            "name": "Priya Sharma",
            "email": "priya.sharma@skillgraph.internal",
            "current_role": "Frontend Developer",
            "department": "Engineering",
            "experience_years": 2,
            "qualification": "Bachelor's in Information Technology",
            "target_role": "Full Stack Developer",
            "skills": [
                {"name": "JavaScript", "proficiency": "Advanced", "verified": True},
                {"name": "TypeScript", "proficiency": "Intermediate", "verified": True},
                {"name": "React", "proficiency": "Advanced", "verified": True},
                {"name": "HTML/CSS", "proficiency": "Expert", "verified": True},
                {"name": "UI/UX Design", "proficiency": "Intermediate", "verified": True},
                {"name": "Git", "proficiency": "Intermediate", "verified": True}
            ],
            "completed_courses": ["CRS-002", "CRS-010"],
            "bio": "Frontend specialist experienced in responsive UI component libraries. Looking to expand into backend APIs and microservices."
        },
        {
            "employee_id": "EMP-003",
            "name": "Marcus Chen",
            "email": "marcus.chen@skillgraph.internal",
            "current_role": "Data Analyst",
            "department": "Data Science",
            "experience_years": 3,
            "qualification": "Bachelor's in Statistics & Mathematics",
            "target_role": "Data Scientist",
            "skills": [
                {"name": "Python", "proficiency": "Intermediate", "verified": True},
                {"name": "SQL", "proficiency": "Advanced", "verified": True},
                {"name": "Pandas", "proficiency": "Advanced", "verified": True},
                {"name": "Data Analysis", "proficiency": "Expert", "verified": True},
                {"name": "Data Visualization", "proficiency": "Advanced", "verified": True},
                {"name": "Communication", "proficiency": "Advanced", "verified": True}
            ],
            "completed_courses": ["CRS-001", "CRS-004", "CRS-012"],
            "bio": "Quantitative analyst with strong statistical background, focusing on expanding into predictive machine learning."
        },
        {
            "employee_id": "EMP-004",
            "name": "Elena Rostova",
            "email": "elena.rostova@skillgraph.internal",
            "current_role": "Backend Developer",
            "department": "Engineering",
            "experience_years": 4,
            "qualification": "Master's in Software Engineering",
            "target_role": "DevOps Engineer",
            "skills": [
                {"name": "Python", "proficiency": "Advanced", "verified": True},
                {"name": "FastAPI", "proficiency": "Advanced", "verified": True},
                {"name": "PostgreSQL", "proficiency": "Advanced", "verified": True},
                {"name": "Docker", "proficiency": "Intermediate", "verified": True},
                {"name": "Linux", "proficiency": "Advanced", "verified": True},
                {"name": "REST APIs", "proficiency": "Expert", "verified": True}
            ],
            "completed_courses": ["CRS-001", "CRS-003", "CRS-004", "CRS-007", "CRS-011"],
            "bio": "Backend software architect with deep experience in database design and high-load APIs. Interested in DevOps and infrastructure automation."
        },
        {
            "employee_id": "EMP-005",
            "name": "David Kim",
            "email": "david.kim@skillgraph.internal",
            "current_role": "QA Automation Engineer",
            "department": "Quality Assurance",
            "experience_years": 2,
            "qualification": "Bachelor's in Computer Science",
            "target_role": "Backend Developer",
            "skills": [
                {"name": "Python", "proficiency": "Intermediate", "verified": True},
                {"name": "Git", "proficiency": "Intermediate", "verified": True},
                {"name": "Linux", "proficiency": "Beginner", "verified": True},
                {"name": "REST APIs", "proficiency": "Intermediate", "verified": True},
                {"name": "Problem Solving", "proficiency": "Advanced", "verified": True}
            ],
            "completed_courses": ["CRS-001"],
            "bio": "Test automation engineer seeking to transition directly into core backend software development."
        },
        {
            "employee_id": "EMP-006",
            "name": "Sarah Jenkins (HR Admin)",
            "email": "sarah.jenkins@skillgraph.internal",
            "current_role": "HR Director",
            "department": "People & Culture",
            "experience_years": 8,
            "qualification": "Master's in Human Resources & Organizational Development",
            "target_role": "HR Director",
            "skills": [
                {"name": "Leadership", "proficiency": "Expert", "verified": True},
                {"name": "Communication", "proficiency": "Expert", "verified": True},
                {"name": "Agile Methodologies", "proficiency": "Advanced", "verified": True},
                {"name": "Teamwork", "proficiency": "Expert", "verified": True}
            ],
            "completed_courses": ["CRS-018"],
            "bio": "Head of Talent Development leading workforce planning, internal mobility strategy, and skill gap remediation."
        }
    ]

    emp_out = os.path.join(PROCESSED_DIR, "employees_seed.json")
    with open(emp_out, "w") as f:
        json.dump(employees, f, indent=2)
    print(f"  -> Generated {len(employees)} seed employees into {emp_out}")
    return employees

# ---------------------------------------------------------
# 5. HR Workforce Demand Forecasting
# ---------------------------------------------------------
def build_workforce_demand():
    print("[5/6] Generating organizational workforce demand metrics...")
    demand_data = {
        "summary": {
            "total_headcount": 142,
            "open_positions": 28,
            "projected_q4_hires": 35,
            "internal_mobility_target_pct": 65,
            "upskilling_active_employees": 46
        },
        "role_demands": [
            {
                "role_title": "Cloud Engineer",
                "department": "Infrastructure",
                "current_headcount": 6,
                "projected_demand": 14,
                "gap": 8,
                "priority": "High",
                "urgency_score": 92,
                "top_internal_feeders": ["Software Developer", "DevOps Engineer", "Backend Developer"]
            },
            {
                "role_title": "Data Scientist",
                "department": "Data Science",
                "current_headcount": 5,
                "projected_demand": 11,
                "gap": 6,
                "priority": "High",
                "urgency_score": 88,
                "top_internal_feeders": ["Data Analyst", "Software Developer"]
            },
            {
                "role_title": "Machine Learning Engineer",
                "department": "AI Engineering",
                "current_headcount": 3,
                "projected_demand": 8,
                "gap": 5,
                "priority": "Critical",
                "urgency_score": 95,
                "top_internal_feeders": ["Data Scientist", "Backend Developer"]
            },
            {
                "role_title": "Full Stack Developer",
                "department": "Engineering",
                "current_headcount": 12,
                "projected_demand": 18,
                "gap": 6,
                "priority": "Medium",
                "urgency_score": 75,
                "top_internal_feeders": ["Frontend Developer", "Backend Developer"]
            },
            {
                "role_title": "Security Analyst",
                "department": "Information Security",
                "current_headcount": 4,
                "projected_demand": 7,
                "gap": 3,
                "priority": "Medium",
                "urgency_score": 70,
                "top_internal_feeders": ["DevOps Engineer", "Backend Developer"]
            }
        ],
        "top_skill_shortages": [
            {"skill": "Kubernetes", "missing_count": 22, "category": "Cloud & DevOps"},
            {"skill": "AWS", "missing_count": 19, "category": "Cloud & DevOps"},
            {"skill": "Machine Learning", "missing_count": 16, "category": "Data Science & AI"},
            {"skill": "Docker", "missing_count": 14, "category": "Cloud & DevOps"},
            {"skill": "CI/CD", "missing_count": 13, "category": "Cloud & DevOps"},
            {"skill": "FastAPI", "missing_count": 11, "category": "Backend"},
            {"skill": "TypeScript", "missing_count": 10, "category": "Web Development"}
        ]
    }

    out_file = os.path.join(PROCESSED_DIR, "workforce_demand.json")
    with open(out_file, "w") as f:
        json.dump(demand_data, f, indent=2)
    print(f"  -> Generated workforce demand data into {out_file}")
    return demand_data

# ---------------------------------------------------------
# 6. Train Machine Learning Transition Readiness Model
# ---------------------------------------------------------
def train_readiness_model():
    print("[6/6] Training transition readiness ML prediction model...")
    # Synthetic feature engineering based on authentic organizational dynamics
    np.random.seed(42)
    n_samples = 2500

    # Features:
    # 0: skill_match_ratio (0.0 to 1.0)
    # 1: core_skill_coverage (0.0 to 1.0)
    # 2: experience_delta (current_exp - required_exp, e.g. -3 to +5)
    # 3: education_alignment (0.0 to 1.0)
    # 4: prerequisite_readiness (0.0 to 1.0)

    skill_match = np.random.beta(a=3, b=2, size=n_samples)
    core_coverage = np.random.beta(a=2.5, b=2, size=n_samples)
    exp_delta = np.random.normal(loc=0.5, scale=1.5, size=n_samples)
    edu_align = np.random.choice([0.5, 0.8, 1.0], size=n_samples, p=[0.2, 0.3, 0.5])
    prereq_readiness = np.clip(skill_match + np.random.normal(0, 0.1, n_samples), 0, 1)

    X = np.column_stack([skill_match, core_coverage, exp_delta, edu_align, prereq_readiness])

    # True composite readiness score formula with realistic non-linearities and noise
    score = (
        0.40 * skill_match +
        0.25 * core_coverage +
        0.15 * np.clip((exp_delta + 2) / 4.0, 0, 1) +
        0.10 * edu_align +
        0.10 * prereq_readiness +
        np.random.normal(0, 0.04, n_samples)
    )
    score = np.clip(score, 0.0, 1.0)

    # Classification label: 1 if ready (score >= 0.70), 0 otherwise
    y = (score >= 0.70).astype(int)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    clf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    clf.fit(X_scaled, y)

    train_acc = clf.score(X_scaled, y)
    print(f"  -> Model trained successfully. Accuracy: {train_acc*100:.2f}%")

    model_artifacts = {
        "model": clf,
        "scaler": scaler,
        "feature_names": [
            "skill_match_ratio",
            "core_skill_coverage",
            "experience_delta",
            "education_alignment",
            "prerequisite_readiness"
        ]
    }
    model_path = os.path.join(MODELS_DIR, "readiness_model.joblib")
    joblib.dump(model_artifacts, model_path)
    print(f"  -> Saved pre-trained model to {model_path}")

if __name__ == "__main__":
    print("==================================================")
    print("Starting SkillGraph Data Preprocessing Pipeline...")
    print("==================================================")
    skills = build_skills_catalog()
    roles = build_roles_catalog(skills)
    courses = build_course_catalog()
    seed_emp = build_seed_employees()
    demand = build_workforce_demand()
    train_readiness_model()
    print("==================================================")
    print("All processed artifacts successfully constructed!")
    print("==================================================")
