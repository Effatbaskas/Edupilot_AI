"""Create the first administrator from a trusted local shell.

Run from the backend directory after configuring its private .env file:
    python scripts/create_admin.py
"""

import asyncio
import getpass

from app.database.connection import AsyncSessionLocal
from app.database.models.user import UserRole
from app.database.repositories.user_repository import UserRepository
from app.core.security import hash_password


async def create_admin(email: str, full_name: str, password: str) -> None:
    async with AsyncSessionLocal() as session:
        users = UserRepository(session)
        if await users.get_by_email(email):
            raise ValueError("An account with this email already exists")
        await users.create(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=UserRole.admin,
        )
        await session.commit()


def main() -> None:
    email = input("Administrator email: ").strip().lower()
    full_name = input("Administrator name: ").strip()
    password = getpass.getpass("Password (12 to 72 UTF-8 bytes): ")
    confirmation = getpass.getpass("Confirm password: ")
    if not email or not full_name:
        raise SystemExit("Email and name are required")
    if password != confirmation:
        raise SystemExit("Passwords do not match")
    if len(password) < 12 or len(password.encode("utf-8")) > 72:
        raise SystemExit("Password must be 12 to 72 UTF-8 bytes")
    try:
        asyncio.run(create_admin(email, full_name, password))
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print("Administrator account created.")


if __name__ == "__main__":
    main()
