import hashlib
import base64
from typing import Generator, List

import bcrypt
from db.session import SessionLocal


def _prehash(password: str) -> bytes:
    """
    SHA-256 prehash → base64 encode → always 44 ASCII bytes.
    """
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(digest)  # 44 bytes, safe for bcrypt

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
    """Hash a password using SHA-256 prehash + bcrypt."""
    hashed = bcrypt.hashpw(_prehash(password), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(_prehash(plain_password), hashed_password.encode("utf-8"))


async def get_current_user_with_role(
    required_roles: List[UserRole],
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role not in required_roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user