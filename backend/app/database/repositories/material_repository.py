from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.material import LearningMaterial, MaterialStatus
from app.database.models.material_chunk import MaterialChunk


class MaterialRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: UUID,
        title: str,
        filename: str,
        file_path: str,
        file_size: int,
        mime_type: str = "application/pdf",
    ) -> LearningMaterial:
        material = LearningMaterial(
            user_id=user_id,
            title=title,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            status=MaterialStatus.pending,
        )
        self.db.add(material)
        await self.db.flush()
        await self.db.refresh(material)
        return material

    async def get_by_id(self, material_id: UUID, user_id: Optional[UUID] = None) -> Optional[LearningMaterial]:
        query = select(LearningMaterial).where(LearningMaterial.id == material_id)
        if user_id:
            query = query.where(LearningMaterial.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> List[LearningMaterial]:
        result = await self.db.execute(
            select(LearningMaterial)
            .where(LearningMaterial.user_id == user_id)
            .order_by(LearningMaterial.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        material_id: UUID,
        status: MaterialStatus,
        total_chunks: Optional[int] = None,
    ) -> Optional[LearningMaterial]:
        material = await self.get_by_id(material_id)
        if not material:
            return None
        material.status = status
        if total_chunks is not None:
            material.total_chunks = total_chunks
        self.db.add(material)
        await self.db.flush()
        await self.db.refresh(material)
        return material

    async def delete(self, material_id: UUID, user_id: UUID) -> bool:
        material = await self.get_by_id(material_id, user_id=user_id)
        if not material:
            return False
        await self.db.delete(material)
        await self.db.flush()
        return True

    async def get_chunks_by_user(
        self,
        user_id: UUID,
        material_id: Optional[UUID] = None,
    ) -> List[MaterialChunk]:
        query = select(MaterialChunk).where(MaterialChunk.user_id == user_id)
        if material_id:
            query = query.where(MaterialChunk.material_id == material_id)
        result = await self.db.execute(query.order_by(MaterialChunk.chunk_index))
        return list(result.scalars().all())

    async def save_chunk(self, chunk: MaterialChunk) -> MaterialChunk:
        self.db.add(chunk)
        await self.db.flush()
        return chunk

    async def save_chunks_bulk(self, chunks: List[MaterialChunk]) -> None:
        for chunk in chunks:
            self.db.add(chunk)
        await self.db.flush()

    async def count_by_user(self, user_id: UUID) -> int:
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count(LearningMaterial.id)).where(LearningMaterial.user_id == user_id)
        )
        return result.scalar() or 0
