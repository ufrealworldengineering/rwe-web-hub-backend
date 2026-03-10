"""
api.routes.auth.router
  POST /api/auth/login   – email + password → access + refresh tokens
  POST /api/auth/refresh – refresh token   → new access token
  GET  /api/auth/me      – current user info
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas.schemas import UserResponse
from api.core.security import (
    REFRESH_SECRET_KEY,
    create_access_token,
    create_refresh_token,
    get_current_active_user,
    verify_token,
)
from .service import authenticate_user, register_preentered_user
from db.models import User
from .schemas import Token, AccessToken, RefreshRequest, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    """Authenticate with email (username field) + password."""
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    return Token(
        access_token=create_access_token(subject=user.email),
        refresh_token=create_refresh_token(subject=user.email),
    )


@router.post("/refresh", response_model=AccessToken)
async def refresh_access_token(
    body: RefreshRequest,
    db: Annotated[Session, Depends(get_db)],  
) -> AccessToken:
    email = verify_token(body.refresh_token, REFRESH_SECRET_KEY, expected_type="refresh")
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    
    return AccessToken(access_token=create_access_token(subject=email))

@router.get("/me", response_model=UserResponse)
async def me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Return the currently authenticated user."""
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return None

@router.post("/register", response_model=UserResponse)
def register(
    registration_data: UserRegister,
    db: Session = Depends(get_db)
):
    """Allows a pre-entered user to set their password and activate their account."""
    return register_preentered_user(db, registration_data)