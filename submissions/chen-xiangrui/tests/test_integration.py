"""
Integration tests for the banking client.

These tests run against the actual banking API server.
Server must be running at http://localhost:8123
"""

import asyncio
from decimal import Decimal

import pytest

from api_client import BankingAPIClient
from config import Config
from models import TransferRequest
from services import TransferService


@pytest.fixture
def config():
    """Create configuration for integration tests."""
    return Config(base_url="http://localhost:8123")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_transfer_flow(config):
    """
    Test complete transfer flow with real API.

    Requires: Banking server running at http://localhost:8123

    To run:
        docker run -d -p 8123:8123 singhacksbjb/sidequest-server:latest
        pytest tests/test_integration.py -m integration
    """
    async with BankingAPIClient(config) as api_client:
        service = TransferService(api_client)

        # Test 1: Validate accounts
        from_valid = await service.validate_account("ACC1000")
        to_valid = await service.validate_account("ACC1001")

        assert from_valid is True, "Source account should be valid"
        assert to_valid is True, "Destination account should be valid"

        # Test 2: Execute transfer
        request = TransferRequest(
            from_account="ACC1000",
            to_account="ACC1001",
            amount=Decimal("50.00"),
        )

        response = await service.transfer(request)

        assert response.status == "SUCCESS"
        assert response.transaction_id is not None
        assert response.from_account == "ACC1000"
        assert response.to_account == "ACC1001"
        assert response.amount == Decimal("50.00")

        print(f"\n✅ Integration test passed!")
        print(f"Transaction ID: {response.transaction_id}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_authenticated_transfer(config):
    """Test transfer with JWT authentication."""
    async with BankingAPIClient(config) as api_client:
        service = TransferService(api_client)

        # Authenticate
        token = await service.authenticate(username="alice", password="any")
        assert token is not None, "Authentication should succeed"

        # Transfer with authentication
        request = TransferRequest(
            from_account="ACC1000",
            to_account="ACC1001",
            amount=Decimal("25.00"),
        )

        response = await service.transfer(request)

        assert response.status == "SUCCESS"
        print(f"\n✅ Authenticated transfer successful!")
        print(f"Transaction ID: {response.transaction_id}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_account_transfer(config):
    """Test transfer with invalid account."""
    async with BankingAPIClient(config) as api_client:
        service = TransferService(api_client)

        # Validate invalid account
        invalid = await service.validate_account("ACC9999")
        assert invalid is False, "Invalid account should fail validation"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_accounts(config):
    """Test listing all accounts."""
    async with BankingAPIClient(config) as api_client:
        service = TransferService(api_client)

        accounts = await service.list_accounts()

        assert len(accounts) > 0, "Should return at least one account"
        print(f"\n✅ Found {len(accounts)} accounts")


if __name__ == "__main__":
    """Run integration tests directly."""
    print("Running integration tests...")
    print("Ensure banking server is running at http://localhost:8123\n")

    config = Config(base_url="http://localhost:8123")

    # Run all tests
    asyncio.run(test_full_transfer_flow(config))
    asyncio.run(test_authenticated_transfer(config))
    asyncio.run(test_invalid_account_transfer(config))
    asyncio.run(test_list_accounts(config))

    print("\n🎉 All integration tests passed!")
