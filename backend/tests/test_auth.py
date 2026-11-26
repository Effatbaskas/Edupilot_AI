from collections.abc import AsyncIterator
from types import SimpleNamespace
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.dependencies import get_db
from app.core.security import create_access_token, create_refresh_token, hash_password
from app.database.models.user import User, UserRole
from app.main import app


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        # Auth tests need only the users table; full metadata includes the
        # PostgreSQL-only vector column used by learning materials.
        await connection.run_sync(User.__table__.create)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        test_client.test_session_factory = session_factory
        yield test_client
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_docs_endpoint_is_available(client: AsyncClient) -> None:
    response = await client.get("/docs")
    assert response.status_code == 200
    assert "EduPilot AI API" in response.text


@pytest.mark.asyncio
async def test_register_login_and_access_token_authentication(client: AsyncClient) -> None:
    registration = await client.post(
        "/api/v1/auth/register",
        json={"email": "Student@Example.com", "password": "correct-horse-123", "full_name": "  A Student  "},
    )
    assert registration.status_code == 201
    assert registration.json()["email"] == "student@example.com"
    assert registration.json()["full_name"] == "A Student"
    assert registration.json()["role"] == "student"

    login = await client.post(
        "/api/v1/auth/login",
        data={"username": "student@example.com", "password": "correct-horse-123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert token
    assert "hashed_password" not in login.json()["user"]

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "student@example.com"


@pytest.mark.asyncio
async def test_registration_rejects_privileged_roles_and_duplicate_email(client: AsyncClient) -> None:
    for role in ("admin", "teacher"):
        forbidden_role = await client.post(
            "/api/v1/auth/register",
            json={"email": f"{role}@example.com", "password": "correct-horse-123", "full_name": role, "role": role},
        )
        assert forbidden_role.status_code == 422

    body = {"email": "repeat@example.com", "password": "correct-horse-123", "full_name": "Repeat"}
    assert (await client.post("/api/v1/auth/register", json=body)).status_code == 201
    duplicate = await client.post("/api/v1/auth/register", json=body)
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_invalid_credentials_and_invalid_or_wrong_type_jwt_are_rejected(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "student@example.com", "password": "correct-horse-123", "full_name": "Student"},
    )
    bad_password = await client.post(
        "/api/v1/auth/login",
        data={"username": "student@example.com", "password": "incorrect-password"},
    )
    assert bad_password.status_code == 401

    invalid_token = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert invalid_token.status_code == 401

    refresh = create_refresh_token({"sub": str(uuid4())})
    wrong_type = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {refresh}"})
    assert wrong_type.status_code == 401


@pytest.mark.asyncio
async def test_admin_route_rejects_students(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "student@example.com", "password": "correct-horse-123", "full_name": "Student"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": "student@example.com", "password": "correct-horse-123"},
    )
    denied = await client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_admin_route_allows_a_trusted_admin_account(client: AsyncClient) -> None:
    session_factory = client.test_session_factory
    async with session_factory() as session:
        admin = User(
            email="trusted-admin@example.com",
            hashed_password=hash_password("correct-horse-123"),
            full_name="Trusted Admin",
            role=UserRole.admin,
        )
        session.add(admin)
        await session.commit()
        admin_id = str(admin.id)

    token = create_access_token({"sub": admin_id})
    response = await client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert any(item["email"] == "trusted-admin@example.com" for item in response.json())


@pytest.mark.asyncio
async def test_admin_can_assign_teacher_role_but_cannot_demote_self(client: AsyncClient) -> None:
    session_factory = client.test_session_factory
    async with session_factory() as session:
        admin = User(
            email="trusted-admin@example.com",
            hashed_password=hash_password("correct-horse-123"),
            full_name="Trusted Admin",
            role=UserRole.admin,
        )
        teacher_candidate = User(
            email="teacher-candidate@example.com",
            hashed_password=hash_password("correct-horse-123"),
            full_name="Teacher Candidate",
            role=UserRole.student,
        )
        session.add_all([admin, teacher_candidate])
        await session.commit()
        admin_id = str(admin.id)
        candidate_id = str(teacher_candidate.id)

    token = create_access_token({"sub": admin_id})
    headers = {"Authorization": f"Bearer {token}"}
    promotion = await client.put(
        f"/api/v1/admin/users/{candidate_id}/role",
        json={"role": "teacher"},
        headers=headers,
    )
    assert promotion.status_code == 200
    assert promotion.json()["role"] == "teacher"

    self_demotion = await client.put(
        f"/api/v1/admin/users/{admin_id}/role",
        json={"role": "teacher"},
        headers=headers,
    )
    assert self_demotion.status_code == 409


@pytest.mark.asyncio
async def test_role_dependencies_enforce_student_teacher_and_admin_roles(client: AsyncClient) -> None:
    from app.core.dependencies import get_current_admin, get_current_student, get_current_teacher

    async def allowed(dependency, role: UserRole) -> bool:
        identity = SimpleNamespace(role=role, is_active=True)
        try:
            await dependency(current_user=identity)
            return True
        except HTTPException:
            return False

    assert await allowed(get_current_student, UserRole.student)
    assert await allowed(get_current_teacher, UserRole.teacher)
    assert await allowed(get_current_admin, UserRole.admin)
    assert not await allowed(get_current_student, UserRole.teacher)
    assert not await allowed(get_current_teacher, UserRole.student)
    assert not await allowed(get_current_admin, UserRole.teacher)
