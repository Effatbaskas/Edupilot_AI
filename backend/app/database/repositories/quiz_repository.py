from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.quiz import Quiz
from app.database.models.question import Question
from app.database.models.attempt import QuizAttempt


class QuizRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_quiz_with_questions(
        self,
        user_id: UUID,
        title: str,
        topic: str,
        difficulty: str,
        quiz_type: str,
        material_id: Optional[UUID],
        questions_data: List[Dict],
    ) -> Quiz:
        quiz = Quiz(
            user_id=user_id,
            material_id=material_id,
            title=title,
            topic=topic,
            difficulty=difficulty,
            quiz_type=quiz_type,
            total_questions=len(questions_data),
        )
        self.db.add(quiz)
        await self.db.flush()

        for idx, q_data in enumerate(questions_data):
            question = Question(
                quiz_id=quiz.id,
                question_text=q_data["question_text"],
                question_type=q_data.get("question_type", "mcq"),
                options=q_data.get("options"),
                correct_answer=q_data["correct_answer"],
                explanation=q_data.get("explanation"),
                topic=q_data.get("topic", topic),
                difficulty=q_data.get("difficulty", difficulty),
                order_index=idx,
            )
            self.db.add(question)

        await self.db.flush()
        await self.db.refresh(quiz)
        return quiz

    async def get_quiz(
        self,
        quiz_id: UUID,
        user_id: Optional[UUID] = None,
        load_questions: bool = True,
    ) -> Optional[Quiz]:
        query = select(Quiz).where(Quiz.id == quiz_id)
        if user_id:
            query = query.where(Quiz.user_id == user_id)
        if load_questions:
            query = query.options(selectinload(Quiz.questions))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_quizzes(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Quiz]:
        result = await self.db.execute(
            select(Quiz)
            .where(Quiz.user_id == user_id)
            .order_by(Quiz.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def save_attempt(
        self,
        quiz_id: UUID,
        user_id: UUID,
        answers: Dict[str, str],
        time_taken_seconds: Optional[int],
        questions: List[Question],
    ) -> Tuple[QuizAttempt, List[Dict]]:
        """Score the attempt server-side and persist it."""
        correct_count = 0
        results = []

        for question in questions:
            q_id = str(question.id)
            user_answer = answers.get(q_id, "").strip().lower()
            correct = question.correct_answer.strip().lower()
            is_correct = user_answer == correct
            if is_correct:
                correct_count += 1
            results.append({
                "question_id": question.id,
                "question_text": question.question_text,
                "your_answer": answers.get(q_id, ""),
                "correct_answer": question.correct_answer,
                "is_correct": is_correct,
                "explanation": question.explanation,
                "topic": question.topic,
            })

        total = len(questions)
        score = (correct_count / total * 100) if total > 0 else 0.0

        attempt = QuizAttempt(
            quiz_id=quiz_id,
            user_id=user_id,
            answers=answers,
            score=score,
            total_questions=total,
            correct_count=correct_count,
            time_taken_seconds=time_taken_seconds,
            completed_at=datetime.now(timezone.utc),
        )
        self.db.add(attempt)
        await self.db.flush()
        await self.db.refresh(attempt)
        return attempt, results

    async def get_attempts(
        self,
        user_id: UUID,
        quiz_id: Optional[UUID] = None,
        limit: int = 20,
    ) -> List[QuizAttempt]:
        query = select(QuizAttempt).where(QuizAttempt.user_id == user_id)
        if quiz_id:
            query = query.where(QuizAttempt.quiz_id == quiz_id)
        result = await self.db.execute(
            query.order_by(QuizAttempt.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
