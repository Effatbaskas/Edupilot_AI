from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ProcessingStatus(BaseModel):
    status: str
    total_chunks: Optional[int] = None
    message: Optional[str] = None


class MaterialUploadResponse(BaseModel):
    id: UUID
    title: str
    filename: str
    file_size: int
    mime_type: str
    status: str
    created_at: datetime
    message: str = "File uploaded successfully. Processing in background."

    model_config = {"from_attributes": True}


class MaterialResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    status: str
    total_chunks: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MaterialListResponse(BaseModel):
    materials: list[MaterialResponse]
    total: int
    page: int = 1
    per_page: int = 20
