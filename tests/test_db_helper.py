"""
Test Database Helper for SkillGraph Automated Test Suites.
Provides isolated, deterministic temporary SQLite databases for tests.
Guarantees clean test execution, proper schema migration, and clean teardown.
"""

import os
import shutil
import tempfile
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.db import REPO_ROOT
from backend.database.init_db import ensure_schema_migrations
from backend.models.models import Base

def get_test_baseline_backup(phase_name: str = "phase4") -> Path:
    """
    Finds the most suitable baseline backup file to initialize an isolated test database.
    Falls back progressively so tests never fail on missing snapshot files.
    """
    candidates = [
        REPO_ROOT / "data" / "processed" / f"skillgraph_backup_{phase_name}.db",
        REPO_ROOT / "data" / "processed" / "skillgraph_backup_phase4.db",
        REPO_ROOT / "data" / "processed" / "skillgraph_backup_phase3.db",
        REPO_ROOT / "data" / "processed" / "skillgraph_backup_phase2.db",
        REPO_ROOT / "data" / "processed" / "skillgraph_backup_phase1.db",
        REPO_ROOT / "data" / "processed" / "skillgraph.db",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None

def create_isolated_test_database(phase_name: str = "phase4"):
    """
    Initializes an isolated temporary SQLite database for a test session.
    Applies all schema migrations and returns (temp_db_path, test_engine, TestingSessionLocal).
    """
    temp_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db_path = temp_db_file.name
    temp_db_file.close()

    baseline = get_test_baseline_backup(phase_name)
    if baseline and baseline.exists():
        shutil.copyfile(str(baseline), temp_db_path)

    test_engine = create_engine(
        f"sqlite:///{temp_db_path}",
        connect_args={"check_same_thread": False}
    )

    Base.metadata.create_all(bind=test_engine)
    ensure_schema_migrations(test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    return temp_db_path, test_engine, TestingSessionLocal
