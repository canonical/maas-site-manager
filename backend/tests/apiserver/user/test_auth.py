from collections.abc import Iterator
from unittest.mock import AsyncMock, Mock
import uuid

from fastapi import FastAPI
import pytest

from msm.apiserver.db.models import User
from msm.apiserver.db.models.user import Worker
from msm.apiserver.exceptions.catalog import (
    BadGatewayException,
    ForbiddenException,
    UnauthorizedException,
)
from msm.apiserver.exceptions.constants import ExceptionCode
from msm.apiserver.service import ServiceCollection
from msm.apiserver.user.auth import (
    authenticated_admin,
    authenticated_user,
    authenticated_worker,
    oidc_authenticated_user,
)
from msm.common.cookie_manager import MSMOAuth2Cookie
from msm.common.oauth2_client import OAuthRefreshData
from tests.fixtures.app import get_api_routes
from tests.fixtures.client import Client

AUTHENTICATED_ROUTES = (
    ("GET", "/api/v1/refresh-index"),
    ("GET", "/api/v1/bootasset-sources"),
    ("GET", "/api/v1/bootasset-sources/{id}"),
    ("POST", "/api/v1/bootasset-sources"),
    ("PATCH", "/api/v1/bootasset-sources/{id}"),
    ("DELETE", "/api/v1/bootasset-sources/{id}"),
    ("GET", "/api/v1/bootasset-sources/{id}/versions"),
    ("PUT", "/api/v1/bootasset-sources/{id}/assets"),
    ("PUT", "/api/v1/bootasset-sources/{id}/available-selections"),
    ("GET", "/api/v1/bootasset-sources/{id}/selections"),
    ("POST", "/api/v1/images"),
    ("POST", "/api/v1/images:remove"),
    ("GET", "/api/v1/image-sources"),
    ("PATCH", "/api/v1/bootasset-items/{id}"),
    ("GET", "/api/v1/selectable-images"),
    ("POST", "/api/v1/selectable-images:select"),
    ("GET", "/api/v1/bootasset-items/{id}"),
    ("GET", "/api/v1/external-auth"),
    ("POST", "/api/v1/external-auth"),
    ("PATCH", "/api/v1/external-auth/{id}"),
    ("DELETE", "/api/v1/external-auth/{id}"),
    ("GET", "/api/v1/selected-images"),
    ("POST", "/api/v1/selected-images:remove"),
    ("GET", "/api/v1/settings"),
    ("PATCH", "/api/v1/settings"),
    ("GET", "/api/v1/sites"),
    ("GET", "/api/v1/sites/coordinates"),
    ("GET", "/api/v1/sites/pending"),
    ("POST", "/api/v1/sites/pending"),
    ("GET", "/api/v1/sites/{id}"),
    ("PATCH", "/api/v1/sites/{id}"),
    ("DELETE", "/api/v1/sites/{id}"),
    ("DELETE", "/api/v1/sites"),
    ("GET", "/api/v1/site-status/{site_id}"),
    ("POST", "/api/v1/bootasset-versions:remove"),
    ("GET", "/api/v1/tokens"),
    ("POST", "/api/v1/tokens"),
    ("DELETE", "/api/v1/tokens"),
    ("GET", "/api/v1/tokens/export"),
    ("DELETE", "/api/v1/tokens/{id}"),
    ("GET", "/api/v1/users"),
    ("POST", "/api/v1/users"),
    ("GET", "/api/v1/users/me"),
    ("PATCH", "/api/v1/users/me"),
    ("PATCH", "/api/v1/users/me/password"),
    ("GET", "/api/v1/users/{id}"),
    ("PATCH", "/api/v1/users/{id}"),
    ("DELETE", "/api/v1/users/{id}"),
    ("GET", "/api/v1/profiles"),
    ("GET", "/api/v1/profiles/{id}"),
    ("POST", "/api/v1/profiles"),
    ("DELETE", "/api/v1/profiles/{id}"),
    ("PATCH", "/api/v1/profiles/{id}"),
    ("POST", "/api/v1/worker-refresh"),
)

UNAUTHENTICATED_ROUTES = (
    ("GET", "/api/v1/login-info"),
    ("POST", "/api/v1/login"),
    ("POST", "/api/v1/logout"),
    ("GET", "/api/v1/external-auth/callback"),
)

