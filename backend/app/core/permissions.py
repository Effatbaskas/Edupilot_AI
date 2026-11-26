from uuid import UUID

from fastapi import HTTPException, status


def check_material_ownership(material, user) -> None:
    """Raise 403 if the user does not own the material."""
    if str(material.user_id) != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this material",
        )


def check_quiz_ownership(quiz, user) -> None:
    """Raise 403 if the user does not own the quiz."""
    if str(quiz.user_id) != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this quiz",
        )


def check_data_isolation(resource_user_id: UUID, current_user_id: UUID) -> None:
    """Raise 403 if resource belongs to a different user (strict isolation)."""
    if str(resource_user_id) != str(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: data isolation policy violation",
        )
