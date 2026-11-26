"""
Response parser and sanitiser for EduPilot AI.

Parses raw LLM output into structured Python objects and validates that
the parsed data is well-formed before it reaches the service layer.

SECURITY: sanitize_response() strips SQL fragments and prompt-injection
patterns from document content before it enters the AI pipeline.
"""

from __future__ import annotations

import json
import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dangerous pattern regexes for sanitisation
# ---------------------------------------------------------------------------

_SQL_PATTERNS = re.compile(
    r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|EXEC|EXECUTE"
    r"|UNION|GRANT|REVOKE|PRAGMA|ATTACH|DETACH)\b",
    re.IGNORECASE,
)

_PROMPT_INJECTION_PATTERNS = re.compile(
    r"(ignore\s+(all\s+)?previous\s+instructions?"
    r"|forget\s+your\s+instructions?"
    r"|you\s+are\s+now\s+(a\s+)?(different|new|another)"
    r"|system\s*:\s*you\s+are"
    r"|<\s*/?system\s*>"
    r"|###\s*(system|user|assistant)\s*###)",
    re.IGNORECASE,
)

_DB_CREDENTIAL_PATTERNS = re.compile(
    r"(password\s*=|DATABASE_URL|postgres(ql)?://|mysql://|mongodb(\+srv)?://|SECRET_KEY\s*=)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def parse_quiz_response(raw_text: str) -> list[dict]:
    """
    Parse a quiz generation response into a list of question dicts.

    Accepts:
    - JSON object with a "questions" key
    - JSON array of question objects

    Args:
        raw_text: Raw LLM response string.

    Returns:
        List of question dicts. Invalid questions are skipped with a warning.
    """
    cleaned = _strip_markdown_fences(raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to extract a JSON block from embedded text
        data = _extract_json_block(cleaned)
        if data is None:
            logger.warning("parse_quiz_response: could not extract JSON from response")
            return []

    # Normalise to a list
    if isinstance(data, dict):
        questions_raw = data.get("questions", [])
    elif isinstance(data, list):
        questions_raw = data
    else:
        logger.warning("parse_quiz_response: unexpected data type %s", type(data))
        return []

    questions: list[dict] = []
    for i, q in enumerate(questions_raw):
        if not isinstance(q, dict):
            logger.warning("parse_quiz_response: question %d is not a dict, skipping", i)
            continue
        if validate_quiz_question(q):
            questions.append(q)
        else:
            logger.warning("parse_quiz_response: question %d failed validation, skipping", i)

    logger.info("parse_quiz_response: parsed %d valid questions", len(questions))
    return questions


def parse_misconception_response(raw_text: str) -> list[dict]:
    """
    Parse a misconception detection response.

    Args:
        raw_text: Raw LLM response string.

    Returns:
        List of misconception dicts (usually one, but wrapped in a list for
        consistency with other parsers).
    """
    cleaned = _strip_markdown_fences(raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        data = _extract_json_block(cleaned)
        if data is None:
            logger.warning("parse_misconception_response: could not parse JSON")
            return []

    if isinstance(data, dict):
        # Single misconception object
        required_fields = {"topic", "pattern", "explanation"}
        if required_fields.issubset(data.keys()):
            data.setdefault("targeted_questions", [])
            return [data]
        logger.warning(
            "parse_misconception_response: missing fields %s",
            required_fields - data.keys(),
        )
        return []

    if isinstance(data, list):
        return [
            m for m in data
            if isinstance(m, dict) and {"topic", "pattern", "explanation"}.issubset(m.keys())
        ]

    return []


def sanitize_response(text: str) -> str:
    """
    Sanitise document content or LLM-generated text before further processing.

    Removes:
    - SQL injection fragments
    - Prompt injection attempts
    - Database credential patterns

    Args:
        text: Text to sanitise.

    Returns:
        Sanitised text with dangerous patterns replaced by placeholders.
    """
    if not text:
        return text

    # Replace SQL keywords in context (they're almost certainly document content
    # but we still neutralise them to prevent accidental execution)
    sanitised = _SQL_PATTERNS.sub("[SQL_KEYWORD_REMOVED]", text)

    # Remove prompt injection attempts
    sanitised = _PROMPT_INJECTION_PATTERNS.sub("[CONTENT_REMOVED]", sanitised)

    # Remove credential-looking strings
    sanitised = _DB_CREDENTIAL_PATTERNS.sub("[CREDENTIAL_REMOVED]", sanitised)

    return sanitised


def validate_quiz_question(question: dict) -> bool:
    """
    Validate a single quiz question dict.

    Rules:
    - Must have: question_text, question_type, correct_answer
    - MCQ: must have exactly 4 options; correct_answer must be in options
    - Short answer: options can be absent or empty

    Args:
        question: Question dict to validate.

    Returns:
        True if valid, False otherwise.
    """
    required = {"question_text", "question_type", "correct_answer"}
    if not required.issubset(question.keys()):
        logger.debug(
            "validate_quiz_question: missing required fields %s",
            required - question.keys(),
        )
        return False

    q_type = question.get("question_type", "").lower()
    correct = question.get("correct_answer", "")
    options = question.get("options", [])

    # question_text must be non-empty
    if not str(question.get("question_text", "")).strip():
        logger.debug("validate_quiz_question: empty question_text")
        return False

    # correct_answer must be non-empty
    if not str(correct).strip():
        logger.debug("validate_quiz_question: empty correct_answer")
        return False

    if q_type == "mcq":
        if not isinstance(options, list) or len(options) != 4:
            logger.debug(
                "validate_quiz_question: MCQ must have 4 options, got %d",
                len(options) if isinstance(options, list) else -1,
            )
            return False
        # Normalised comparison (strip whitespace)
        normalised_options = [str(o).strip() for o in options]
        if str(correct).strip() not in normalised_options:
            logger.debug(
                "validate_quiz_question: correct_answer '%s' not in options %s",
                correct,
                normalised_options,
            )
            return False

    elif q_type == "short_answer":
        # Short answer questions just need non-empty correct_answer (already checked)
        pass
    else:
        logger.debug("validate_quiz_question: unknown question_type '%s'", q_type)
        return False

    return True


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _strip_markdown_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` wrappers from LLM output."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # Drop first line (``` or ```json) and last line (```)
        inner_lines = []
        for line in lines[1:]:
            if line.strip() == "```":
                break
            inner_lines.append(line)
        return "\n".join(inner_lines).strip()
    return text


def _extract_json_block(text: str) -> dict | list | None:
    """
    Try to find and parse the first JSON object or array embedded in text.
    """
    # Try object first
    for pattern in (r"\{.*\}", r"\[.*\]"):
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue
    return None
