"""
SkillGraph Backend Application.
FastAPI main entrypoint with CORS, route registration, and startup database verification.
"""

import os
import sys

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from backend.database.db import engine, Base
from backend.database.init_db import seed_database
from backend.api.routes import api_router

app = FastAPI(
    title="SkillGraph API",
    description="AI-Powered Workforce Skill Gap Analysis & Internal Talent Mobility Platform",
    version="1.0.0"
)

# Enable CORS for local Vite dev server and production clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(api_router, prefix="/api")

@app.on_event("startup")
def on_startup():
    """Verify database tables and seed if necessary on startup."""
    print("[SERVER] Initializing database and ensuring seed data...")
    seed_database()
    print("[SERVER] SkillGraph backend ready.")

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "service": "SkillGraph API",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