ADMIN_ROUTES = (
    ("GET", "/api/v1/settings"),
    ("PATCH", "/api/v1/settings"),
    ("GET", "/api/v1/users"),
    ("POST", "/api/v1/users"),
    ("GET", "/api/v1/users/{id}"),
    ("DELETE", "/api/v1/users/{id}"),
    ("PATCH", "/api/v1/users/{id}"),
    ("GET", "/api/v1/external-auth"),
    ("POST", "/api/v1/external-auth"),
    ("PATCH", "/api/v1/external-auth/{id}"),
    ("DELETE", "/api/v1/external-auth/{id}"),
)


@pytest.fixture
def api_routes(api_app: FastAPI) -> Iterator[set[tuple[str, str]]]:
    yield get_api_routes(api_app, "/api")


def test_all_routes_checked(api_routes: set[tuple[str, str]]) -> None:
    assert api_routes == set(AUTHENTICATED_ROUTES + UNAUTHENTICATED_ROUTES)


@pytest.mark.asyncio
class TestAuthentication:
    @pytest.mark.parametrize("method,url", AUTHENTICATED_ROUTES)
    async def test_handler_auth_required(
        self, app_client: Client, method: str, url: str
    ) -> None:
        response = await app_client.request(method, url)
        assert (
            response.status_code == 401
        ), f"Auth should be required for {method} {url}"

    @pytest.mark.parametrize("method,url", UNAUTHENTICATED_ROUTES)
    async def test_handler_auth_not_required(
        self, app_client: Client, method: str, url: str
    ) -> None:
        response = await app_client.request(method, url)
        assert not response.is_server_error
        assert (
            response.status_code != 401
        ), f"Auth should not be required for {method} {url}"

    @pytest.mark.parametrize("method,url", ADMIN_ROUTES)
    async def test_handler_admin_required(
        self,
        app_client: Client,
        api_user: User,
        method: str,
        url: str,
    ) -> None:
        app_client.authenticate(api_user.auth_id)
        response = await app_client.request(method, url)
        assert (
            response.status_code == 403
        ), f"Admin should be required for {method} {url}"


@pytest.mark.asyncio
class TestAuthenticatedUser:
    async def test_valid_token(
        self,
        api_services: ServiceCollection,
        api_user: User,
    ) -> None:
        user = await authenticated_user(api_services, api_user.auth_id)
        assert user == api_user

    async def test_invalid_auth_id(
        self, api_services: ServiceCollection
    ) -> None:
        with pytest.raises(UnauthorizedException) as error:
            await authenticated_user(api_services, uuid.uuid4())
        assert error.value.status_code == 401
        assert error.value.message == "The token is not valid."
        assert error.value.code == ExceptionCode.INVALID_TOKEN


@pytest.mark.asyncio
class TestAuthenticatedWorker:
    async def test_valid_token(
        self,
        api_services: ServiceCollection,
        api_worker: Worker,
    ) -> None:
        worker = await authenticated_worker(api_services, api_worker.auth_id)
        assert worker == api_worker

    async def test_invalid_auth_id(
        self, api_services: ServiceCollection
    ) -> None:
        with pytest.raises(UnauthorizedException) as error:
            await authenticated_worker(api_services, uuid.uuid4())
        assert error.value.status_code == 401
        assert error.value.message == "The token is not valid."
        assert error.value.code == ExceptionCode.INVALID_TOKEN


class TestAuthenticatedAdmin:
    def test_admin(
        self,
        api_admin: User,
    ) -> None:
        admin = authenticated_admin(api_admin)
        assert admin == api_admin

    def test_not_admin(self, api_user: User) -> None:
        with pytest.raises(ForbiddenException) as error:
            authenticated_admin(api_user)
        assert error.value.message == "Unauthorized credentials."
        assert error.value.code == ExceptionCode.MISSING_PERMISSIONS
        assert error.value.status_code == 403


def make_cookie_manager(
    access_token: str | None = None,
    id_token: str | None = None,
    refresh_token: str | None = None,
) -> Mock:
    cookies = {
        MSMOAuth2Cookie.OAUTH2_ACCESS_TOKEN: access_token,
        MSMOAuth2Cookie.OAUTH2_ID_TOKEN: id_token,
        MSMOAuth2Cookie.OAUTH2_REFRESH_TOKEN: refresh_token,
    }
    manager = Mock()
    manager.get_cookie = Mock(side_effect=lambda key: cookies.get(key))
    manager.set_auth_cookie = Mock()
    manager.clear_cookie = Mock()
    return manager


