# UNIT IV: Foundations of Data Science Programming with Python

**Course:** Data Science (Computer Engineering Syllabus - AY 2026-27, Vishwakarma Institute of Technology)  
**Project:** SkillGraph — AI-Driven Graph Talent Intelligence & Predictive Career Mobility Platform  
**Directory:** `d:\vit\ty-sem1\ds\cp\second`

---

## 1. Syllabus Overview & Learning Objectives

| Topic Heading | Syllabus Scope |
| :--- | :--- |
| **NumPy Arrays & Vectors** | 1D vectors, array creation, data types, indexing, slicing, memory layouts, and subsetting. |
| **Matrices & Multidimensional Arrays** | 2D matrices, array reshaping, matrix transposition, dot products, and multi-axis operations. |
| **Matrix Subsetting & Slicing** | 2D slicing syntax: `array[row_slice, col_slice]`, boolean masking, and vectorized filtering. |
| **Principal Component Analysis (PCA)** | Dimensionality reduction, orthogonal linear projections, variance maximization, and feature compression. |
| **Categorical Data & Pandas DataFrames** | `loc` (label-based indexing) vs. `iloc` (integer position-based indexing), category types, summaries, sorting, and extending DataFrames. |
| **Python Lists & Dictionaries in Data Science** | Using primitive hash tables and sequences to parse and aggregate CSV data without heavyweight libraries. |
| **Vector Engineering & Vectorized Operations** | SIMD vector arithmetic, Euclidean norms, dot product vectorization, and avoiding slow Python `for` loops. |

---

## 2. Realization in SkillGraph

### 2.1 Vector Engineering & NumPy Multi-Dimensional Arrays
In [`backend/ml/role_matching.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/ml/role_matching.py) and [`backend/ml/readiness.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/ml/readiness.py), mathematical computations are vectorized using NumPy:

```python
import numpy as np

# Dense 119-dimensional vectors representing candidate and role requirements
def build_skill_vectors(candidate_skills: dict, role_requirements: dict, vocabulary: list) -> tuple:
    """
    Transforms candidate and role skill profiles into dense 1D NumPy float arrays.
    """
    n_dim = len(vocabulary)
    vec_candidate = np.zeros(n_dim, dtype=np.float32)
    vec_role = np.zeros(n_dim, dtype=np.float32)

    for idx, skill in enumerate(vocabulary):
        if skill in candidate_skills:
            # Vector engineering: Proficiency (1-4) * Verification weight (1.0 or 0.85)
            vec_candidate[idx] = candidate_skills[skill]["weight"]
        if skill in role_requirements:
            vec_role[idx] = role_requirements[skill]["importance"]

    return vec_candidate, vec_role
```

* **Vectorized Operations (Dot Product & Cosine Similarity):**
  Instead of iterating with nested loops across 96 roles, SkillGraph computes similarity using vectorized linear algebra:
  ```python
  # Vectorized Dot Product and L2 Euclidean Norms
  dot_product = np.dot(vec_candidate, vec_role)
  norm_candidate = np.linalg.norm(vec_candidate)
  norm_role = np.linalg.norm(vec_role)

  if norm_candidate > 0 and norm_role > 0:
      cosine_sim = dot_product / (norm_candidate * norm_role)
  else:
      cosine_sim = 0.0
  ```

### 2.2 Matrix Subsetting & Multi-Dimensional Slicing
In batch candidate evaluation (`backend/ml/readiness.py`), feature matrices of dimension $N \times 5$ (samples by features) are manipulated using NumPy 2D slicing:

```python
# Matrix of N candidates with 5 features:
# [skill_match, core_coverage, exp_delta, edu_align, prereq_readiness]
X = np.column_stack([skill_match, core_coverage, exp_delta, edu_align, prereq_readiness])

# Subsetting rows 0 to 10 and features 0 to 2 (skill_match and core_coverage)
core_features_subset = X[0:10, 0:2]

# Boolean indexing: select candidates with skill_match >= 0.70
qualified_matrix = X[X[:, 0] >= 0.70, :]
```

### 2.3 Principal Component Analysis (PCA) for Skill Space Compression
* **The High-Dimensional Problem:** With 119 canonical skills, visualizing the talent landscape requires compressing 119 dimensions down to a 2D or 3D coordinate space without losing relational variance.
* **PCA Application in SkillGraph:**
  In [`backend/graph/skill_graph.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/graph/skill_graph.py), PCA is applied to the role-skill affinity matrix ($96 \times 119$):
  1. **Mean Centering:** Center the matrix by subtracting column means.
  2. **Covariance Matrix:** Compute $\mathbf{\Sigma} = \frac{1}{n} \mathbf{X}^T \mathbf{X}$.
  3. **Eigen Decomposition:** Extract eigenvectors and eigenvalues to identify the principal directions of skill variance (e.g., PC1 = Cloud/DevOps vs. PC2 = Data/AI).
  4. **Projection:** Project the 119-dimensional skill space onto 2 principal components to seed initial layout coordinates for the interactive force-directed canvas.

### 2.4 Categorical Data & Pandas DataFrames: `loc`, `iloc`, and Summaries
In [`backend/api/routes.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/api/routes.py) and data inspection endpoints, Pandas DataFrames process role and applicant tables:

```python
import pandas as pd

# Load roles catalog into a DataFrame
df_roles = pd.read_json("data/processed/canonical_roles.json")

# Category handling
df_roles["department"] = df_roles["department"].astype("category")
print(df_roles["department"].cat.categories)  # Inspection of category levels

# Label-based slicing using .loc
engineering_roles = df_roles.loc[df_roles["department"] == "Engineering", ["role_id", "title", "experience_years"]]

# Position-based slicing using .iloc
first_five_records = df_roles.iloc[0:5, 0:3]

# Sorting by experience requirements descending
sorted_roles = df_roles.sort_values(by="experience_years", ascending=False)

# Extending DataFrame with derived columns
df_roles["seniority_tier"] = df_roles["experience_years"].apply(
    lambda x: "Senior" if x >= 5 else ("Mid" if x >= 2 else "Junior")
)
```

### 2.5 Primitive Python Lists & Dictionaries in Data Science Pipelines
While Pandas is ideal for static batch tables, **SkillGraph uses high-performance Python dictionaries and hash sets** for real-time graph lookups and CSV stream parsing:
* **Constant Time Lookups $O(1)$:**
  In [`backend/ml/learning_path.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/ml/learning_path.py#L38-L62):
  ```python
  self.courses: Dict[str, Dict[str, Any]] = {}
  self.skill_to_courses: Dict[str, List[str]] = {}
  ```
  Mapping `skill_to_courses` using a Python dictionary allows the roadmap generator to find candidate courses covering a missing skill in $O(1)$ time rather than conducting full $O(N)$ table scans.
* **Analyzing Raw CSVs using Primitive Lists and Dicts:**
  In lightweight ingestion utilities:
  ```python
  import csv

  with open("data/raw/all_job_post.csv", mode="r", encoding="utf-8") as f:
      reader = csv.DictReader(f)
      department_counts = {}
      for row in reader:
          dept = row.get("department", "Unknown")
          department_counts[dept] = department_counts.get(dept, 0) + 1
  ```

