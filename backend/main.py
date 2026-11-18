"""
SkillGraph Backend Application.
FastAPI main entrypoint with CORS, route registration, and startup database verification.
"""

import os
import sys

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database.db import engine, Base
from backend.database.init_db import seed_database
from backend.api.routes import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Verify database tables and seed if necessary on startup."""
    print("[SERVER] Initializing database and ensuring seed data...")
    seed_database()
    print("[SERVER] SkillGraph backend ready.")
    yield

app = FastAPI(
    title="SkillGraph API",
    description="AI-Powered Workforce Skill Gap Analysis & Self-Service Career Mobility Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS securely for local Vite dev server and explicit production origins
raw_origins = os.getenv("ALLOWED_ORIGINS", "")
if raw_origins.strip():
    allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
else:
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(api_router, prefix="/api")

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
