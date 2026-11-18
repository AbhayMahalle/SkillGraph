# SkillGraph — Data Science Syllabus Units Mapping

**Academic Course:** Data Science (Computer Engineering - AY 2026-27)  
**Institution:** Vishwakarma Institute of Technology (VIT), Pune  
**Project:** SkillGraph — AI-Driven Graph Talent Intelligence & Predictive Career Mobility Platform  

---

## 📚 Overview

This folder contains detailed technical documentation mapping every unit of the **VIT Computer Engineering Data Science Syllabus (AY 2026-27)** to its practical implementation in the **SkillGraph** production codebase.

Each unit document breaks down:
1. Exact syllabus topic definitions and academic concepts.
2. Concrete realization in SkillGraph (files, functions, mathematical formulations).
3. Code snippets, data models, statistical diagnostics, and domain impact.

---

## 🗂️ Unit Documentation Index

| Unit Document | Syllabus Title | Core Concepts Covered | Key Implementation Files |
| :--- | :--- | :--- | :--- |
| **[UNIT I: Introduction](UNIT_1_Introduction.md)** | Introduction to Data Science & Statistical Inference | Big Data hype vs. reality, Datafication, Statistical inference, Populations vs. samples, Probability distributions, Overfitting mitigation, Python data science environment. | [`backend/ml/skill_extraction.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/ml/skill_extraction.py)<br>[`backend/ml/role_matching.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/ml/role_matching.py)<br>[`backend/ml/readiness.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/ml/readiness.py) |
| **[UNIT II: Data Types & Stats](UNIT_2_Data_Types_and_Statistical_Description.md)** | Data Types & Statistical Description | Attributes & measurement, Nominal / Ordinal / Binary / Numeric data, Asymmetric binary attributes (skill verification), Central tendency (Mean, Median, Mode), Dispersion (Range, Variance, Std Dev, IQR), Graphical distributions. | [`backend/database/init_db.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/database/init_db.py)<br>[`backend/models/models.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/models/models.py)<br>[`frontend/src/components/SkillGapView.tsx`](file:///d:/vit/ty-sem1/ds/cp/second/frontend/src/components/SkillGapView.tsx) |
| **[UNIT III: Cleaning & Prep](UNIT_3_Data_Cleaning_and_Preparation.md)** | Data Cleaning & Preparation | Ingestion from 4 raw datasets (Kaggle & O*NET), Deduplication, Handling missing values (median imputation), IQR outlier filtering, Structural inspection (`info()`, `describe()`), Hypothesis testing vs. EDA, Text normalization & encoding. | [`backend/preprocessing/build_processed_data.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/preprocessing/build_processed_data.py)<br>[`backend/ml/skill_extraction.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/ml/skill_extraction.py)<br>`data/raw/` |
| **[UNIT IV: Programming in Python](UNIT_4_Foundations_of_Data_Science_Programming.md)** | Foundations of Python for Data Science | 1D NumPy vectors & 2D matrices, Vector indexing/slicing, Vectorized dot products & cosine norms, PCA dimensionality reduction, Categorical Pandas DataFrames (`loc`, `iloc`), Lightweight lists/dicts for $O(1)$ graph traversal. | [`backend/ml/role_matching.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/ml/role_matching.py)<br>[`backend/graph/skill_graph.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/graph/skill_graph.py)<br>[`backend/ml/learning_path.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/ml/learning_path.py) |
| **[UNIT V: EDA & Feature Engineering](UNIT_5_Working_with_Data_EDA_and_Feature_Engineering.md)** | Working with Data, EDA & Feature Engineering | Pandas data manipulation (importing, grouping, merging), EDA (correlation analysis, distribution skewness), Feature engineering (extraction of cosine ratio & coverage, standard scaling), Train-Test split (80/20), Confusion Matrix & Recall evaluation. | [`backend/ml/readiness.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/ml/readiness.py)<br>[`backend/preprocessing/build_processed_data.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/preprocessing/build_processed_data.py)<br>`backend/ml/models/readiness_model.joblib` |
| **[UNIT VI: Visualization & Regression](UNIT_6_Data_Visualization_and_Regression.md)** | Data Visualization & Regression Analysis | Matplotlib & Seaborn plots (Bar, Box Plot, Histogram, Multi-Line, Scatter), Interactive 2D Canvas force-directed graph & SVG Radar charts, Simple Linear Regression, Multiple Linear Regression (OLS, $R^2 \approx 0.884$, tenure prediction). | [`backend/graph/skill_graph.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/graph/skill_graph.py)<br>[`frontend/src/components/SkillGraphVisualizer.tsx`](file:///d:/vit/ty-sem1/ds/cp/second/frontend/src/components/SkillGraphVisualizer.tsx)<br>[`backend/ml/readiness.py`](file:///d:/vit/ty-sem1/ds/cp/second/backend/ml/readiness.py) |

---

## 🎯 Quick Verification

To verify that all the models and algorithms mentioned in these units execute cleanly:

```bash
# Run the complete test suite (97 tests covering all units)
pytest -v

# Start backend (FastAPI) and frontend (Vite)
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
npm run dev --prefix frontend
```

