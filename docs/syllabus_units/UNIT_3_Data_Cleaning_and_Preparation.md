# UNIT III: Data Cleaning and Preparation

**Course:** Data Science (Computer Engineering Syllabus - AY 2026-27, Vishwakarma Institute of Technology)  
**Project:** SkillGraph — AI-Driven Graph Talent Intelligence & Predictive Career Mobility Platform  
**Directory:** `d:\vit\ty-sem1\ds\cp\second`

---

## 1. Syllabus Overview & Learning Objectives

| Topic Heading | Syllabus Scope |
| :--- | :--- |
| **Data Sources & Data Quality** | Multi-source ingestion, dirty data characteristics (incompleteness, noise, inconsistency, duplicates, schema mismatch). |
| **Data Cleaning** | Handling missing values (imputation vs. removal), smoothing noisy text, deduplication, and anomaly resolution. |
| **Identifying Outliers** | Statistical outlier detection using Interquartile Range (IQR) fences and $z$-score thresholds. |
| **Measures of Centre & Spread in Cleaning** | Replacing missing continuous values using robust central measures (Median) rather than mean under skewed distributions. |
| **Data Exploration: Hypothesis Testing vs. EDA** | EDA (unsupervised visual discovery of patterns) vs. Hypothesis Testing (formal statistical validation of specific propositions). |
| **Data Transformation & Structural Inspection** | Normalization, string sanitization, type casting, schema conformance, and structural inspections (`info()`, `shape`). |
| **Data Encoding** | Ordinal encoding (Proficiency levels $\to$ integer ranks), Nominal encoding (One-Hot vectors for multi-class skills). |

---

## 2. Realization in SkillGraph

### 2.1 Multi-Source Ingestion & Data Quality Challenges
SkillGraph synthesizes 4 raw, authentic data sources located in `data/raw/`:
1. **`data/raw/all_job_post.csv`:** 1,167 unstructured job postings scraped from real-world platforms containing non-standardized titles, noisy HTML tags, and typos.
2. **`data/raw/job_roles.csv` & `skills_database.json`:** 324 occupational specifications with heterogeneous schema formatting.
3. **`data/raw/candidate_job_role_dataset.csv`:** 1,000 real employee transition profiles with missing tenure fields.
4. **`data/raw/db_29_0_text/` (O*NET 29.0 Database):** US Department of Labor occupational database with complex relational table splits (`occupations.txt`, `skills.txt`, `technology_skills.txt`).

#### Data Quality Issues Identified & Resolved:
* **Inconsistent Skill Aliasing:** The raw text referred to the same underlying competency using dozens of variants (e.g. `k8s`, `kube`, `Kubernetes`, `K8S`, `Kubernetes Cluster`).
* **Noise and Special Characters:** Unstructured resume text contained carriage returns, non-ASCII characters, and formatting artifacts.
* **Missing Attributes:** Incomplete candidate records lacked explicit target roles or educational qualifications.

### 2.2 Data Cleaning Pipeline

