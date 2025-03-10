"""Exception handling for the API"""

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from msm.api.exceptions.catalog import (
    BadRequestException,
    FileTooLargeException,
    ForbiddenException,
    MsmBaseException,
    NotFoundException,
    UnauthorizedException,
)
from msm.api.exceptions.responses import (
    BadRequestErrorBodyResponse,
    BadRequestErrorResponse,
    BadRequestErrorResponseModel,
    ErrorBodyResponse,
    ErrorResponse,
    ErrorResponseModel,
    FileTooLargeErrorBodyResponse,
    FileTooLargeErrorResponse,
    FileTooLargeErrorResponseModel,
    ForbiddenErrorBodyResponse,
    ForbiddenErrorResponse,
    ForbiddenErrorResponseModel,
    NotFoundErrorBodyResponse,
    NotFoundErrorResponse,
    NotFoundErrorResponseModel,
    UnauthorizedErrorBodyResponse,
    UnauthorizedErrorResponse,
    UnauthorizedErrorResponseModel,
    ValidationErrorBodyResponse,
    ValidationErrorResponse,
    ValidationErrorResponseModel,
)


class ExceptionMiddleware(BaseHTTPMiddleware):
    """Middleware to catch all the custom defined exceptions."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        try:
            return await call_next(request)
        except BadRequestException as e:
            return BadRequestErrorResponse(
                err=BadRequestErrorResponseModel(
                    error=BadRequestErrorBodyResponse.from_exc(e)
                )
            )
        except UnauthorizedException as e:
            return UnauthorizedErrorResponse(
                err=UnauthorizedErrorResponseModel(
                    error=UnauthorizedErrorBodyResponse.from_exc(e)
                )
            )
        except ForbiddenException as e:
            return ForbiddenErrorResponse(
                err=ForbiddenErrorResponseModel(
                    error=ForbiddenErrorBodyResponse.from_exc(e)
                )
            )
        except NotFoundException as e:
            return NotFoundErrorResponse(
                err=NotFoundErrorResponseModel(
                    error=NotFoundErrorBodyResponse.from_exc(e)
                )
            )
        except FileTooLargeException as e:
            return FileTooLargeErrorResponse(
                err=FileTooLargeErrorResponseModel(
                    error=FileTooLargeErrorBodyResponse.from_exc(e)
                )
            )
        except MsmBaseException as e:
            return ErrorResponse(
                err=ErrorResponseModel(error=ErrorBodyResponse.from_exc(e))
            )


async def request_validation_error_handler(
    request: Request, exc: Exception
) -> ValidationErrorResponse:
    """Middleware to handle RequestValidationError exceptions."""
    assert isinstance(exc, RequestValidationError)
    err = ValidationErrorResponseModel(
        error=ValidationErrorBodyResponse.from_validation_exc(exc)
    )

    return ValidationErrorResponse(err=err)
