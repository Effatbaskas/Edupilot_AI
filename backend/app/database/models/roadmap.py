import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, Boolean, Date, Text, Enum as SAEnum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


class TaskType(str, enum.Enum):
    learn = "learn"
    practice = "practice"
    review = "review"
    assessment = "assessment"


class TaskPriority(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"


class TaskStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    skipped = "skipped"


class Roadmap(Base):
    __tablename__ = "roadmaps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    exam_date = Column(Date, nullable=True)
    daily_hours = Column(Float, nullable=False, default=2.0)
    target_score = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    generated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="roadmap")
    tasks = relationship("StudyTask", back_populates="roadmap", cascade="all, delete-orphan", order_by="StudyTask.day_number")

    def __repr__(self) -> str:
        return f"<Roadmap id={self.id} user_id={self.user_id}>"


class StudyTask(Base):
    __tablename__ = "study_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roadmap_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roadmaps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_number = Column(Integer, nullable=False)
    topic = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=True)
    task_type = Column(SAEnum(TaskType), nullable=False, default=TaskType.learn)
    duration_minutes = Column(Integer, nullable=False, default=60)
    priority = Column(SAEnum(TaskPriority), nullable=False, default=TaskPriority.medium)
    status = Column(SAEnum(TaskStatus), nullable=False, default=TaskStatus.pending)
    description = Column(Text, nullable=True)
    is_ai_generated = Column(Boolean, default=True, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    roadmap = relationship("Roadmap", back_populates="tasks")

    def __repr__(self) -> str:
        return f"<StudyTask id={self.id} day={self.day_number} topic={self.topic} status={self.status}>"
