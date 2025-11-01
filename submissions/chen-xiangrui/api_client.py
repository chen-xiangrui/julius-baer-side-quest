"""
HTTP API Client for Core Banking API.

Modern implementation using aiohttp for async HTTP requests.
Includes retry logic, timeout handling, and structured error handling.
"""

import asyncio
import logging
from typing import Any, Optional

import aiohttp

from config import Config
from models import AuthToken

logger = logging.getLogger(__name__)


class BankingAPIError(Exception):
    """Base exception for banking API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class BankingAPIClient:
    """
    Modern HTTP client for Core Banking API.

    Features:
    - Async/await with aiohttp
    - Automatic retry on transient failures
    - Proper timeout handling
    - Structured error handling
    - JWT token management
    """

    def __init__(self, config: Config):
        """
        Initialize the API client.

        Args:
            config: Configuration object with API settings
        """
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.auth_token: Optional[AuthToken] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def set_auth_token(self, token: str):
        """
        Set the authentication token for subsequent requests.

        Args:
            token: JWT token string
        """
        self.auth_token = AuthToken(token=token)
        logger.debug("Authentication token set")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[dict] = None,
        params: Optional[dict] = None,
        retry_count: int = 0,
    ) -> dict:
        """
        Make an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            json_data: JSON request body
            params: Query parameters
            retry_count: Current retry attempt

        Returns:
            dict: Parsed JSON response

        Raises:
            BankingAPIError: On API errors
            ConnectionError: On connection failures
        """
        if not self.session:
            raise RuntimeError("Client session not initialized. Use async context manager.")

        url = f"{self.config.base_url}{endpoint}"

        # Add authentication header if token is available
        headers = {}
        if self.auth_token and not self.auth_token.is_expired():
            headers["Authorization"] = self.auth_token.get_header_value()

        try:
            logger.debug(f"{method} {url} - Attempt {retry_count + 1}/{self.config.max_retries + 1}")

            async with self.session.request(
                method=method,
                url=url,
                json=json_data,
                params=params,
                headers=headers,
            ) as response:
                response_text = await response.text()

                # Log response for debugging
                logger.debug(f"Response status: {response.status}")
                logger.debug(f"Response body: {response_text[:500]}")

                # Handle non-200 responses
                if response.status >= 400:
                    error_msg = f"API error (status {response.status}): {response_text}"
                    logger.error(error_msg)
                    raise BankingAPIError(error_msg, status_code=response.status)

                # Parse JSON response
                try:
                    return await response.json()
                except aiohttp.ContentTypeError:
                    # Handle non-JSON responses
                    if response.status < 300:
                        return {"status": "success", "message": response_text}
                    raise BankingAPIError(f"Invalid JSON response: {response_text}")

        except asyncio.TimeoutError:
            error_msg = f"Request timeout after {self.config.timeout}s: {method} {url}"
            logger.error(error_msg)

            # Retry on timeout
            if retry_count < self.config.max_retries:
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                return await self._make_request(
                    method, endpoint, json_data, params, retry_count + 1
                )

            raise ConnectionError(error_msg)

        except aiohttp.ClientConnectionError as e:
            error_msg = f"Connection failed: {e}"
            logger.error(error_msg)

            # Retry on connection errors
            if retry_count < self.config.max_retries:
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                return await self._make_request(
                    method, endpoint, json_data, params, retry_count + 1
                )

            raise ConnectionError(
                f"{error_msg}\n"
                f"Please ensure the banking server is running at {self.config.base_url}"
            )

        except Exception as e:
            logger.exception(f"Unexpected error in API request: {e}")
            raise

    async def get_auth_token(
        self, username: str = "alice", password: str = "any", claim: str = "transfer"
    ) -> str:
        """
        Retrieve JWT authentication token from the API.

        Args:
            username: Username for authentication
            password: Password for authentication
            claim: Token scope (enquiry or transfer)

        Returns:
            str: JWT token

        Raises:
            BankingAPIError: On authentication failure
        """
        logger.info(f"Requesting auth token with claim: {claim}")

        response = await self._make_request(
            method="POST",
            endpoint="/authToken",
            json_data={"username": username, "password": password},
            params={"claim": claim},
        )

        token = response.get("token")
        if not token:
            raise BankingAPIError("No token in authentication response")

        logger.info("Successfully retrieved authentication token")
        return token

    async def validate_account(self, account_number: str) -> bool:
        """
        Validate if an account exists and is active.

        Args:
            account_number: Account number to validate

        Returns:
            bool: True if account is valid
        """
        logger.debug(f"Validating account: {account_number}")

        try:
            response = await self._make_request(
                method="GET",
                endpoint=f"/accounts/validate/{account_number}",
            )

            # API returns {"isValid": true/false, "accountId": "...", "status": "ACTIVE/INACTIVE"}
            is_valid = response.get("isValid", False)
            logger.debug(f"Account {account_number} validation: {is_valid} (status: {response.get('status', 'UNKNOWN')})")
            return is_valid

        except BankingAPIError as e:
            logger.warning(f"Account validation failed for {account_number}: {e}")
            return False

    async def get_account_balance(self, account_number: str) -> dict:
        """
        Get account balance information.

        Args:
            account_number: Account number

        Returns:
            dict: Account balance data with keys: accountId, balance, currency, status

        Raises:
            BankingAPIError: On API errors
        """
        logger.debug(f"Fetching balance for account: {account_number}")

        response = await self._make_request(
            method="GET",
            endpoint=f"/accounts/balance/{account_number}",
        )
        
        # API returns {"accountId": "ACC1000", "balance": 1000.00, "currency": "USD", "status": "ACTIVE"}
        logger.debug(f"Account {account_number} balance: {response.get('balance', 0)} {response.get('currency', 'USD')}")
        return response

    async def list_accounts(self) -> list:
        """
        List all available accounts.

        Returns:
            list: List of account information

        Raises:
            BankingAPIError: On API errors
        """
        logger.debug("Fetching all accounts")

        response = await self._make_request(
            method="GET",
            endpoint="/accounts",
        )

        # API returns {"accounts": [...], "totalAccounts": 100, "bonusPoints": "..."}
        if isinstance(response, dict) and "accounts" in response:
            accounts = response["accounts"]
            logger.info(f"Retrieved {len(accounts)} accounts")
            return accounts
        
        return response if isinstance(response, list) else []

    async def transfer(self, transfer_data: dict) -> dict:
        """
        Execute a fund transfer.

        Args:
            transfer_data: Transfer request data
                {
                    "fromAccount": "ACC1000",
                    "toAccount": "ACC1001",
                    "amount": 100.00
                }

        Returns:
            dict: Transfer response with transaction details

        Raises:
            BankingAPIError: On transfer failure
        """
        logger.info(f"Executing transfer: {transfer_data}")

        return await self._make_request(
            method="POST",
            endpoint="/transfer",
            json_data=transfer_data,
        )

    async def validate_token(self, token: str) -> bool:
        """
        Validate JWT token using the /auth/validate endpoint (BONUS).

        Args:
            token: JWT token to validate

        Returns:
            bool: True if token is valid

        Raises:
            BankingAPIError: On API errors
        """
        logger.debug("Validating JWT token")

        try:
            # Temporarily set token for this request
            original_token = self.auth_token
            self.auth_token = AuthToken(token=token)

            response = await self._make_request(
                method="POST",
                endpoint="/auth/validate",
            )

            # Restore original token
            self.auth_token = original_token

            is_valid = response.get("valid", False)
            logger.debug(f"Token validation result: {is_valid}")
            return is_valid

        except BankingAPIError as e:
            logger.warning(f"Token validation failed: {e}")
            return False

    async def get_transaction_history(
        self, account_number: Optional[str] = None, limit: int = 10
    ) -> list:
        """
        Get transaction history (BONUS endpoint - requires authentication).

        Args:
            account_number: Optional account number to filter by
            limit: Maximum number of transactions to return

        Returns:
            list: List of transaction records

        Raises:
            BankingAPIError: On API errors
        """
        logger.debug(f"Fetching transaction history for account: {account_number}")

        params = {"limit": limit}
        if account_number:
            params["accountNumber"] = account_number

        response = await self._make_request(
            method="GET",
            endpoint="/transactions/history",
            params=params,
        )
        
        # API returns: {"transactions": [...], "totalReturned": n, "bonusPoints": "..."}
        return response.get("transactions", [])
