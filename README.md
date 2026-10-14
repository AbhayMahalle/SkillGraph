# SkillGraph

**AI-Powered Self-Service Career Development & Skill-Gap Analysis Platform**

SkillGraph is an AI-driven, self-service workforce skill intelligence platform built for individual professionals seeking internal career mobility and skill-gap analysis. Operating directly on authentic datasets (Job Skill Set, Resume Dataset, Candidate–Job Role Dataset, and O*NET 29.0 Database), SkillGraph connects individual competencies with occupational standards, prerequisite-aware course DAGs, and predictive transition models to answer essential career questions:

1. *"Which career roles can I realistically transition into based on my verified skills and experience?"*
2. *"What specific competencies am I missing for a target role, and what is the exact gap breakdown?"*
3. *"What foundational courses must I take first before tackling advanced dependencies?"*
4. *"How will my career readiness evolve as I master prerequisite skills?"*

---

## 🧭 Product Vision & Positioning

SkillGraph is designed exclusively as a **self-service career exploration platform** for individual users.

### The Self-Service User Journey
```text
Individual Registration & Skill Profile
  └── Select Target Career Role
        ├── Empirical Role Matching & Multi-Factor Compatibility
        ├── Competency Radar & Granular Skill Gap Inventory
        ├── Prerequisite-Aware Topological Roadmap (DAG Sort)
        ├── Interactive Career Sandbox ("What-If" Skill Simulator)
        └── Transition Readiness Evaluation
```

> [!NOTE]
> SkillGraph is a self-service tool for individual career progression. It does not contain an HR administration portal, workforce headcount planning modules, administrator roles, or employee/administrator perspective toggles.

---

## 🏛️ System Architecture

```text
 ┌─────────────────────────────────────────────────────────┐
 │               Frontend (React 18 + Vite + TS)           │
 │  - Personal Career Dashboard - Competency Radar Chart   │
 │  - Resume Skill Parser (NLP) - Topological DAG Roadmap  │
 │  - Career Simulation Sandbox - 2D SkillGraph (Canvas)   │
 │  - Role Explorer (96 Roles)  - Dataset Lineage Inspector│
 └────────────────────────────┬────────────────────────────┘
                              │ REST APIs (JSON / JWT)
                              ▼
 ┌─────────────────────────────────────────────────────────┐
 │                  Backend (FastAPI + Python)             │
 │  - Self-Service Auth / JWT  - NLP Entity Extractor      │
 │  - Canonical Normalizer     - Multi-Factor Role Matcher │
 │  - Topological DAG Engine   - ML Readiness Predictor    │
 │  - NetworkX Graph Engine    - Repo-Root-Aware DB Engine │
 └──────────────┬────────────────────────────┬─────────────┘
                │                            │
 ┌──────────────▼─────────────┐ ┌────────────▼─────────────┐
 │    Structured Database     │ │      Knowledge Graph     │
 │    SQLite (Preserved)      │ │   (NetworkX In-Memory)   │
 └────────────────────────────┘ └──────────────────────────┘
```

---

## 📊 Authentic Data Sources

SkillGraph operates directly on 4 verified datasets in `data/raw/`:
1. **Job Skill Set Dataset (`all_job_post.csv`)**: 1,167 real job postings across IT, Finance, Sales, and Operations with empirical skill distributions.
2. **Resume Dataset (`job_roles.csv` & `skills_database.json`)**: 324 canonical role profiles, experience requirements, and benchmark salary tiers.
3. **Candidate–Job Role Dataset (`candidate_job_role_dataset.csv`)**: 1,000 empirical employee records mapping transition paths.
4. **O*NET 29.0 Database (`db_29_0_text/`)**: US Department of Labor national taxonomy providing official SOC codes, descriptions, and technology competencies.

### Verified Catalog Assets
- **119 Canonical Skills** (`data/processed/canonical_skills.json`)
- **96 Career Roles** (`data/processed/canonical_roles.json`)
- **18 Courses & Prerequisite DAG** (`data/processed/course_catalog.json`)

---

## 📂 Project Structure

