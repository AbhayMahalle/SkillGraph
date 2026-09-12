# BUILD THE COMPLETE PROJECT — SKILLGRAPH

Build the complete, functional web application:

**SkillGraph — AI-Powered Workforce Skill Gap Analysis and Internal Career Mobility System**

This is a college/research project focused on **AI-powered internal employee mobility, skill-gap analysis, role matching, future-readiness prediction, personalized learning paths, what-if simulations, and workforce planning**.

The project must be implemented as a real working system, not merely a UI mockup.

---

# 1. FIRST: UNDERSTAND THE EXISTING PROJECT

Before writing code:

1. Inspect the entire existing repository.
2. Inspect the existing folder structure.
3. Inspect every dataset inside:

```text
data/raw/
```

4. Identify the actual filenames, formats, columns, data types, missing values, relationships, and useful fields.
5. Inspect the existing notebooks if present.
6. Reuse existing code where appropriate.
7. Do NOT rename or replace existing datasets.
8. Do NOT invent dataset columns.
9. Do NOT generate fake datasets if the real datasets are available.
10. Adapt the implementation to the actual schemas found in `data/raw/`.

The datasets that must be used are the datasets already discussed for SkillGraph:

* Job Skill Set dataset
* Resume dataset
* Candidate–Job Role dataset
* O*NET database

The O*NET data may contain multiple files. Inspect them and use the relevant occupation, skill, technology-skill, task, and related-occupation information rather than blindly loading every file.

---

# 2. PROJECT OBJECTIVE

SkillGraph should answer two major questions.

## Employee-level question

"For a particular employee, which internal roles can they move into, what skills are they missing, what should they learn first, and how ready will they become after upskilling?"

## Organization-level question

"What future roles will the organization need, which existing employees can potentially fill those roles, what skill gaps exist, and what training can close those gaps?"

The system should therefore connect:

```text
Employee
   ↓
Skills
   ↓
Target Role
   ↓
Required Skills
   ↓
Skill Gap
   ↓
Prerequisites
   ↓
Learning Path
   ↓
Readiness Prediction
   ↓
Internal Mobility
   ↓
Workforce Planning
```

---

# 3. CORE DIFFERENTIATOR

Do NOT position this as merely:

"Employee skill gap analysis."

The central concept is:

**Predictive Internal Talent Mobility**

The system should go beyond saying:

> "You are missing AWS."

It should provide something like:

```text
Current Role:
Software Developer

Target Role:
Cloud Engineer

Current Match:
58%

Missing Skills:
AWS
Docker
Kubernetes

Recommended Learning Path:
Linux
↓
Networking
↓
AWS
↓
Docker
↓
Kubernetes

Predicted Readiness:
Current: 58%
After learning path: 82%

Mobility Status:
Potential Internal Candidate
```

The exact numerical values must be calculated by the implemented system/model and must NOT be hardcoded.

---

# 4. TECHNOLOGY STACK

Use the following architecture unless the existing project already has a compatible implementation:

## Frontend

* React
* TypeScript
* Tailwind CSS
* Modern responsive UI
* Recharts or equivalent charting library
* React Router

## Backend

* Python
* FastAPI
* Pydantic
* REST APIs

## Database

Use:

* PostgreSQL for structured employee/role/course/application data
* Neo4j for the SkillGraph knowledge graph

If running the complete database infrastructure is impractical during development, provide a clean fallback/local development mode, but structure the application so PostgreSQL and Neo4j can be connected properly.

## Machine Learning

Use:

* pandas
* NumPy
* scikit-learn
* XGBoost where appropriate

## NLP

Use:

* spaCy
* Transformers where useful

NLP should be used for extracting/normalizing skills from resume text.

## Deployment / infrastructure

Use Docker and Docker Compose where practical.

---

# 5. REQUIRED APPLICATION MODULES

Build these modules.

---

## MODULE 1 — LANDING / HOME

Create a professional landing/dashboard entry page.

Include:

