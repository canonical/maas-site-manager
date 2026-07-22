from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from msm.apiserver.db.models import User
from msm.apiserver.db.models.oidc_provider import OIDCProvider
from msm.apiserver.exceptions.constants import ExceptionCode
from msm.apiserver.exceptions.responses import UnauthorizedErrorResponseModel
from msm.common.cookie_manager import MSMOAuth2Cookie
from msm.common.oauth2_client import OAuthInitiateData
from tests.fixtures.client import Client


@pytest.mark.asyncio
async def test_post(app_client: Client, api_admin: User) -> None:
    response = await app_client.post(
        "/api/v1/login",
        data={"username": api_admin.email, "password": "admin"},
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "Bearer"


@pytest.mark.asyncio
async def test_post_fails_with_wrong_password(
    app_client: Client, api_admin: User
) -> None:
    response = await app_client.post(
        "/api/v1/login",
        data={"username": api_admin.email, "password": "incorrect_pass"},
    )
    assert response.status_code == 401
    err = UnauthorizedErrorResponseModel(**response.json())
    assert err.error.code == ExceptionCode.INVALID_CREDENTIALS
    assert err.error.message == "Wrong username or password."


TEST_PROVIDER_1_ID = 1
TEST_PROVIDER_2_ID = 2
TEST_PROVIDER_NAME = "test-provider"


def _make_provider(
    provider_id: int = TEST_PROVIDER_1_ID, name: str = TEST_PROVIDER_NAME
) -> Mock:
    provider = Mock(spec=OIDCProvider)
    provider.id = provider_id
    provider.name = name
    return provider


def _make_user(provider_id: int | None) -> Mock:
    user = Mock(spec=User)
    user.provider_id = provider_id
    return user


@pytest.mark.asyncio
class TestGetLoginInfo:
    BASE_PATH = "/api/v1/login-info"

    async def test_login_info_oidc_enabled_unknown_user(
        self, app_client: Client, mocker: MockerFixture
    ) -> None:
        mocker.patch(
            "msm.apiserver.service.oidc.OIDCService.get_by_enabled",
            return_value=_make_provider(),
        )
        mocker.patch(
            "msm.apiserver.service.user.UserService.get_by_username",
            return_value=None,
        )
        client_mock = Mock()
        client_mock.generate_authorization_url.return_value = (
            OAuthInitiateData(
                authorization_url=(
                    "https://example.com/auth?state=abc123&nonce=def123"
                ),
                state="abc123",
                nonce="def123",
            )
        )
        mocker.patch(
            "msm.apiserver.service.oidc.OIDCService._get_oauth_client",
            return_value=client_mock,
        )
        set_auth_cookie = mocker.patch(
            "msm.common.cookie_manager.EncryptedCookieManager.set_auth_cookie",
            return_value=None,
        )

        response = await app_client.get(
            f"{self.BASE_PATH}"
            "?email=test@example.com&redirect_target=/machines"
        )

        assert response.status_code == 200
        data = response.json()
        assert (
            data["auth_url"]
            == "https://example.com/auth?state=abc123&nonce=def123"
        )
        assert data["provider_name"] == TEST_PROVIDER_NAME
        assert data["oidc"] is True
        client_mock.generate_authorization_url.assert_called_once_with(
            redirect_target="/machines"
        )
        set_auth_cookie.assert_any_call(
            key=MSMOAuth2Cookie.AUTH_STATE, value="abc123"
        )
        set_auth_cookie.assert_any_call(
            key=MSMOAuth2Cookie.AUTH_NONCE, value="def123"
        )

    async def test_login_info_oidc_enabled_local_profile_uses_password(
        self, app_client: Client, mocker: MockerFixture
    ) -> None:
        mocker.patch(
            "msm.apiserver.service.oidc.OIDCService.get_by_enabled",
            return_value=_make_provider(),
        )
        mocker.patch(
            "msm.apiserver.service.user.UserService.get_by_username",
            return_value=_make_user(provider_id=None),
        )
        get_client = mocker.patch(
            "msm.apiserver.service.oidc.OIDCService._get_oauth_client",
        )

        response = await app_client.get(
            f"{self.BASE_PATH}?email=local_user@example.com"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["auth_url"] is None
        assert data["provider_name"] is None
        assert data["oidc"] is False
        get_client.assert_not_called()

    async def test_login_info_oidc_enabled_other_provider_conflict(
        self, app_client: Client, mocker: MockerFixture
    ) -> None:
        mocker.patch(
            "msm.apiserver.service.oidc.OIDCService.get_by_enabled",
            return_value=_make_provider(provider_id=TEST_PROVIDER_1_ID),
        )
        mocker.patch(
            "msm.apiserver.service.user.UserService.get_by_username",
            return_value=_make_user(provider_id=TEST_PROVIDER_2_ID),
        )
        get_client = mocker.patch(
            "msm.apiserver.service.oidc.OIDCService._get_oauth_client",
        )

        response = await app_client.get(
            f"{self.BASE_PATH}?email=other_provider_user@example.com"
        )

        assert response.status_code == 409
        error = response.json()["error"]
        assert error["code"] == ExceptionCode.MISSING_PROVIDER_CONFIG
        assert error["details"][0]["messages"] == [
            "This account is linked to an OIDC provider "
            "that is not currently enabled."
        ]
        get_client.assert_not_called()

    async def test_login_info_oidc_disabled_oidc_bound_profile_conflict(
        self, app_client: Client, mocker: MockerFixture
    ) -> None:
        mocker.patch(
            "msm.apiserver.service.oidc.OIDCService.get_by_enabled",
            return_value=None,
        )
        mocker.patch(
            "msm.apiserver.service.user.UserService.get_by_username",
            return_value=_make_user(provider_id=7),
        )
        get_client = mocker.patch(
            "msm.apiserver.service.oidc.OIDCService._get_oauth_client",
        )

        response = await app_client.get(
            f"{self.BASE_PATH}?email=oidc_user@example.com"
        )

        assert response.status_code == 409
        error = response.json()["error"]
        assert error["code"] == ExceptionCode.MISSING_PROVIDER_CONFIG
        get_client.assert_not_called()

    async def test_login_info_oidc_disabled_local_user_allowed(
        self, app_client: Client, mocker: MockerFixture
    ) -> None:
        mocker.patch(
            "msm.apiserver.service.oidc.OIDCService.get_by_enabled",
            return_value=None,
        )
        mocker.patch(
            "msm.apiserver.service.user.UserService.get_by_username",
            return_value=_make_user(provider_id=None),
        )
        get_client = mocker.patch(
            "msm.apiserver.service.oidc.OIDCService._get_oauth_client",
        )

        response = await app_client.get(
            f"{self.BASE_PATH}?email=local_user@example.com"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["auth_url"] is None
        assert data["provider_name"] is None
        assert data["oidc"] is False
        get_client.assert_not_called()


@pytest.mark.asyncio
async def test_post_logout_revokes_oidc_tokens_and_clears_cookies(
    app_client: Client, mocker: MockerFixture
) -> None:
    get_cookie = mocker.patch(
        "msm.common.cookie_manager.EncryptedCookieManager.get_cookie",
        side_effect=["id-token", "refresh-token"],
    )
    revoke_token = mocker.patch(
        "msm.apiserver.service.oidc.OIDCService.revoke_token",
        return_value=None,
    )
    clear_cookie = mocker.patch(
        "msm.common.cookie_manager.EncryptedCookieManager.clear_cookie",
        return_value=None,
    )

    response = await app_client.post("/api/v1/logout")

    assert response.status_code == 204
    assert not response.content
    assert get_cookie.call_count == 2
    revoke_token.assert_awaited_once_with(
        id_token="id-token", refresh_token="refresh-token"
    )
    clear_cookie.assert_any_call(key=MSMOAuth2Cookie.OAUTH2_ACCESS_TOKEN)
    clear_cookie.assert_any_call(key=MSMOAuth2Cookie.OAUTH2_ID_TOKEN)
    clear_cookie.assert_any_call(key=MSMOAuth2Cookie.OAUTH2_REFRESH_TOKEN)
    assert clear_cookie.call_count == 3
