"""Authentication use cases, separated from HTTP and database details."""

from fastapi import HTTPException, status

from app.core.security import create_access_token, hash_password, verify_password
from app.database.models.user import User, UserRole
from app.database.repositories.user_repository import UserRepository
from app.schemas.auth import AccessTokenResponse, RegisterRequest, UserResponse


class AccountAlreadyExists(Exception):
    """Raised when an email address is already registered."""


class InvalidCredentials(Exception):
    """Raised when an email/password pair is not valid."""


class AuthService:
    def __init__(self, users: UserRepository):
        self.users = users

    async def register(self, request: RegisterRequest) -> User:
        email = str(request.email).strip().lower()
        if await self.users.get_by_email(email):
            raise AccountAlreadyExists
        return await self.users.create(
            email=email,
            hashed_password=hash_password(request.password),
            full_name=request.full_name,
            role=UserRole.student,
        )

    async def login(self, email: str, password: str) -> AccessTokenResponse:
        user = await self.users.get_by_email(email.strip().lower())
        # Use the same response for unknown users and bad passwords to avoid
        # revealing which email addresses have accounts.
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentials
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )

        access_token = create_access_token({"sub": str(user.id)})
        return AccessTokenResponse(
            access_token=access_token,
            user=UserResponse.model_validate(user),
        )