* SkillGraph branding
* Short explanation
* Employee Mobility
* Skill Gap Intelligence
* AI Readiness Prediction
* Learning Paths
* Workforce Planning

CTA buttons:

* Employee Portal
* HR Dashboard

Keep the design modern and professional.

---

# 6. MODULE 2 — AUTHENTICATION AND ROLE-BASED ACCESS

Implement basic authentication.

Roles:

```text
EMPLOYEE
HR / ADMIN
```

Employees should only access their own profile, skills, recommendations, learning paths, and simulations.

HR/Admin should access organizational analytics and workforce planning.

Implement RBAC properly.

Use JWT authentication in the backend.

For development/demo purposes, provide clearly documented demo accounts if authentication is implemented without an external identity provider.

---

# 7. MODULE 3 — EMPLOYEE PROFILE

Create an employee profile page.

Display:

* Name
* Current role
* Department
* Experience
* Education
* Certifications
* Projects
* Skills
* Skill proficiency where available
* Resume

Allow resume upload.

The system should extract skills from resume text using NLP.

Pipeline:

```text
Resume
 ↓
Text extraction
 ↓
Skill entity extraction
 ↓
Skill normalization
 ↓
Skill mapping
 ↓
Employee skill profile
```

Do not simply search for exact words.

Normalize related skills where possible.

For example:

```text
React.js
React JS
ReactJS
```

should map to a common canonical skill such as:

```text
React
```

Do the same for obvious technology aliases.

---

# 8. MODULE 4 — SKILL GRAPH

This is the central component.

Represent relationships between:

```text
Employee
Skill
Role
Course
Technology
Task
```

Example:

```text
Employee
   ├── HAS_SKILL → Python
   ├── HAS_SKILL → SQL
   └── HAS_SKILL → React

Role
   ├── REQUIRES → Python
   ├── REQUIRES → AWS
   ├── REQUIRES → Docker
   └── REQUIRES → Kubernetes

Course
   ├── TEACHES → Docker
   └── REQUIRES → Linux
```

Use Neo4j for the graph representation.

Create graph relationships based on the real datasets wherever possible.

Do not create arbitrary relationships simply to make the graph look impressive.

---

# 9. MODULE 5 — ROLE EXPLORER

Create a page where an employee can browse internal target roles.

Display:

* Role name
* Required skills
* Skill coverage
* Match percentage
* Missing skills
* Readiness status

Example:

```text
AI Engineer

Skill Match: 72%

Matched:
✓ Python
✓ Machine Learning
✓ SQL

Missing:
✗ Deep Learning
✗ NLP
✗ MLOps

Status:
Needs Upskilling
```

Allow the employee to select:

**"View Skill Gap"**

---

# 10. MODULE 6 — SKILL GAP ANALYSIS

For a selected employee and target role, calculate:

```text
Current Skills
vs
Required Skills
```

Categorize:

### Strong match

Skills already possessed at sufficient proficiency.

### Partial match

Skill exists but proficiency/experience is insufficient.

### Missing

Skill is not present.

Display:

* Overall skill match
* Skill-by-skill comparison
* Missing skills
* Partial skills
* Strong skills

Use visualizations such as:

* Progress bars
* Radar chart
* Skill matrix
* Bar charts

Do NOT hardcode percentages.

---

# 11. MODULE 7 — ROLE MATCHING ENGINE

Build an actual role recommendation system.

For each employee, rank suitable roles.

Possible scoring components:

```text
Skill similarity
+
Skill coverage
+
Experience compatibility
+
Education compatibility where available
+
Certification compatibility
```

Normalize the final score to 0–100.

Return:

```text
Role
Match Score
Matched Skills
Missing Skills
Readiness
```

Use the actual datasets to derive role/skill relationships.

Avoid making the score completely arbitrary.

Document the scoring methodology.

---

# 12. MODULE 8 — READINESS PREDICTION

Build a machine-learning based readiness prediction component.

Goal:

Predict the probability that an employee can become ready for a target role after completing an upskilling plan.

Potential features:

