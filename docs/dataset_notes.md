# Dataset Notes

## Job Skill Set
- **Source**: Kaggle
- **URL**: https://www.kaggle.com/datasets/batuhanmutlu/job-skill-set
- **Why SkillGraph uses it**: Maps job roles to required skill sets and analyzes skill frequency across job categories.
- **Important files**: `all_job_post.csv`
- **Number of rows**: 1,167
- **Number of columns**: 5
- **Important columns**: 
  - `job_id` (int64) - Unique identifier for the job post.
  - `category` (object/string) - Job domain/category (e.g., HR, Tech).
  - `job_title` (object/string) - Full job title.
  - `job_description` (object/string) - Complete text description of the job.
  - `job_skill_set` (object/string) - Extracted skills formatted as list strings.
- **Data type**: Tabular CSV containing structured metadata, descriptions, and stringified lists.
- **Potential future use**: Role-skill knowledge graph construction, skill distribution analysis per job role.
- **Known limitations**: `job_skill_set` is formatted as Python string representation of lists (`['skill1', 'skill2']`) requiring AST parsing.

---

## Resume Dataset
- **Source**: Kaggle
- **URL**: https://www.kaggle.com/datasets/trendcart/resume-dataset
- **Why SkillGraph uses it**: Provides resume text, candidate profiles, education, experience years, skills, and target job roles/categories.
- **Important files**:
  - `training_data.csv` (Primary resume dataset)
  - `job_roles.csv` (Job role requirements and salary benchmarks)
  - `skills_list.csv` (List of standardized skills and categories)
  - `skills_database.json`, `test_resumes.json` (Supporting JSON files)
- **Number of rows**: 
  - `training_data.csv`: 10,000 rows
  - `job_roles.csv`: 324 rows
  - `skills_list.csv`: 120 rows
- **Number of columns**: 
  - `training_data.csv`: 7 columns (`Resume ID`, `Resume Text`, `Education`, `Experience Years`, `Skills`, `Job Role`, `Category`)
  - `job_roles.csv`: 6 columns (`Job Title`, `Category`, `Education Requirement`, `Experience Years`, `Required Skills`, `Salary Range`)
  - `skills_list.csv`: 2 columns (`Skill Name`, `Category`)
- **Important columns**: `Resume Text`, `Education`, `Experience Years`, `Skills`, `Job Role`, `Category`
- **Data type**: Tabular CSV and structured JSON files.
- **Potential future use**: Resume text parsing, skill extraction benchmarking, and candidate profiling.
- **Known limitations**: Skills in `training_data.csv` are pipe-delimited (`|`); resume texts are semi-structured/synthetic.

---

## Candidate Job Role
- **Source**: Kaggle
- **URL**: https://www.kaggle.com/datasets/ckshetty/candidate-job-role-dataset
- **Why SkillGraph uses it**: Connects candidate skills, education, and experience levels to suitable job roles.
- **Important files**: `candidate_job_role_dataset.csv`
- **Number of rows**: 1,000
- **Number of columns**: 5
- **Important columns**:
  - `candidate_id` (int64) - Candidate identifier.
  - `skills` (object/string) - Comma-separated list of candidate skills.
  - `qualification` (object/string) - Degree / educational qualification.
  - `experience_level` (object/string) - Seniority tier (e.g., Senior, Mid, Entry).
  - `job_role` (object/string) - Target/assigned job role.
- **Data type**: Tabular CSV.
- **Potential future use**: Candidate-to-role matching, classification, and gap analysis.
- **Known limitations**: Relatively small sample size (1,000 rows); comma-separated skills require tokenization and standardization.

---

## O*NET 29.0 Database
- **Source**: Kaggle / O*NET Resource Center
- **URL**: https://www.kaggle.com/datasets/emarkhauser/onet-29-0-database
- **Why SkillGraph uses it**: Standardized, comprehensive occupational taxonomy, skill classifications, knowledge, abilities, work activities, and technology tools.
- **Important files**:
  - `Occupation Data.txt` (1,016 rows, 3 columns: `O*NET-SOC Code`, `Title`, `Description`)
  - `Skills.txt` (61,530 rows, 13 columns: `O*NET-SOC Code`, `Element Name`, `Scale ID`, `Data Value`, etc.)
  - `Technology Skills.txt` (32,470 rows, 6 columns: `O*NET-SOC Code`, `Example`, `Commodity Title`, `Hot Technology`, `In Demand`)
  - `Knowledge.txt` (58,014 rows, 13 columns)
  - `Abilities.txt` (91,416 rows, 13 columns)
  - `Task Statements.txt` (18,796 rows, 7 columns)
- **Number of rows**: 1,016 standard occupations; 60,000+ skill ratings; 32,000+ technology tool entries.
- **Number of columns**: Varies across 41 files (3 to 13 columns).
- **Important columns**: `O*NET-SOC Code`, `Title`, `Element Name`, `Scale ID`, `Data Value`, `Example` (Technology)
- **Data type**: Tab-delimited text (`.txt`) relational dataset.
- **Potential future use**: Ground-truth ontology, role standardizations, skill hierarchies, and prerequisite mapping.
- **Known limitations**: Multi-table relational schema requiring joins on `O*NET-SOC Code` and `Element ID`.
