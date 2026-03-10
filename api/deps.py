from typing import Generator, List
from db.session import SessionLocal
from passlib.context import CryptContext

from fastapi import HTTPException, Depends
from db.models import UserRole, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

async def get_current_user_with_role(
    required_roles: List[UserRole],
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role not in required_roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user