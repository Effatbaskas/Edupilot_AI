import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Text, Enum as SAEnum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship

from app.database.base import Base


class QuestionType(str, enum.Enum):
    mcq = "mcq"
    short_answer = "short_answer"


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id = Column(
        UUID(as_uuid=True),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_text = Column(Text, nullable=False)
    question_type = Column(SAEnum(QuestionType), nullable=False, default=QuestionType.mcq)
    options = Column(JSON, nullable=True)  # list of strings for MCQ
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    topic = Column(String(255), nullable=True)
    difficulty = Column(String(50), nullable=True)
    order_index = Column(Integer, nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")

    def __repr__(self) -> str:
        return f"<Question id={self.id} quiz_id={self.quiz_id} type={self.question_type}>"