```text
SkillGraph/
├── backend/
│   ├── api/
│   │   ├── auth.py                  # JWT authentication and user session verification
│   │   └── routes.py                # Self-service REST endpoints (Profiles, Roles, Gaps, Roadmap)
│   ├── database/
│   │   ├── db.py                    # Repository-root-aware SQLAlchemy configuration (SQLite)
│   │   └── init_db.py               # Non-destructive idempotent database seeder
│   ├── graph/
│   │   ├── neo4j_export.cypher      # Pre-generated Cypher graph export
│   │   └── skill_graph.py           # NetworkX MultiDiGraph manager
│   ├── ml/
│   │   ├── models/
│   │   │   └── readiness_model.joblib # Serialized readiness classifier & scaler
│   │   ├── learning_path.py         # Prerequisite-aware topological DAG ordering
│   │   ├── readiness.py             # Career transition readiness predictor & heuristic engine
│   │   ├── role_matching.py         # Multi-factor algorithmic role matching engine
│   │   └── skill_extraction.py      # Resume NLP entity extractor & canonical normalizer
│   ├── models/
│   │   └── models.py                # SQLAlchemy ORM entity definitions
│   ├── preprocessing/
│   │   └── build_processed_data.py  # Dataset preprocessing & model training pipeline
│   └── main.py                      # FastAPI application entrypoint with lifespan events
├── data/
│   ├── processed/
│   │   ├── canonical_roles.json     # 96 standardized role definitions
│   │   ├── canonical_skills.json    # 119 canonical skill ontologies
│   │   ├── course_catalog.json      # 18 courses with verified prerequisite edges
│   │   ├── employees_seed.json      # 6 seed employee profiles
│   │   └── skillgraph.db            # SQLite database file (10 tables, preserved)
│   └── raw/                         # 4 original Kaggle & O*NET raw datasets
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DatasetsExplorer.tsx     # Raw dataset lineage & audit inspector
│   │   │   ├── EmployeeDashboard.tsx    # Personal career mobility hub
│   │   │   ├── LandingView.tsx          # Self-service product landing page
│   │   │   ├── LearningPathView.tsx     # Topological DAG prerequisite roadmap
│   │   │   ├── Navbar.tsx               # Unified navigation bar
│   │   │   ├── ProfileView.tsx          # Resume text parser & skill portfolio manager
│   │   │   ├── RoleExplorer.tsx         # 96-role catalog browser & requirement viewer
│   │   │   ├── SkillGapView.tsx         # SVG Competency Radar chart & categorized gaps
│   │   │   ├── SkillGraphVisualizer.tsx # 2D Canvas force-directed knowledge graph
│   │   │   └── WhatIfSimulator.tsx      # Interactive career development simulation sandbox
│   │   ├── App.tsx                  # Main client routing and state container
│   │   └── main.tsx                 # React DOM mount point
│   ├── package.json                 # Node dependencies (React 18, Vite, Lucide)
│   └── vite.config.ts               # Vite configuration with /api backend proxy
├── tests/
│   └── test_skillgraph.py           # Comprehensive pytest suite (11 test cases)
└── requirements.txt                 # Python dependencies
```

---

## 🛠️ Local Setup & Execution Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Node.js 18+ and npm

### 1. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI server (runs on http://127.0.0.1:8000)
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
- API Documentation (Swagger): `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/api/health`

### 2. Frontend Setup
```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite dev server (runs on http://localhost:5173)
npm run dev
```

### 3. Running Automated Tests
```bash
# Execute full backend test suite (Phase 1 Foundation + Phase 2 Auth & Data Isolation)
pytest -v tests/

# Execute frontend TypeScript check & production bundle build
cd frontend && npm run build
```

---

## 🔐 Phase 2: Authentication & Personal Profiles