* Current skill coverage
* Number of missing skills
* Skill similarity
* Experience
* Certifications
* Education
* Number of completed courses
* Course coverage of missing skills
* Prerequisite completion

Possible models:

* Logistic Regression
* Random Forest
* Gradient Boosting
* XGBoost

Compare reasonable models during development and select an appropriate model based on actual validation results.

Do NOT claim unrealistic accuracy.

Display:

```text
Current Readiness
Predicted Readiness
Probability
```

Example:

```text
Current readiness: 61%
Predicted readiness after recommended path: 84%

Probability of becoming role-ready: 0.84
```

These values must come from the implemented methodology.

If the available datasets do not contain a valid target variable for supervised prediction, do NOT fabricate labels.

Instead:

1. Clearly identify the limitation.
2. Build a defensible readiness score/probabilistic framework using available evidence.
3. Keep the architecture ready for future supervised training.

---

# 13. MODULE 9 — LEARNING PATH GENERATOR

Generate a personalized learning path.

This is NOT just a list of random courses.

The path must consider:

```text
Missing Skills
+
Skill Dependencies
+
Course Prerequisites
+
Current Employee Skills
```

Example:

```text
Target Role: Cloud Engineer

Missing:
Kubernetes
Docker
AWS
Networking

Learning Path:

1. Networking Fundamentals
       ↓
2. Linux Fundamentals
       ↓
3. AWS Fundamentals
       ↓
4. Docker
       ↓
5. Kubernetes
```

The system should determine ordering based on prerequisite relationships.

If the datasets do not contain course information/prerequisites, create a clearly separated course catalog/configuration layer rather than pretending the dataset contains those fields.

---

# 14. MODULE 10 — WHAT-IF SIMULATOR

This is an important feature.

Allow employees/HR to select courses or skills and simulate the effect.

Example:

```text
Current readiness:
61%

Select:
✓ AWS
✓ Docker
✓ Kubernetes

Simulated readiness:
79%

Add:
✓ MLOps

Simulated readiness:
86%
```

Show:

* Before
* After
* Improvement
* Skills gained
* Roles unlocked

The simulation should use the same underlying scoring/readiness logic as the main system.

Do not create a separate unrelated formula.

---

# 15. MODULE 11 — EMPLOYEE DASHBOARD

Create a polished employee dashboard.

Display:

### Overview

* Current role
* Skills count
* Recommended roles
* Current readiness
* Learning progress

### Recommended roles

Cards such as:

```text
Cloud Engineer
82% Match

AI Engineer
76% Match

Data Engineer
71% Match
```

### Skill gaps

Show top missing skills.

### Learning path

Show current course progress.

### Career mobility

Display:

```text
Current Role
      ↓
Potential Role
      ↓
Required Skills
      ↓
Learning Path
      ↓
Predicted Readiness
```

---

# 16. MODULE 12 — HR / ADMIN DASHBOARD

Create a separate HR dashboard.

Display organization-level statistics.

Examples:

```text
Total Employees
Open/Future Roles
Average Skill Coverage
Potential Internal Candidates
Critical Skill Gaps
Employees Needing Upskilling
```

Charts:

* Employees by department
* Skills distribution
* Role readiness distribution
* Most common skill gaps
* Potential internal mobility
* Training demand

Do not fabricate statistics.

Use database/dataset-derived data.

---

# 17. MODULE 13 — WORKFORCE PLANNING

This is one of the most important features.

Allow HR to define/select future workforce requirements.

Example:

```text
Future Role:
AI Engineer

Required:
20 employees

Current internal candidates:
14

Immediately ready:
4

Can become ready with training:
10

Gap:
6
```

Show:

* Required headcount
* Current workforce
* Internal candidates
* Ready candidates
* Upskill candidates
* Remaining gap

Provide recommendations:

```text
Candidate A → AI Engineer
Missing: NLP

Candidate B → AI Engineer
Missing: Deep Learning

Candidate C → AI Engineer
Missing: MLOps
```

