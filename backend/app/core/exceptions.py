from fastapi import HTTPException, status


class EduPilotException(Exception):
    """Base exception for EduPilot AI."""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "An unexpected error occurred"

    def __init__(self, detail: str = None):
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)

    def to_http_exception(self) -> HTTPException:
        return HTTPException(status_code=self.status_code, detail=self.detail)


class NotFoundError(EduPilotException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found"


class ForbiddenError(EduPilotException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Access forbidden"


class ValidationError(EduPilotException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "Validation failed"


class AIServiceError(EduPilotException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    detail = "AI service temporarily unavailable"


class ProcessingError(EduPilotException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Processing failed"


class ConflictError(EduPilotException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Resource already exists"


class UnauthorizedError(EduPilotException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Authentication required"
