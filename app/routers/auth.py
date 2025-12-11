from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.auth import (
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_token,
)
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.token import RefreshTokenRequest, Token
from app.models.user import (
    User,
    UserCreate,
    UserInDB,
    PasswordChange,
    PasswordResetRequest,
    PasswordReset,
)
from app.repositories.user import UserRepository

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db=Depends(get_db)):
    """
    Register a new user.

    Args:
        user: User registration data
        db: Database connection

    Returns:
        Created user data

    Raises:
        HTTPException: If username or email already exists
    """
    user_repo = UserRepository(db)

    # Check if username exists
    if user_repo.get_by_username(user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email exists
    if user_repo.get_by_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create user
    db_user = user_repo.create(user)
    return User(**db_user)


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db=Depends(get_db)
):
    """
    Login and get access token.

    Args:
        form_data: OAuth2 password form (username and password)
        db: Database connection

    Returns:
        Access token and refresh token

    Raises:
        HTTPException: If credentials are invalid
    """
    user_repo = UserRepository(db)

    # Get user by username
    user = user_repo.get_by_username(form_data.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    # Create tokens
    access_token = create_access_token(data={"sub": user["username"]})
    refresh_token = create_refresh_token(data={"sub": user["username"]})

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_request: RefreshTokenRequest, db=Depends(get_db)):
    """
    Refresh access token using refresh token.

    Args:
        refresh_request: Refresh token request
        db: Database connection

    Returns:
        New access token and refresh token

    Raises:
        HTTPException: If refresh token is invalid
    """
    # Verify refresh token
    payload = verify_token(refresh_request.refresh_token, token_type="refresh")

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user still exists and is active
    user_repo = UserRepository(db)
    user = user_repo.get_by_username(username)

    if not user or not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create new tokens
    access_token = create_access_token(data={"sub": username})
    new_refresh_token = create_refresh_token(data={"sub": username})

    return Token(access_token=access_token, refresh_token=new_refresh_token)


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
):
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user from token

    Returns:
        Current user data
    """
    return User(**current_user.model_dump())


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_change: PasswordChange,
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
    db=Depends(get_db),
):
    """
    Change password for current user.

    Args:
        password_change: Old and new password
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Success message

    Raises:
        HTTPException: If old password is incorrect
    """
    # Verify old password
    if not verify_password(password_change.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect old password"
        )

    # Update password
    user_repo = UserRepository(db)
    success = user_repo.update_password(current_user.id, password_change.new_password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        )

    return {"message": "Password changed successfully"}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: PasswordResetRequest,
    db=Depends(get_db),
):
    """
    Request password reset token.

    Args:
        request: Email for password reset
        db: Database connection

    Returns:
        Reset token (in production, send via email)
    """
    from datetime import datetime, timedelta
    from app.core.auth import generate_reset_token

    user_repo = UserRepository(db)
    user = user_repo.get_by_email(request.email)

    # Always return success to prevent email enumeration
    if not user:
        return {"message": "If email exists, reset token has been sent"}

    # Generate reset token
    reset_token = generate_reset_token()
    expires_at = datetime.utcnow() + timedelta(hours=1)

    # Store token in database
    user_repo.set_reset_token(request.email, reset_token, expires_at)

    # In production, send email with token
    # For development, return token in response
    return {
        "message": "Password reset token generated",
        "reset_token": reset_token,  # Remove this in production
        "expires_at": expires_at.isoformat(),
    }


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    reset_data: PasswordReset,
    db=Depends(get_db),
):
    """
    Reset password using token.

    Args:
        reset_data: Reset token and new password
        db: Database connection

    Returns:
        Success message

    Raises:
        HTTPException: If token is invalid or expired
    """

    user_repo = UserRepository(db)
    user = user_repo.get_by_reset_token(reset_data.token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Update password
    success = user_repo.update_password(user["id"], reset_data.new_password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password",
        )

    # Clear reset token
    user_repo.clear_reset_token(user["id"])

    return {"message": "Password reset successfully"}
