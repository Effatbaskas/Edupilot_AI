import uuid
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.chat import AIChat, ChatRole


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_message(
        self,
        user_id: UUID,
        session_id: UUID,
        role: ChatRole,
        content: str,
        sources: Optional[List[Dict]] = None,
    ) -> AIChat:
        message = AIChat(
            user_id=user_id,
            session_id=session_id,
            role=role,
            content=content,
            sources=sources,
        )
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        return message

    async def get_session_history(
        self,
        user_id: UUID,
        session_id: UUID,
        limit: int = 50,
    ) -> List[AIChat]:
        result = await self.db.execute(
            select(AIChat)
            .where(AIChat.user_id == user_id, AIChat.session_id == session_id)
            .order_by(AIChat.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_all_sessions(self, user_id: UUID) -> List[Dict]:
        """Return distinct sessions with the last message preview."""
        result = await self.db.execute(
            select(AIChat)
            .where(AIChat.user_id == user_id)
            .order_by(AIChat.created_at.desc())
        )
        messages = result.scalars().all()

        seen = {}
        for msg in messages:
            sid = str(msg.session_id)
            if sid not in seen:
                seen[sid] = {
                    "session_id": msg.session_id,
                    "last_message_at": msg.created_at.isoformat(),
                    "preview": msg.content[:120],
                    "message_count": 0,
                }
            seen[sid]["message_count"] += 1

        return list(seen.values())

    async def delete_session(self, user_id: UUID, session_id: UUID) -> int:
        result = await self.db.execute(
            delete(AIChat).where(
                AIChat.user_id == user_id,
                AIChat.session_id == session_id,
            )
        )
        return result.rowcount
