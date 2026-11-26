import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


class Performance(Base):
    __tablename__ = "performances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    topic = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=True)
    correct_count = Column(Integer, nullable=False, default=0)
    total_count = Column(Integer, nullable=False, default=0)
    score_percentage = Column(Float, nullable=False, default=0.0)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="performances")

    __table_args__ = (
        UniqueConstraint("user_id", "topic", name="uq_user_topic_performance"),
    )

    def __repr__(self) -> str:
        return f"<Performance id={self.id} user_id={self.user_id} topic={self.topic} score={self.score_percentage}>"
