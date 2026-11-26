"""Mock-first tutor chat with persisted, user-scoped chat history."""
from uuid import UUID, uuid4
from datetime import timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_active_user
from app.database.connection import get_db
from app.database.models.chat import AIChat, ChatRole
from app.database.models.material_chunk import MaterialChunk
from app.database.models.user import User

router = APIRouter(prefix="/tutor", tags=["AI Tutor"])
class ChatPayload(BaseModel):
    question: str = Field(min_length=2, max_length=4000)
    session_id: UUID | None = None
    language: str = "auto"

def _mock_answer(question: str, context: str, language: str) -> str:
    bangla = language == "bn" or any("\u0980" <= ch <= "\u09ff" for ch in question)
    if context:
        if bangla:
            return f"তোমার আপলোড করা উপকরণ থেকে পাওয়া তথ্যের ভিত্তিতে:\n\n{context[:900]}\n\nসহজভাবে: প্রশ্নটির মূল ধারণাটি উপরের অংশে ব্যাখ্যা করা হয়েছে। এটি Mock Tutor response—আরও নির্দিষ্ট প্রশ্ন করলে ধাপে ধাপে বুঝিয়ে দেব।"
        return f"Based on your uploaded study material:\n\n{context[:900]}\n\nIn short, the key idea is explained above. This is a deterministic Mock Tutor response; ask a narrower follow-up for a step-by-step explanation."
    if bangla:
        return f"তোমার প্রশ্ন: “{question}”\n\nএটি EduPilot AI-এর Mock Tutor। এখনো কোনো study material পাওয়া যায়নি, তাই নির্দিষ্ট বইয়ের তথ্য দাবি করছি না। বিষয়টি ছোট ছোট ধাপে ভাগ করে পড়ো: (১) মূল সংজ্ঞা, (২) একটি উদাহরণ, (৩) নিজে অনুশীলন। সংশ্লিষ্ট PDF upload করলে সেটির তথ্য ধরে উত্তর দিতে পারব।"
    return f"You asked: “{question}”\n\nThis is EduPilot AI's Mock Tutor. No uploaded study material was found, so I will not invent textbook-specific facts. Break the topic into (1) the core definition, (2) one worked example, and (3) a short practice question. Upload a PDF for answers grounded in your own material."

@router.post("/chat")
async def chat(payload: ChatPayload, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    session_id = payload.session_id or uuid4()
    history = (await db.scalars(select(AIChat).where(AIChat.user_id == user.id, AIChat.session_id == session_id).order_by(AIChat.created_at.desc()).limit(12))).all()
    if payload.session_id and not history:
        # A new client-provided UUID is allowed; ownership is established on first message.
        pass
    chunks = (await db.scalars(select(MaterialChunk).where(MaterialChunk.user_id == user.id).order_by(MaterialChunk.created_at.desc()).limit(5))).all()
    context = " ".join(c.content for c in reversed(chunks))
    answer = _mock_answer(payload.question, context, payload.language)
    db.add(AIChat(user_id=user.id, session_id=session_id, role=ChatRole.user, content=payload.question))
    db.add(AIChat(user_id=user.id, session_id=session_id, role=ChatRole.assistant, content=answer,
                  sources=[{"material_id": str(c.material_id), "chunk_id": str(c.id)} for c in chunks]))
    await db.flush()
    language_used = "bn" if any("\u0980" <= ch <= "\u09ff" for ch in payload.question) else "en"
    return {"answer": answer, "session_id": str(session_id), "sources": [], "language_used": language_used, "mode": "mock"}

@router.get("/history")
async def history(session_id: UUID | None = None, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    query = select(AIChat).where(AIChat.user_id == user.id)
    if session_id: query = query.where(AIChat.session_id == session_id)
    rows = (await db.scalars(query.order_by(AIChat.created_at.asc()).limit(200))).all()
    return {"session_id": str(session_id) if session_id else None, "messages": [
        {"id": str(m.id), "role": m.role.value, "content": m.content, "sources": m.sources,
         "created_at": m.created_at.isoformat()} for m in rows], "total": len(rows)}

@router.get("/sessions")
async def sessions(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    rows = (await db.execute(select(AIChat.session_id, func.count(AIChat.id), func.max(AIChat.created_at))
        .where(AIChat.user_id == user.id).group_by(AIChat.session_id).order_by(func.max(AIChat.created_at).desc()))).all()
    result = []
    for sid, count, last in rows:
        first = await db.scalar(select(AIChat.content).where(AIChat.user_id == user.id, AIChat.session_id == sid, AIChat.role == ChatRole.user).order_by(AIChat.created_at.asc()).limit(1))
        result.append({"session_id": str(sid), "message_count": count, "last_message_at": last.isoformat(), "preview": (first or "")[:100]})
    return result
