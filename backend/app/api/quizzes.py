"""Quiz generation and scoring. Deterministic mock generation needs no paid AI key."""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.database.connection import get_db
from app.database.models.attempt import QuizAttempt
from app.database.models.material import LearningMaterial
from app.database.models.material_chunk import MaterialChunk
from app.database.models.performance import Performance
from app.database.models.question import Question, QuestionType
from app.database.models.quiz import Quiz, QuizDifficulty, QuizStatus, QuizType
from app.database.models.user import User

router = APIRouter(prefix="/quiz", tags=["Quizzes"])

class GeneratePayload(BaseModel):
    topic: str = Field(min_length=2, max_length=255)
    material_id: UUID | None = None
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    num_questions: int = Field(default=5, ge=1, le=20)
    quiz_type: str = Field(default="mcq", pattern="^(mcq|short_answer|mixed)$")

class SubmitPayload(BaseModel):
    answers: dict[str, str]
    time_taken_seconds: int | None = Field(default=None, ge=0, le=86400)


def _mock_questions(topic: str, count: int, difficulty: str, source: str, quiz_type: str):
    """Clearly labelled educational template questions for offline development."""
    snippets = [s.strip() for s in source.split(".") if len(s.strip()) > 25]
    concepts = snippets[:count]
    questions = []
    for i in range(count):
        concept = concepts[i % len(concepts)] if concepts else f"{topic} is the subject being studied"
        question = f"Which statement best reflects this {topic} concept: {concept[:180]}?"
        correct = concept[:220] if snippets else f"A core idea related to {topic} that should be reviewed in the study material"
        question_type = "short_answer" if quiz_type == "short_answer" or (quiz_type == "mixed" and i % 2 == 1) else "mcq"
        questions.append({"question_text": question, "question_type": question_type,
            "options": None if question_type == "short_answer" else [correct, "It describes an unrelated concept", "It contradicts the concept", "None of these statements"],
            "correct_answer": correct, "explanation": f"Review the source material about {topic}: {concept[:300]}.",
            "topic": topic, "difficulty": difficulty, "order_index": i})
    return questions


