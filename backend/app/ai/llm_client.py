"""
LLM Client for EduPilot AI.

Wraps the Google Generative AI (Gemini) API with retry logic, timeouts,
structured output support, and a mock mode for testing.

SECURITY NOTE:
- This module NEVER receives or stores DB credentials.
- It only receives plain text prompts and returns plain text responses.
- API keys flow in only through Settings injection, never direct env access.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class AIServiceError(Exception):
    """Raised when the AI service is unavailable or times out."""


class AIResponseError(Exception):
    """Raised when the AI returns an unparseable or invalid response."""


# ---------------------------------------------------------------------------
# Main LLM Client
# ---------------------------------------------------------------------------


class LLMClient:
    """
    Async Gemini LLM client with retry logic, timeout handling, and
    structured output support.

    Instances MUST be created via settings injection — never pull env vars
    directly inside this class.
    """

    LLM_TIMEOUT = 30  # seconds

    def __init__(self, settings: Any) -> None:
        """
        Initialise with an injected settings object.

        Args:
            settings: Application settings object (pydantic-settings BaseSettings).
                      Must expose `gemini_api_key` and `llm_model`.
        """
        self._model_name: str = getattr(settings, "LLM_MODEL", getattr(settings, "llm_model", "gemini-1.5-flash"))
        api_key: str = getattr(settings, "GEMINI_API_KEY", getattr(settings, "gemini_api_key", ""))

        genai.configure(api_key=api_key)
        self._client = genai.GenerativeModel(self._model_name)

        logger.info("LLMClient initialised with model=%s", self._model_name)

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate a text response for a given prompt.

        Args:
            prompt: User-facing prompt text.
            system_instruction: Optional system-level instruction prepended
                                 to the conversation.
            temperature: Sampling temperature (0-1).
            max_tokens: Maximum output token count.

        Returns:
            Generated response string.

        Raises:
            AIServiceError: On timeout or unrecoverable API error.
        """
        call_id = uuid.uuid4().hex[:8]
        logger.info(
            "LLM generate start call_id=%s prompt_len=%d temp=%.2f max_tokens=%d",
            call_id,
            len(prompt),
            temperature,
            max_tokens,
        )
        t0 = time.monotonic()

        try:
            result = await asyncio.wait_for(
                self._generate_with_retry(
                    prompt, system_instruction, temperature, max_tokens
                ),
                timeout=self.LLM_TIMEOUT,
            )
        except asyncio.TimeoutError as exc:
            raise AIServiceError(
                f"LLM generate timed out after {self.LLM_TIMEOUT}s"
            ) from exc

        latency = time.monotonic() - t0
        logger.info(
            "LLM generate done call_id=%s response_len=%d latency=%.2fs",
            call_id,
            len(result),
            latency,
        )
        return result

    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict,
        system_instruction: str | None = None,
    ) -> dict:
        """
        Generate a response conforming to a JSON schema.

        The model is instructed to return valid JSON; this method parses it.

        Args:
            prompt: Prompt describing the task.
            response_schema: Expected JSON schema (used in the system prompt).
            system_instruction: Optional extra system instruction.

        Returns:
            Parsed dict matching the schema.

        Raises:
            AIServiceError: On timeout.
            AIResponseError: If the model's output is not valid JSON.
        """
        import json

        schema_str = json.dumps(response_schema, indent=2)
        json_instruction = (
            f"You MUST respond with valid JSON only, matching this schema:\n{schema_str}\n"
            "Do NOT include markdown code fences or any text outside the JSON object."
        )
        combined_system = (
            f"{system_instruction}\n\n{json_instruction}"
            if system_instruction
            else json_instruction
        )

        raw = await self.generate(
            prompt=prompt,
            system_instruction=combined_system,
            temperature=0.2,  # Lower temp for structured output
            max_tokens=4096,
        )

        # Strip markdown fences if the model added them despite instructions
        clean = raw.strip()
        if clean.startswith("```"):
            lines = clean.splitlines()
            # Drop first and last fence lines
            clean = "\n".join(
                line for line in lines if not line.strip().startswith("```")
            )

        try:
            return json.loads(clean)
        except json.JSONDecodeError as exc:
            raise AIResponseError(
                f"LLM returned non-JSON output: {clean[:200]}"
            ) from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _generate_with_retry(
        self,
        prompt: str,
        system_instruction: str | None,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call Gemini with exponential back-off on rate-limit / service errors."""
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type((ResourceExhausted, ServiceUnavailable)),
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=20),
            reraise=True,
        ):
            with attempt:
                if system_instruction:
                    model = genai.GenerativeModel(
                        self._model_name,
                        system_instruction=system_instruction,
                    )
                else:
                    model = self._client

                response = await asyncio.to_thread(
                    model.generate_content,
                    prompt,
                    generation_config=generation_config,
                )
                return response.text

        raise AIServiceError("LLM generate_with_retry exhausted all attempts")


# ---------------------------------------------------------------------------
# Mock LLM Client (for testing / when API key is "mock" or absent)
# ---------------------------------------------------------------------------


class MockLLMClient:
    """
    Deterministic fake LLM client used in tests and when GEMINI_API_KEY is
    absent or set to 'mock'.

    Returns predictable, structured responses that the rest of the codebase
    can parse safely.
    """

    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        logger.debug("MockLLMClient.generate called prompt_len=%d", len(prompt))
        await asyncio.sleep(0.01)  # Simulate tiny async latency

        # Return a sensible default depending on prompt keywords
        prompt_lower = prompt.lower()
        if "quiz" in prompt_lower or "question" in prompt_lower:
            return self._mock_quiz_response()
        if "misconception" in prompt_lower:
            return self._mock_misconception_response()
        if "roadmap" in prompt_lower or "schedule" in prompt_lower:
            return self._mock_roadmap_response()
        return (
            "This is a mock AI response for testing purposes. "
            "The EduPilot AI system is operating in mock mode. "
            "In production, this would be a real Gemini response."
        )

    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict,
        system_instruction: str | None = None,
    ) -> dict:
        import json

        logger.debug("MockLLMClient.generate_structured called")
        await asyncio.sleep(0.01)

        prompt_lower = prompt.lower()
        if "quiz" in prompt_lower or "question" in prompt_lower:
            raw = self._mock_quiz_response()
        elif "misconception" in prompt_lower:
            raw = self._mock_misconception_response()
        else:
            raw = '{"result": "mock structured response"}'

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"result": "mock structured response"}

    # ------------------------------------------------------------------
    # Private mock response builders
    # ------------------------------------------------------------------

    @staticmethod
    def _mock_quiz_response() -> str:
        import json

        questions = [
            {
                "question_text": "What is the powerhouse of the cell?",
                "question_type": "mcq",
                "options": ["Nucleus", "Mitochondria", "Ribosome", "Golgi apparatus"],
                "correct_answer": "Mitochondria",
                "explanation": "The mitochondria produces ATP, the cell's energy currency.",
                "topic": "Cell Biology",
                "difficulty": "easy",
            },
            {
                "question_text": "Which organelle contains DNA?",
                "question_type": "mcq",
                "options": ["Lysosome", "Vacuole", "Nucleus", "Cell membrane"],
                "correct_answer": "Nucleus",
                "explanation": "The nucleus houses the cell's genetic material.",
                "topic": "Cell Biology",
                "difficulty": "easy",
            },
            {
                "question_text": "What process do plants use to make food?",
                "question_type": "mcq",
                "options": ["Respiration", "Fermentation", "Photosynthesis", "Digestion"],
                "correct_answer": "Photosynthesis",
                "explanation": "Plants convert sunlight, CO2, and water into glucose via photosynthesis.",
                "topic": "Plant Biology",
                "difficulty": "easy",
            },
        ]
        return json.dumps({"questions": questions})

    @staticmethod
    def _mock_misconception_response() -> str:
        import json

        result = {
            "topic": "Mock Topic",
            "pattern": "Student consistently confuses similar concepts",
            "explanation": "The student appears to have a fundamental misunderstanding of the core concept.",
            "targeted_questions": [
                "Can you explain the difference between X and Y?",
                "What is the defining characteristic of Z?",
            ],
        }
        return json.dumps(result)

    @staticmethod
    def _mock_roadmap_response() -> str:
        return (
            "Here is your personalised study roadmap:\n"
            "Week 1: Focus on foundational concepts.\n"
            "Week 2: Practice with exercises.\n"
            "Week 3: Review and consolidate knowledge.\n"
            "Week 4: Final revision and mock exams."
        )


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------


def get_llm_client(settings: Any) -> LLMClient | MockLLMClient:
    """
    Return an LLMClient or MockLLMClient based on settings.

    Uses MockLLMClient when GEMINI_API_KEY is 'mock', empty, or absent.
    """
    api_key: str = getattr(settings, "GEMINI_API_KEY", getattr(settings, "gemini_api_key", "")) or ""
    mode: str = getattr(settings, "AI_MODE", getattr(settings, "ai_mode", "mock")) or "mock"
    if mode.lower() != "gemini" or not api_key or api_key.lower() == "mock":
        logger.warning(
            "GEMINI_API_KEY is absent or 'mock' — using MockLLMClient"
        )
        return MockLLMClient()
    return LLMClient(settings)