### Authentication & Profile API Endpoints
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/register` | Registers new user with PBKDF2 password hashing & creates private linked employee record | No |
| `POST` | `/api/auth/login` | Authenticates credentials, auto-upgrades legacy hashes to PBKDF2, issues HS256 JWT | No |
| `POST` | `/api/auth/logout` | Revokes active JWT token on the server and terminates session | Yes (Bearer) |
| `POST` | `/api/auth/change-password` | Updates password after verifying current credentials | Yes (Bearer) |
| `GET` | `/api/users/me` | Retrieves authenticated user identity and strictly linked personal employee profile | Yes (Bearer) |
| `PATCH` | `/api/users/me` | Updates profile details (name, bio, department, target role, experience, qualification) | Yes (Bearer) |
| `GET` | `/api/skills/catalog` | Retrieves canonical 119-skill ontology with category and search query filtering | No |
| `GET` | `/api/employees/skills` | Lists authenticated user's personal skills with proficiency, provenance source, and evidence | Yes (Bearer) |
| `POST` | `/api/employees/skills` | Adds or updates personal skill with proficiency validation (`Beginner` to `Expert`) | Yes (Bearer) |
| `PUT` | `/api/employees/skills/{skill}`| Updates proficiency level and evidence snippet for an existing personal skill | Yes (Bearer) |
| `DELETE` | `/api/employees/skills/{skill}`| Removes a skill from the authenticated user's personal profile | Yes (Bearer) |
| `POST` | `/api/employees/resume-upload`| Uploads PDF, DOCX, or TXT file (or raw text), parses text, and stages candidate skills | Yes (Bearer) |
| `GET` | `/api/employees/resume/extracted`| Retrieves staged candidate skill mentions with match confidence and context snippets | Yes (Bearer) |
| `POST` | `/api/employees/resume/confirm-skills`| Saves user-reviewed and approved candidate skills to profile as `resume_extracted` | Yes (Bearer) |

### Security & Cryptographic Safeguards
1. **Password Hashing**: Implements standard-library `PBKDF2-HMAC-SHA256` with 100,000 iterations and 16-byte random salts (`secrets.token_hex(16)`). Format: `pbkdf2_sha256$100000$<salt>$<digest>`.
2. **Constant-Time Verification**: Uses `hmac.compare_digest` for all credential comparisons to eliminate side-channel timing attacks.
3. **Legacy Hash Auto-Upgrade**: Seamless backward-compatibility verifies legacy Phase 1 SHA-256 hashes and immediately re-hashes them to PBKDF2 upon successful login.
4. **Token Invalidation on Logout**: Maintains an active token revocation blacklist; logged-out tokens are immediately rejected on subsequent requests with `401 Unauthorized`.
5. **Strict Data Isolation**: Identity is strictly derived from verified JWT claims (`sub`), never from client-supplied IDs. All fallback queries to other employee records have been completely eliminated.
6. **Protected Field Immutability**: `PATCH /api/users/me` strictly ignores or disallows modifications to `id`, `email`, `role`, `hashed_password`, or `employee_id`.
7. **Upload Security & File Isolation**: Resume files are validated against allowed extensions (`.pdf`, `.docx`, `.txt`), magic byte signatures (`%PDF`, `PK\x03\x04`), and a 10 MB file size limit. Files are stored outside web roots in user-segregated directories (`data/uploads/resumes/{user_id}/`) with path traversal sanitization.
8. **Candidate Skill Provenance & Non-Auto-Verification**: Extracted skills are staged in a review buffer and **never** automatically saved as verified expertise. Confirmed skills are persisted with `source="resume_extracted"` and `verified=False`.

---

## 📄 Resume Intelligence & Processing Pipeline

### Supported Formats & Extraction Engine
- **PDF Documents (`.pdf`)**: Extracted using PyMuPDF (`pymupdf` / `fitz`) with text layer verification. Scanned or image-only PDFs without readable text return graceful error alerts without falsely claiming OCR capabilities.
- **Word Documents (`.docx`)**: Parsed using `python-docx` across paragraph and table blocks.
- **Plain Text (`.txt`)**: Decoded via UTF-8 with automatic Latin-1 fallback.

### Provenance Tracking (`employee_skills`)
- `source`: Provenance source indicator (`self_reported`, `resume_extracted`, `project`, `assessment`).
- `verified`: Boolean flag indicating formal verification status (candidate resume mentions remain `False` until verified).
- `evidence`: Text snippet or context citation documenting skill usage.
- `created_at` & `updated_at`: ISO-8601 audit timestamps.

### Staged Candidate Review & Confirmation Flow
```text
Resume Upload (PDF/DOCX/TXT) 
  ──► Magic Byte & Size Validation 
  ──► Text Extraction (PyMuPDF / python-docx)
  ──► NLP Ontology Mapping (119 Canonical Skills)
  ──► Staging Cache (GET /api/employees/resume/extracted)
  ──► User Review Interface:
        ├── Select / Deselect candidate skills
        ├── Adjust proficiency levels (Beginner, Intermediate, Advanced, Expert)
        └── Inspect contextual evidence snippets and confidence percentages
  ──► Confirm & Persist (POST /api/employees/resume/confirm-skills)
        └── Saved with source="resume_extracted" & verified=False
