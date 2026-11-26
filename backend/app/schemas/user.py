from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserPublic(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserWithStats(UserPublic):
    total_materials: int = 0
    total_quizzes: int = 0
    total_attempts: int = 0
    avg_score: Optional[float] = None


class RoleUpdateRequest(BaseModel):
    role: Literal["student", "teacher", "admin"]
