

# SkillGraph — Master Project Handoff Prompt

You are continuing an existing project called:

**SkillGraph — AI-Powered Workforce Skill Gap Analysis and Internal Career Mobility System**

Please read and understand the entire context below before responding to anything about this project.

Do not change the project's core idea or selected datasets unless I explicitly ask you to.

---

# 1. Project Overview

SkillGraph is an AI-powered system for **workforce skill-gap analysis and internal career mobility**.

The main idea is:

> Companies already have employees who may be capable of moving into new roles, but their skills, role requirements, career paths, and learning opportunities are often disconnected.

SkillGraph aims to connect these components and help an organization answer:

- What skills does an employee currently have?
- What skills are required for another role?
- What is the employee's skill gap?
- Which internal roles are suitable for the employee?
- What should the employee learn?
- In what order should they learn it?
- How likely are they to become ready for the target role?
- What happens to their readiness if they complete certain courses?
- Which existing employees could potentially fill future organizational roles?

The core conceptual flow is:

```text
Employee Data
      ↓
Skill Extraction
      ↓
Employee Skill Profile
      ↓
Skill Graph
      ↓
Skill Gap Analysis
      ↓
Role Matching
      ↓
Learning Path
      ↓
Future Readiness Prediction
      ↓
What-if Simulation
      ↓
Internal Career Mobility
      ↓
Workforce Planning
```

---

# 2. Core Graph Concept

The main knowledge representation will eventually be:

```text
Employee
    ↓
Skills
    ↓
Roles
    ↓
Courses
    ↓
Prerequisites
```

More specifically:

```text
Employee ──HAS_SKILL──> Skill
Role ──REQUIRES_SKILL──> Skill
Course ──TEACHES──> Skill
Course ──REQUIRES──> Course
Employee ──CURRENT_ROLE──> Role
Employee ──TARGET_ROLE──> Role
Role ──RELATED_TO──> Role
```

The important point is that SkillGraph is **not simply a resume-to-job matching system**.

Its main focus is **internal employee mobility**.

---

# 3. Main Differentiator

The strongest differentiator of SkillGraph is the combination of:

```text
Internal Employee Mobility
+
Skill Gap Analysis
+
Role Matching
+
Prerequisite-Aware Learning Paths
+
Future Readiness Prediction
+
What-if Simulation
+
Workforce Planning
```

The intended system should eventually move beyond:

> "You are missing these skills."

and provide something closer to:

> "You currently have a 58% match with the Cloud Engineer role. Completing Linux → Networking → AWS → Docker → Kubernetes can improve your skill profile, and the system predicts your future readiness for the role."

At the HR level:

> "The organization will need more Cloud Engineers in the future. SkillGraph identifies existing employees who are closest to becoming Cloud Engineers and recommends what they need to learn."

---

# 4. Selected Datasets

These are the **final 4 datasets** selected for the project.

Do not replace them unless explicitly asked.

---

## Dataset 1 — Job Skill Set

**Link:**

https://www.kaggle.com/datasets/batuhanmutlu/job-skill-set

### Purpose

Primarily provides:

```text
Job Role → Required Skills
```

It will be useful for:

- Job-role analysis
- Required-skill analysis
- Role/skill relationships
- Building the future role-skill knowledge layer

Example conceptual relationship:

```text
Cloud Engineer
    ├── Linux
    ├── Networking
    ├── AWS
    ├── Docker
    └── Kubernetes
```

---

## Dataset 2 — Resume Dataset

**Link:**

https://www.kaggle.com/datasets/trendcart/resume-dataset

### Purpose

Primarily provides:

```text
Resume → Candidate Profile / Skills
```

It will eventually support:

- Resume analysis
- Skill extraction
- Candidate profiling
- Understanding resume categories
- Connecting candidate information to roles

The future pipeline could be:

```text
Resume
   ↓
NLP Skill Extraction
   ↓
Skill Profile
```

For the current phase, only basic EDA is required.

---

## Dataset 3 — Candidate Job Role Dataset

**Link:**

https://www.kaggle.com/datasets/ckshetty/candidate-job-role-dataset

### Purpose

Primarily provides:

```text
Candidate → Skills / Experience → Job Role
```

It will eventually support:

- Candidate-role matching
- Role classification
- Skill-gap analysis
- Understanding relationships between experience, skills and roles

Example:

```text
Candidate
   ↓
Skills + Experience
   ↓
Suitable Role
```

Important: treat the dataset according to its actual contents after inspection. Do not invent columns or statistics.

---

## Dataset 4 — O*NET Database v29.0

**Link:**

https://www.kaggle.com/datasets/emarkhauser/onet-29-0-database

### Purpose

This dataset is the main occupational knowledge source.

It can provide relationships such as:

```text
Occupation
   ├── Skills
   ├── Technology Skills
   ├── Tasks
   └── Related Occupations
```

