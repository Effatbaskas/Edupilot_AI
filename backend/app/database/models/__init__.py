# Import all models so Alembic can discover them and relationships resolve correctly
from app.database.models.user import User, UserRole
from app.database.models.material import LearningMaterial, MaterialStatus
from app.database.models.material_chunk import MaterialChunk
from app.database.models.chat import AIChat, ChatRole
from app.database.models.quiz import Quiz, QuizDifficulty, QuizType, QuizStatus
from app.database.models.question import Question, QuestionType
from app.database.models.attempt import QuizAttempt
from app.database.models.performance import Performance
from app.database.models.roadmap import Roadmap, StudyTask, TaskType, TaskPriority, TaskStatus

# Used by main.py to trigger model registration
__all_models__ = [
    User,
    LearningMaterial,
    MaterialChunk,
    AIChat,
    Quiz,
    Question,
    QuizAttempt,
    Performance,
    Roadmap,
    StudyTask,
]

__all__ = [
    "User",
    "UserRole",
    "LearningMaterial",
    "MaterialStatus",
    "MaterialChunk",
    "AIChat",
    "ChatRole",
    "Quiz",
    "QuizDifficulty",
    "QuizType",
    "QuizStatus",
    "Question",
    "QuestionType",
    "QuizAttempt",
    "Performance",
    "Roadmap",
    "StudyTask",
    "TaskType",
    "TaskPriority",
    "TaskStatus",
    "__all_models__",
]
