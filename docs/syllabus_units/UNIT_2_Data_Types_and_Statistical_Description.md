# UNIT II: Data Types & Statistical Description

**Course:** Data Science (Computer Engineering Syllabus - AY 2026-27, Vishwakarma Institute of Technology)  
**Project:** SkillGraph — AI-Driven Graph Talent Intelligence & Predictive Career Mobility Platform  
**Directory:** `d:\vit\ty-sem1\ds\cp\second`

---

## 1. Syllabus Overview & Learning Objectives

| Topic Heading | Syllabus Scope |
| :--- | :--- |
| **Attributes and Measurement** | Formal definition of an attribute, scale of measurement, domain of values, and observation entities. |
| **Types of Attributes** | Categorization of attributes: Nominal, Binary (Symmetric vs. Asymmetric), Ordinal, and Numeric (Interval vs. Ratio). |
| **Number of Values** | Discrete attributes (finite or countable values) versus Continuous attributes (infinite real-valued scale). |
| **Asymmetric Binary Attributes** | Situations where the presence of an attribute is significantly more informative than its absence (e.g. specialized skills, rare certifications). |
| **Measures of Central Tendency** | Mean (Arithmetic average), Median (50th percentile robust to skew), Mode (most frequent category/value). |
| **Measures of Dispersion** | Range ($\text{Max} - \text{Min}$), Quartiles ($Q_1, Q_2, Q_3$), Variance ($\sigma^2$), Standard Deviation ($\sigma$), and Interquartile Range ($\text{IQR} = Q_3 - Q_1$). |
| **Graphic Displays of Statistical Data** | Box plots, histograms, quantile-quantile plots, scatter plots, and empirical distributions. |

---

## 2. Realization in SkillGraph

### 2.1 Formal Attribute Taxonomy in SkillGraph

SkillGraph stores and processes multifaceted workforce data across relational tables in SQLite (`data/processed/skillgraph.db`) and in-memory data structures. Every attribute adheres to strict data science measurement criteria:

| Attribute Name | Entity / Table | Measurement Type | Value Domain | Concrete Implementation & Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **`category`** | `skills`, `roles` | **Nominal** (Categorical) | `{'Technology', 'Data & AI', 'Cloud & Platform', 'Security', ...}` | Non-ordered labeling used for grouping competencies and department filtering. |
| **`department`** | `employees`, `roles` | **Nominal** | `{'Engineering', 'Platform Engineering', 'Data Science', ...}` | Department categorization for cohort analysis. |
| **`verified`** | `employee_skills` | **Asymmetric Binary** | `{True, False}` (or `{1, 0}`) | **1 = Verified by peer/exam, 0 = Self-reported.** Presence of verification carries high informational weight in calculating talent match confidence. |
| **`is_active`** | `roles` | **Symmetric Binary** | `{True, False}` | Both active and inactive states carry equal diagnostic balance for requisition planning. |
| **`proficiency`** | `employee_skills` | **Ordinal** | `{'Beginner', 'Intermediate', 'Advanced', 'Expert'}` | Quantized ordered scale mapped mathematically to rank scores: $\text{Beginner}=1.0$, $\text{Intermediate}=2.0$, $\text{Advanced}=3.0$, $\text{Expert}=4.0$. |
| **`level`** | `courses` | **Ordinal** | `{'Beginner', 'Intermediate', 'Advanced'}` | Defines structural curriculum tiers for DAG prerequisite sequencing. |
| **`experience_years`** | `employees`, `roles` | **Numeric (Discrete)** | $\mathbb{Z}_{\ge 0} \in [0, 40]$ | Integer count of years of professional employment. |
| **`duration_weeks`** | `courses` | **Numeric (Discrete)** | $\mathbb{Z}^+ \in [1, 24]$ | Estimated full-time learning duration. |
| **`match_score`** | Role Matching Engine | **Numeric (Continuous Ratio)** | $\mathbb{R} \in [0.0, 100.0]$ | Ratio-scale score derived from weighted cosine vector calculations. |
| **`salary_min` / `salary_max`** | Job Postings / Roles | **Numeric (Continuous Ratio)** | $\mathbb{R}^+ \in [\$40,000, \$350,000]$ | Compensation ranges used in dispersion calculations. |

