"""
Database configuration and session management for SkillGraph.
Supports SQLite out of the box with zero configuration,
as well as PostgreSQL via the DATABASE_URL environment variable.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/processed/skillgraph.db")

# SQLite needs check_same_thread=False for multi-threaded FastAPI workers
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency generator for FastAPI endpoints to yield database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