This connects individual skill-gap analysis to organization-level workforce planning.

---

# 18. MODULE 14 — INTERNAL MOBILITY

Create a page showing possible employee movements.

Example:

```text
Frontend Developer
      ↓
Full Stack Developer
      ↓
Software Architect
```

or:

```text
Data Analyst
      ↓
Data Engineer
      ↓
ML Engineer
```

Display:

* Current role
* Potential target role
* Match score
* Skill gap
* Training required
* Predicted readiness

This should be generated from the actual role/skill graph.

---

# 19. MODULE 15 — DATA EXPLORATION / RESEARCH PAGE

Create an admin/research section showing how SkillGraph uses the datasets.

Datasets:

### Job Skill Set

Use for:

* Job roles
* Required skills
* Role-skill relationships

### Resume Dataset

Use for:

* Resume text
* Resume categories
* Skill extraction
* NLP experiments

### Candidate–Job Role Dataset

Use for:

* Candidate-role relationships
* Experience
* Skills
* Role compatibility

### O*NET

Use for:

* Occupations
* Skills
* Technology skills
* Tasks
* Related occupations

Show dataset statistics dynamically.

Example:

```text
Dataset
Records
Columns
Unique Roles
Unique Skills
Missing Values
```

---

# 20. REQUIRED DATA ANALYSIS NOTEBOOKS

Preserve/create these notebooks:

```text
notebooks/
├── 01_job_skill_set_analysis.ipynb
├── 02_resume_dataset_analysis.ipynb
├── 03_candidate_job_role_analysis.ipynb
└── 04_onet_database_analysis.ipynb
```

They must use the actual files in:

```text
data/raw/
```

Each notebook should:

* Load the real dataset
* Display first rows
* Shape
* Columns
* Info
* Missing values
* Duplicates
* Descriptive statistics
* Important categorical values
* Useful visualizations
* Short conclusions

Do not fabricate results.

---

# 21. DATA PIPELINE

Create a clean data pipeline:

```text
data/raw/
     ↓
data/processed/
     ↓
Normalization
     ↓
Skill extraction
     ↓
Skill canonicalization
     ↓
Role-skill mapping
     ↓
Database
     ↓
Graph
     ↓
ML / Recommendation Engine
     ↓
FastAPI
     ↓
React
```

Keep raw datasets untouched.

Do not overwrite original files.

---

# 22. DATABASE DESIGN

Create appropriate PostgreSQL tables such as:

```text
users
employees
departments
skills
employee_skills
roles
role_skills
courses
course_skills
course_prerequisites
employee_courses
future_workforce_requirements
predictions
```

Adapt the schema where necessary based on the actual datasets.

Use proper primary keys and foreign keys.

---

# 23. NEO4J GRAPH MODEL

Use nodes:

```text
Employee
Skill
Role
Course
Occupation
Technology
Task
```

Possible relationships:

```text
(:Employee)-[:HAS_SKILL]->(:Skill)

(:Role)-[:REQUIRES]->(:Skill)

(:Course)-[:TEACHES]->(:Skill)

(:Course)-[:REQUIRES]->(:Skill)

(:Occupation)-[:HAS_SKILL]->(:Skill)

(:Occupation)-[:USES_TECHNOLOGY]->(:Technology)

(:Occupation)-[:PERFORMS]->(:Task)

(:Role)-[:RELATED_TO]->(:Role)
```

Only create relationships supported by data or clearly defined project rules.

---

# 24. API DESIGN

Create FastAPI endpoints approximately like:

```text
POST /auth/login

GET /employees
GET /employees/{id}
POST /employees/{id}/resume

GET /skills
GET /roles
GET /roles/{id}

GET /employees/{id}/skills
GET /employees/{id}/recommended-roles

GET /employees/{id}/skill-gap/{role_id}

GET /employees/{id}/learning-path/{role_id}

POST /employees/{id}/what-if

GET /employees/{id}/readiness/{role_id}

GET /admin/dashboard
GET /admin/skill-gaps
GET /admin/workforce-planning

GET /datasets
GET /datasets/{dataset_name}
```

