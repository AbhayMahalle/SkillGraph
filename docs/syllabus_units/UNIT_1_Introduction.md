# UNIT I: Introduction to Data Science & Statistical Inference

**Course:** Data Science (Computer Engineering Syllabus - AY 2026-27, Vishwakarma Institute of Technology)  
**Project:** SkillGraph — AI-Driven Graph Talent Intelligence & Predictive Career Mobility Platform  
**Directory:** `d:\vit\ty-sem1\ds\cp\second`

---

## 1. Syllabus Overview & Learning Objectives

| Topic Heading | Syllabus Scope |
| :--- | :--- |
| **Definition of Data Science** | Multi-disciplinary field combining domain knowledge, statistics, algorithms, and software engineering to extract actionable insights from structured/unstructured data. |
| **Big Data & Data Science Hype vs. Reality** | Getting past promotional buzzwords, black-box AI claims, and subjective claims by applying disciplined, auditable mathematical models. |
| **Datafication** | Transforming everyday qualitative phenomena (human resumes, career aspirations, job descriptions) into quantified, computable data formats. |
| **Current Landscape of Perspectives** | Rule-based heuristics vs. Machine Learning vs. Graph/Knowledge structures vs. Generative LLMs. |
| **Statistical Inference & Populations vs. Samples** | Inferring population-level occupational standards (O*NET 29.0, global job markets) from localized candidate/posting samples. |
| **Statistical Modelling & Probability Distributions** | Fitting mathematical models, prior/posterior distribution estimation, and bounding score probabilities. |
| **Overfitting & Generalization** | Mitigating variance, preventing over-parametrization on small cohorts, cross-validation, and bounded penalty functions. |
| **Python Environment for Data Science** | Tooling ecosystem: virtual environments, package ecosystems (`numpy`, `pandas`, `scipy`, `scikit-learn`, `networkx`, `fastapi`, `pydantic`). |

---

## 2. Realization in SkillGraph

### 2.1 Definition of Data Science & Getting Past the Hype
* **The Hype:** In modern Human Capital Management (HCM) and Applicant Tracking Systems (ATS), "AI" is often promoted as an omniscient black-box LLM prompt that arbitrarily rates resumes on a scale of 1-100 without explainability, reproducibility, or auditability.
* **SkillGraph's Data Science Reality:** SkillGraph replaces qualitative hype with an **auditable, deterministic multi-stage data science pipeline**:
  1. Unstructured text is parsed and mapped to standardized entities via regex boundary tokenization and canonical Levenshtein distance matching ([`backend/ml/skill_extraction.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/ml/skill_extraction.py)).
  2. Candidate profiles and job specifications are converted into dense vector space models with mathematically provable cosine distances ([`backend/ml/role_matching.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/ml/role_matching.py)).
  3. Career progression is sequenced using Directed Acyclic Graph (DAG) topological sorting ([`backend/ml/learning_path.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/ml/learning_path.py)).
  4. Transition probabilities are estimated using an ensemble Random Forest classifier ([`backend/ml/readiness.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/ml/readiness.py)).

### 2.2 Datafication of Human Competencies
Datafication in SkillGraph is the systematic transformation of qualitative career experience into structured numerical objects:
* **Resumes & Bios $\to$ Quantified Skill Vectors:** Free-text descriptions such as *"Developed distributed microservices in Docker and orchestrated them using Kubernetes on AWS for 3 years"* are extracted and converted into:
  ```json
  [
    {"skill_id": "SKL-003", "name": "Docker", "proficiency_weight": 2.0, "verified": true},
    {"skill_id": "SKL-004", "name": "Kubernetes", "proficiency_weight": 2.0, "verified": true},
    {"skill_id": "SKL-005", "name": "AWS", "proficiency_weight": 2.0, "verified": true}
  ]
  ```
* **Job Postings $\to$ Canonical Occupational Standards:** Raw text job descriptions from `data/raw/all_job_post.csv` and O*NET 29.0 database are compiled into 96 standardized roles with mandatory vs. elective skill weights.

### 2.3 Statistical Inference: Populations and Samples
* **Population:** The complete global universe of occupational classifications, salary bounds, and skill requirements represented by:
  - **O*NET 29.0 (US Department of Labor):** 900+ Standard Occupational Classification (SOC) taxonomies.
  - **Kaggle Job Postings (`all_job_post.csv`):** 1,167 industry postings.
* **Sample:** The internal organization cohort:
  - 6 initial seed employee profiles (`data/processed/employees_seed.json`) and 1,000 empirical transition records from `data/raw/candidate_job_role_dataset.csv`.
* **Inference Applied:** We use sample parameters (e.g. employee skill co-occurrences, completion rates, tenure distributions) to infer parameter estimates for the broader organizational skill inventory and predict whether an employee has high likelihood of clearing a transition threshold ($\ge 75\%$).

### 2.4 Statistical Modelling & Probability Distributions
In [`backend/preprocessing/build_processed_data.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/preprocessing/build_processed_data.py#L813-L875), the career transition model generates training data using controlled statistical distributions:
* **Normal Distribution Noise:** Experience deltas and testing noise are simulated with Gaussian perturbations:
  $$\epsilon \sim \mathcal{N}(\mu=0, \sigma=0.1)$$
* **Logistic / Sigmoid Probability Link Function:** Transition readiness probabilities are bounded between $0.05$ and $0.98$ using probability calibration:
  $$P(\text{Transition Success} \mid \vec{X}) = \frac{1}{1 + e^{-z}}$$
  where $z = w_1 \cdot \text{SkillMatch} + w_2 \cdot \text{CoreCoverage} + w_3 \cdot \Delta_{\text{Experience}} + w_4 \cdot \text{Prerequisites} + \epsilon$.
* **Predictive Output:** The Random Forest classifier generates class probability estimates via `predict_proba()` in [`backend/ml/readiness.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/ml/readiness.py#L63-L66), giving employees probabilistic transition odds rather than arbitrary binary decisions.

### 2.5 Preventing Overfitting
Overfitting occurs when a model memorizes idiosyncrasies of small sample profiles rather than true occupational qualifications. SkillGraph guards against overfitting through three architectural safeguards:
1. **Regularization & Bounded Ceilings:** In [`backend/ml/role_matching.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/ml/role_matching.py), experience bonuses are capped with ceiling functions:
   $$\text{Experience Score} = \min(1.0, \frac{\text{Candidate Exp}}{\text{Required Exp}})$$
   This prevents a 25-year veteran from mathematically distorting a junior role match score.
2. **Constrained Tree Depth in Random Forest:** The transition classifier sets `max_depth=6` and `n_estimators=100` (`backend/preprocessing/build_processed_data.py`), bounding model complexity and eliminating leaf-node over-specialization.
3. **Explicit Cross-Validation / Train-Test Split:** A strict 80-20 partition guarantees that evaluation metrics reflect unseen candidate test cases.

### 2.6 Python Data Science Environment
The project relies on a production Python 3.10+ stack configured in [`requirements.txt`](file:///d:/vit/ty-sem1/ds/cp/second/requirements.txt):
* **NumPy (`numpy`):** Vectorized mathematical calculations, matrix norms, dot products.
* **Pandas (`pandas`):** Tabular manipulation of CSVs, aggregation, category handling, indexing.
* **SciPy & Scikit-Learn (`scikit-learn`):** Data scaling (`StandardScaler`), Random Forest model training, accuracy evaluation metrics.
* **NetworkX (`networkx`):** Graph network modeling, DAG prerequisite validation, topological sorting.
* **FastAPI + Uvicorn:** Exposing machine learning inference over low-latency REST endpoints.

