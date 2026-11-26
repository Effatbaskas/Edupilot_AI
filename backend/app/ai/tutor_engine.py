"""
TutorEngine — orchestrates the RAG + LLM pipeline for answering student questions.

Architecture:
- Receives a question and chat history as plain Python objects.
- Delegates retrieval to the injected RAGRetriever (which owns the DB query).
- Delegates generation to the injected LLMClient.
- Returns a plain dict — NEVER writes to the database.

SECURITY:
- engine never touches DB credentials.
- document content is sanitised before being sent to the LLM.
"""

from __future__ import annotations

import logging
import re
import time
from typing import TYPE_CHECKING

from app.ai.prompt_templates import TUTOR_SYSTEM_PROMPT, build_tutor_prompt
from app.ai.response_parser import sanitize_response

if TYPE_CHECKING:
    from app.ai.llm_client import LLMClient
    from app.rag.retriever import RAGRetriever

logger = logging.getLogger(__name__)

# Simple heuristic: Bangla Unicode block U+0980–U+09FF
_BANGLA_RE = re.compile(r"[\u0980-\u09FF]")


class TutorEngine:
    """
    Orchestrates the retrieval-augmented tutoring pipeline.

    Dependencies are injected; the engine never creates them directly.
    """

    def __init__(self, llm_client: "LLMClient", retriever: "RAGRetriever") -> None:
        """
        Args:
            llm_client: Configured LLM client (real or mock).
            retriever:  Configured RAG retriever. The retriever receives the
                        db_session and handles all database interaction.
        """
        self._llm = llm_client
        self._retriever = retriever

    async def answer_question(
        self,
        question: str,
        user_id: str,
        session_id: str,
        chat_history: list[dict],
        db_session,
        material_id: str | None = None,
        top_k: int = 5,
    ) -> dict:
        """
        Answer a student question using RAG.

        Steps:
        1. Retrieve relevant document chunks via retriever (retriever owns DB).
        2. Sanitise and build context string from chunks.
        3. Detect language from the question.
        4. Build prompt using prompt_templates.
        5. Generate answer via LLM.
        6. Return result dict (caller is responsible for persisting to DB).

        Args:
            question:     The student's question (may be in Bangla or English).
            user_id:      Authenticated user ID (for data-isolation in retriever).
            session_id:   Chat session ID (for logging context, not used by LLM).
            chat_history: Previous messages in this session [{role, content}].
            db_session:   SQLAlchemy async session — passed through to retriever only.
            material_id:  Optional UUID of a specific material to restrict retrieval.
            top_k:        Number of chunks to retrieve.

        Returns:
            dict with keys:
              - answer (str): LLM-generated response.
              - sources (list[dict]): Source references for citations.
              - language_detected (str): 'bangla' | 'english' | 'mixed'.
        """
        t0 = time.monotonic()
        logger.info(
            "TutorEngine.answer_question user_id=%s session_id=%s q_len=%d",
            user_id,
            session_id,
            len(question),
        )

        # Step 1: Retrieve relevant chunks
        chunks = await self._retriever.retrieve(
            query=question,
            user_id=user_id,
            db_session=db_session,
            top_k=top_k,
            material_id=material_id,
        )
        logger.debug("Retrieved %d chunks for user_id=%s", len(chunks), user_id)

        # Step 2: Build context from chunks
        from app.rag.context_builder import ContextBuilder

        builder = ContextBuilder()
        context_text, source_refs = builder.build_context(chunks, max_tokens=2000)

        # Sanitise document content before sending to LLM
        safe_context = sanitize_response(context_text)

        # Step 3: Detect language
        language_hint = self._detect_language(question)

        # Step 4: Build prompt
        prompt = build_tutor_prompt(
            question=question,
            context=safe_context,
            chat_history=chat_history,
            language_hint=language_hint,
        )

        # Step 5: Generate answer
        answer = await self._llm.generate(
            prompt=prompt,
            system_instruction=TUTOR_SYSTEM_PROMPT,
            temperature=0.6,
            max_tokens=2048,
        )

        latency = time.monotonic() - t0
        logger.info(
            "TutorEngine.answer_question done user_id=%s latency=%.2fs sources=%d",
            user_id,
            latency,
            len(source_refs),
        )

        return {
            "answer": answer,
            "sources": source_refs,
            "language_detected": language_hint,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_language(text: str) -> str:
        """
        Heuristic language detection.

        Returns 'bangla', 'english', or 'mixed'.
        """
        bangla_chars = len(_BANGLA_RE.findall(text))
        total_chars = len(text.strip())
        if total_chars == 0:
            return "english"

        ratio = bangla_chars / total_chars
        if ratio > 0.4:
            return "bangla"
        if ratio > 0.1:
            return "mixed"
        return "english"
