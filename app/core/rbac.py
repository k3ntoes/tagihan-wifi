from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.core.dependencies import get_current_active_user
from app.models.enums import Role
from app.models.user import UserInDB


async def require_admin(
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
) -> UserInDB:
    """
    Require user to have ADMIN role.

    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user


async def require_user(
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
) -> UserInDB:
    """
    Require user to be authenticated (any role).

    This is an alias for get_current_active_user for semantic clarity.
    """
    return current_user
