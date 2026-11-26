from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class QuizGenerateRequest(BaseModel):
    material_id: Optional[UUID] = None
    topic: str
    difficulty: str = "medium"
    num_questions: int = 10
    quiz_type: str = "mcq"

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        if v not in {"easy", "medium", "hard"}:
            raise ValueError("Difficulty must be easy, medium, or hard")
        return v

    @field_validator("quiz_type")
    @classmethod
    def validate_quiz_type(cls, v: str) -> str:
        if v not in {"mcq", "short_answer", "mixed"}:
            raise ValueError("Quiz type must be mcq, short_answer, or mixed")
        return v

    @field_validator("num_questions")
    @classmethod
    def validate_num_questions(cls, v: int) -> int:
        if not 1 <= v <= 50:
            raise ValueError("Number of questions must be between 1 and 50")
        return v


class QuestionResponse(BaseModel):
    id: UUID
    question_text: str
    question_type: str
    options: Optional[List[str]] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    order_index: int

    model_config = {"from_attributes": True}


class QuizResponse(BaseModel):
    id: UUID
    user_id: UUID
    material_id: Optional[UUID] = None
    title: str
    topic: str
    difficulty: str
    quiz_type: str
    status: str
    total_questions: int
    questions: List[QuestionResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuizSubmitRequest(BaseModel):
    answers: Dict[str, str]  # {question_id: answer}
    time_taken_seconds: Optional[int] = None


class QuestionResult(BaseModel):
    question_id: UUID
    question_text: str
    your_answer: str
    correct_answer: str
    is_correct: bool
    explanation: Optional[str] = None
    topic: Optional[str] = None


class QuizResultResponse(BaseModel):
    attempt_id: UUID
    quiz_id: UUID
    score: float
    correct_count: int
    total_questions: int
    time_taken_seconds: Optional[int] = None
    results: List[QuestionResult]
    weak_topics: List[str] = []
    strong_topics: List[str] = []
    completed_at: datetime
