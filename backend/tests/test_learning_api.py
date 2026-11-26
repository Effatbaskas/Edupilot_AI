from collections.abc import AsyncIterator
from datetime import date, timedelta
from pathlib import Path

import fitz
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api import materials as materials_api
from app.core.dependencies import get_db
from app.database.base import Base
from app.database.models import __all_models__  # noqa: F401 - register all tables
from app.database.models.material_chunk import MaterialChunk
from app.main import app


@pytest_asyncio.fixture
async def learning_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> AsyncIterator[AsyncClient]:
    """Use an isolated SQLite database and temp storage, never a developer DB."""
    monkeypatch.setattr(MaterialChunk.__table__.c.embedding, "type", Text())
    monkeypatch.setattr(materials_api.settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

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
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
    await engine.dispose()


async def register_and_login(client: AsyncClient, email: str) -> str:
    registered = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "safe-test-password-123",
        "full_name": "Test Learner",
    })
    assert registered.status_code == 201
    logged_in = await client.post("/api/v1/auth/login", data={
        "username": email,
        "password": "safe-test-password-123",
    })
    assert logged_in.status_code == 200
    return logged_in.json()["access_token"]


@pytest.mark.asyncio
async def test_pdf_upload_is_saved_and_private_to_its_owner(learning_client: AsyncClient) -> None:
    owner_token = await register_and_login(learning_client, "owner@example.com")
    other_token = await register_and_login(learning_client, "other@example.com")
    headers = {"Authorization": f"Bearer {owner_token}"}

    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Water cycle study notes explain evaporation and condensation.")
    pdf_bytes = document.tobytes()
    document.close()

    uploaded = await learning_client.post(
        "/api/v1/materials/upload",
        files={"file": ("water-cycle.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert uploaded.status_code == 201
    material_id = uploaded.json()["id"]
    assert uploaded.json()["status"] == "ready"
    assert uploaded.json()["total_chunks"] >= 1

    owner_list = await learning_client.get("/api/v1/materials/", headers=headers)
    assert owner_list.status_code == 200
    assert any(item["id"] == material_id for item in owner_list.json()["materials"])
    search = await learning_client.get("/api/v1/materials/", params={"search": "water"}, headers=headers)
    assert search.status_code == 200
    assert any(item["id"] == material_id for item in search.json()["materials"])
    detail = await learning_client.get(f"/api/v1/materials/{material_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["title"] == "water-cycle"

    private_read = await learning_client.get(
        f"/api/v1/materials/{material_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert private_read.status_code == 404

    mock_reply = await learning_client.post(
        "/api/v1/tutor/chat",
        json={"question": "Explain evaporation", "language": "en"},
        headers=headers,
    )
    assert mock_reply.status_code == 200
    assert mock_reply.json()["mode"] == "mock"
    assert "Water cycle study notes" in mock_reply.json()["answer"]
    history = await learning_client.get(
        "/api/v1/tutor/history",
        params={"session_id": mock_reply.json()["session_id"]},
        headers=headers,
    )
    assert history.status_code == 200
    assert len(history.json()["messages"]) == 2
    private_history = await learning_client.get(
        "/api/v1/tutor/history",
        params={"session_id": mock_reply.json()["session_id"]},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert private_history.status_code == 200
    assert private_history.json()["messages"] == []
    deleted = await learning_client.delete(f"/api/v1/materials/{material_id}", headers=headers)
    assert deleted.status_code == 204
    missing = await learning_client.get(f"/api/v1/materials/{material_id}", headers=headers)
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_quiz_scoring_persists_attempt_and_updates_topic_performance(learning_client: AsyncClient) -> None:
    token = await register_and_login(learning_client, "quiz@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    generated = await learning_client.post(
        "/api/v1/quiz/generate",
        json={"topic": "Fractions", "difficulty": "easy", "num_questions": 2, "quiz_type": "mcq"},
        headers=headers,
    )
    assert generated.status_code == 201
    quiz = generated.json()
    answers = {question["id"]: question["options"][0] for question in quiz["questions"]}

    submitted = await learning_client.post(
        f"/api/v1/quiz/{quiz['id']}/submit",
        json={"answers": answers},
        headers=headers,
    )
    assert submitted.status_code == 200
    assert submitted.json()["score"] == 100
    assert submitted.json()["correct_count"] == 2

    duplicate = await learning_client.post(
        f"/api/v1/quiz/{quiz['id']}/submit",
        json={"answers": answers},
        headers=headers,
    )
    assert duplicate.status_code == 409

    progress = await learning_client.get("/api/v1/performance/overview", headers=headers)
    assert progress.status_code == 200
    assert progress.json()["total_quizzes"] == 1
    assert progress.json()["total_attempts"] == 1
    assert progress.json()["strong_topics"] == ["Fractions"]
    history = await learning_client.get("/api/v1/quiz/history", headers=headers)
    assert history.status_code == 200
    assert len(history.json()) == 1
    assert history.json()[0]["score"] == 100
    assert history.json()[0]["topic"] == "Fractions"
    other_token = await register_and_login(learning_client, "other-quiz@example.com")
    other_headers = {"Authorization": f"Bearer {other_token}"}
    private_quiz = await learning_client.get(f"/api/v1/quiz/{quiz['id']}", headers=other_headers)
    assert private_quiz.status_code == 404
    assert (await learning_client.get("/api/v1/quiz/history", headers=other_headers)).json() == []


@pytest.mark.asyncio
async def test_roadmap_uses_saved_weak_topic_performance_and_persists_task_updates(learning_client: AsyncClient) -> None:
    token = await register_and_login(learning_client, "roadmap@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    past_exam = await learning_client.post(
        "/api/v1/roadmap/generate",
        json={"exam_date": (date.today() - timedelta(days=1)).isoformat()},
        headers=headers,
    )
    assert past_exam.status_code == 422
    quiz_response = await learning_client.post(
        "/api/v1/quiz/generate",
        json={"topic": "Algebra", "difficulty": "easy", "num_questions": 2, "quiz_type": "mcq"},
        headers=headers,
    )
    quiz = quiz_response.json()
    wrong_answers = {question["id"]: question["options"][1] for question in quiz["questions"]}
    scored = await learning_client.post(
        f"/api/v1/quiz/{quiz['id']}/submit", json={"answers": wrong_answers}, headers=headers
    )
    assert scored.status_code == 200 and scored.json()["score"] == 0

    weak_topics = await learning_client.get("/api/v1/performance/topics", headers=headers)
    assert weak_topics.status_code == 200
    assert weak_topics.json()[0]["topic"] == "Algebra"
    assert weak_topics.json()[0]["score_pct"] == 0
    misconceptions = await learning_client.get("/api/v1/performance/misconceptions", headers=headers)
    assert misconceptions.status_code == 200
    assert misconceptions.json()[0]["topic"] == "Algebra"

    generated = await learning_client.post(
        "/api/v1/roadmap/generate",
        json={
            "exam_date": (date.today() + timedelta(days=30)).isoformat(),
            "daily_hours": 1.5,
            "target_score": 85,
            "weak_topics": [],
        },
        headers=headers,
    )
    assert generated.status_code == 201
    roadmap = generated.json()
    assert roadmap["tasks"]
    algebra_task = next(task for task in roadmap["tasks"] if task["topic"] == "Algebra")
    assert algebra_task["priority"] == "high"
    task_id = algebra_task["id"]

    invalid_status = await learning_client.patch(
        f"/api/v1/roadmap/tasks/{task_id}", json={"status": "finished"}, headers=headers
    )
    assert invalid_status.status_code == 422

    updated = await learning_client.patch(
        f"/api/v1/roadmap/tasks/{task_id}",
        json={"status": "completed"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "completed"

    saved = await learning_client.get("/api/v1/roadmap/", headers=headers)
    assert saved.status_code == 200
    assert any(task["id"] == task_id and task["status"] == "completed" for task in saved.json()["tasks"])
    other_token = await register_and_login(learning_client, "other-roadmap@example.com")
    private_update = await learning_client.patch(
        f"/api/v1/roadmap/tasks/{task_id}", json={"status": "skipped"},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert private_update.status_code == 404


@pytest.mark.asyncio
async def test_learning_routes_require_auth_and_upload_rejects_non_pdf(learning_client: AsyncClient) -> None:
    protected_paths = (
        "/api/v1/materials/", "/api/v1/quiz/", "/api/v1/quiz/history",
        "/api/v1/tutor/history", "/api/v1/tutor/sessions", "/api/v1/performance/overview",
        "/api/v1/performance/topics", "/api/v1/performance/misconceptions", "/api/v1/roadmap/",
    )
    for path in protected_paths:
        response = await learning_client.get(path)
        assert response.status_code == 401

    token = await register_and_login(learning_client, "file-check@example.com")
    rejected = await learning_client.post(
        "/api/v1/materials/upload",
        files={"file": ("notes.txt", b"not a PDF", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert rejected.status_code == 415


@pytest.mark.asyncio
async def test_material_upload_rejects_unreadable_empty_text_and_oversized_pdfs(
    learning_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    token = await register_and_login(learning_client, "invalid-pdf@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    unreadable = await learning_client.post(
        "/api/v1/materials/upload",
        files={"file": ("broken.pdf", b"not a PDF document", "application/pdf")},
        headers=headers,
    )
    assert unreadable.status_code == 422

    blank_document = fitz.open()
    blank_document.new_page()
    blank_pdf = blank_document.tobytes()
    blank_document.close()
    no_text = await learning_client.post(
        "/api/v1/materials/upload",
        files={"file": ("scan.pdf", blank_pdf, "application/pdf")},
        headers=headers,
    )
    assert no_text.status_code == 422

    monkeypatch.setattr(materials_api.settings, "MAX_FILE_SIZE_MB", 1)
    oversized = await learning_client.post(
        "/api/v1/materials/upload",
        files={"file": ("large.pdf", b"x" * (1024 * 1024 + 1), "application/pdf")},
        headers=headers,
    )
    assert oversized.status_code == 413


@pytest.mark.asyncio
async def test_tutor_sessions_and_empty_analytics_are_scoped_to_current_user(learning_client: AsyncClient) -> None:
    owner_token = await register_and_login(learning_client, "tutor-owner@example.com")
    other_token = await register_and_login(learning_client, "tutor-other@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}

    empty_overview = await learning_client.get("/api/v1/performance/overview", headers=other_headers)
    assert empty_overview.status_code == 200
    assert empty_overview.json()["total_quizzes"] == 0
    assert empty_overview.json()["avg_score"] == 0
    assert (await learning_client.get("/api/v1/performance/topics", headers=other_headers)).json() == []
    assert (await learning_client.get("/api/v1/performance/misconceptions", headers=other_headers)).json() == []
    assert (await learning_client.get("/api/v1/quiz/", headers=other_headers)).json() == []
    assert (await learning_client.get("/api/v1/roadmap/", headers=other_headers)).json()["roadmap"] is None

    sent = await learning_client.post(
        "/api/v1/tutor/chat", json={"question": "Explain cells", "language": "en"}, headers=owner_headers
    )
    assert sent.status_code == 200
    sessions = await learning_client.get("/api/v1/tutor/sessions", headers=owner_headers)
    assert sessions.status_code == 200
    assert len(sessions.json()) == 1
    assert "Explain cells" in sessions.json()[0]["preview"]
    assert (await learning_client.get("/api/v1/tutor/sessions", headers=other_headers)).json() == []


@pytest.mark.asyncio
async def test_quiz_types_payload_validation_and_saved_quiz_listing(learning_client: AsyncClient) -> None:
    token = await register_and_login(learning_client, "quiz-types@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    invalid = await learning_client.post(
        "/api/v1/quiz/generate",
        json={"topic": "Cells", "num_questions": 21, "quiz_type": "unknown"},
        headers=headers,
    )
    assert invalid.status_code == 422

    short_answer = await learning_client.post(
        "/api/v1/quiz/generate",
        json={"topic": "Cells", "num_questions": 2, "quiz_type": "short_answer"},
        headers=headers,
    )
    assert short_answer.status_code == 201
    quiz = short_answer.json()
    assert all(question["question_type"] == "short_answer" for question in quiz["questions"])
    assert all(question["options"] is None for question in quiz["questions"])

    unknown_question = await learning_client.post(
        f"/api/v1/quiz/{quiz['id']}/submit", json={"answers": {"not-a-question-id": "answer"}}, headers=headers
    )
    assert unknown_question.status_code == 422

    mixed = await learning_client.post(
        "/api/v1/quiz/generate",
        json={"topic": "Cells", "num_questions": 2, "quiz_type": "mixed"},
        headers=headers,
    )
    assert mixed.status_code == 201
    assert [q["question_type"] for q in mixed.json()["questions"]] == ["mcq", "short_answer"]

    saved = await learning_client.get("/api/v1/quiz/", headers=headers)
    assert saved.status_code == 200
    assert {item["id"] for item in saved.json()} == {quiz["id"], mixed.json()["id"]}
