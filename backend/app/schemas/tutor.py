from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    session_id: Optional[UUID] = None
    language: str = "auto"


class SourceReference(BaseModel):
    chunk_id: UUID
    material_id: UUID
    material_title: str
    page_number: Optional[int] = None
    content_preview: str


class ChatResponse(BaseModel):
    answer: str
    session_id: UUID
    sources: List[SourceReference] = []
    language_used: str = "en"


class ChatMessage(BaseModel):
    id: UUID
    role: str
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    created_at: str

    model_config = {"from_attributes": True}


class ChatHistory(BaseModel):
    session_id: UUID
    messages: List[ChatMessage]
    total: int


class SessionSummary(BaseModel):
    session_id: UUID
    message_count: int
    last_message_at: str
    preview: str
