from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class RoadmapGenerateRequest(BaseModel):
    exam_date: Optional[date] = None
    daily_hours: float = 2.0
    target_score: Optional[float] = None
    weak_topics: Optional[List[str]] = None


class StudyTaskResponse(BaseModel):
    id: UUID
    roadmap_id: UUID
    day_number: int
    topic: str
    subject: Optional[str] = None
    task_type: str
    duration_minutes: int
    priority: str
    status: str
    description: Optional[str] = None
    is_ai_generated: bool
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RoadmapResponse(BaseModel):
    id: UUID
    user_id: UUID
    exam_date: Optional[date] = None
    daily_hours: float
    target_score: Optional[float] = None
    is_active: bool
    generated_at: datetime
    updated_at: datetime
    tasks: List[StudyTaskResponse] = []
    total_days: int = 0
    prioritization_explanation: str = ""

    model_config = {"from_attributes": True}


class TaskUpdateRequest(BaseModel):
    status: str

    def validate_status(self) -> None:
        allowed = {"pending", "in_progress", "completed", "skipped"}
        if self.status not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
