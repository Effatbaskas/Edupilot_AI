"""Administrator-only user management endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin
from app.database.connection import get_db
from app.database.models.user import User, UserRole
from app.database.repositories.user_repository import UserRepository
from app.schemas.auth import UserResponse
from app.schemas.user import RoleUpdateRequest

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    current_admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[User]:
    return await UserRepository(db).list_all(skip=skip, limit=limit)


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: str,
    payload: RoleUpdateRequest,
    current_admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    from uuid import UUID

    try:
        parsed_id = UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid user ID") from exc

    users = UserRepository(db)
    target = await users.get_by_id(parsed_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == current_admin.id and payload.role != UserRole.admin.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An administrator cannot remove their own admin role",
        )
    return await users.update(target, role=UserRole(payload.role))
