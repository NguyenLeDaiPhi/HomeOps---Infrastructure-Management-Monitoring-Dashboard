import logging
from collections import defaultdict, deque
from time import time as current_time
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field

from database.connection import get_db_session
from auth.service import AuthService
from auth.dependencies import get_current_user, require_role

logger = logging.getLogger("AuthRoutes")
router = APIRouter(prefix="/auth", tags=["Authentication & User Management"])

LOGIN_ATTEMPTS = defaultdict(deque)
LOGIN_RATE_LIMIT_WINDOW_SECONDS = 300
LOGIN_MAX_ATTEMPTS = 5


def _is_rate_limited(client_ip: str) -> bool:
    now = current_time()
    attempts = LOGIN_ATTEMPTS[client_ip]
    while attempts and now - attempts[0] > LOGIN_RATE_LIMIT_WINDOW_SECONDS:
        attempts.popleft()
    return len(attempts) >= LOGIN_MAX_ATTEMPTS


def _record_login_attempt(client_ip: str) -> None:
    attempts = LOGIN_ATTEMPTS[client_ip]
    attempts.append(current_time())
    while len(attempts) > LOGIN_MAX_ATTEMPTS:
        attempts.popleft()

# ---------------------------------------------------------------------------
# Pydantic Request / Response Schemas
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900
    user: Dict[str, Any]

class UserResponse(BaseModel):
    id: str
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[str] = None
    last_login: Optional[str] = None

class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6)
    role: str = Field("viewer", description="Role: admin, operator, or viewer")
    full_name: Optional[str] = None
    email: Optional[str] = None

class UpdateUserRequest(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    new_password: Optional[str] = None

# ---------------------------------------------------------------------------
# Auth Endpoints
# ---------------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request):
    """Authenticates user with username & password and issues JWT access/refresh tokens."""
    client_ip = request.client.host if request.client else "unknown"
    if _is_rate_limited(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please wait a few minutes before trying again."
        )

    with get_db_session() as session:
        user = AuthService.authenticate_user(session, body.username, body.password)
        if not user:
            _record_login_attempt(client_ip)
            AuthService.create_audit_log(
                session,
                user_id=None,
                action="LOGIN_FAILED",
                resource=f"user:{body.username}",
                ip_address=client_ip,
                result="FAILURE"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password."
            )

        _record_login_attempt(client_ip)
        token_data = AuthService.create_user_session(session, user, ip_address=client_ip)
        return token_data

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, request: Request):
    """Exchanges a valid refresh token for a new access token and rotated refresh token."""
    client_ip = request.client.host if request.client else "unknown"
    with get_db_session() as session:
        token_data = AuthService.refresh_user_session(session, body.refresh_token, ip_address=client_ip)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token."
            )
        return token_data

@router.post("/logout")
async def logout(
    body: Optional[RefreshRequest] = None,
    request: Request = None,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """Revokes the user's refresh token and ends the session."""
    client_ip = request.client.host if (request and request.client) else "unknown"
    if body and body.refresh_token:
        with get_db_session() as session:
            user_id = current_user.get("id") if current_user else None
            AuthService.revoke_user_refresh_token(session, body.refresh_token, user_id=user_id, ip_address=client_ip)
    return {"status": "success", "message": "Session logged out successfully."}

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Returns profile details of the currently authenticated user."""
    with get_db_session() as session:
        from database.models import User
        user = session.get(User, current_user["id"])
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return AuthService.user_to_dict(user)

# ---------------------------------------------------------------------------
# Admin User Management Endpoints (Requires 'admin' Role)
# ---------------------------------------------------------------------------

@router.get("/users", response_model=List[UserResponse])
async def list_all_users(admin_user: Dict[str, Any] = Depends(require_role(["admin"]))):
    """[Admin Only] Retrieves list of all registered dashboard user accounts."""
    with get_db_session() as session:
        return AuthService.list_users(session)

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: CreateUserRequest,
    request: Request,
    admin_user: Dict[str, Any] = Depends(require_role(["admin"]))
):
    """[Admin Only] Creates a new user account with specified role (admin, operator, viewer)."""
    client_ip = request.client.host if request.client else "unknown"
    valid_roles = {"admin", "operator", "viewer"}
    if body.role.lower() not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{body.role}'. Must be one of: {valid_roles}"
        )

    with get_db_session() as session:
        try:
            new_user = AuthService.create_user(
                session,
                username=body.username,
                password=body.password,
                role=body.role,
                full_name=body.full_name,
                email=body.email,
                creator_user_id=admin_user["id"],
                ip_address=client_ip
            )
            return AuthService.user_to_dict(new_user)
        except ValueError as val_err:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    body: UpdateUserRequest,
    request: Request,
    admin_user: Dict[str, Any] = Depends(require_role(["admin"]))
):
    """[Admin Only] Updates user account details, role, status, or password."""
    client_ip = request.client.host if request.client else "unknown"
    if body.role and body.role.lower() not in {"admin", "operator", "viewer"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be one of: admin, operator, viewer"
        )

    with get_db_session() as session:
        updated = AuthService.update_user(
            session,
            user_id=user_id,
            role=body.role,
            is_active=body.is_active,
            full_name=body.full_name,
            email=body.email,
            new_password=body.new_password,
            operator_user_id=admin_user["id"],
            ip_address=client_ip
        )
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")
        return AuthService.user_to_dict(updated)

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    request: Request,
    admin_user: Dict[str, Any] = Depends(require_role(["admin"]))
):
    """[Admin Only] Deletes a user account."""
    client_ip = request.client.host if request.client else "unknown"
    if user_id == admin_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot delete their own active account."
        )

    with get_db_session() as session:
        success = AuthService.delete_user(
            session,
            user_id=user_id,
            operator_user_id=admin_user["id"],
            ip_address=client_ip
        )
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")
        return {"status": "success", "message": "User account deleted successfully."}
