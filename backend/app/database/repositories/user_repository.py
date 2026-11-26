from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User, UserRole
from app.database.models.quiz import Quiz
from app.database.models.attempt import QuizAttempt
from app.database.models.material import LearningMaterial
from app.schemas.user import UserWithStats


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(func.lower(User.email) == email.strip().lower())
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        hashed_password: str,
        full_name: str,
        role: UserRole = UserRole.student,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=UserRole(role),
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        result = await self.db.execute(
            select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_with_stats(self, user_id: UUID) -> Optional[UserWithStats]:
        user = await self.get_by_id(user_id)
        if not user:
            return None

        # Count materials
        mat_result = await self.db.execute(
            select(func.count(LearningMaterial.id)).where(LearningMaterial.user_id == user_id)
        )
        total_materials = mat_result.scalar() or 0

        # Count quizzes
        quiz_result = await self.db.execute(
            select(func.count(Quiz.id)).where(Quiz.user_id == user_id)
        )
        total_quizzes = quiz_result.scalar() or 0

        # Count attempts + avg score
        attempt_result = await self.db.execute(
            select(func.count(QuizAttempt.id), func.avg(QuizAttempt.score)).where(
                QuizAttempt.user_id == user_id
            )
        )
        row = attempt_result.one()
        total_attempts = row[0] or 0
        avg_score = round(float(row[1]), 2) if row[1] else None

        return UserWithStats(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at,
            total_materials=total_materials,
            total_quizzes=total_quizzes,
            total_attempts=total_attempts,
            avg_score=avg_score,
        )

    async def count_all(self) -> int:
        result = await self.db.execute(select(func.count(User.id)))
        return result.scalar() or 0