Use proper validation and error handling.

---

# 25. FRONTEND ROUTES

Implement routes such as:

```text
/
 /login
 /employee/dashboard
 /employee/profile
 /employee/roles
 /employee/roles/:id
 /employee/skill-gap/:roleId
 /employee/learning-path/:roleId
 /employee/simulator
 /employee/mobility

/admin/dashboard
/admin/employees
/admin/roles
/admin/skills
/admin/workforce-planning
/admin/datasets
```

---

# 26. UI / UX REQUIREMENTS

The application should look like a polished modern SaaS product.

Use:

* Clean dashboard
* Sidebar navigation
* Top navigation
* Cards
* Charts
* Progress indicators
* Skill chips
* Tables
* Search
* Filters
* Responsive layouts
* Empty states
* Loading states
* Error states

Use a professional color palette.

Do not make every screen excessively colorful.

Prioritize readability.

---

# 27. SKILL GRAPH VISUALIZATION

Create a visual graph page.

Allow users to see:

```text
Employee
  |
  +-- Python
  +-- SQL
  +-- React
  |
  +------> Target Role
              |
              +-- AWS
              +-- Docker
              +-- Kubernetes
```

Allow basic:

* Zoom
* Pan
* Node selection
* Relationship highlighting

Do not make this a decorative graph. It must represent actual application data.

---

# 28. SEARCH AND FILTERING

Implement search/filtering for:

Employees:

* Name
* Department
* Role
* Skills

Roles:

* Role name
* Skills
* Readiness

Skills:

* Skill name
* Category

Workforce planning:

* Role
* Department
* Readiness
* Skill gap

Add pagination to large tables.

---

# 29. ML / AI ARCHITECTURE

Separate the intelligence layer from the API.

Suggested structure:

```text
backend/
├── api/
├── models/
├── services/
├── ml/
│   ├── skill_extraction/
│   ├── role_matching/
│   ├── skill_gap/
│   ├── readiness/
│   └── learning_path/
├── graph/
├── database/
└── utils/
```

Do not put all intelligence inside route handlers.

---

# 30. SKILL NORMALIZATION

Create a canonical skill representation.

Examples:

```text
Python
Python Programming
Python 3
```

→

```text
Python
```

and:

```text
JavaScript
Javascript
JS
```

→

```text
JavaScript
```

Maintain a mapping/configuration so this can be expanded.

Do not aggressively merge unrelated technologies.

---

# 31. ROLE NORMALIZATION

Normalize role titles where appropriate.

For example:

```text
Software Engineer
Software Developer
Software Development Engineer
```

may be mapped into a canonical role family when justified.

Do not blindly merge distinct occupations.

Use O*NET as an important reference for occupation normalization.

---

# 32. RECOMMENDATION LOGIC

The recommendation engine should explain itself.

For every recommended role, show:

```text
Why this role?

Matched skills:
Python
SQL
Git

Missing:
AWS
Docker

Experience compatibility:
High

Overall match:
78%
```

Avoid black-box recommendations with no explanation.

---

# 33. PRIVACY AND SECURITY

Because the system deals with employee data:

* Passwords must never be stored in plaintext.
* Use password hashing.
* JWT authentication.
* Role-based access control.
* Employees cannot access another employee's private information.
* Validate uploaded files.
* Restrict resume file types.
* Do not expose sensitive data unnecessarily.
* Do not log passwords or private resume contents.

---

# 34. IMPORTANT: NO FAKE AI

Do not make a UI that says:

> "AI-powered"

while all values are hardcoded.

The following must actually be generated from data/logic:

* Skill extraction
* Role matching
* Skill gap
* Learning path
* Readiness
* What-if simulation
* Workforce recommendations

Where a true ML model cannot be justified by available labels, explicitly use a transparent scoring/recommendation approach instead of inventing training results.

---

# 35. IMPORTANT: NO FAKE DATASET RESULTS