```

---

## 🗄️ Database Architecture & Safety

- **Database Engine**: SQLite 3
- **Database Path**: `data/processed/skillgraph.db`
- **Path Resolution**: The path is resolved dynamically relative to the repository root via `Path(__file__).resolve().parent.parent.parent` in `backend/database/db.py`.
- **Verified Backups**:
  - Phase 1 Baseline Backup: `data/processed/skillgraph_backup_phase1.db`
  - Phase 2 Pre-Migration Backup: `data/processed/skillgraph_backup_phase2.db`
  - Phase 3 Pre-Migration Backup: `data/processed/skillgraph_backup_phase3.db`
  - Phase 4 Pre-Migration Backup: `data/processed/skillgraph_backup_phase4.db`
- **Schema Enhancements**:
  - `employee_skills.source`: `VARCHAR(50)` (default: `'self_reported'`)
  - `employee_skills.evidence`: `TEXT` (surrounding context snippet or user evidence)
  - `employee_skills.created_at`: `VARCHAR(50)` (ISO-8601 creation timestamp)
  - `employee_skills.updated_at`: `VARCHAR(50)` (ISO-8601 update timestamp)
  - `employees.target_role_id`: `VARCHAR(50)` (Foreign key / canonical role ID link to `roles.role_id`)
  - Unique Constraint: `ix_employee_skills_emp_skill` on `(employee_id, skill_id)` preventing duplicate skills per employee.
- **Data Integrity & Preserved Catalogs**:
  - `skills`: 119 records (Canonical skill taxonomy)
  - `roles`: 96 records (Standardized career roles)
  - `courses`: 18 records (Prerequisite DAG courses)
  - `course_skills`: 38 records
  - `course_prerequisites`: 20 records
  - `employees`: 6 records (Baseline seeded profiles preserved)
  - `users`: 6 records (Baseline accounts preserved)
- **Isolated Test Execution**: Automated tests run against isolated temporary copies of the verified baseline database (`tempfile.NamedTemporaryFile`), ensuring zero test artifacts or destructive writes to `skillgraph.db`.

---

## 🎯 Phase 4: Target-Role Matching & Skill-Gap Analysis

### Role Matching & Gap Analysis Endpoints
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/roles` | Lists canonical roles with keyword query (`?q=...`) and category filtering | No |
| `GET` | `/api/roles/{role_id}` | Retrieves canonical role details, requirements, and skill weights | No |
| `PUT` / `POST` | `/api/employees/target-role` | Sets and persists the authenticated user's target career role | Yes (Bearer) |
| `GET` | `/api/roles/compare` | Compares 2 to 4 canonical roles side-by-side against the user's verified profile | Yes (Bearer) |
| `GET` | `/api/roles/match/{role_id}` | Calculates personalized match score, mobility status, and mathematical explainability | Yes (Bearer) |
| `GET` | `/api/analysis/skill-gap/{role_id}` | Performs skill-gap analysis: Met, Partially Met, Missing classifications, radar metrics, and priority rankings | Yes (Bearer) |
| `GET` | `/api/roles/recommendations` | Computes personalized multi-factor match scores across all roles with provenance awareness | Yes (Bearer) |

