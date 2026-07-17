from enum import StrEnum


class ExceptionCode(StrEnum):
    ALREADY_EXISTS = "AlreadyExists"
    CONFLICT = "Conflict"
    INVALID_CREDENTIALS = "InvalidCredentials"
    INVALID_PARAMS = "InvalidParameters"
    INVALID_PENDING_SITES = "InvalidPendingSites"
    INVALID_TOKEN = "InvalidToken"
    MISSING_PROVIDER_CONFIG = "MissingProviderConfig"
    MISSING_RESOURCE = "MissingResource"
    MISSING_PERMISSIONS = "MissingPermissions"
    NOT_AUTHENTICATED = "NotAuthenticated"
    FILE_TOO_LARGE = "FileTooLarge"
    PROVIDER_COMMUNICATION_FAILED = "ProviderCommunicationFailed"
