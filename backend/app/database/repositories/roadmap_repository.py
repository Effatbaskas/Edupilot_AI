from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.roadmap import Roadmap, StudyTask, TaskStatus


class RoadmapRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_roadmap(self, user_id: UUID) -> Optional[Roadmap]:
        result = await self.db.execute(
            select(Roadmap)
            .where(Roadmap.user_id == user_id)
            .options(selectinload(Roadmap.tasks))
        )
        return result.scalar_one_or_none()

    async def create_or_update_roadmap(
        self,
        user_id: UUID,
        exam_date,
        daily_hours: float,
        target_score: Optional[float],
        tasks_data: List[dict],
    ) -> Roadmap:
        existing = await self.get_roadmap(user_id)

        # Collect completed task IDs to preserve
        completed_tasks = []
        if existing:
            completed_tasks = await self.preserve_completed_tasks(user_id)
            # Delete non-completed tasks
            await self.db.execute(
                delete(StudyTask).where(
                    StudyTask.roadmap_id == existing.id,
                    StudyTask.status.in_([TaskStatus.pending, TaskStatus.in_progress, TaskStatus.skipped]),
                )
            )
            existing.exam_date = exam_date
            existing.daily_hours = daily_hours
            existing.target_score = target_score
            existing.is_active = True
            existing.generated_at = datetime.now(timezone.utc)
            roadmap = existing
        else:
            roadmap = Roadmap(
                user_id=user_id,
                exam_date=exam_date,
                daily_hours=daily_hours,
                target_score=target_score,
                is_active=True,
            )
            self.db.add(roadmap)
            await self.db.flush()

        # Create new tasks
        for task_data in tasks_data:
            task = StudyTask(
                roadmap_id=roadmap.id,
                day_number=task_data["day_number"],
                topic=task_data["topic"],
                subject=task_data.get("subject"),
                task_type=task_data.get("task_type", "learn"),
                duration_minutes=task_data.get("duration_minutes", 60),
                priority=task_data.get("priority", "medium"),
                description=task_data.get("description"),
                is_ai_generated=task_data.get("is_ai_generated", True),
                status=TaskStatus.pending,
            )
            self.db.add(task)

        await self.db.flush()
        await self.db.refresh(roadmap)
        return roadmap

    async def get_tasks(self, roadmap_id: UUID) -> List[StudyTask]:
        result = await self.db.execute(
            select(StudyTask)
            .where(StudyTask.roadmap_id == roadmap_id)
            .order_by(StudyTask.day_number.asc())
        )
        return list(result.scalars().all())

    async def update_task_status(
        self,
        task_id: UUID,
        status: str,
        user_id: UUID,
    ) -> Optional[StudyTask]:
        # Verify ownership via roadmap
        result = await self.db.execute(
            select(StudyTask)
            .join(Roadmap, StudyTask.roadmap_id == Roadmap.id)
            .where(StudyTask.id == task_id, Roadmap.user_id == user_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            return None

        task.status = status
        if status == TaskStatus.completed.value:
            task.completed_at = datetime.now(timezone.utc)

        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def preserve_completed_tasks(self, user_id: UUID) -> List[StudyTask]:
        roadmap = await self.get_roadmap(user_id)
        if not roadmap:
            return []
        result = await self.db.execute(
            select(StudyTask).where(
                StudyTask.roadmap_id == roadmap.id,
                StudyTask.status == TaskStatus.completed,
            )
        )
        return list(result.scalars().all())