def make_oidc_services(
    user: User | Mock | None = None,
    access_token_valid: bool = True,
    refresh_result: OAuthRefreshData | None = None,
    refresh_error: Exception | None = None,
) -> Mock:
    oidc = Mock()
    if access_token_valid:
        oidc.validate_access_token = AsyncMock(return_value="valid")
    else:
        oidc.validate_access_token = AsyncMock(
            side_effect=UnauthorizedException(
                code=ExceptionCode.INVALID_TOKEN,
                message="invalid",
                details=[],
            )
        )
    if refresh_error is not None:
        oidc.refresh_access_token = AsyncMock(side_effect=refresh_error)
    else:
        oidc.refresh_access_token = AsyncMock(return_value=refresh_result)
    oidc.get_user_from_id_token = AsyncMock(return_value=user)
    services = Mock(spec=ServiceCollection)
    services.oidc = oidc
    return services


@pytest.mark.asyncio
class TestOIDCAuthenticatedUser:
    async def test_valid_access_token_returns_user(
        self, api_user: User
    ) -> None:
        cookie_manager = make_cookie_manager(
            access_token="access",
            id_token="id",
            refresh_token="refresh",
        )
        services = make_oidc_services(user=api_user, access_token_valid=True)

        user = await oidc_authenticated_user(cookie_manager, services)

        assert user == api_user
        services.oidc.refresh_access_token.assert_not_awaited()
        services.oidc.get_user_from_id_token.assert_awaited_once_with("id")
        cookie_manager.set_auth_cookie.assert_not_called()

    async def test_missing_id_token_rejects_and_clears_cookies(self) -> None:
        cookie_manager = make_cookie_manager(
            access_token="access",
            id_token=None,
            refresh_token="refresh",
        )
        services = make_oidc_services()

        with pytest.raises(UnauthorizedException) as error:
            await oidc_authenticated_user(cookie_manager, services)

        assert error.value.code == ExceptionCode.NOT_AUTHENTICATED
        assert cookie_manager.clear_cookie.call_count == 3

    async def test_missing_refresh_token_rejects_and_clears_cookies(
        self,
    ) -> None:
        cookie_manager = make_cookie_manager(
            access_token="access",
            id_token="id",
            refresh_token=None,
        )
        services = make_oidc_services()

        with pytest.raises(UnauthorizedException) as error:
            await oidc_authenticated_user(cookie_manager, services)

        assert error.value.code == ExceptionCode.NOT_AUTHENTICATED
        assert cookie_manager.clear_cookie.call_count == 3

    async def test_invalid_access_token_refreshes_and_returns_user(
        self, api_user: User
    ) -> None:
        cookie_manager = make_cookie_manager(
            access_token="expired",
            id_token="id",
            refresh_token="refresh",
        )
        services = make_oidc_services(
            user=api_user,
            access_token_valid=False,
            refresh_result=OAuthRefreshData(
                access_token="new-access", refresh_token="new-refresh"
            ),
        )

        user = await oidc_authenticated_user(cookie_manager, services)

        assert user == api_user
        services.oidc.refresh_access_token.assert_awaited_once_with("refresh")
        cookie_manager.set_auth_cookie.assert_any_call(
            key=MSMOAuth2Cookie.OAUTH2_ACCESS_TOKEN, value="new-access"
        )
        cookie_manager.set_auth_cookie.assert_any_call(
            key=MSMOAuth2Cookie.OAUTH2_REFRESH_TOKEN, value="new-refresh"
        )

    async def test_refresh_keeps_refresh_cookie_when_unchanged(
        self, api_user: User
    ) -> None:
        cookie_manager = make_cookie_manager(
            access_token="expired",
            id_token="id",
            refresh_token="refresh",
        )
        services = make_oidc_services(
            user=api_user,
            access_token_valid=False,
            refresh_result=OAuthRefreshData(
                access_token="new-access", refresh_token="refresh"
            ),
        )

        await oidc_authenticated_user(cookie_manager, services)

        cookie_manager.set_auth_cookie.assert_called_once_with(
            key=MSMOAuth2Cookie.OAUTH2_ACCESS_TOKEN, value="new-access"
        )

    async def test_refresh_failure_rejects_and_clears_cookies(self) -> None:
        cookie_manager = make_cookie_manager(
            access_token="expired",
            id_token="id",
            refresh_token="refresh",
        )
        services = make_oidc_services(
            access_token_valid=False,
            refresh_error=BadGatewayException(
                code=ExceptionCode.PROVIDER_COMMUNICATION_FAILED,
                message="boom",
                details=[],
            ),
        )

        with pytest.raises(UnauthorizedException) as error:
            await oidc_authenticated_user(cookie_manager, services)

        assert error.value.code == ExceptionCode.INVALID_TOKEN
        assert cookie_manager.clear_cookie.call_count == 3
        services.oidc.get_user_from_id_token.assert_not_awaited()
