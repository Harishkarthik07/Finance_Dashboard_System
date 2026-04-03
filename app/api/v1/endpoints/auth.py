from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user import LoginRequest, TokenResponse, UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201,
             summary="Register a new user (default role: viewer)")
def register(data: UserCreate, db: Annotated[Session, Depends(get_db)]):
    # Public registration always creates a VIEWER; role assignment is admin-only
    from app.models.user import UserRole
    data.role = UserRole.VIEWER
    return UserService.create_user(db, data)


@router.post("/login", response_model=TokenResponse, summary="Login and receive JWT token")
def login(data: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    return UserService.login(db, data.email, data.password)
