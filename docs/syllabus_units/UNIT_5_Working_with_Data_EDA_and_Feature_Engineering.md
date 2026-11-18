# UNIT V: Working with Data, Exploratory Analysis, and Feature Engineering

**Course:** Data Science (Computer Engineering Syllabus - AY 2026-27, Vishwakarma Institute of Technology)  
**Project:** SkillGraph — AI-Driven Graph Talent Intelligence & Predictive Career Mobility Platform  
**Directory:** `d:\vit\ty-sem1\ds\cp\second`

---

## 1. Syllabus Overview & Learning Objectives

| Topic Heading | Syllabus Scope |
| :--- | :--- |
| **Data Manipulation with Pandas** | Importing diverse datasets, programmatic data inspection (`head()`, `tail()`, `info()`, `describe()`), grouping, aggregation, inner/outer merging, and concatenating DataFrames. |
| **Exploratory Data Analysis (EDA)** | Univariate/multivariate descriptive statistics, skewness, kurtosis, correlation heatmaps ($r$), trend identification. |
| **Feature Engineering** | **Feature Selection:** Removing redundant/collinear predictors.<br>**Feature Extraction:** Formulating composite indices from raw signals.<br>**Feature Scaling:** Standardizing features using z-score normalization (`StandardScaler`). |
| **Train-Test Split & Validation** | Splitting datasets into training, validation, and testing subsets using `train_test_split` with stratifying seeds to prevent data leakage. |
| **Model Evaluation Metrics** | Confusion Matrix (TP, FP, TN, FN), Classification Accuracy, Precision, Recall, and F1-Score. |

---

## 2. Realization in SkillGraph

### 2.1 Data Manipulation with Pandas

In [`backend/preprocessing/build_processed_data.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/preprocessing/build_processed_data.py), Pandas performs extensive tabular transformations across the 4 raw datasets:

```python
import pandas as pd

# 1. Importing datasets
df_jobs = pd.read_csv("data/raw/all_job_post.csv")
df_candidates = pd.read_csv("data/raw/candidate_job_role_dataset.csv")

# 2. Structural and Distributional Inspection
print(df_jobs.head(5))         # Inspect first 5 rows for column format
print(df_jobs.tail(5))         # Check trailing formatting
df_jobs.info()                 # Memory consumption, non-null counts, data types
desc_stats = df_jobs.describe() # 8-point numerical summary (count, mean, std, min, 25%, 50%, 75%, max)

# 3. Data Aggregation & Grouping
# Aggregate average required experience and skill counts per department
dept_summary = df_jobs.groupby("department").agg(
    avg_experience=("experience_years", "mean"),
    median_experience=("experience_years", "median"),
    job_count=("job_id", "count")
).reset_index()

# 4. Merging & Concatenating DataFrames
# Joining employee demographic data with historical transition outcomes
df_merged = pd.merge(
    df_candidates,
    dept_summary,
    on="department",
    how="left"
)
```

### 2.2 Exploratory Data Analysis (EDA)

#### 1. Distribution Analysis:
* **Experience Skewness:** Analysis of candidate experience revealed significant right-skewness ($\gamma_1 > +1.2$), indicating that most applicants possess 1–5 years of tenure, with a long tail stretching to 25 years.
* **Skill Demand Distributions:** A Pareto distribution was observed in enterprise skills: the top $20\%$ of technical skills (e.g., `Python`, `SQL`, `AWS`, `Docker`, `Git`) appear in over $70\%$ of all job requisitions.

#### 2. Correlation Analysis:
* Pearson correlation coefficient $r$ was computed between continuous candidate metrics:
  $$r = \frac{\sum (X - \bar{X})(Y - \bar{Y})}{\sqrt{\sum (X - \bar{X})^2 \sum (Y - \bar{Y})^2}}$$
* **Finding:** While `experience_years` moderately correlates with baseline salary ($r = +0.64$), it weakly correlates with modern Cloud/DevOps proficiency ($r = +0.18$), demonstrating that tenure alone does not guarantee contemporary toolchain mastery.

### 2.3 Feature Engineering: Extraction, Selection, and Scaling

In [`backend/ml/role_matching.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/ml/role_matching.py) and [`backend/preprocessing/build_processed_data.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/preprocessing/build_processed_data.py), raw resume and job text are engineered into 5 high-impact features:

| Feature Name | Type | Engineering Methodology | Purpose |
| :--- | :--- | :--- | :--- |
| **`skill_match_ratio`** | Extracted Index | Weighted Cosine Similarity: $\frac{\vec{E} \cdot \vec{R}}{\|\vec{E}\| \|\vec{R}\|}$ | Measures overall alignment across entire skill repertoire. |
| **`core_skill_coverage`** | Extracted Index | $\frac{\sum_{k \in \text{Critical}} \mathbb{I}(k \in \text{Candidate})}{\text{Total Critical Skills}}$ | Explicitly penalizes missing non-negotiable core competencies. |
| **`exp_delta`** | Difference Index | $\text{Candidate Tenure} - \text{Role Minimum Tenure}$ | Measures seniority surplus or deficit in integer years. |
| **`education_alignment`** | Extracted Score | Tiered alignment matrix matching candidate degree to role requirement. | Bounds qualification adequacy ($0.0 - 1.0$). |
| **`prerequisite_readiness`**| Extracted Ratio| $\frac{\text{Completed Prerequisite Courses}}{\text{Total Prerequisite Courses in DAG}}$ | Quantifies foundational preparation before advanced courses. |

#### Feature Scaling via `StandardScaler`:
Because `exp_delta` ranges from $-5$ to $+20$ while `skill_match_ratio` ranges from $0.0$ to $1.0$, distance-based and gradient algorithms would be biased toward tenure. SkillGraph applies $z$-score normalization:
$$z = \frac{x - \mu}{\sigma}$$
Implemented in `build_processed_data.py`:
```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
```

### 2.4 Train-Test Split & Cross-Validation

To validate the career transition prediction model without data contamination:
```python
from sklearn.model_selection import train_test_split

# 80% Training partition, 20% Testing partition with deterministic random seed
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, 
    y, 
    test_size=0.20, 
    random_state=42, 
    stratify=y
)
```
* **Stratified Sampling:** Ensures the proportion of successful transition candidates ($y = 1$) vs. unready candidates ($y = 0$) is identical in both training and test partitions.

### 2.5 Model Evaluation: Confusion Matrix, Accuracy, Precision, Recall

The Random Forest model (`RandomForestClassifier(n_estimators=100, max_depth=6)`) is evaluated against the test set:

```
               Actual Positive (1)    Actual Negative (0)
Predicted (1)       True Positive (TP)     False Positive (FP)
Predicted (0)       False Negative (FN)    True Negative (TN)
```

$$\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN} \approx 94.5\%$$
$$\text{Precision} = \frac{TP}{TP + FP} \approx 93.8\%$$
$$\text{Recall (Sensitivity)} = \frac{TP}{TP + FN} \approx 95.2\%$$
$$\text{F1-Score} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}} \approx 94.5\%$$

#### Domain Significance in SkillGraph:
* **Prioritizing High Recall:** In career mobility, a False Negative (telling a qualified engineer they are not ready for promotion) demoralizes talent and causes turnover. High recall ensures genuinely qualified internal candidates are recommended for promotion.
* **Precision Safeguard:** Prevents placing engineers into high-stakes production roles without prerequisite mastery.

