"""
Prompt templates for EduPilot AI.

All prompts are defined here as constants or builder functions so that
the rest of the AI layer can import them without coupling to raw strings.

SECURITY NOTES:
- Templates never embed raw user input directly — callers must pass
  sanitised text.
- Context from documents is wrapped so the LLM knows it comes from
  retrieved material, not from its training data.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

TUTOR_SYSTEM_PROMPT = """You are EduPilot AI, a friendly and expert educational tutor built to help students learn effectively.

Your core responsibilities:
- Explain concepts clearly, step by step, using simple language before introducing technical terms.
- Support both Bangla (বাংলা) and English. Detect the language from the student's question and respond in the same language. If the question mixes both, prefer Bangla.
- Use practical, relatable examples to illustrate abstract ideas.
- When context from uploaded study materials is provided, cite the material title and page number.
- NEVER claim information is from a document if it was not retrieved from the provided context.
- NEVER invent sources, references, or citations.
- If you do not know an answer, say so honestly rather than guessing.
- Keep answers focused and educational — avoid unnecessary tangents.
- Use markdown formatting (headers, bullets, bold) to improve readability.
- Always encourage the student positively.

Boundaries:
- You are an educational tutor only. Do not assist with requests unrelated to learning.
- Do not reproduce large verbatim excerpts from copyrighted material.
- Do not generate harmful, offensive, or inappropriate content.
"""

QUIZ_GENERATOR_SYSTEM_PROMPT = """You are EduPilot AI Quiz Generator. Your task is to create high-quality educational quiz questions.

Rules:
- Generate exactly the number of questions requested.
- Each question MUST be clearly worded and unambiguous.
- For MCQ questions: provide exactly 4 options, with only ONE correct answer.
- The correct_answer field MUST match one of the option strings exactly.
- Include a brief explanation for why the correct answer is right.
- Vary difficulty within the requested level.
- Return ONLY valid JSON — no markdown fences, no extra text.
"""

MISCONCEPTION_SYSTEM_PROMPT = """You are EduPilot AI Misconception Analyst. You identify specific conceptual errors a student is making based on their wrong answers.

Rules:
- Be specific about the misconception — not just "the student got it wrong".
- Explain the likely root cause of the confusion.
- Suggest 2-3 targeted follow-up questions to address the gap.
- Keep explanations concise and actionable.
- Return ONLY valid JSON.
"""

ROADMAP_SYSTEM_PROMPT = """You are EduPilot AI Study Planner. You generate human-readable explanations for study roadmaps.

Rules:
- Be motivating and realistic.
- Acknowledge the student's time constraints.
- Explain WHY certain topics are prioritised.
- If the schedule is infeasible, say so kindly and suggest what can be done.
- Support both Bangla and English based on context.
"""


# ---------------------------------------------------------------------------
# Prompt builder functions
# ---------------------------------------------------------------------------


def build_tutor_prompt(
    question: str,
    context: str,
    chat_history: list[dict],
    language_hint: str = "auto",
) -> str:
    """
    Build the full tutor prompt including context and chat history.

    Args:
        question: The student's question (sanitised).
        context: Retrieved document context (sanitised).
        chat_history: List of previous messages [{role, content}].
                      Roles are 'user' or 'assistant'.
        language_hint: 'bangla', 'english', or 'auto'.

    Returns:
        Full prompt string ready to send to the LLM.
    """
    parts: list[str] = []

    # Language instruction
    if language_hint == "bangla":
        parts.append("NOTE: Please respond in Bangla (বাংলা).\n")
    elif language_hint == "english":
        parts.append("NOTE: Please respond in English.\n")

    # Document context
    if context and context.strip():
        parts.append(
            "=== RETRIEVED STUDY MATERIAL CONTEXT ===\n"
            f"{context.strip()}\n"
            "=== END OF CONTEXT ===\n"
            "\nUse the above context to inform your answer. "
            "Cite the source when referencing it.\n"
        )
    else:
        parts.append(
            "[No study material context was retrieved for this question. "
            "Answer from general knowledge and be explicit that no document context is available.]\n"
        )

    # Chat history (last 10 turns to avoid token overflow)
    if chat_history:
        history_tail = chat_history[-10:]
        parts.append("\n=== CONVERSATION HISTORY ===")
        for msg in history_tail:
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "")
            parts.append(f"{role}: {content}")
        parts.append("=== END HISTORY ===\n")

    # The actual question
    parts.append(f"Student Question: {question}")

    return "\n".join(parts)


def build_quiz_generation_prompt(
    topic: str,
    context: str,
    num_questions: int,
    difficulty: str,
    quiz_type: str,
) -> str:
    """
    Build a quiz generation prompt.

    Args:
        topic: Subject / topic for the quiz.
        context: Retrieved document content to base questions on.
        num_questions: How many questions to generate.
        difficulty: 'easy', 'medium', or 'hard'.
        quiz_type: 'mcq', 'short_answer', or 'mixed'.

    Returns:
        Prompt string.
    """
    type_instructions = {
        "mcq": (
            "Generate ONLY multiple-choice questions. "
            "Each must have exactly 4 options and one correct answer."
        ),
        "short_answer": (
            "Generate ONLY short-answer questions. "
            "The correct_answer should be a concise phrase or sentence. "
            "options field should be an empty list []."
        ),
        "mixed": (
            f"Generate a mix of MCQ and short-answer questions. "
            f"Aim for roughly {num_questions // 2} of each type."
        ),
    }
    type_instruction = type_instructions.get(quiz_type, type_instructions["mcq"])

    context_section = ""
    if context and context.strip():
        context_section = (
            "\n=== STUDY MATERIAL CONTEXT ===\n"
            f"{context.strip()}\n"
            "=== END CONTEXT ===\n"
            "Base questions primarily on the above material where possible.\n"
        )

    return f"""Generate {num_questions} quiz questions on the topic: "{topic}"

