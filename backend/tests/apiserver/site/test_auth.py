from collections.abc import Iterator
import uuid

from fastapi import FastAPI
import pytest

from msm.apiserver.db.models import Site
from msm.apiserver.exceptions.catalog import UnauthorizedException
from msm.apiserver.exceptions.constants import ExceptionCode
from msm.apiserver.service import ServiceCollection
from msm.apiserver.site.auth import authenticated_site
from tests.fixtures.app import get_api_routes
from tests.fixtures.client import Client
from tests.fixtures.factory import Factory

AUTHENTICATED_ROUTES = (
    ("POST", "/site/v1/details"),
    ("GET", "/site/v1/enroll"),
    ("POST", "/site/v1/enroll"),
    ("GET", "/site/v1/enroll/refresh"),
    ("GET", "/site/v1/enroll/verify"),
    (
        "GET",
        "/site/v1/images/{track}/{risk}/{boot_source_id}/{file_path:path}",
    ),
    ("GET", "/site/v1/images/{track}/{risk}/streams/v1/{index_path:path}"),
    ("GET", "/site/v1/site-config"),
    ("PATCH", "/site/v1/site-status"),
)


@pytest.fixture
def api_routes(api_app: FastAPI) -> Iterator[set[tuple[str, str]]]:
    yield get_api_routes(api_app, "/site")


def test_all_routes_checked(api_routes: set[tuple[str, str]]) -> None:
    assert api_routes == set(AUTHENTICATED_ROUTES)


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


@pytest.mark.asyncio
class TestAuthenticatedSite:
    async def test_valid_token(
        self,
        api_services: ServiceCollection,
        api_site: Site,
        api_site_auth_id: uuid.UUID,
    ) -> None:
        site = await authenticated_site(api_services, api_site_auth_id)
        assert site == api_site

    async def test_invalid_auth_id(
        self, api_services: ServiceCollection
    ) -> None:
        with pytest.raises(UnauthorizedException) as error:
            await authenticated_site(api_services, uuid.uuid4())
        assert error.value.status_code == 401
        assert error.value.message == "The token is not valid."
        assert error.value.code == ExceptionCode.INVALID_TOKEN

    async def test_update_last_seen(
        self,
        factory: Factory,
        api_services: ServiceCollection,
        api_site: Site,
        api_site_auth_id: uuid.UUID,
    ) -> None:
        # no SiteData entry exists
        assert await factory.get("site_data") == []

        await authenticated_site(api_services, api_site_auth_id)
        # the entry gets created
        [site_data] = await factory.get("site_data")
        assert site_data["site_id"] == api_site.id

        await authenticated_site(api_services, api_site_auth_id)
        # the entry gets updated
        [new_site_data] = await factory.get("site_data")
        assert site_data["last_seen"] < new_site_data["last_seen"]
