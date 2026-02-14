"""
Authentication and authorization module.
Implements JWT token management and RBAC.
"""

from datetime import datetime, timedelta, timezone
from typing import Callable

import bcrypt
import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer

from app.core.config import settings
from app.db.database import Database
from app.schemas import RoleEnum, UserResponse, TokenResponse


class PasswordManager:
    """Manage password hashing and verification"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


class TokenManager:
    """Manage JWT token generation and verification"""

    @staticmethod
    def create_access_token(user_id: int, username: str, role: str) -> TokenResponse:
        """Create JWT access token"""
        expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.now(timezone.utc) + expires_delta

        payload = {
            "sub": str(user_id),
            "username": username,
            "role": role,
            "exp": expire,
        }

        token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

        return TokenResponse(
            access_token=token,
            expires_in=int(expires_delta.total_seconds()),
        )

    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )


class AuthService:
    """Service for authentication operations"""

    def __init__(self, db: Database):
        self.db = db

    def create_user(
        self, username: str, password: str, role: RoleEnum = RoleEnum.USER
    ) -> UserResponse:
        """Create new user"""
        password_hash = PasswordManager.hash_password(password)

        try:
            result = self.db.conn.execute(
                """
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
                RETURNING id, username, role, is_active, created_at
                """,
                [username, password_hash, role.value],
            ).fetchall()

            if result:
                user = result[0]
                return UserResponse(
                    id=user[0],
                    username=user[1],
                    role=RoleEnum(user[2]),
                    is_active=user[3],
                    created_at=user[4],
                )
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already exists",
                )
            raise

    def authenticate_user(self, username: str, password: str) -> TokenResponse:
        """Authenticate user and return JWT token"""
        user = self.db.conn.execute(
            "SELECT id, username, role, password_hash FROM users WHERE username = ?",
            [username],
        ).fetchall()

        if not user or not PasswordManager.verify_password(password, user[0][3]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        user_data = user[0]
        return TokenManager.create_access_token(user_data[0], user_data[1], user_data[2])

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password"""
        return PasswordManager.hash_password(password)

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return PasswordManager.verify_password(password, password_hash)

    @staticmethod
    def get_current_user(token: str) -> dict:
        """Get current user from token"""
        payload = TokenManager.verify_token(token)
        return payload


# FastAPI Dependencies

security = HTTPBearer()


def get_current_user(credentials = Depends(security)) -> dict:
    """FastAPI dependency to get current authenticated user"""
    return TokenManager.verify_token(credentials.credentials)


def require_role(*allowed_roles: str) -> Callable:
    """FastAPI dependency factory for role-based access control"""

    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of the following roles: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker
