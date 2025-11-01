"""
Business logic services for banking operations.

Implements the service layer pattern to separate business logic
from API client and presentation concerns.
"""

import logging
from typing import Optional

from api_client import BankingAPIClient
from models import TransferRequest, TransferResponse

logger = logging.getLogger(__name__)


class TransferService:
    """
    Service for handling fund transfer operations.

    Implements business logic and validation for transfers,
    delegating HTTP operations to the API client.
    """

    def __init__(self, api_client: BankingAPIClient):
        """
        Initialize the transfer service.

        Args:
            api_client: Banking API client instance
        """
        self.api_client = api_client

    async def authenticate(
        self, username: str = "alice", password: str = "any"
    ) -> Optional[str]:
        """
        Authenticate and retrieve JWT token.

        Args:
            username: Username for authentication
            password: Password for authentication

        Returns:
            str: JWT token, or None if authentication fails
        """
        try:
            token = await self.api_client.get_auth_token(
                username=username, password=password, claim="transfer"
            )
            self.api_client.set_auth_token(token)
            logger.info("Authentication successful")
            return token

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return None

    async def validate_account(self, account_number: str) -> bool:
        """
        Validate an account number.

        Args:
            account_number: Account number to validate

        Returns:
            bool: True if account is valid
        """
        try:
            return await self.api_client.validate_account(account_number)
        except Exception as e:
            logger.error(f"Account validation error for {account_number}: {e}")
            return False

    async def transfer(self, request: TransferRequest) -> TransferResponse:
        """
        Execute a fund transfer.

        Args:
            request: TransferRequest object with transfer details

        Returns:
            TransferResponse: Response with transaction details

        Raises:
            ValueError: If request validation fails
            BankingAPIError: If transfer fails
        """
        logger.info(f"Processing transfer request: {request}")

        # Execute transfer via API client
        response_data = await self.api_client.transfer(request.to_dict())

        # Parse response into model
        response = TransferResponse.from_dict(response_data)

        logger.info(f"Transfer completed successfully: {response.transaction_id}")
        return response

    async def get_balance(self, account_number: str) -> dict:
        """
        Get account balance.

        Args:
            account_number: Account number

        Returns:
            dict: Balance information
        """
        try:
            return await self.api_client.get_account_balance(account_number)
        except Exception as e:
            logger.error(f"Failed to retrieve balance for {account_number}: {e}")
            raise

    async def list_accounts(self) -> list:
        """
        List all available accounts.

        Returns:
            list: List of accounts
        """
        try:
            return await self.api_client.list_accounts()
        except Exception as e:
            logger.error(f"Failed to list accounts: {e}")
            raise

    async def validate_token(self, token: str) -> bool:
        """
        Validate a JWT token using the /auth/validate endpoint (BONUS).

        Args:
            token: JWT token to validate

        Returns:
            bool: True if token is valid
        """
        try:
            return await self.api_client.validate_token(token)
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False

    async def get_transaction_history(
        self, account_number: str = None, limit: int = 10
    ) -> list:
        """
        Get transaction history (BONUS endpoint - requires authentication).

        Args:
            account_number: Optional account number to filter
            limit: Maximum transactions to return

        Returns:
            list: Transaction history
        """
        try:
            return await self.api_client.get_transaction_history(account_number, limit)
        except Exception as e:
            logger.error(f"Failed to retrieve transaction history: {e}")
            raise