### Explainable Match Calculation & Guardrails
1. **Proficiency Representation**: 4-level scale (`Beginner`: 1, `Intermediate`: 2, `Advanced`: 3, `Expert`: 4).
2. **Benchmark Derivation**: Grounded in canonical role requirements (`experience_years >= 5` → Level 3 / Advanced; `>= 2` → Level 2 / Intermediate; `< 2` → Level 1 / Beginner).
3. **Provenance & Unverified Skill Discounting**: Skills extracted from resumes that have not been formally verified (`source="resume_extracted"` and `verified=False`) receive an automatic 1-level discount (floor of Level 1) and a 15% weight factor penalty. Resume mentions are never treated as verified expertise.
4. **Deterministic Scoring Formula**:
   $$\text{Coverage} = \frac{\sum w_i \cdot \min(1.0, \frac{\text{demonstrated}_i}{\text{required}_i}) \cdot \text{mult}_i}{\sum w_i}$$
   $$\text{Match Score} = \min\left(100.0, \text{Coverage} \times \text{Experience Factor} \times 100.0\right)$$
   Where Experience Factor adjusts for experience delta bounded between 0.70x and 1.05x.
5. **Skill-Gap Classification & Priority Matrix**:
   - **Met**: User possesses skill with verified evidence and demonstrated level meets/exceeds role requirement.
   - **Partially Met**: Skill possessed but below benchmark proficiency or unverified. Gap = $\max(1, \text{required} - \text{demonstrated})$.
   - **Missing**: Skill completely absent from user profile. Gap = $\text{required\_level}$.
   - **Priority Metric**: $\text{Gap Depth} \times \text{Importance Weight}$. Classified as:
     - $\ge 3.0 \rightarrow$ `Critical`
     - $\ge 2.0 \rightarrow$ `High`
     - $\ge 1.0 \rightarrow$ `Medium`
     - $< 1.0 \rightarrow$ `Low`

---

## 🧪 Verified Capabilities & Test Suite (55 Passing Tests)

| Component | Status | Verified Details |
|---|---|---|
| **Phase 1 Foundation Suite** | ✅ 11/11 PASS | DAG topology, NLP extraction, matching math, catalog counts, health |
| **Phase 2 Authentication Suite** | ✅ 16/16 PASS | Registration, login, PBKDF2 hash upgrade, token invalidation, profile patch, isolation |
| **Phase 3 Skill Profiling & Resume Suite** | ✅ 16/16 PASS | Skill CRUD, validation, PDF/DOCX/TXT extraction, staging, review, provenance |
| **Phase 4 Matching & Gap Suite** | ✅ 12/12 PASS | Target-role selection, search, explainable match, gap classification, multi-role comparison, isolation |
| **Total Automated Tests** | ✅ **55/55 PASS** | Complete regression test suite passes cleanly in 5.81s |
| **Frontend Production Build** | ✅ **PASS** | `tsc && vite build` builds 0 errors in 2.25s (295 kB bundle) |
| **Live API End-to-End** | ✅ **PASS** | Verified live on port 8000 (search, target role persistence, 3-role comparison, gap breakdown) |

---

## 🔬 Known Limitations & Future Roadmap

1. **Token Storage**: JWT access tokens are stored in `localStorage` for SPA client state. In future enterprise phases, tokens may be transitioned to `HttpOnly` SameSite cookies with CSRF protection.
2. **Token Revocation Storage**: Revoked tokens are currently tracked in-memory per process instance. In distributed multi-worker deployments, a shared Redis cache or database revocation table should be used.
3. **OCR Processing**: Scanned/image-only PDFs are safely detected and rejected with a helpful user prompt; optical character recognition (OCR) can be integrated in later phases if required.
4. **Readiness Model Training Data**: The transition readiness model (`readiness_model.joblib`) uses synthetic feature distributions. Phase 6 will retrain the predictor with authentic employee transition data.
5. **Scope Boundaries**: Learning roadmap generation, course enrollment/progress, assessments, and readiness retraining are deferred to Phase 5 and beyond.


