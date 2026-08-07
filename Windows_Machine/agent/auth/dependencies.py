import logging
from typing import List, Dict, Any, Optional
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from auth.jwt import decode_token
from database.connection import get_db_session
from database.models import User

logger = logging.getLogger("AuthDependencies")
security_bearer = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
) -> Dict[str, Any]:
    """
    FastAPI dependency that extracts and validates the Bearer JWT access token.
    Raises 401 Unauthorized if missing, expired, or invalid.
    """
    token = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    else:
        # Fallback: check query parameter ?token=... (useful for EventSource / WebSocket)
        token = request.query_params.get("token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Bearer token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        payload = decode_token(token, verify_type="access")
        user_id = payload.get("sub")
        username = payload.get("username")
        role = payload.get("role")

        if not user_id or not username or not role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload structure.",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Verify user still exists and is active in DB
        with get_db_session() as session:
            user = session.get(User, user_id)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive or no longer exists.",
                    headers={"WWW-Authenticate": "Bearer"}
                )

        return {
            "id": user_id,
            "username": username,
            "role": role,
            "raw_token": token
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired.",
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\", error_description=\"The token has expired\""}
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {e}",
            headers={"WWW-Authenticate": "Bearer"}
        )

def require_role(allowed_roles: List[str]):
    """
    Dependency factory enforcing Role-Based Access Control (RBAC).
    Usage: Depends(require_role(["admin", "operator"]))
    Raises HTTP 403 Forbidden if user's role is not in allowed_roles.
    """
    allowed_set = {r.lower() for r in allowed_roles}

    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = (current_user.get("role") or "").lower()
        if user_role not in allowed_set:
            logger.warning(
                f"Access denied for user '{current_user.get('username')}' "
                f"(role: '{user_role}') -> Required: {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Role '{user_role}' cannot access this resource."
            )
        return current_user

    return role_checker

def verify_ws_token(token_str: str) -> Dict[str, Any]:
    """
    Validates a JWT token string during WebSocket connection handshake.
    Returns user payload dictionary or raises ValueError on invalid token.
    """
    if not token_str:
        raise ValueError("Missing WebSocket authentication token.")

    payload = decode_token(token_str, verify_type="access")
    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("Invalid WebSocket token payload.")

    with get_db_session() as session:
        user = session.get(User, user_id)
        if not user or not user.is_active:
            raise ValueError("User account is inactive or missing.")

    return {
        "id": user_id,
        "username": payload.get("username"),
        "role": payload.get("role")
    }
