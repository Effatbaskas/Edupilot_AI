"""AI module for EduPilot AI - LLM client, prompt templates, and AI engines."""

from app.ai.llm_client import LLMClient, MockLLMClient, get_llm_client
from app.ai.prompt_templates import (
    TUTOR_SYSTEM_PROMPT,
    build_tutor_prompt,
    build_quiz_generation_prompt,
    build_misconception_prompt,
    build_roadmap_explanation_prompt,
)
from app.ai.response_parser import (
    parse_quiz_response,
    parse_misconception_response,
    sanitize_response,
    validate_quiz_question,
)
from app.ai.tutor_engine import TutorEngine
from app.ai.quiz_generator import QuizGenerator
from app.ai.misconception_detector import MisconceptionDetector
from app.ai.recommendation_engine import RecommendationEngine

__all__ = [
    "LLMClient",
    "MockLLMClient",
    "get_llm_client",
    "TUTOR_SYSTEM_PROMPT",
    "build_tutor_prompt",
    "build_quiz_generation_prompt",
    "build_misconception_prompt",
    "build_roadmap_explanation_prompt",
    "parse_quiz_response",
    "parse_misconception_response",
    "sanitize_response",
    "validate_quiz_question",
    "TutorEngine",
    "QuizGenerator",
    "MisconceptionDetector",
    "RecommendationEngine",
]
