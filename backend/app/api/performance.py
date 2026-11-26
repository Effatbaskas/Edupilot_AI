"""Performance analytics derived from persisted quiz attempts."""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_active_user
from app.database.connection import get_db
from app.database.models.attempt import QuizAttempt
from app.database.models.performance import Performance
from app.database.models.user import User

router = APIRouter(prefix="/performance", tags=["Performance"])

@router.get("/overview")
async def overview(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    attempts = (await db.scalars(select(QuizAttempt).where(QuizAttempt.user_id == user.id, QuizAttempt.completed_at.is_not(None)).order_by(QuizAttempt.completed_at.asc()))).all()
    topics = (await db.scalars(select(Performance).where(Performance.user_id == user.id).order_by(Performance.score_percentage.desc()))).all()
    scores = [a.score for a in attempts if a.score is not None]
    recent = scores[-3:]; previous = scores[-6:-3]
    trend = "stable"
    if recent and previous:
        delta = sum(recent)/len(recent) - sum(previous)/len(previous)
        trend = "improving" if delta >= 5 else "declining" if delta <= -5 else "stable"
    return {"avg_score": round(sum(scores)/len(scores), 2) if scores else 0,
        "total_quizzes": len({str(a.quiz_id) for a in attempts}), "total_attempts": len(attempts),
        "strong_topics": [p.topic for p in topics if p.score_percentage >= 80],
        "weak_topics": [p.topic for p in topics if p.score_percentage < 60], "recent_trend": trend,
        "topics": [{"topic": p.topic, "score_pct": p.score_percentage, "attempts": 0,
            "correct_count": p.correct_count, "total_count": p.total_count, "last_attempt": p.last_attempt_at} for p in topics]}

@router.get("/topics")
async def topic_performance(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    rows = (await db.scalars(select(Performance).where(Performance.user_id == user.id).order_by(Performance.score_percentage.asc()))).all()
    return [{"topic": p.topic, "score_pct": p.score_percentage, "attempts": p.total_count,
             "correct_count": p.correct_count, "total_count": p.total_count, "last_attempt": p.last_attempt_at} for p in rows]

@router.get("/misconceptions")
async def misconceptions(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    rows = (await db.scalars(select(Performance).where(Performance.user_id == user.id, Performance.score_percentage < 60).order_by(Performance.score_percentage.asc()))).all()
    return [{"topic": p.topic, "score_percentage": p.score_percentage, "attempts": p.total_count,
        "pattern": "Low accuracy across recorded quiz answers", "evidence": f"{p.correct_count} correct out of {p.total_count}",
        "suggestion": f"Review the fundamentals of {p.topic} and retry a short practice quiz."} for p in rows]