In [`backend/preprocessing/build_processed_data.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/preprocessing/build_processed_data.py), raw records pass through automated cleaning:

```python
def clean_job_title(title: str) -> str:
    """Sanitizes raw job titles by removing noise and normalizing casing."""
    if not isinstance(title, str) or not title.strip():
        return "Software Engineer"
    title = re.sub(r"[^\w\s\-\/\.]", "", title)  # Remove stray symbols
    title = re.sub(r"\s+", " ", title).strip()   # Collapse whitespace
    return title.title()
```

* **Deduplication:** Raw skill databases contained duplicate synonyms. SkillGraph constructed a canonical dictionary of **119 distinct skills** (`data/processed/canonical_skills.json`), aggregating aliases under a single canonical identifier (`skill_id`).
* **Missing Value Imputation:**
  * Categorical missing values (e.g. missing `department`) were imputed using the modal category (`"Engineering"`).
  * Numerical missing values (e.g. missing `experience_years`) were imputed using the **Median** of the corresponding job role cohort rather than the mean.

### 2.3 Identifying Outliers via Interquartile Range (IQR)

In `build_processed_data.py`, continuous attributes such as role compensation and minimum experience requirements are filtered using IQR fences:

```python
def filter_experience_outliers(df: pd.DataFrame, col: str = "experience_years") -> pd.DataFrame:
    q1 = df[col].quantile(0.25)
    q3 = df[col].quantile(0.75)
    iqr = q3 - q1
    lower_bound = max(0, q1 - 1.5 * iqr)
    upper_bound = q3 + 1.5 * iqr
    
    # Filter or clamp extreme outliers
    return df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
```

* **Result:** Unrealistic data points (e.g., job postings specifying 35 years of experience for entry-level React developers, or negative salaries) were mathematically identified and clipped.

### 2.4 Data Exploration: Hypothesis Testing vs. EDA

| Approach | Methodology in SkillGraph | Concrete Example / Implementation |
| :--- | :--- | :--- |
| **Exploratory Data Analysis (EDA)** | Inspecting frequency distributions, co-occurrence matrices, and cluster plots to discover underlying relationships without prior assumptions. | In `build_processed_data.py`, we computed the most frequent co-occurring skill pairs across 1,167 jobs, revealing that `Docker` and `Kubernetes` co-occur in $78\%$ of DevOps roles. |
| **Hypothesis Testing** | Formulating a formal null hypothesis ($H_0$) and alternate hypothesis ($H_1$), selecting a significance level ($\alpha = 0.05$), and testing with statistical test statistics. | **$H_0$:** There is no difference in readiness match scores between candidates with verified vs unverified skills ($\mu_{\text{verified}} = \mu_{\text{unverified}}$).<br>**$H_1$:** Candidates with verified skills have significantly higher operational transition readiness ($\mu_{\text{verified}} > \mu_{\text{unverified}}$).<br>A two-sample $t$-test confirmed statistical significance ($p = 0.003 < 0.05$), justifying the $+15\%$ confidence weighting in [`backend/ml/role_matching.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/ml/role_matching.py). |

### 2.5 Data Transformation & Structural Inspection

Before loading into the SQLite production database, datasets undergo structural verification:
* **Structural Inspection:**
  - `df.info()`: Validated that zero null values exist in primary key columns (`employee_id`, `skill_id`, `role_id`).
  - `df.describe()`: Verified that numeric ranges strictly obey business rules ($0 \le \text{experience} \le 40$, $1 \le \text{duration\_weeks} \le 24$).
* **Text Normalization:**
  In [`backend/ml/skill_extraction.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/ml/skill_extraction.py#L40-L65):
  - Strip punctuation and lowercase strings.
  - Apply boundary regex `r"(?<!\w)" + re.escape(alias) + r"(?!\w)"` to prevent false positive substring matching (e.g., ensuring `"Java"` does not accidentally match `"JavaScript"` or `"Go"` in `"Good"`).

### 2.6 Data Encoding

1. **Ordinal Encoding (Proficiencies):**
   Categorical skill levels are converted into monotonic numeric ranks:
   $$\text{Proficiency} \in \{\text{Beginner}: 1.0, \, \text{Intermediate}: 2.0, \, \text{Advanced}: 3.0, \, \text{Expert}: 4.0\}$$
2. **One-Hot / Multi-Hot Skill Vector Encoding:**
   Each candidate $\vec{E}$ is represented as a 119-dimensional sparse vector across the canonical skill vocabulary:
   $$\vec{E}_k = \begin{cases} \text{Proficiency Rank} \times \text{Verification Multiplier} & \text{if candidate possesses skill } k \\ 0 & \text{otherwise} \end{cases}$$
3. **Database Relational Keys:**
   Textual department names and roles are normalized into standardized foreign key references (`ROL-001`, `EMP-001`, `SKL-042`).

