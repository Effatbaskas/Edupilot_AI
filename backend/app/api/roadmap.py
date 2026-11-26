"""Rule-based personalized study roadmap CRUD."""
from datetime import date, datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_active_user
from app.database.connection import get_db
from app.database.models.performance import Performance
from app.database.models.roadmap import Roadmap, StudyTask, TaskPriority, TaskStatus, TaskType
from app.database.models.user import User

router = APIRouter(prefix="/roadmap", tags=["Learning Roadmap"])
class GeneratePayload(BaseModel):
    exam_date: date | None = None
    daily_hours: float = Field(default=2, gt=0, le=12)
    target_score: float | None = Field(default=None, ge=0, le=100)
    weak_topics: list[str] | None = None
class UpdatePayload(BaseModel):
    status: str = Field(pattern="^(pending|in_progress|completed|skipped)$")

async def _payload(db, roadmap):
    tasks = (await db.scalars(select(StudyTask).where(StudyTask.roadmap_id == roadmap.id).order_by(StudyTask.day_number))).all()
    return {"id": str(roadmap.id), "user_id": str(roadmap.user_id), "exam_date": roadmap.exam_date,
        "daily_hours": roadmap.daily_hours, "target_score": roadmap.target_score, "is_active": roadmap.is_active,
        "generated_at": roadmap.generated_at, "updated_at": roadmap.updated_at,
        "tasks": [{"id": str(t.id), "roadmap_id": str(t.roadmap_id), "day_number": t.day_number, "topic": t.topic,
            "subject": t.subject, "task_type": t.task_type.value, "duration_minutes": t.duration_minutes,
            "priority": t.priority.value, "status": t.status.value, "description": t.description,
            "is_ai_generated": t.is_ai_generated, "completed_at": t.completed_at, "created_at": t.created_at} for t in tasks],
        "total_days": max([t.day_number for t in tasks], default=0),
        "prioritization_explanation": "Rule-based mock plan: lower-performing topics are scheduled first; remaining time is reserved for practice and review."}

@router.get("/")
async def get_roadmap(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    roadmap = await db.scalar(select(Roadmap).where(Roadmap.user_id == user.id, Roadmap.is_active.is_(True)))
    if not roadmap: return {"roadmap": None, "message": "No roadmap generated yet"}
    return await _payload(db, roadmap)

@router.post("/generate", status_code=201)
async def generate_roadmap(payload: GeneratePayload, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    if payload.exam_date and payload.exam_date <= date.today(): raise HTTPException(422, "exam_date must be in the future")
    rows = (await db.scalars(select(Performance).where(Performance.user_id == user.id).order_by(Performance.score_percentage.asc()))).all()
    topics = payload.weak_topics or [p.topic for p in rows if p.score_percentage < 80]
    if not topics: topics = ["Foundational concepts", "Core subject practice", "Revision"]
    topics = list(dict.fromkeys(t.strip() for t in topics if t.strip()))[:20]
    roadmap = await db.scalar(select(Roadmap).where(Roadmap.user_id == user.id))
    if roadmap:
        roadmap.exam_date = payload.exam_date; roadmap.daily_hours = payload.daily_hours; roadmap.target_score = payload.target_score
        roadmap.is_active = True
        await db.execute(__import__('sqlalchemy').delete(StudyTask).where(StudyTask.roadmap_id == roadmap.id))
    else:
        roadmap = Roadmap(user_id=user.id, exam_date=payload.exam_date, daily_hours=payload.daily_hours, target_score=payload.target_score)
        db.add(roadmap); await db.flush()
    minutes = int(payload.daily_hours * 60)
    for index, topic in enumerate(topics):
        score = next((p.score_percentage for p in rows if p.topic == topic), 100)
        priority = TaskPriority.high if score < 60 else TaskPriority.medium if score < 80 else TaskPriority.low
        db.add(StudyTask(roadmap_id=roadmap.id, day_number=index+1, topic=topic,
            task_type=TaskType.learn if index == 0 else TaskType.practice if index % 2 else TaskType.review,
            duration_minutes=minutes, priority=priority, description=f"Study {topic}; complete focused notes and practice questions.", is_ai_generated=False))
    await db.flush()
    return await _payload(db, roadmap)

@router.patch("/tasks/{task_id}")
async def update_task(task_id: UUID, payload: UpdatePayload, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    task = await db.scalar(select(StudyTask).join(Roadmap).where(StudyTask.id == task_id, Roadmap.user_id == user.id))
    if not task: raise HTTPException(404, "Task not found")
    task.status = TaskStatus(payload.status)
    task.completed_at = datetime.now(timezone.utc) if task.status == TaskStatus.completed else None
    await db.flush()
    return {"id": str(task.id), "status": task.status.value, "completed_at": task.completed_at}
