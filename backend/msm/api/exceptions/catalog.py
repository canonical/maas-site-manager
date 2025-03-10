from fastapi import status
from pydantic import BaseModel

from msm.api.exceptions.constants import ExceptionCode


class BaseExceptionDetail(BaseModel):
    """Additional details for an exception."""

    reason: str
    messages: list[str]
    field: str | None = None
    location: str | None = None


class MsmBaseException(Exception):
    """Base exception from which all the custom exception must inherit."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(
        self,
        message: str,
        code: ExceptionCode,
        details: list[BaseExceptionDetail] | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


class BadRequestException(MsmBaseException):
    status_code = status.HTTP_400_BAD_REQUEST


class UnauthorizedException(MsmBaseException):
    status_code = status.HTTP_401_UNAUTHORIZED


class ForbiddenException(MsmBaseException):
    status_code = status.HTTP_403_FORBIDDEN


class NotFoundException(MsmBaseException):
    status_code = status.HTTP_404_NOT_FOUND


class FileTooLargeException(MsmBaseException):
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE


class InternalServerErrorException(MsmBaseException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
