import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Enum as SAEnum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


class QuizDifficulty(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class QuizType(str, enum.Enum):
    mcq = "mcq"
    short_answer = "short_answer"
    mixed = "mixed"


class QuizStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    completed = "completed"


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    material_id = Column(
        UUID(as_uuid=True),
        ForeignKey("learning_materials.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title = Column(String(500), nullable=False)
    topic = Column(String(255), nullable=False)
    difficulty = Column(SAEnum(QuizDifficulty), nullable=False, default=QuizDifficulty.medium)
    quiz_type = Column(SAEnum(QuizType), nullable=False, default=QuizType.mcq)
    status = Column(SAEnum(QuizStatus), nullable=False, default=QuizStatus.active)
    total_questions = Column(Integer, nullable=False, default=0)
    created_at = Column(
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
    user = relationship("User", back_populates="quizzes")
    material = relationship("LearningMaterial", back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan", order_by="Question.order_index")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Quiz id={self.id} title={self.title} difficulty={self.difficulty}>"
