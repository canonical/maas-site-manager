from unittest.mock import AsyncMock, patch

import pytest
from typing_extensions import Generator

from msm.temporal.worker import run_worker


class TestWorker:
    """Test class for the Temporal worker."""

    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        """Mock Temporal client."""
        client = AsyncMock()
        return client

    @pytest.fixture
    def mock_worker(self) -> Generator[AsyncMock, None, None]:
        """Mock Temporal worker."""
        with patch("msm.temporal.worker.Worker") as mock_worker_class:
            mock_worker_instance = AsyncMock()
            mock_worker_class.return_value = mock_worker_instance
            yield mock_worker_instance

    @pytest.mark.asyncio
    async def test_run_worker_success(
        self,
        mock_client: AsyncMock,
        mock_worker: AsyncMock,
    ) -> None:
        """Test successful worker initialization and execution."""
        with patch(
            "msm.temporal.worker.Client.connect",
            return_value=mock_client,
        ) as mock_connect:
            await run_worker()

            # Verify client connection
            mock_connect.assert_called_once()

            # Verify worker run was called
            mock_worker.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_worker_client_connection_parameters(
        self,
        mock_client: AsyncMock,
        mock_worker: AsyncMock,
    ) -> None:
        """Test that client is connected with correct parameters."""
        with (
            patch(
                "msm.temporal.worker.Client.connect",
                return_value=mock_client,
            ) as mock_connect,
            patch("msm.temporal.worker.Options") as mock_options,
            patch("msm.temporal.worker.EncryptionOptions") as mock_encryption,
        ):
            await run_worker()

            # Verify encryption options are created
            mock_encryption.assert_called_once()

            # Verify options are created with encryption
            mock_options.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_worker_worker_initialization(
        self,
        mock_client: AsyncMock,
        mock_worker: AsyncMock,
    ) -> None:
        """Test that worker is initialized with correct workflows and activities."""
        with (
            patch(
                "msm.temporal.worker.Client.connect",
                return_value=mock_client,
            ),
            patch("msm.temporal.worker.Worker") as mock_worker_class,
            patch("msm.temporal.worker.WorkerOptions") as mock_worker_options,
            patch("msm.temporal.worker.SentryOptions") as mock_sentry_options,
        ):
            mock_worker_class.return_value = mock_worker

            await run_worker()

            # Verify WorkerOptions and SentryOptions are created
            mock_sentry_options.assert_called_once()
            mock_worker_options.assert_called_once()

            # Verify Worker is initialized
            mock_worker_class.assert_called_once()
            call_args = mock_worker_class.call_args

            # Check that required parameters are present
            assert "client" in call_args.kwargs
            assert "workflows" in call_args.kwargs
            assert "activities" in call_args.kwargs
            assert "worker_opt" in call_args.kwargs

            # Check workflows list length
            assert len(call_args.kwargs["workflows"]) == 6

            # Check activities list length
            assert len(call_args.kwargs["activities"]) == 13
