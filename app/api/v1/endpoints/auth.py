"""
Authentication API endpoints
"""

from fastapi import APIRouter, Depends, status

from app.core.auth import AuthService, get_current_user
from app.db.database import Database, get_db
from app.schemas import UserLogin, TokenResponse, UserCreate, UserResponse, SingleUserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=SingleUserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Database = Depends(get_db)):
    """Register new user"""
    auth_service = AuthService(db)
    user = auth_service.create_user(user_data.username, user_data.password, user_data.role)
    return SingleUserResponse(data=user)


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Database = Depends(get_db)):
    """Login and get JWT token"""
    auth_service = AuthService(db)
    return auth_service.authenticate_user(credentials.username, credentials.password)


@router.get("/me", response_model=SingleUserResponse)
async def get_me(current_user: dict = Depends(get_current_user), db: Database = Depends(get_db)):
    """Get current user info"""
    user = db.conn.execute(
        "SELECT id, username, role, is_active, created_at FROM users WHERE id = ?",
        [int(current_user["sub"])],
    ).fetchall()

    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    user_data = user[0]
    from app.schemas import RoleEnum
    user = UserResponse(
        id=user_data[0],
        username=user_data[1],
        role=RoleEnum(user_data[2]),
        is_active=user_data[3],
        created_at=user_data[4],
    )
    return SingleUserResponse(data=user)
