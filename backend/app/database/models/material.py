import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, BigInteger, Enum as SAEnum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


class MaterialStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class LearningMaterial(Base):
    __tablename__ = "learning_materials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False, default="application/pdf")
    status = Column(SAEnum(MaterialStatus), nullable=False, default=MaterialStatus.pending)
    total_chunks = Column(Integer, nullable=True)
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
    user = relationship("User", back_populates="materials")
    chunks = relationship("MaterialChunk", back_populates="material", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="material")

    def __repr__(self) -> str:
        return f"<LearningMaterial id={self.id} title={self.title} status={self.status}>"
