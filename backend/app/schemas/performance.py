from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class TopicPerformance(BaseModel):
    topic: str
    score_pct: float
    attempts: int
    correct_count: int
    total_count: int
    last_attempt: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PerformanceOverview(BaseModel):
    avg_score: float
    total_quizzes: int
    total_attempts: int
    strong_topics: List[str]
    weak_topics: List[str]
    recent_trend: str  # "improving", "declining", "stable"
    topics: List[TopicPerformance] = []


class MisconceptionReport(BaseModel):
    topic: str
    score_percentage: float
    attempts: int
    pattern: str
    evidence: str
    suggestion: str


class PerformanceTrend(BaseModel):
    date: str
    avg_score: float
    attempts: int
