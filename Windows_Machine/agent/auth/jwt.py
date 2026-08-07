import jwt
import hashlib
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from config.config import WindowsConfig

SECRET_KEY = WindowsConfig.JWT_SECRET
ALGORITHM = WindowsConfig.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = WindowsConfig.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = WindowsConfig.REFRESH_TOKEN_EXPIRE_DAYS

def create_access_token(user_id: str, username: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Generates a signed JWT access token containing sub, username, role, iat, exp claims."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: str, expires_delta: Optional[timedelta] = None) -> tuple[str, str, datetime]:
    """Generates a signed JWT refresh token and returns (raw_token, token_hash, expires_at_dt)."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    jti = str(uuid.uuid4())
    payload = {
        "sub": user_id,
        "jti": jti,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }

    raw_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    token_hash = hash_token(raw_token)
    return raw_token, token_hash, expire

def decode_token(token: str, verify_type: Optional[str] = None) -> Dict[str, Any]:
    """Decodes and verifies a JWT token. Raises PyJWT exceptions on invalid signature or expiry."""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if verify_type and payload.get("type") != verify_type:
        raise jwt.InvalidTokenError(f"Token type mismatch: expected {verify_type}, got {payload.get('type')}")
    return payload

def hash_token(token: str) -> str:
    """SHA-256 hash helper for storing refresh tokens safely in DB."""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()
