from unittest.mock import PropertyMock

from httpx import AsyncClient, Response
import pytest
from pytest_mock import MockerFixture
from temporalio.exceptions import ApplicationError
from temporalio.testing import ActivityEnvironment

from msm.temporal.activities.worker_refresh import (
    WorkerJwtRefreshParams,
    WorkerRefreshActivities,
)


@pytest.fixture
async def worker_refresh_act(mocker: MockerFixture) -> WorkerRefreshActivities:
    mock_client = mocker.create_autospec(AsyncClient)
    mocker.patch.object(
        WorkerRefreshActivities, "_create_client", return_value=mock_client
    )
    return WorkerRefreshActivities()


class TestWorkerRefreshActivities:
    @pytest.mark.asyncio
    async def test_worker_jwt_refresh_success(
        self,
        mocker: MockerFixture,
        worker_refresh_act: WorkerRefreshActivities,
    ) -> None:
        """Test that a 200 response from the API completes without error."""
        mock_response = mocker.create_autospec(Response)
        type(mock_response).status_code = PropertyMock(return_value=200)
        worker_refresh_act.client.post.return_value = mock_response  # type: ignore[attr-defined]

        params = WorkerJwtRefreshParams(
            msm_base_url="http://test.msm.url",
            msm_jwt="test.jwt.token",
        )
        act_env = ActivityEnvironment()
        await act_env.run(worker_refresh_act.worker_jwt_refresh, params)

        worker_refresh_act.client.post.assert_called_once_with(  # type: ignore[attr-defined]
            "http://test.msm.url/api/v1/worker-refresh",
            headers={"Authorization": "bearer test.jwt.token"},
        )

    @pytest.mark.asyncio
    async def test_worker_jwt_refresh_401_raises_non_retryable(
        self,
        mocker: MockerFixture,
        worker_refresh_act: WorkerRefreshActivities,
    ) -> None:
        """Test that a 401 response raises a non-retryable ApplicationError."""
        mock_response = mocker.create_autospec(Response)
        type(mock_response).status_code = PropertyMock(return_value=401)
        mock_response.text = "Unauthorized"
        worker_refresh_act.client.post.return_value = mock_response  # type: ignore[attr-defined]

        params = WorkerJwtRefreshParams(
            msm_base_url="http://test.msm.url",
            msm_jwt="test.jwt.token",
        )
        act_env = ActivityEnvironment()
        with pytest.raises(ApplicationError) as exc:
            await act_env.run(worker_refresh_act.worker_jwt_refresh, params)
        assert exc.value.non_retryable

    @pytest.mark.asyncio
    async def test_worker_jwt_refresh_404_raises_retryable(
        self,
        mocker: MockerFixture,
        worker_refresh_act: WorkerRefreshActivities,
    ) -> None:
        """Test that a 404 response raises a retryable ApplicationError."""
        mock_response = mocker.create_autospec(Response)
        type(mock_response).status_code = PropertyMock(return_value=404)
        mock_response.text = "Not Found"
        worker_refresh_act.client.post.return_value = mock_response  # type: ignore[attr-defined]

        params = WorkerJwtRefreshParams(
            msm_base_url="http://test.msm.url",
            msm_jwt="test.jwt.token",
        )
        act_env = ActivityEnvironment()
        with pytest.raises(ApplicationError) as exc:
            await act_env.run(worker_refresh_act.worker_jwt_refresh, params)
        assert not exc.value.non_retryable