Never write things like:

```text
10,000 employees
92% model accuracy
87% readiness
```

unless those values are actually produced by the data/model.

All statistics must be calculated dynamically.

---

# 36. MODEL EVALUATION

If supervised ML is possible with the actual datasets, include:

* Train/test split
* Cross-validation where appropriate
* Accuracy
* Precision
* Recall
* F1-score
* ROC-AUC where appropriate
* Confusion matrix

For regression:

* MAE
* RMSE
* R²

Choose metrics according to the actual prediction problem.

Do not force a classification problem if the data does not support it.

---

# 37. EXPLAINABILITY

For ML-based recommendations, provide simple explanations.

For example:

```text
Readiness increased because:

+ AWS skill acquired
+ Docker skill acquired
+ Required skill coverage increased
+ Prerequisites completed
```

If using tree-based models, optionally expose feature importance.

---

# 38. ERROR HANDLING

The application must gracefully handle:

* Missing datasets
* Empty employee profile
* Resume without recognizable skills
* Unknown skill
* Unknown role
* Missing O*NET mapping
* Database unavailable
* Neo4j unavailable
* ML model unavailable

Do not crash the frontend.

Show useful error messages.

---

# 39. DEMO MODE

Because this is a college project demonstration, create a clean demo mode.

The demo should allow:

```text
Demo Employee
    ↓
View Profile
    ↓
Select Target Role
    ↓
View Skill Gap
    ↓
Generate Learning Path
    ↓
Run What-if Simulation
    ↓
View Predicted Readiness
```

Also provide:

```text
Demo HR
    ↓
Dashboard
    ↓
Workforce Planning
    ↓
Find Internal Candidates
    ↓
View Skill Gaps
```

Demo mode should still use the actual processed project data wherever possible.

---

# 40. SAMPLE END-TO-END SCENARIO

The complete system should support a flow similar to:

```text
Employee:
Software Developer

Current Skills:
Python
SQL
Git
React

Target:
Data Engineer

Required:
Python
SQL
ETL
Spark
Cloud
Data Warehousing

        ↓

Skill Gap

Missing:
ETL
Spark
Cloud
Data Warehousing

        ↓

Learning Path

Data Warehousing
        ↓
ETL
        ↓
Spark
        ↓
Cloud

        ↓

What-if Simulation

Current readiness: X
After ETL: X
After Spark: X
After Cloud: X

        ↓

Recommendation

Potential internal transition:
Software Developer → Data Engineer
```

The actual numbers must be generated by the system.

---

# 41. PROJECT STRUCTURE

Maintain a clean structure similar to:

```text
SkillGraph/
│
├── frontend/
│   ├── src/
│   ├── components/
│   ├── pages/
│   ├── services/
│   └── ...
│
├── backend/
│   ├── api/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── ml/
│   ├── graph/
│   ├── database/
│   └── main.py
│
├── data/
│   ├── raw/
│   └── processed/
│
├── notebooks/
│   ├── 01_job_skill_set_analysis.ipynb
│   ├── 02_resume_dataset_analysis.ipynb
│   ├── 03_candidate_job_role_analysis.ipynb
│   └── 04_onet_database_analysis.ipynb
│
├── models/
│
├── docker/
│
├── README.md
├── docker-compose.yml
└── .env.example
```

Adapt this to the existing project instead of destroying the existing structure.

---

# 42. README

Create/update the README with:

## Project Title

**SkillGraph — AI-Powered Workforce Skill Gap Analysis and Internal Career Mobility System**

## Problem Statement

Explain the problem of organizations having fragmented employee skill information and difficulty identifying internal candidates for future roles.

## Objectives

Include:

* Skill extraction
* Skill-gap analysis
* Role recommendation
* Readiness prediction
* Personalized learning paths
* What-if simulation
* Internal mobility
* Workforce planning

## Datasets

Document the four dataset groups actually used:

* Job Skill Set
* Resume Dataset
* Candidate–Job Role
* O*NET

