from typing import Any, Generic, Self, TypeVar

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from msm.api.exceptions.catalog import (
    BaseExceptionDetail,
    MsmBaseException,
)
from msm.api.exceptions.constants import ExceptionCode


def _build_json_path(loc: list[Any]) -> str:
    elements: list[str] = []
    for l in loc:
        if isinstance(l, int) and elements:
            elements.append(f"{elements.pop()}[{l}]")
        else:
            elements.append(str(l))
    return ".".join(elements)


class ErrorBodyResponse(BaseModel):
    """Model for the error response body.

    Attributes:
        code: The exception code.
        message: A message explaining what went wrong.
        details: An optional list of additional details. Usually only used with
          RequestValidationError.
        status_code: The HTTP status code to be returned to the client.
    """

    code: ExceptionCode
    message: str
    details: list[BaseExceptionDetail] | None = None
    status_code: int = Field(
        default=status.HTTP_500_INTERNAL_SERVER_ERROR, exclude=True
    )

    @classmethod
    def from_exc(cls, exc: MsmBaseException) -> Self:
        return cls(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            status_code=exc.status_code,
        )


E = TypeVar("E", bound=ErrorBodyResponse)


class ErrorResponseModel(BaseModel, Generic[E]):
    error: E


class ValidationErrorBodyResponse(ErrorBodyResponse):
    code: ExceptionCode = ExceptionCode.INVALID_PARAMS
    message: str = "One or more request parameters are invalid"
    status_code: int = Field(
        status.HTTP_422_UNPROCESSABLE_ENTITY, exclude=True
    )

    @classmethod
    def from_validation_exc(cls, exc: RequestValidationError) -> Self:
        """Constructor for RequestValidationError.

        FastAPI raises a RequestValidationError for any validation error that
        occurs during the request processing, from JSON decoder errors to pydantic
        field/model validation issues.

        Each error in the `exc.errors()` is an instance of `pydantic_core.ErrorDetails`
        that has the following attributes:
            type: the name of the error
            msg: the description of the error
            loc: a tuple explaining where the failure happened. The first item
              could be one of: path, query, header, cookie, body. The next items
              specify the path of the wrong field. E.g. if the passed json is in
              the form `{"foo": {"bar": [0, "wrong-field"]}}` the loc parameter
              would be something like `(<location>, "foo", "bar", 1)`.
            ctx: additional context regarding the input data.

        Attributes:
            exc: The RequestValidationError raised by FastAPI.
        """
        details: list[BaseExceptionDetail] = []
        for err in exc.errors():
            d = BaseExceptionDetail(
                reason="".join(x for x in err["type"].title() if x.isalnum()),
                messages=[err["msg"]],
                location=err["loc"][0],
                field=_build_json_path(err["loc"][1:]),
            )
            if ctx := err.get("ctx", None):
                if loc := ctx.get("loc", None):
                    d.field = loc
                if msg := ctx.get("reason", None):
                    d.messages = [msg]

            details.append(d)
        return cls(
            code=ExceptionCode.INVALID_PARAMS,
            message="One or more request parameters are invalid",
            details=details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class ValidationErrorResponseModel(
    ErrorResponseModel[ValidationErrorBodyResponse]
):
    pass


class ValidationErrorResponse(JSONResponse):
    def __init__(self, err: ValidationErrorResponseModel):
        super().__init__(
            content=jsonable_encoder(err, exclude_none=True),
            status_code=err.error.status_code,
        )


class BadRequestErrorBodyResponse(ErrorBodyResponse):
    code: ExceptionCode = ExceptionCode.ALREADY_EXISTS
    message: str = "Bad Request"
    status_code: int = Field(status.HTTP_400_BAD_REQUEST, exclude=True)


class BadRequestErrorResponseModel(
    ErrorResponseModel[BadRequestErrorBodyResponse]
):
    pass


class BadRequestErrorResponse(JSONResponse):
    def __init__(self, err: BadRequestErrorResponseModel):
        super().__init__(
            content=jsonable_encoder(err, exclude_none=True),
            status_code=err.error.status_code,
        )


class UnauthorizedErrorBodyResponse(ErrorBodyResponse):
    code: ExceptionCode = ExceptionCode.INVALID_CREDENTIALS
    message: str = "Not authenticated"
    status_code: int = Field(status.HTTP_401_UNAUTHORIZED, exclude=True)


class UnauthorizedErrorResponseModel(
    ErrorResponseModel[UnauthorizedErrorBodyResponse]
):
    pass


class UnauthorizedErrorResponse(JSONResponse):
    def __init__(self, err: UnauthorizedErrorResponseModel):
        super().__init__(
            content=jsonable_encoder(err, exclude_none=True),
            status_code=err.error.status_code,
        )


class ForbiddenErrorBodyResponse(ErrorBodyResponse):
    code: ExceptionCode = ExceptionCode.MISSING_PERMISSIONS
    message: str = "Insufficient permissions"
    status_code: int = Field(status.HTTP_403_FORBIDDEN, exclude=True)


class ForbiddenErrorResponseModel(
    ErrorResponseModel[ForbiddenErrorBodyResponse]
):
    pass


class ForbiddenErrorResponse(JSONResponse):
    def __init__(self, err: ForbiddenErrorResponseModel):
        super().__init__(
            content=jsonable_encoder(err, exclude_none=True),
            status_code=err.error.status_code,
        )


class NotFoundErrorBodyResponse(ErrorBodyResponse):
    code: ExceptionCode = ExceptionCode.MISSING_RESOURCE
    message: str = "Resource not found"
    status_code: int = Field(status.HTTP_404_NOT_FOUND, exclude=True)


class NotFoundErrorResponseModel(
    ErrorResponseModel[NotFoundErrorBodyResponse]
):
    pass


class NotFoundErrorResponse(JSONResponse):
    def __init__(self, err: NotFoundErrorResponseModel):
        super().__init__(
            content=jsonable_encoder(err, exclude_none=True),
            status_code=err.error.status_code,
        )


class FileTooLargeErrorBodyResponse(ErrorBodyResponse):
    code: ExceptionCode = ExceptionCode.FILE_TOO_LARGE
    message: str = "Uploaded file is too large"
    status_code: int = Field(
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, exclude=True
    )


class FileTooLargeErrorResponseModel(
    ErrorResponseModel[FileTooLargeErrorBodyResponse]
):
    pass


class FileTooLargeErrorResponse(JSONResponse):
    def __init__(self, err: FileTooLargeErrorResponseModel):
        super().__init__(
            content=jsonable_encoder(err, exclude_none=True),
            status_code=err.error.status_code,
        )


class ErrorResponse(JSONResponse):
    def __init__(self, err: ErrorResponseModel[ErrorBodyResponse]):
        super().__init__(
            content=jsonable_encoder(err, exclude_none=True),
            status_code=err.error.status_code,
        )
