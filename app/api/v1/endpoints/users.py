from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import CurrentUser, require_admin
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse, summary="Get current user profile")
def get_me(current_user: CurrentUser):
    return current_user


@router.get("/", response_model=list[UserResponse], summary="List all users (admin only)")
def list_users(
    skip: int = 0,
    limit: int = 50,
    db: Annotated[Session, Depends(get_db)] = None,
    _: Annotated[User, Depends(require_admin)] = None,
):
    return UserService.list_users(db, skip=skip, limit=limit)


@router.post("/", response_model=UserResponse, status_code=201,
             summary="Create user with any role (admin only)")
def create_user(
    data: UserCreate,
    db: Annotated[Session, Depends(get_db)] = None,
    actor: Annotated[User, Depends(require_admin)] = None,
):
    return UserService.create_user(db, data)


@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID (admin only)")
def get_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)] = None,
    _: Annotated[User, Depends(require_admin)] = None,
):
    return UserService.get_user(db, user_id)


@router.patch("/{user_id}", response_model=UserResponse, summary="Update user (admin only)")
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Annotated[Session, Depends(get_db)] = None,
    actor: Annotated[User, Depends(require_admin)] = None,
):
    return UserService.update_user(db, user_id, data, actor)


@router.delete("/{user_id}", status_code=204, summary="Delete user (admin only)")
def delete_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)] = None,
    actor: Annotated[User, Depends(require_admin)] = None,
):
    UserService.delete_user(db, user_id, actor)