Use the actual filenames found in `data/raw/`.

## Architecture

Explain:

```text
Datasets
 ↓
Processing
 ↓
Skill Graph
 ↓
Recommendation / ML
 ↓
FastAPI
 ↓
React
```

## Setup

Explain how to run:

```text
Frontend
Backend
PostgreSQL
Neo4j
Notebooks
```

## Demo flow

Explain the employee and HR flows.

---

# 43. TESTING

Add basic tests for:

* Skill normalization
* Skill-gap calculation
* Role matching
* Learning path generation
* What-if simulation
* API endpoints
* Authentication
* Authorization

Test edge cases.

---

# 44. PERFORMANCE

Do not perform expensive model/database operations on every page render.

Use:

* Caching where useful
* Preprocessing
* Database indexes
* Efficient queries
* Model loading once
* Graph query optimization

---

# 45. IMPORTANT IMPLEMENTATION RULES

DO:

* Use real datasets.
* Inspect datasets before coding.
* Build actual working functionality.
* Keep backend and frontend separated.
* Keep ML logic modular.
* Keep graph logic modular.
* Use transparent recommendation logic.
* Make UI polished.
* Make the project demonstrable.
* Document assumptions.
* Keep raw datasets unchanged.

DO NOT:

* Invent dataset columns.
* Invent employee statistics.
* Invent ML accuracy.
* Hardcode recommendation scores.
* Hardcode fake workforce statistics.
* Pretend a simple rule is an ML model.
* Create unnecessary microservices.
* Add irrelevant features.
* Replace the datasets.
* Destroy the existing project structure.
* Make the project unnecessarily enterprise-scale.

---

# 46. FINAL ACCEPTANCE CRITERIA

The project is considered complete only when the following end-to-end flow works:

### Employee

```text
Login
 ↓
Dashboard
 ↓
Profile / Resume
 ↓
Skill Extraction
 ↓
Skills
 ↓
Recommended Roles
 ↓
Select Role
 ↓
Skill Gap
 ↓
Learning Path
 ↓
What-if Simulation
 ↓
Readiness Prediction
 ↓
Internal Mobility
```

### HR

```text
Login
 ↓
HR Dashboard
 ↓
Employee Workforce View
 ↓
Skill Gap Analytics
 ↓
Future Role Requirement
 ↓
Internal Candidate Identification
 ↓
Upskilling Recommendations
 ↓
Workforce Gap
```

### Research

```text
Raw Datasets
 ↓
EDA Notebooks
 ↓
Processing
 ↓
Skill/Role Knowledge Graph
 ↓
Recommendation Engine
 ↓
ML/Readiness Layer
```

Everything should use the same underlying data and logic.

---

# 47. PRIORITY ORDER

If implementation needs to be completed incrementally, follow this order:

### Priority 1

Dataset inspection and preprocessing

### Priority 2

PostgreSQL schema + data ingestion

### Priority 3

Skill normalization and role-skill mapping

### Priority 4

Skill-gap engine

### Priority 5

Role matching engine

### Priority 6

Employee dashboard

### Priority 7

Learning-path engine

### Priority 8

What-if simulator

### Priority 9

Readiness prediction

### Priority 10

Neo4j SkillGraph

### Priority 11

HR dashboard

### Priority 12

Workforce planning

### Priority 13

Authentication/RBAC hardening

### Priority 14

Testing, documentation and polish

---

# MOST IMPORTANT INSTRUCTION

Do not start by generating random application code.

**FIRST inspect the existing repository and all datasets in `data/raw/`.**

Determine:

1. What files exist?
2. What are their actual columns?
3. What information can actually be extracted?
4. Which datasets can be joined?
5. Which relationships can be represented in Neo4j?
6. Which ML tasks are actually supported by the available data?
7. Which components need a transparent rule-based approach because labeled data does not exist?

Then implement the system around those findings.

The final product should be a **realistic, research-oriented college project** that can be demonstrated to faculty and explained technically, rather than an over-engineered fake enterprise application.