@router.post("/generate", status_code=201)
async def generate_quiz(payload: GeneratePayload, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    source = ""
    if payload.material_id:
        material = await db.scalar(select(LearningMaterial).where(LearningMaterial.id == payload.material_id, LearningMaterial.user_id == user.id))
        if not material:
            raise HTTPException(404, "Material not found")
        chunks = (await db.scalars(select(MaterialChunk).where(MaterialChunk.material_id == material.id, MaterialChunk.user_id == user.id).order_by(MaterialChunk.chunk_index))).all()
        source = " ".join(c.content for c in chunks)
    items = _mock_questions(payload.topic, payload.num_questions, payload.difficulty, source, payload.quiz_type)
    quiz = Quiz(user_id=user.id, material_id=payload.material_id, title=f"{payload.topic} Practice Quiz", topic=payload.topic,
        difficulty=QuizDifficulty(payload.difficulty), quiz_type=QuizType(payload.quiz_type), status=QuizStatus.active, total_questions=len(items))
    db.add(quiz)
    await db.flush()
    for item in items:
        db.add(Question(quiz_id=quiz.id, question_text=item["question_text"], question_type=QuestionType(item["question_type"]),
            options=item["options"], correct_answer=item["correct_answer"], explanation=item["explanation"],
            topic=item["topic"], difficulty=item["difficulty"], order_index=item["order_index"]))
    await db.flush()
    return await _quiz_payload(db, quiz)


async def _quiz_payload(db, quiz):
    qs = (await db.scalars(select(Question).where(Question.quiz_id == quiz.id).order_by(Question.order_index))).all()
    return {"id": str(quiz.id), "user_id": str(quiz.user_id), "material_id": str(quiz.material_id) if quiz.material_id else None,
        "title": quiz.title, "topic": quiz.topic, "difficulty": quiz.difficulty.value, "quiz_type": quiz.quiz_type.value,
        "status": quiz.status.value, "total_questions": quiz.total_questions, "created_at": quiz.created_at,
        "updated_at": quiz.updated_at, "questions": [{"id": str(q.id), "question_text": q.question_text,
        "question_type": q.question_type.value, "options": q.options, "topic": q.topic, "difficulty": q.difficulty,
        "order_index": q.order_index} for q in qs]}


@router.get("/")
async def list_quizzes(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    quizzes = (await db.scalars(select(Quiz).where(Quiz.user_id == user.id).order_by(Quiz.created_at.desc()))).all()
    return [await _quiz_payload(db, q) for q in quizzes]


@router.get("/history")
async def quiz_history(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    """Return only completed attempts belonging to the signed-in student."""
    rows = (await db.execute(
        select(QuizAttempt, Quiz)
        .join(Quiz, Quiz.id == QuizAttempt.quiz_id)
        .where(Quiz.user_id == user.id, QuizAttempt.user_id == user.id, QuizAttempt.completed_at.is_not(None))
        .order_by(QuizAttempt.completed_at.desc())
        .limit(50)
    )).all()
    return [{
        "attempt_id": str(attempt.id),
        "quiz_id": str(quiz.id),
        "title": quiz.title,
        "topic": quiz.topic,
        "score": attempt.score,
        "correct_count": attempt.correct_count,
        "total_questions": attempt.total_questions,
        "completed_at": attempt.completed_at,
    } for attempt, quiz in rows]


@router.get("/{quiz_id}")
async def get_quiz(quiz_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    quiz = await db.scalar(select(Quiz).where(Quiz.id == quiz_id, Quiz.user_id == user.id))
    if not quiz: raise HTTPException(404, "Quiz not found")
    return await _quiz_payload(db, quiz)


@router.post("/{quiz_id}/submit")
async def submit_quiz(quiz_id: UUID, payload: SubmitPayload, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    quiz = await db.scalar(select(Quiz).where(Quiz.id == quiz_id, Quiz.user_id == user.id))
    if not quiz: raise HTTPException(404, "Quiz not found")
    existing = await db.scalar(select(QuizAttempt.id).where(QuizAttempt.quiz_id == quiz.id, QuizAttempt.user_id == user.id, QuizAttempt.completed_at.is_not(None)))
    if existing:
        raise HTTPException(409, "This quiz has already been submitted. Generate a new quiz to try again.")
    questions = (await db.scalars(select(Question).where(Question.quiz_id == quiz.id).order_by(Question.order_index))).all()
    question_ids = {str(q.id) for q in questions}
    if set(payload.answers) - question_ids:
        raise HTTPException(422, "Answers contain question IDs that do not belong to this quiz")
    if not questions: raise HTTPException(409, "Quiz has no questions")
    results, correct, topic_stats = [], 0, {}
    for q in questions:
        answer = payload.answers.get(str(q.id), "").strip()
        is_correct = answer.casefold() == q.correct_answer.strip().casefold()
        correct += int(is_correct)
        topic = q.topic or quiz.topic
        stats = topic_stats.setdefault(topic, [0, 0]); stats[0] += int(is_correct); stats[1] += 1
        results.append({"question_id": str(q.id), "question_text": q.question_text, "your_answer": answer,
            "correct_answer": q.correct_answer, "is_correct": is_correct, "explanation": q.explanation, "topic": topic})
    score = round(correct / len(questions) * 100, 2)
    now = datetime.now(timezone.utc)
    attempt = QuizAttempt(quiz_id=quiz.id, user_id=user.id, answers=payload.answers, score=score,
        total_questions=len(questions), correct_count=correct, time_taken_seconds=payload.time_taken_seconds, completed_at=now)
    db.add(attempt)
    for topic, (c, total) in topic_stats.items():
        perf = await db.scalar(select(Performance).where(Performance.user_id == user.id, Performance.topic == topic))
        if perf:
            perf.correct_count += c; perf.total_count += total
            perf.score_percentage = round(perf.correct_count / perf.total_count * 100, 2); perf.last_attempt_at = now
        else:
            db.add(Performance(user_id=user.id, topic=topic, correct_count=c, total_count=total,
                score_percentage=round(c/total*100, 2), last_attempt_at=now))
    quiz.status = QuizStatus.completed
    await db.flush()
    weak = [t for t, (c, n) in topic_stats.items() if c/n < .6]
    strong = [t for t, (c, n) in topic_stats.items() if c/n >= .8]
    return {"attempt_id": str(attempt.id), "quiz_id": str(quiz.id), "score": score,
        "correct_count": correct, "total_questions": len(questions), "time_taken_seconds": payload.time_taken_seconds,
        "results": results, "weak_topics": weak, "strong_topics": strong, "completed_at": now}
