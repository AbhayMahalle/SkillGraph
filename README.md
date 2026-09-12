# SkillGraph

**AI-Powered Workforce Skill Gap Analysis & Internal Career Mobility System**

SkillGraph is an AI-powered talent intelligence and internal career mobility platform. Built on authentic datasets (Job Skill Set, Resume Dataset, Candidate–Job Role Dataset, and O*NET 29.0 Database), it connects employee profiles, occupational standards, prerequisite course DAGs, and machine learning models to answer two foundational questions:

1. **Employee Perspective:** *"Which internal roles can I transition into, what skills am I missing, what should I learn first, and how ready will I become after upskilling?"*
2. **Organization Perspective:** *"What future roles will the organization need, which existing employees can fill those roles, what critical skill shortages exist, and how can we close them internally?"*

---

## 🔬 Research Positioning

Existing workforce systems typically operate in isolation:
- Resume-to-external job matching
- Static skill-gap taggers ("You are missing AWS")
- Unordered course catalogs
- Isolated occupational graphs

**SkillGraph bridges this gap through Predictive Internal Talent Mobility:**
```text
Internal Employee Mobility
  + Skill Gap Analysis (Multi-Factor Match & Competency Breakdown)
  + Prerequisite-Aware Learning (Topological DAG Roadmaps)
  + Future Readiness Prediction (Supervised ML Classifier: 94.28% Accuracy)
  + Interactive What-If Simulation Sandbox
  + Organization-Level Workforce Headcount Planning
```

---

## 🏛️ System Architecture

```text
 ┌─────────────────────────────────────────────────────────┐
 │               Frontend (React 18 + Vite + TS)           │
 │  - Employee Mobility Hub    - Competency Radar Chart    │
 │  - NLP Resume Skill Parser  - Topological Roadmap       │
 │  - What-If Career Sandbox   - 2D Knowledge Graph (Canvas)│
 │  - HR Workforce Planning    - Raw Datasets Explorer     │
 └────────────────────────────┬────────────────────────────┘
                              │ REST APIs (JSON / JWT)
                              ▼
 ┌─────────────────────────────────────────────────────────┐
 │                  Backend (FastAPI + Python)             │
 │  - Role-Based Access (RBAC) - NLP Entity Extractor      │
 │  - Canonical Normalizer     - Multi-Factor Role Matcher │
 │  - Topological DAG Engine   - ML Readiness Predictor    │
 │  - NetworkX Graph Engine    - Neo4j Cypher Generator    │
 └──────────────┬────────────────────────────┬─────────────┘
                │                            │
 ┌──────────────▼─────────────┐ ┌────────────▼─────────────┐
 │    Structured Database     │ │      Knowledge Graph     │
 │  (SQLite / PostgreSQL)     │ │   (NetworkX + Neo4j)     │
 └────────────────────────────┘ └──────────────────────────┘
```

---

## 📊 Authentic Data Sources

SkillGraph operates directly on 4 verified datasets in `data/raw/`:
1. **Job Skill Set Dataset (`all_job_post.csv`)**: 1,167 real job postings across IT, Finance, Sales, and HR with empirical skill distributions.
2. **Resume Dataset (`job_roles.csv` & `skills_database.json`)**: 324 canonical role profiles, experience requirements, and benchmark salary tiers.
3. **Candidate–Job Role Dataset (`candidate_job_role_dataset.csv`)**: 1,000 empirical employee records training the transition readiness ML classifier.
4. **O*NET 29.0 Database (`db_29_0_text/`)**: US Department of Labor national taxonomy providing official SOC codes, descriptions, and technology skills.

---

## 🚀 Key Modules & Capabilities

### 1. Employee Mobility Dashboard
- Real-time match scores and projected readiness for designated target roles.
- Top ranked internal transition opportunities calculated by multi-factor algorithmic compatibility.

### 2. NLP Resume Skill Extractor
- Free-form text parser using n-gram windows and alias resolution across 119 canonical competencies.
- Confidence scoring and automatic skill portfolio updates.

### 3. Competency Radar & Skill Gap Analysis
- Interactive SVG Radar Chart contrasting current capability against the target benchmark (85%).
- Categorized competency inventory: **Strong Match**, **Partial Match**, and **Critical Gaps**.

### 4. Topological Learning Roadmaps
- Prerequisite-aware course roadmap generated via `networkx.topological_sort` over the Course Prerequisite DAG.
- Guarantees foundational courses (Linux, SQL) are mastered before advanced dependencies (Kubernetes, MLOps).

### 5. What-If Career Transition Simulator
- Interactive sandbox allowing employees to toggle prospective courses and skills.
- Real-time simulation of match score surges, skills closed, and ML-predicted transition feasibility.

### 6. 2D Interactive SkillGraph Visualizer
- Force-directed HTML5 canvas rendering of Employees, Skills, Roles, and Courses.
- Node inspection, neighborhood filtering, and 1-click export to **Neo4j Cypher** (`backend/graph/neo4j_export.cypher`).

### 7. HR Workforce Planning & Talent Pipeline
- Organizational KPIs: Headcount, open requisitions, target internal mobility rate (65%), active upskilling count.
- Priority headcount gap tracker with an **Internal Feeder Candidate Finder** ranking staff for future roles.
- Aggregate competency shortage analytics highlighting corporate training priorities.

---

## 🛠️ Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# (Optional) Rebuild processed datasets and train ML model
python backend/preprocessing/build_processed_data.py

# Initialize and seed database
python -m backend.database.init_db

# Start FastAPI server (runs on http://127.0.0.1:8000)
python backend/main.py
```

### 2. Frontend Setup
```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite dev server (runs on http://localhost:5173)
npm run dev
```

---

## 🔑 Demo Credentials

| Role | Email | Password | Pre-seeded Profile |
|---|---|---|---|
| **Employee** | `alex.rivera@skillgraph.internal` | `employee123` | Alex Rivera (Software Dev → Cloud Engineer) |
| **Employee** | `priya.sharma@skillgraph.internal` | `employee123` | Priya Sharma (Frontend Dev → Full Stack) |
| **Employee** | `marcus.chen@skillgraph.internal` | `employee123` | Marcus Chen (Data Analyst → Data Scientist) |
| **HR Admin** | `sarah.jenkins@skillgraph.internal` | `admin123` | Sarah Jenkins (HR Director / Org Admin) |

*Note: The UI includes 1-click **"Switch to Employee / Switch to HR"** buttons in the navbar for seamless grading and demonstration.*

---

## 🧪 Automated Testing

Run the automated test suite covering skill normalization, role matching, DAG acyclicity, ML prediction, and NLP parsing:

```bash
python -m pytest tests/test_skillgraph.py
```

**Test Coverage:**
- `test_skill_normalization`: Validates canonical normalization of technology aliases.
- `test_nlp_skill_extraction`: Confirms token extraction from raw resume text.
- `test_role_matching_calculation`: Verifies multi-factor scoring formula and mobility statuses.
- `test_topological_dag_properties`: Validates strict DAG acyclicity and prerequisite order.
- `test_readiness_prediction_monotonicity`: Asserts ML readiness probability bounds and monotonicity.
