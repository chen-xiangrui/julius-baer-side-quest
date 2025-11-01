"""
Unit tests for the banking client.

Tests use pytest with mock responses to avoid external dependencies.
"""

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api_client import BankingAPIClient
from config import Config
from models import TransferRequest, TransferResponse
from services import TransferService


@pytest.fixture
def config():
    """Create a test configuration."""
    return Config(
        base_url="http://localhost:8123",
        timeout=10,
        max_retries=1,
    )


@pytest.fixture
def mock_session():
    """Create a mock aiohttp session."""
    session = MagicMock()
    return session


class TestTransferRequest:
    """Test TransferRequest model validation."""

    def test_valid_transfer_request(self):
        """Test creating a valid transfer request."""
        request = TransferRequest(
            from_account="ACC1000",
            to_account="ACC1001",
            amount=Decimal("100.00"),
        )

        assert request.from_account == "ACC1000"
        assert request.to_account == "ACC1001"
        assert request.amount == Decimal("100.00")

    def test_empty_from_account(self):
        """Test validation fails with empty from_account."""
        with pytest.raises(ValueError, match="Source account cannot be empty"):
            TransferRequest(
                from_account="",
                to_account="ACC1001",
                amount=Decimal("100.00"),
            )

    def test_empty_to_account(self):
        """Test validation fails with empty to_account."""
        with pytest.raises(ValueError, match="Destination account cannot be empty"):
            TransferRequest(
                from_account="ACC1000",
                to_account="",
                amount=Decimal("100.00"),
            )

    def test_same_accounts(self):
        """Test validation fails when from and to accounts are the same."""
        with pytest.raises(ValueError, match="Source and destination accounts must be different"):
            TransferRequest(
                from_account="ACC1000",
                to_account="ACC1000",
                amount=Decimal("100.00"),
            )

    def test_negative_amount(self):
        """Test validation fails with negative amount."""
        with pytest.raises(ValueError, match="Transfer amount must be positive"):
            TransferRequest(
                from_account="ACC1000",
                to_account="ACC1001",
                amount=Decimal("-50.00"),
            )

    def test_zero_amount(self):
        """Test validation fails with zero amount."""
        with pytest.raises(ValueError, match="Transfer amount must be positive"):
            TransferRequest(
                from_account="ACC1000",
                to_account="ACC1001",
                amount=Decimal("0"),
            )

    def test_to_dict(self):
        """Test conversion to dictionary."""
        request = TransferRequest(
            from_account="ACC1000",
            to_account="ACC1001",
            amount=Decimal("100.00"),
        )

        result = request.to_dict()

        assert result["fromAccount"] == "ACC1000"
        assert result["toAccount"] == "ACC1001"
        assert result["amount"] == 100.00


class TestTransferResponse:
    """Test TransferResponse model."""

    def test_from_dict(self):
        """Test creating TransferResponse from API response."""
        data = {
            "transactionId": "txn-123",
            "status": "SUCCESS",
            "fromAccount": "ACC1000",
            "toAccount": "ACC1001",
            "amount": 100.00,
            "timestamp": "2025-11-01T10:00:00Z",
            "message": "Transfer completed",
        }

        response = TransferResponse.from_dict(data)

        assert response.transaction_id == "txn-123"
        assert response.status == "SUCCESS"
        assert response.from_account == "ACC1000"
        assert response.to_account == "ACC1001"
        assert response.amount == Decimal("100.00")
        assert response.message == "Transfer completed"


class TestBankingAPIClient:
    """Test BankingAPIClient."""

    @pytest.mark.asyncio
    async def test_validate_account_success(self, config):
        """Test account validation success."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            # Setup mock
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"valid": True})
            mock_response.text = AsyncMock(return_value='{"valid": true}')

            mock_session = AsyncMock()
            mock_session.request = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.__aexit__ = AsyncMock()

            mock_session_class.return_value = mock_session

            # Test
            async with BankingAPIClient(config) as client:
                result = await client.validate_account("ACC1000")

                assert result is True

    @pytest.mark.asyncio
    async def test_validate_account_invalid(self, config):
        """Test account validation for invalid account."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            # Setup mock
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"valid": False})
            mock_response.text = AsyncMock(return_value='{"valid": false}')

            mock_session = AsyncMock()
            mock_session.request = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.__aexit__ = AsyncMock()

            mock_session_class.return_value = mock_session

            # Test
            async with BankingAPIClient(config) as client:
                result = await client.validate_account("ACC9999")

                assert result is False

    @pytest.mark.asyncio
    async def test_transfer_success(self, config):
        """Test successful transfer."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            # Setup mock
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={
                    "transactionId": "txn-123",
                    "status": "SUCCESS",
                    "fromAccount": "ACC1000",
                    "toAccount": "ACC1001",
                    "amount": 100.00,
                    "timestamp": "2025-11-01T10:00:00Z",
                }
            )
            mock_response.text = AsyncMock(return_value='{"status": "SUCCESS"}')

            mock_session = AsyncMock()
            mock_session.request = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.__aexit__ = AsyncMock()

            mock_session_class.return_value = mock_session

            # Test
            async with BankingAPIClient(config) as client:
                result = await client.transfer(
                    {
                        "fromAccount": "ACC1000",
                        "toAccount": "ACC1001",
                        "amount": 100.00,
                    }
                )

                assert result["status"] == "SUCCESS"
                assert result["transactionId"] == "txn-123"


class TestTransferService:
    """Test TransferService business logic."""

    @pytest.mark.asyncio
    async def test_transfer_success(self, config):
        """Test successful transfer through service."""
        # Create mock API client
        mock_client = AsyncMock(spec=BankingAPIClient)
        mock_client.transfer = AsyncMock(
            return_value={
                "transactionId": "txn-123",
                "status": "SUCCESS",
                "fromAccount": "ACC1000",
                "toAccount": "ACC1001",
                "amount": 100.00,
                "timestamp": "2025-11-01T10:00:00Z",
            }
        )

        # Test service
        service = TransferService(mock_client)

        request = TransferRequest(
            from_account="ACC1000",
            to_account="ACC1001",
            amount=Decimal("100.00"),
        )

        response = await service.transfer(request)

        assert response.status == "SUCCESS"
        assert response.transaction_id == "txn-123"
        mock_client.transfer.assert_called_once()


class TestConfig:
    """Test configuration management."""

    def test_default_config(self):
        """Test default configuration values."""
        config = Config()

        assert config.base_url == "http://localhost:8123"
        assert config.timeout == 30
        assert config.max_retries == 3

    def test_custom_config(self):
        """Test custom configuration values."""
        config = Config(
            base_url="http://example.com:9000",
            timeout=60,
            max_retries=5,
        )

        assert config.base_url == "http://example.com:9000"
        assert config.timeout == 60
        assert config.max_retries == 5

    def test_config_from_env(self):
        """Test loading configuration from environment variables."""
        with patch.dict(
            "os.environ",
            {
                "BANKING_API_URL": "http://test.com:8080",
                "BANKING_API_TIMEOUT": "45",
            },
        ):
            config = Config.load()

            assert config.base_url == "http://test.com:8080"
            assert config.timeout == 45