Difficulty level: {difficulty.upper()}
Question type: {quiz_type.upper()}
{type_instruction}
{context_section}
Return a JSON object with this exact structure:
{{
  "questions": [
    {{
      "question_text": "...",
      "question_type": "mcq" or "short_answer",
      "options": ["A", "B", "C", "D"],
      "correct_answer": "A",
      "explanation": "Brief explanation of the correct answer.",
      "topic": "{topic}",
      "difficulty": "{difficulty}"
    }}
  ]
}}

IMPORTANT:
- correct_answer MUST exactly match one of the strings in options (for MCQ).
- Do not include any text outside the JSON object.
- Generate exactly {num_questions} questions.
"""


def build_misconception_prompt(
    topic: str,
    wrong_answers: list[dict],
    context: str,
) -> str:
    """
    Build a misconception detection prompt.

    Args:
        topic: The topic being assessed.
        wrong_answers: List of dicts: {question, student_answer, correct_answer}.
        context: Optional retrieved context about the topic.

    Returns:
        Prompt string.
    """
    wrong_answer_lines = "\n".join(
        f"  {i+1}. Question: {wa.get('question', 'N/A')}\n"
        f"     Student answered: {wa.get('student_answer', 'N/A')}\n"
        f"     Correct answer: {wa.get('correct_answer', 'N/A')}"
        for i, wa in enumerate(wrong_answers)
    )

    context_section = ""
    if context and context.strip():
        context_section = (
            "\n=== RELEVANT STUDY MATERIAL ===\n"
            f"{context.strip()}\n"
            "=== END ===\n"
        )

    return f"""Analyse the following wrong answers by a student on the topic "{topic}" and identify the likely misconception(s).

Wrong answers:
{wrong_answer_lines}
{context_section}
Return a JSON object with this structure:
{{
  "topic": "{topic}",
  "pattern": "Brief description of the error pattern",
  "explanation": "Detailed explanation of the likely conceptual misunderstanding",
  "targeted_questions": [
    "Follow-up question 1 to address the gap",
    "Follow-up question 2 to address the gap"
  ]
}}
"""


def build_roadmap_explanation_prompt(
    weak_topics: list[dict],
    schedule: list[dict],
    exam_days: int | None,
) -> str:
    """
    Build a prompt for generating a human-readable roadmap explanation.

    Args:
        weak_topics: List of dicts {topic, score_pct, urgency}.
        schedule: List of daily tasks [{day, topic, duration_minutes, task_type}].
        exam_days: Days until exam (None if no exam set).

    Returns:
        Prompt string.
    """
    exam_note = (
        f"The student has an exam in {exam_days} days."
        if exam_days is not None
        else "No specific exam date has been set."
    )

    weak_topic_lines = "\n".join(
        f"  - {wt.get('topic', 'Unknown')}: {wt.get('score_pct', 0):.0f}% "
        f"(urgency score: {wt.get('urgency', 0):.2f})"
        for wt in weak_topics[:10]  # Cap to avoid huge prompts
    )

    schedule_summary = "\n".join(
        f"  Day {s.get('day', '?')}: {s.get('topic', '?')} — "
        f"{s.get('duration_minutes', 0)} min ({s.get('task_type', 'study')})"
        for s in schedule[:14]  # Show up to 2 weeks
    )
    if len(schedule) > 14:
        schedule_summary += f"\n  ... and {len(schedule) - 14} more days"

    return f"""Write a friendly, motivating explanation for the following personalised study roadmap.

{exam_note}

Weak topics identified (prioritised by urgency):
{weak_topic_lines}

Proposed study schedule:
{schedule_summary}

Write 2-3 paragraphs explaining:
1. Why these topics were prioritised in this order.
2. How the daily schedule is structured to maximise learning.
3. Words of encouragement for the student.

Keep it concise, positive, and actionable. If the schedule is tight, acknowledge it honestly.
"""
