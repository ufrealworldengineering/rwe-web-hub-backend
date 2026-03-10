from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.deps import get_db
from api.schemas.schemas import UserCreate, UserUpdate, UserResponse
from . import service as user_service   

from api.deps import require_roles
from db.models import UserRole, User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_roles([UserRole.president, UserRole.treasurer])),
    db: Session = Depends(get_db),
):
    return user_service.get_users(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    current_user: User = Depends(require_roles([UserRole.president, UserRole.treasurer])),
    db: Session = Depends(get_db)
):
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.get("/email/{email}", response_model=UserResponse)
def get_user_by_email(
    email: str,
    current_user: User = Depends(require_roles([UserRole.president, UserRole.treasurer])),
    db: Session = Depends(get_db)
):
    """Get a user by email"""
    user = user_service.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    current_user: User = Depends(require_roles([UserRole.president])),
    db: Session = Depends(get_db)
):
    return user_service.create_user(db, user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    current_user: User = Depends(require_roles([UserRole.president])),
    db: Session = Depends(get_db)
):
    user = user_service.update_user(db, user_id, user_update)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_roles([UserRole.president])),
    db: Session = Depends(get_db)
):
    success = user_service.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")