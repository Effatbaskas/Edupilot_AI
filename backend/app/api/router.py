"""Top-level API router."""

from fastapi import APIRouter

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.materials import router as materials_router
from app.api.quizzes import router as quizzes_router
from app.api.tutor import router as tutor_router
from app.api.performance import router as performance_router
from app.api.roadmap import router as roadmap_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(materials_router)
api_router.include_router(quizzes_router)
api_router.include_router(tutor_router)
api_router.include_router(performance_router)
api_router.include_router(roadmap_router)
