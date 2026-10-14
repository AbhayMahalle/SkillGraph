"""
JWT Authentication & Role-Based Access Control (RBAC) for SkillGraph.
Secured with PBKDF2-HMAC-SHA256 password hashing, token revocation tracking,
and strict cryptographic verification.
"""

import os
import hashlib
import secrets
import hmac
import jwt
from datetime import datetime, timedelta
from typing import Optional, Set
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.models.models import User, Employee

# Cryptographic token configuration
JWT_SECRET = os.getenv("JWT_SECRET", "skillgraph-ai-talent-secret-key-2026-production-safe")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Security scheme
security = HTTPBearer()

# In-memory token revocation blacklist (tracks logged-out tokens)
REVOKED_TOKENS: Set[str] = set()

def revoke_token(token: str) -> None:
    """Add a token to the revoked blacklist."""
    REVOKED_TOKENS.add(token)

def is_token_revoked(token: str) -> bool:
    """Check if token has been revoked."""
    return token in REVOKED_TOKENS

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with 100,000 iterations.
    Returns format: pbkdf2_sha256$<iterations>$<salt>$<hex_digest>
    """
    if salt is None:
        salt = secrets.token_hex(16)
    iterations = 100000
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations
    )
    return f"pbkdf2_sha256${iterations}${salt}${derived.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a stored hash.
    Supports PBKDF2-HMAC-SHA256 and backward-compatible SHA256 hashes using
    constant-time comparison.
    """
    if not hashed_password or not plain_password:
        return False

    # Check for PBKDF2 format
    if hashed_password.startswith("pbkdf2_sha256$"):
        try:
            parts = hashed_password.split("$")
            if len(parts) != 4:
                return False
            iterations = int(parts[1])
            salt = parts[2].encode("utf-8")
            expected_hex = parts[3]
            derived = hashlib.pbkdf2_hmac(
                "sha256",
                plain_password.encode("utf-8"),
                salt,
                iterations
            )
            return hmac.compare_digest(derived.hex(), expected_hex)
        except Exception:
            return False

    # Backward compatibility with legacy Phase 1 SHA-256 hashes
    legacy_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy_hash, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed HS256 JWT access token with expiration and issued-at claims."""
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire,
        "iat": now
    })
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Validates the bearer token, checks revocation, extracts identity from verified claim,
    and returns the active User.
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been terminated. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

