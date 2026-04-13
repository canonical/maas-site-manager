from collections.abc import Iterator
import uuid

from fastapi import FastAPI
import pytest

from msm.apiserver.db.models import User
from msm.apiserver.db.models.user import Worker
from msm.apiserver.exceptions.catalog import (
    ForbiddenException,
    UnauthorizedException,
)
from msm.apiserver.exceptions.constants import ExceptionCode
from msm.apiserver.service import ServiceCollection
from msm.apiserver.user.auth import (
    authenticated_admin,
    authenticated_user,
    authenticated_worker,
)
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
)

UNAUTHENTICATED_ROUTES = (("POST", "/api/v1/login"),)

ADMIN_ROUTES = (
    ("GET", "/api/v1/settings"),
    ("PATCH", "/api/v1/settings"),
    ("GET", "/api/v1/users"),
    ("POST", "/api/v1/users"),
    ("GET", "/api/v1/users/{id}"),
    ("DELETE", "/api/v1/users/{id}"),
    ("PATCH", "/api/v1/users/{id}"),
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
