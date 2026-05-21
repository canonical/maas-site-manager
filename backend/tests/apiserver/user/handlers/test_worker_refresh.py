from collections.abc import AsyncIterator
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import FastAPI
import pytest
from pytest_mock import MockerFixture, MockType

from msm.apiserver.db.models import Config, Worker
from msm.common.jwt import TokenAudience, TokenPurpose
from tests.apiserver.conftest import make_api_client
from tests.fixtures.client import Client
from tests.fixtures.factory import Factory


@pytest.fixture
async def api_worker(factory: Factory) -> AsyncIterator[Worker]:
    """A worker with a valid access token in the database."""
    auth_id = uuid4()
    await factory.make_Token(
        auth_id=auth_id,
        audience=TokenAudience.WORKER,
        purpose=TokenPurpose.ACCESS,
    )
    yield Worker(auth_id=auth_id)


@pytest.fixture
async def worker_client(
    api_app: FastAPI, api_config: Config, api_worker: Worker
) -> AsyncIterator[Client]:
    """Authenticated HTTP client acting as a Temporal worker."""
    async with make_api_client(
        api_app, api_config, prefix="/api/v1"
    ) as client:
        client.authenticate(
            api_worker.auth_id,
            token_audience=TokenAudience.WORKER,
            token_purpose=TokenPurpose.ACCESS,
        )
        yield client


@pytest.mark.asyncio
class TestWorkerRefreshPost:
    async def test_authenticated_worker_returns_new_jwt(
        self,
        mocker: MockerFixture,
        worker_client: Client,
        mock_workflow_service: MockType,
    ) -> None:
        """An authenticated worker receives a new JWT in the response."""
        new_jwt = "new-worker-jwt-value"
        mock_workflow_service.refresh_worker_jwt = AsyncMock(
            return_value=new_jwt
        )

        response = await worker_client.post("/worker-refresh")

        assert response.status_code == 200
        assert response.json() == {"token": new_jwt}
        mock_workflow_service.refresh_worker_jwt.assert_called_once()

    async def test_unauthenticated_request_returns_401(
        self,
        api_app: FastAPI,
        api_config: Config,
    ) -> None:
        """A request without a bearer token is rejected with 401."""
        async with make_api_client(
            api_app, api_config, prefix="/api/v1"
        ) as client:
            response = await client.post("/worker-refresh")
        assert response.status_code == 401

    async def test_user_jwt_is_rejected(
        self,
        user_client: Client,
    ) -> None:
        """A request authenticated as a regular user (not a worker) is rejected."""
        response = await user_client.post("/worker-refresh")
        assert response.status_code == 401
