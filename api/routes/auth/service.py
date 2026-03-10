from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from db.models import User
from api.deps import verify_password, hash_password
from .schemas import UserRegister


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or user.password_hash is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def register_preentered_user(db: Session, registration_data: UserRegister) -> User:
    # 1. Check if the user was pre-entered by an admin
    user = db.query(User).filter(User.email == registration_data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This email has not been invited. Please contact an administrator."
        )
    
    # 2. Check if they have already set a password
    if user.password_hash is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account already exists. Please log in instead."
        )
    
    # 3. Update the user with their new password
    user.password_hash = hash_password(registration_data.password)
    # user.is_active = True  # Optional: set to True if you use an active flag
    
    db.commit()
    db.refresh(user)
    return user