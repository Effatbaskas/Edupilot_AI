import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship

from app.database.base import Base


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id = Column(
        UUID(as_uuid=True),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    answers = Column(JSON, nullable=False)  # {question_id: answer}
    score = Column(Float, nullable=True)
    total_questions = Column(Integer, nullable=False)
    correct_count = Column(Integer, nullable=True)
    time_taken_seconds = Column(Integer, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    quiz = relationship("Quiz", back_populates="attempts")
    user = relationship("User", back_populates="quiz_attempts")

    def __repr__(self) -> str:
        return f"<QuizAttempt id={self.id} quiz_id={self.quiz_id} score={self.score}>"