It is particularly useful for the future SkillGraph knowledge layer.

It replaced the previously considered DOL Trajectories dataset because O*NET is more directly useful for constructing the occupation/skill side of the graph and is available through Kaggle.

Do not assume the exact files/columns. Inspect the downloaded dataset first.

---

# 5. Why These Four Datasets

The four datasets together provide the initial foundation:

```text
Job Skill Set
      ↓
Role → Required Skills

Resume Dataset
      ↓
Resume → Candidate Skills/Profile

Candidate Job Role
      ↓
Candidate → Suitable Role

O*NET
      ↓
Occupation → Skills → Technology → Tasks → Related Roles
```

Together they support the initial data foundation for:

- Skill analysis
- Role analysis
- Candidate profiling
- Role matching
- Skill-gap analysis
- Occupational knowledge representation

---

# 6. Important Dataset Limitation

This is very important.

The four datasets **do NOT directly provide a complete dataset containing**:

```text
Employee
→ Course Completed
→ Skills Improved
→ Target Role
→ Successful Internal Transition
```

Therefore, do not claim that the four datasets alone can directly train a complete future-readiness model.

Later phases may require:

- Course dataset
- Course → Skill relationships
- Skill prerequisites
- Course prerequisites
- Skill improvement information
- Employee training history
- Historical internal role transitions
- Organizational employee data
- Controlled synthetic data where necessary

For now, these are **future requirements**, not part of the current Phase 1 implementation.

---

# 7. Current Project Status

The project itself has already been initialized.

The current remaining work is the **dataset-specific EDA notebooks**.

We decided NOT to create one large EDA notebook.

Instead, create one notebook per dataset.

Required notebooks:

```text
notebooks/
├── 01_job_skill_set_analysis.ipynb
├── 02_resume_dataset_analysis.ipynb
├── 03_candidate_job_role_analysis.ipynb
└── 04_onet_database_analysis.ipynb
```

---

# 8. Current Phase — Phase 1

Current phase:

**Data Collection + Basic EDA**

The goal is simply to understand the four datasets before starting the actual SkillGraph implementation.

Each notebook should perform basic analysis:

- Load dataset
- `head()`
- `shape`
- `columns`
- `info()`
- Missing values
- Duplicate rows
- Basic statistics
- Important categorical columns
- Unique values
- A few useful visualizations
- Short conclusion

Keep everything simple.

---

# 9. Notebook 1

File:

```text
notebooks/01_job_skill_set_analysis.ipynb
```

Dataset:

https://www.kaggle.com/datasets/batuhanmutlu/job-skill-set

Focus on:

- Job roles
- Required skills
- Number of unique roles
- Common roles
- Common skills
- Basic role/skill distributions

Useful visualizations may include:

- Top job roles
- Top skills
- Skills per role

Do not build ML models.

Do not build the graph yet.

---

# 10. Notebook 2

File:

```text
notebooks/02_resume_dataset_analysis.ipynb
```

Dataset:

https://www.kaggle.com/datasets/trendcart/resume-dataset

Focus on:

- Resume categories
- Resume text columns
- Number of resumes per category
- Basic text length/word count if applicable
- Missing values
- Duplicate rows

Do NOT build an NLP pipeline yet.

No BERT.

No Transformers.

No advanced skill extraction.

Only basic analysis.

---

# 11. Notebook 3

File:

```text
notebooks/03_candidate_job_role_analysis.ipynb
```

Dataset:

https://www.kaggle.com/datasets/ckshetty/candidate-job-role-dataset

Focus on:

- Candidate information
- Skills
- Experience
- Job roles
- Role distribution
- Basic relationship between experience and roles

Possible visualizations:

- Top job roles
- Experience distribution
- Experience vs role
- Common skills

Do not train a classification model yet.

---

# 12. Notebook 4

File:

```text
notebooks/04_onet_database_analysis.ipynb
```

Dataset:

https://www.kaggle.com/datasets/emarkhauser/onet-29-0-database

O*NET contains multiple files.

First inspect the files available.

Then focus only on useful files related to:

- Occupations
- Skills
- Technology skills
- Tasks
- Related occupations

Do not try to analyze every O*NET file.

Useful analysis:

- Number of occupations
- Common skills
- Common technologies
- Skills per occupation
- Related occupations where appropriate

Do not create the actual Neo4j graph yet.

---

# 13. Style of the Notebooks

The notebooks should look like **normal student/research EDA notebooks**.

Do NOT make them look overly polished or AI-generated.

Keep:

- Simple markdown
- Simple headings
- Minimal comments
- Normal Python code
- Clear outputs
- Few useful graphs
- Short conclusions

Avoid:

- Huge explanations
- Excessive markdown
- Fancy architecture diagrams
- Unnecessary abstractions
- Dozens of visualizations
- Complex helper classes/functions
- Over-engineering

