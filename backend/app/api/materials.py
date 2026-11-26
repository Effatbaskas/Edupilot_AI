"""Authenticated learning-material upload and CRUD endpoints (PDF, local storage)."""
from pathlib import Path
from uuid import UUID
import re

import fitz
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.dependencies import get_current_active_user
from app.database.connection import get_db
from app.database.models.material import LearningMaterial, MaterialStatus
from app.database.models.material_chunk import MaterialChunk
from app.database.models.user import User

router = APIRouter(prefix="/materials", tags=["Learning Materials"])
settings = get_settings()
ALLOWED_TYPES = {"application/pdf"}


def _chunks(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []
    result, start = [], 0
    while start < len(clean):
        piece = clean[start:start + size].strip()
        if piece:
            result.append(piece)
        start += size - overlap
    return result


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_material(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    if file.content_type not in ALLOWED_TYPES or not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(415, "Only PDF files are supported")
    data = await file.read(settings.max_file_size_bytes + 1)
    if not data:
        raise HTTPException(400, "Uploaded file is empty")
    if len(data) > settings.max_file_size_bytes:
        raise HTTPException(413, f"File exceeds {settings.MAX_FILE_SIZE_MB} MB limit")
    try:
        document = fitz.open(stream=data, filetype="pdf")
        extracted = "\n".join(page.get_text() for page in document)
        page_count = document.page_count
        document.close()
    except Exception as exc:
        raise HTTPException(422, "The uploaded PDF could not be read") from exc
    if not extracted.strip():
        raise HTTPException(422, "The PDF contains no extractable text; scanned PDFs are not supported in mock mode")

    upload_dir = Path(settings.UPLOAD_DIR) / str(user.id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    material_id = __import__("uuid").uuid4()
    safe_name = Path(file.filename).name.replace("..", "_")
    stored_path = upload_dir / f"{material_id}.pdf"
    stored_path.write_bytes(data)
    material = LearningMaterial(
        id=material_id, user_id=user.id, title=Path(safe_name).stem[:500],
        filename=safe_name[:500], file_path=str(stored_path), file_size=len(data),
        mime_type="application/pdf", status=MaterialStatus.processing,
    )
    db.add(material)
    try:
        await db.flush()
        pieces = _chunks(extracted)
        for index, piece in enumerate(pieces):
            db.add(MaterialChunk(material_id=material.id, user_id=user.id, chunk_index=index, content=piece))
        material.total_chunks = len(pieces)
        material.status = MaterialStatus.ready
        await db.flush()
    except Exception:
        stored_path.unlink(missing_ok=True)
        raise
    return {"id": str(material.id), "title": material.title, "filename": material.filename,
            "file_size": material.file_size, "mime_type": material.mime_type,
            "status": material.status.value, "total_chunks": material.total_chunks,
            "page_count": page_count, "message": "PDF uploaded and text indexed successfully."}


@router.get("/")
async def list_materials(page: int = 1, per_page: int = 20, search: str | None = None,
                        db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    if page < 1 or not 1 <= per_page <= 100:
        raise HTTPException(422, "page must be positive and per_page must be between 1 and 100")
    query = select(LearningMaterial).where(LearningMaterial.user_id == user.id)
    if search:
        query = query.where(LearningMaterial.title.ilike(f"%{search.strip()}%"))
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    rows = (await db.scalars(query.order_by(LearningMaterial.created_at.desc()).offset((page-1)*per_page).limit(per_page))).all()
    return {"materials": [{"id": str(m.id), "user_id": str(m.user_id), "title": m.title,
        "filename": m.filename, "file_size": m.file_size, "mime_type": m.mime_type,
        "status": m.status.value, "total_chunks": m.total_chunks,
        "created_at": m.created_at, "updated_at": m.updated_at} for m in rows], "total": total, "page": page, "per_page": per_page}


@router.get("/{material_id}")
async def get_material(material_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    material = await db.scalar(select(LearningMaterial).where(LearningMaterial.id == material_id, LearningMaterial.user_id == user.id))
    if not material:
        raise HTTPException(404, "Material not found")
    return {"id": str(material.id), "title": material.title, "filename": material.filename,
            "file_size": material.file_size, "status": material.status.value, "total_chunks": material.total_chunks,
            "created_at": material.created_at, "updated_at": material.updated_at}


@router.delete("/{material_id}", status_code=204)
async def delete_material(material_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    material = await db.scalar(select(LearningMaterial).where(LearningMaterial.id == material_id, LearningMaterial.user_id == user.id))
    if not material:
        raise HTTPException(404, "Material not found")
    path = Path(material.file_path)
    await db.delete(material)
    await db.flush()
    path.unlink(missing_ok=True)
