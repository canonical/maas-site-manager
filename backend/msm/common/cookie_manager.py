from enum import StrEnum
from typing import Any

from starlette.requests import Request
from starlette.responses import Response

from msm.common.encryptor import Encryptor

MSM_STATE_COOKIE_NAME = "msm.auth_state_cookie"
MSM_NONCE_COOKIE_NAME = "msm.auth_nonce_cookie"

# OAuth2 token cookies
MSM_OAUTH2_ACCESS_TOKEN_COOKIE_NAME = "msm.oauth2_access_token_cookie"
MSM_OAUTH2_ID_TOKEN_COOKIE_NAME = "msm.oauth2_id_token_cookie"
MSM_OAUTH2_REFRESH_TOKEN_COOKIE_NAME = "msm.oauth2_refresh_token_cookie"


class MSMOAuth2Cookie(StrEnum):
    AUTH_STATE = MSM_STATE_COOKIE_NAME
    AUTH_NONCE = MSM_NONCE_COOKIE_NAME
    OAUTH2_ACCESS_TOKEN = MSM_OAUTH2_ACCESS_TOKEN_COOKIE_NAME
    OAUTH2_ID_TOKEN = MSM_OAUTH2_ID_TOKEN_COOKIE_NAME
    OAUTH2_REFRESH_TOKEN = MSM_OAUTH2_REFRESH_TOKEN_COOKIE_NAME


class EncryptedCookieManager:
    """
    Creates a class for working with encrypted cookies.
    """

    def __init__(
        self,
        request: Request,
        encryptor: Encryptor,
        response: Response | None = None,
        ttl_seconds: int = 3600,
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self.request = request
        self.response = response
        self.encryptor = encryptor
        self._pending: list[tuple[str, str, dict[str, Any]]] = []

    def set_auth_cookie(self, key: MSMOAuth2Cookie, value: str) -> None:
        self.set_cookie(
            key=key,
            value=value,
            max_age=self.ttl_seconds,
            httponly=True,
            secure=True,
        )

    def set_cookie(self, key: str, value: str, **opts: Any) -> None:
        encrypted_value = self.encryptor.encrypt(value)
        self._apply_cookie(key, encrypted_value, **opts)

    def set_unsafe_cookie(self, key: str, value: str, **opts: Any) -> None:
        """Sets a cookie without encryption. Use with caution."""
        self._apply_cookie(key, value, **opts)

    def get_unsafe_cookie(self, key: str) -> str | None:
        """Gets a cookie without decryption. Use with caution."""
        return self.request.cookies.get(key)

    def get_cookie(self, key: str) -> str | None:
        encrypted_value = self.request.cookies.get(key)
        if encrypted_value is None:
            return None
        return self.encryptor.decrypt(encrypted_value)

    def clear_cookie(self, key: str) -> None:
        self._apply_cookie(key, "", max_age=0, expires=0)

    def bind_response(self, response: Response) -> None:
        """Binds a response to the cookie manager and sets any pending cookies."""
        self.response = response
        for key, value, opts in self._pending:
            self.response.set_cookie(key=key, value=value, **opts)
        self._pending.clear()

    def _apply_cookie(self, key: str, value: str, **opts: Any) -> None:
        """Helper to either set the cookie immediately or queue it."""
        if self.response:
            self.response.set_cookie(key=key, value=value, **opts)
        else:
            self._pending.append((key, value, opts))
