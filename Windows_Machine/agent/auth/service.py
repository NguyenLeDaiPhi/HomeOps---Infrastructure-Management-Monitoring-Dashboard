import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from database.connection import get_db_session
from database.models import User, RefreshToken, AuditLog
from auth.password import hash_password, verify_password
from auth.jwt import create_access_token, create_refresh_token, decode_token, hash_token

logger = logging.getLogger("AuthService")

class AuthService:
    """Business logic for User authentication, Session management, RBAC, and Audit Logging."""

    @staticmethod
    def authenticate_user(session, username: str, password: str) -> Optional[User]:
        """Validates username and password. Returns User if valid & active, else None."""
        stmt = select(User).where(User.username == username)
        user = session.scalar(stmt)
        if not user:
            return None
        if not user.is_active:
            logger.warning(f"Authentication rejected for deactivated user: {username}")
            return None
        if not verify_password(password, user.password_hash):
            return None

        # Update last login timestamp
        user.last_login = datetime.now(timezone.utc)
        session.flush()
        return user

    @staticmethod
    def create_user_session(session, user: User, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """Generates access token + refresh token, persists refresh token hash in DB, logs audit event."""
        access_token = create_access_token(user.id, user.username, user.role)
        raw_refresh, refresh_hash, expires_at = create_refresh_token(user.id)

        db_token = RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=expires_at,
            revoked=False
        )
        session.add(db_token)

        AuthService.create_audit_log(
            session,
            user_id=user.id,
            action="LOGIN",
            resource="/auth/login",
            ip_address=ip_address,
            result="SUCCESS"
        )
        session.flush()

        return {
            "access_token": access_token,
            "refresh_token": raw_refresh,
            "token_type": "bearer",
            "expires_in": 900,  # 15 minutes in seconds
            "user": AuthService.user_to_dict(user)
        }

    @staticmethod
    def refresh_user_session(session, raw_refresh_token: str, ip_address: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Validates refresh token, rotates refresh token, and returns new access/refresh tokens."""
        try:
            payload = decode_token(raw_refresh_token, verify_type="refresh")
            user_id = payload.get("sub")
            if not user_id:
                return None

            t_hash = hash_token(raw_refresh_token)
            stmt = select(RefreshToken).where(
                RefreshToken.token_hash == t_hash,
                RefreshToken.revoked == False
            )
            db_token = session.scalar(stmt)
            if not db_token:
                logger.warning("Refresh token not found or already revoked.")
                return None

            # Check expiration
            if db_token.expires_at < datetime.now(timezone.utc):
                logger.warning("Refresh token expired in DB.")
                db_token.revoked = True
                return None

            user = session.get(User, user_id)
            if not user or not user.is_active:
                logger.warning("User for refresh token is inactive or missing.")
                db_token.revoked = True
                return None

            # Revoke used refresh token (Token Rotation)
            db_token.revoked = True

            # Issue new session
            new_access_token = create_access_token(user.id, user.username, user.role)
            new_raw_refresh, new_refresh_hash, new_expires_at = create_refresh_token(user.id)

            new_db_token = RefreshToken(
                user_id=user.id,
                token_hash=new_refresh_hash,
                expires_at=new_expires_at,
                revoked=False
            )
            session.add(new_db_token)

            AuthService.create_audit_log(
                session,
                user_id=user.id,
                action="REFRESH_TOKEN",
                resource="/auth/refresh",
                ip_address=ip_address,
                result="SUCCESS"
            )
            session.flush()

            return {
                "access_token": new_access_token,
                "refresh_token": new_raw_refresh,
                "token_type": "bearer",
                "expires_in": 900,
                "user": AuthService.user_to_dict(user)
            }
        except Exception as e:
            logger.warning(f"Failed to refresh session: {e}")
            return None

    @staticmethod
    def revoke_user_refresh_token(session, raw_refresh_token: str, user_id: Optional[str] = None, ip_address: Optional[str] = None) -> bool:
        """Revokes a refresh token on logout."""
        try:
            t_hash = hash_token(raw_refresh_token)
            stmt = select(RefreshToken).where(RefreshToken.token_hash == t_hash)
            token_obj = session.scalar(stmt)
            if token_obj:
                token_obj.revoked = True
                AuthService.create_audit_log(
                    session,
                    user_id=user_id or token_obj.user_id,
                    action="LOGOUT",
                    resource="/auth/logout",
                    ip_address=ip_address,
                    result="SUCCESS"
                )
                session.flush()
                return True
        except Exception as e:
            logger.error(f"Error revoking refresh token: {e}")
        return False

    @staticmethod
    def create_user(
        session,
        username: str,
        password: str,
        role: str = "viewer",
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        creator_user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> User:
        """Creates a new user account with hashed password."""
        existing = session.scalar(select(User).where(User.username == username))
        if existing:
            raise ValueError(f"Username '{username}' is already taken.")

        hashed = hash_password(password)
        new_user = User(
            username=username,
            password_hash=hashed,
            full_name=full_name,
            email=email,
            role=role.lower(),
            is_active=True
        )
        session.add(new_user)
        session.flush()

        AuthService.create_audit_log(
            session,
            user_id=creator_user_id,
            action="CREATE_USER",
            resource=f"user:{username}",
            ip_address=ip_address,
            result="SUCCESS"
        )
        return new_user

    @staticmethod
    def update_user(
        session,
        user_id: str,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        new_password: Optional[str] = None,
        operator_user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Optional[User]:
        """Updates user profile, role, status, or password."""
        user = session.get(User, user_id)
        if not user:
            return None

        if role is not None:
            user.role = role.lower()
        if is_active is not None:
            user.is_active = is_active
        if full_name is not None:
            user.full_name = full_name
        if email is not None:
            user.email = email
        if new_password:
            user.password_hash = hash_password(new_password)

        session.flush()
        AuthService.create_audit_log(
            session,
            user_id=operator_user_id,
            action="UPDATE_USER",
            resource=f"user:{user.username}",
            ip_address=ip_address,
            result="SUCCESS"
        )
        return user

    @staticmethod
    def delete_user(session, user_id: str, operator_user_id: Optional[str] = None, ip_address: Optional[str] = None) -> bool:
        """Deletes a user account."""
        user = session.get(User, user_id)
        if not user:
            return False
        username = user.username
        session.delete(user)
        session.flush()
        AuthService.create_audit_log(
            session,
            user_id=operator_user_id,
            action="DELETE_USER",
            resource=f"user:{username}",
            ip_address=ip_address,
            result="SUCCESS"
        )
        return True

    @staticmethod
    def list_users(session) -> List[Dict[str, Any]]:
        """Returns all user accounts."""
        stmt = select(User).order_by(User.created_at.desc())
        users = session.scalars(stmt).all()
        return [AuthService.user_to_dict(u) for u in users]

    @staticmethod
    def create_audit_log(
        session,
        user_id: Optional[str],
        action: str,
        resource: Optional[str] = None,
        ip_address: Optional[str] = None,
        result: str = "SUCCESS"
    ):
        """Creates an audit log record in PostgreSQL."""
        try:
            log_entry = AuditLog(
                user_id=user_id,
                action=action,
                resource=resource,
                ip_address=ip_address,
                result=result
            )
            session.add(log_entry)
        except Exception as e:
            logger.error(f"Failed to record audit log: {e}")

    @staticmethod
    def user_to_dict(user: User) -> Dict[str, Any]:
        """Serializes a User instance into a clean dictionary."""
        return {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
