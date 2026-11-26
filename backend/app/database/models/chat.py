import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Text, Enum as SAEnum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship

from app.database.base import Base


class ChatRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class AIChat(Base):
    __tablename__ = "ai_chats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True, default=uuid.uuid4)
    role = Column(SAEnum(ChatRole), nullable=False)
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # list of chunk references
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="chats")

    def __repr__(self) -> str:
        return f"<AIChat id={self.id} session_id={self.session_id} role={self.role}>"
