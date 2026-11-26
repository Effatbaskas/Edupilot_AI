import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    from sqlalchemy import ARRAY, Float
    Vector = None
    PGVECTOR_AVAILABLE = False


class MaterialChunk(Base):
    __tablename__ = "material_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    material_id = Column(
        UUID(as_uuid=True),
        ForeignKey("learning_materials.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768) if PGVECTOR_AVAILABLE and Vector else Text, nullable=True)
    page_number = Column(Integer, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    material = relationship("LearningMaterial", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<MaterialChunk id={self.id} material_id={self.material_id} index={self.chunk_index}>"
