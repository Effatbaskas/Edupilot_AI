"""Registration, login, and current-user endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.database.connection import get_db
from app.database.models.user import User
from app.database.repositories.user_repository import UserRepository
from app.schemas.auth import AccessTokenResponse, RegisterRequest, UserResponse
from app.services.auth_service import (
    AccountAlreadyExists,
    AuthService,
    InvalidCredentials,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuthService:
    return AuthService(UserRepository(db))


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    try:
        return await service.register(payload)
    except AccountAlreadyExists as exc:
        raise HTTPException(status_code=409, detail="An account with this email already exists") from exc
    except IntegrityError as exc:
        # Handles simultaneous requests that race past the duplicate check.
        await service.users.db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists") from exc


@router.post("/login", response_model=AccessTokenResponse)
async def login(
    credentials: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> AccessTokenResponse:
    try:
        return await service.login(credentials.username, credentials.password)
    except InvalidCredentials as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    return current_user
