import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, String, Uuid
from sqlalchemy.orm import relationship

from app.database.base import Base, BaseModel


class UserRole(str, enum.Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"


class User(Base, BaseModel):
    __tablename__ = "users"

    # Generic UUID compiles to PostgreSQL UUID and also supports isolated
    # SQLite tests without changing the production PostgreSQL column type.
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.student)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
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
    materials = relationship("LearningMaterial", back_populates="user", cascade="all, delete-orphan")
    chats = relationship("AIChat", back_populates="user", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="user", cascade="all, delete-orphan")
    performances = relationship("Performance", back_populates="user", cascade="all, delete-orphan")
    roadmap = relationship("Roadmap", back_populates="user", uselist=False, cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
