from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.performance import Performance


class PerformanceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert_topic_performance(
        self,
        user_id: UUID,
        topic: str,
        correct_delta: int,
        total_delta: int,
        subject: Optional[str] = None,
    ) -> Performance:
        """Upsert (insert or update) a Performance record for the given topic."""
        existing = await self.db.execute(
            select(Performance).where(
                Performance.user_id == user_id,
                Performance.topic == topic,
            )
        )
        perf = existing.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if perf:
            perf.correct_count += correct_delta
            perf.total_count += total_delta
            perf.score_percentage = (
                (perf.correct_count / perf.total_count * 100)
                if perf.total_count > 0
                else 0.0
            )
            perf.last_attempt_at = now
            if subject:
                perf.subject = subject
        else:
            score_pct = (correct_delta / total_delta * 100) if total_delta > 0 else 0.0
            perf = Performance(
                user_id=user_id,
                topic=topic,
                subject=subject,
                correct_count=correct_delta,
                total_count=total_delta,
                score_percentage=score_pct,
                last_attempt_at=now,
            )
            self.db.add(perf)

        await self.db.flush()
        await self.db.refresh(perf)
        return perf

    async def get_user_performance(self, user_id: UUID) -> List[Performance]:
        result = await self.db.execute(
            select(Performance)
            .where(Performance.user_id == user_id)
            .order_by(Performance.score_percentage.asc())
        )
        return list(result.scalars().all())

    async def get_weak_topics(self, user_id: UUID, threshold: float = 60.0) -> List[Performance]:
        result = await self.db.execute(
            select(Performance).where(
                Performance.user_id == user_id,
                Performance.score_percentage < threshold,
            ).order_by(Performance.score_percentage.asc())
        )
        return list(result.scalars().all())

    async def get_strong_topics(self, user_id: UUID, threshold: float = 80.0) -> List[Performance]:
        result = await self.db.execute(
            select(Performance).where(
                Performance.user_id == user_id,
                Performance.score_percentage >= threshold,
            ).order_by(Performance.score_percentage.desc())
        )
        return list(result.scalars().all())

    async def get_performance_trend(self, user_id: UUID) -> dict:
        """Return avg score and total attempts for the user."""
        result = await self.db.execute(
            select(
                func.avg(Performance.score_percentage),
                func.sum(Performance.total_count),
                func.count(Performance.id),
            ).where(Performance.user_id == user_id)
        )
        row = result.one()
        return {
            "avg_score": round(float(row[0] or 0), 2),
            "total_attempts": int(row[1] or 0),
            "total_topics": int(row[2] or 0),
        }
