"""User endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ...db.models import User
from ...schemas.user import UserOut
from ..deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