### 2.2 Deep Dive: Asymmetric Binary Attributes in Talent Graphs
In classical statistics, a binary attribute is **asymmetric** if the outcomes are not equally important.
* **Why it matters in SkillGraph:** In a database of 119 canonical skills, an employee might possess only 6 to 12 skills. If we treat skill presence and absence symmetrically, two employees who both lack 110 skills would have high similarity!
* **Implementation:**
  * When comparing an employee vector $\vec{E}$ to a role requirement $\vec{R}$, SkillGraph evaluates **positive matches only**:
    $$\text{Match Contribution} = \sum_{k \in S_{\text{Employee}} \cap S_{\text{Role}}} w_k \cdot p_k$$
  * Absences ($\vec{E}_k = 0 \text{ and } \vec{R}_k = 0$) do not contribute spurious similarity.
  * In [`backend/ml/role_matching.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/ml/role_matching.py#L90-L105), the `verified` attribute is asymmetric:
    $$w_{\text{effective}} = w_{\text{base}} \times (1.0 \text{ if verified else } 0.85)$$
    A verified skill boosts the match score by $15\%$, reflecting rigorous provenance.

### 2.3 Measures of Central Tendency

In [`backend/preprocessing/build_processed_data.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/preprocessing/build_processed_data.py) and [`backend/api/routes.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/api/routes.py), summary statistics describe occupational baselines:

```python
# Statistical Central Tendency computations over Kaggle/O*NET raw data
mean_exp = df["experience_years"].mean()       # Arithmetic average
median_exp = df["experience_years"].median()   # Middle value, resistant to extreme outliers
mode_dept = df["department"].mode()[0]         # Most common enterprise division
```

* **Mean vs. Median in Salary & Tenure:**
  * Executive and specialized staff (e.g. Principal Architects with 25+ years experience or \$300k+ salaries) introduce heavy right-skew into compensation data.
  * Therefore, SkillGraph uses **Median** for default role progression thresholds to avoid upward bias from extreme outliers.

### 2.4 Measures of Dispersion

To characterize variability across role requirements, SkillGraph calculates the five-number summary and dispersion metrics:

$$\text{Range} = X_{\max} - X_{\min}$$
$$\text{Sample Variance } s^2 = \frac{1}{n-1} \sum_{i=1}^n (X_i - \bar{X})^2$$
$$\text{Standard Deviation } s = \sqrt{s^2}$$
$$\text{Interquartile Range (IQR)} = Q_3 - Q_1$$

Where:
* $Q_1$ is the 25th percentile ($25\%$ of candidates have less tenure).
* $Q_2$ is the 50th percentile (Median).
* $Q_3$ is the 75th percentile ($75\%$ of candidates have less tenure).
* **Application in Outlier Thresholding:**
  In data ingestion, records outside the fence:
  $$[Q_1 - 1.5 \times \text{IQR}, \quad Q_3 + 1.5 \times \text{IQR}]$$
  are flagged for manual review or clamped (e.g. negative experience values or typos like 120 years).

### 2.5 Graphic Displays of Statistical Descriptions in the UI

SkillGraph translates statistical distributions into interactive, visual UI components:
1. **Multi-Axis Competency Radar Chart (`frontend/src/components/SkillGapView.tsx`):**
   * Displays the multivariate dispersion of candidate proficiency across 6 key competency axes (Architecture, Cloud, Coding, DevOps, Data, Security).
2. **2D Force-Directed Graph Canvas (`frontend/src/components/SkillGraphVisualizer.tsx`):**
   * Visualizes vertex degree distribution and clustering coefficients among connected skills and target roles.
3. **Distribution Histograms & Progress Gauges (`frontend/src/components/EmployeeDashboard.tsx`):**
   * Renders the candidate's percentile standing relative to organization-wide readiness benchmarks.

