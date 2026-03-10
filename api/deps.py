import hashlib
import base64
from collections.abc import Generator
from typing import Callable, Iterable

import bcrypt
from db.session import SessionLocal


def _prehash(password: str) -> bytes:
    """
    SHA-256 prehash → base64 encode → always 44 ASCII bytes.
    """
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(digest)  # 44 bytes, safe for bcrypt
from fastapi import Depends, HTTPException

from db.models import User, UserRole

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


def require_roles(required_roles: Iterable[UserRole]) -> Callable[..., User]:
    """
    Factory for role-based access control.

    Usage:
      current_user: User = Depends(require_roles([UserRole.president, ...]))
    """
    required = set(required_roles)

    # Import inside to avoid circular import: api.core.security -> api.deps(get_db)
    from api.core.security import get_current_active_user

    def _dep(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in required:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    return _dep