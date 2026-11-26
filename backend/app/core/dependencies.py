from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.database.connection import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Decode the JWT and return the authenticated User object."""
    from app.database.repositories.user_repository import UserRepository

    payload = decode_token(token, expected_type="access")
    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    repo = UserRepository(db)
    try:
        parsed_user_id = UUID(user_id)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = await repo.get_by_id(parsed_user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
    current_user=Depends(get_current_user),
):
    """Ensure the authenticated user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return current_user


def require_role(*roles: str):
    """Factory: returns a dependency that checks the user has one of the given roles."""

    async def role_dependency(current_user=Depends(get_current_active_user)):
        if current_user.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {list(roles)}",
            )
        return current_user

    return role_dependency


# Role shortcuts
get_current_student = require_role("student")
get_current_teacher = require_role("teacher", "admin")
get_current_admin = require_role("admin")