---

# 14. Important Restrictions for Phase 1

Do NOT implement any of these yet:

```text
✗ Machine Learning models
✗ Future-readiness prediction
✗ NLP pipeline
✗ Skill extraction model
✗ Recommendation engine
✗ Learning-path algorithm
✗ Neo4j
✗ PostgreSQL
✗ Backend
✗ FastAPI
✗ Frontend
✗ React
✗ Authentication
✗ APIs
✗ Docker
✗ Deployment
✗ Workforce dashboard
```

Only perform dataset analysis.

---

# 15. Raw Data

Raw datasets should remain unchanged.

Expected structure:

```text
data/
└── raw/
    ├── job_skill_set/
    ├── resume_dataset/
    ├── candidate_job_role/
    └── onet/
```

Do not overwrite the original datasets.

Use relative paths from the notebooks.

Do not use machine-specific absolute paths.

---

# 16. Current Project Philosophy

Keep the project simple and build it phase by phase.

Do not try to build the entire SkillGraph system immediately.

Current priority:

```text
Datasets
   ↓
EDA
   ↓
Understand Data
   ↓
Clean/Normalize
   ↓
Build Skill/Role Knowledge
   ↓
Skill Graph
   ↓
Matching
   ↓
Learning Path
   ↓
Prediction
```

Only move to the next phase when explicitly asked.

---

# 17. Future Technical Direction

The previously discussed future stack is:

### Frontend
React.js + Tailwind CSS

### Backend
Python + FastAPI

### Database
PostgreSQL

### Graph Database
Neo4j

### ML
scikit-learn / XGBoost

### NLP
spaCy / HuggingFace Transformers

### Authentication
JWT + role-based access

### Deployment
Docker

These are **future implementation decisions**, not part of the current EDA phase.

Do not introduce them unnecessarily right now.

---

# 18. Future System Architecture

The conceptual future flow is:

```text
                    ┌──────────────────┐
                    │ Employee / HR    │
                    │ Data             │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ Skill Extraction │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ Employee Skill   │
                    │ Profile          │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │   SkillGraph     │
                    │   Knowledge      │
                    │     Graph        │
                    └────────┬─────────┘
                             ↓
                  ┌──────────┴──────────┐
                  ↓                     ↓
          Skill Gap Analysis       Role Matching
                  ↓                     ↓
                  └──────────┬──────────┘
                             ↓
                    Learning Path
                             ↓
                  Future Readiness
                    Prediction
                             ↓
                    What-if Simulation
                             ↓
                  Internal Mobility
                             ↓
                  Workforce Planning
```

This is the **future architecture**, not something to implement during the current EDA phase.

---

# 19. Research Positioning

The research gap identified for SkillGraph is broadly:

Existing systems often focus on:

- Resume-to-external-job matching
- Static skill-gap analysis
- Career recommendation
- Occupational knowledge graphs

SkillGraph aims to combine:

```text
Internal Employee Mobility
+
Skill Gap Analysis
+
Prerequisite-Aware Learning
+
Future Readiness Prediction
+
What-if Simulation
+
Organization-Level Workforce Planning
```

The important research positioning is:

> Instead of only matching a candidate to a job, SkillGraph aims to determine how an existing employee can become ready for another internal role and how that individual-level development can contribute to future workforce planning.

Do not claim that SkillGraph has already solved all of these components. They are the broader project vision.

---

# 20. How to Continue the Project

When I ask you to continue SkillGraph, first consider the **current phase and existing implementation**.

Do not restart the project.

Do not replace the selected datasets.

Do not create unnecessary files.

Do not introduce new technologies unless they are actually required.

If I ask for code, make it compatible with the existing SkillGraph structure.

If I ask for a new phase, implement only that phase.

If I ask for EDA, use the existing four datasets.

If I ask for dataset-related work, use these exact sources:

1. Job Skill Set  
https://www.kaggle.com/datasets/batuhanmutlu/job-skill-set

2. Resume Dataset  
https://www.kaggle.com/datasets/trendcart/resume-dataset

3. Candidate Job Role Dataset  
https://www.kaggle.com/datasets/ckshetty/candidate-job-role-dataset

4. O*NET Database v29.0  
https://www.kaggle.com/datasets/emarkhauser/onet-29-0-database

---

# 21. Most Important Instruction

Treat this as an **existing project being continued**, not a new project.

The project name is:

**SkillGraph**

Full name:

**SkillGraph — AI-Powered Workforce Skill Gap Analysis and Internal Career Mobility System**

Current phase:

**Basic EDA of the 4 selected datasets**

Current immediate task:

**Create and complete the four dataset-specific EDA notebooks.**

Keep the implementation simple, natural, and student/research-project appropriate.

Do not over-engineer the project.
