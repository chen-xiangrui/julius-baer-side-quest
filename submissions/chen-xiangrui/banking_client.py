#!/usr/bin/env python3
"""
Modern Banking Client for Julius Baer Core Banking API
======================================================

A production-grade banking client demonstrating modernization from legacy code.

Modernization Highlights:
- Python 3.10+ with type hints and dataclasses
- Async/await support with aiohttp
- Structured logging (not print statements)
- Clean architecture with separation of concerns
- Comprehensive error handling
- JWT authentication support
- Configuration management
- SOLID principles applied

Author: Chen Xiangrui
Date: November 2025
"""

import argparse
import asyncio
import logging
import sys
from decimal import Decimal
from typing import Optional

from api_client import BankingAPIClient
from config import Config
from models import TransferRequest, TransferResponse
from services import TransferService

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("banking_client.log"),
    ],
)

logger = logging.getLogger(__name__)


async def main() -> int:
    """
    Main entry point for the banking client CLI.
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Modern Banking Client - Transfer funds between accounts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --from ACC1000 --to ACC1001 --amount 100.00
  %(prog)s --from ACC1000 --to ACC1001 --amount 250.50 --auth
  %(prog)s --from ACC1000 --to ACC1001 --amount 50 --config config/custom.json
        """,
    )

    parser.add_argument(
        "--from",
        dest="from_account",
        required=False,
        help="Source account number (e.g., ACC1000)",
    )

    parser.add_argument(
        "--to",
        dest="to_account",
        required=False,
        help="Destination account number (e.g., ACC1001)",
    )

    parser.add_argument(
        "--amount",
        type=float,
        required=False,
        help="Transfer amount (e.g., 100.00)",
    )

    parser.add_argument(
        "--auth",
        action="store_true",
        help="Use JWT authentication (retrieve token from /authToken)",
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to custom configuration file",
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate accounts before transfer",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    parser.add_argument(
        "--history",
        action="store_true",
        help="Show transaction history (requires --auth)",
    )

    parser.add_argument(
        "--history-limit",
        type=int,
        default=10,
        help="Number of transactions to show in history (default: 10)",
    )

    parser.add_argument(
        "--check-balance",
        action="store_true",
        help="Check account balances before transfer",
    )

    args = parser.parse_args()

    # Validate arguments based on operation mode
    if args.history:
        # History mode doesn't need transfer arguments
        if not args.auth:
            parser.error("--history requires --auth flag")
    else:
        # Transfer mode requires all three arguments
        if not args.from_account or not args.to_account or args.amount is None:
            parser.error("Transfer mode requires --from, --to, and --amount")

    # Enable debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    try:
        # Load configuration
        config = Config.load(args.config) if args.config else Config.load()
        logger.info(f"Loaded configuration from: {config.base_url}")

        # Initialize API client and service
        async with BankingAPIClient(config) as api_client:
            transfer_service = TransferService(api_client)

            # Authenticate if requested
            if args.auth:
                logger.info("Retrieving authentication token...")
                token = await transfer_service.authenticate()
                if token:
                    logger.info("✓ Authentication successful")
                    
                    # Validate token using bonus endpoint
                    is_valid = await transfer_service.validate_token(token)
                    if is_valid:
                        logger.info("✓ Token validated successfully")
                    else:
                        logger.warning("⚠ Token validation failed")
                else:
                    logger.warning("⚠ Authentication failed, proceeding without token")

            # Show transaction history if requested
            if args.history:
                logger.info("Fetching transaction history...")
                try:
                    # Use from_account if provided, otherwise get all history (pass None)
                    account_number = args.from_account if args.from_account else None
                    history = await transfer_service.get_transaction_history(
                        account_number=account_number,
                        limit=args.history_limit
                    )
                    
                    if history:
                        account_info = f" for {account_number}" if account_number else ""
                        print(f"\n{'='*60}")
                        print(f"📜 Transaction History{account_info}")
                        print(f"{'='*60}")
                        for i, txn in enumerate(history[:args.history_limit], 1):
                            print(f"{i:2}. {txn.get('timestamp', 'N/A')[:19]}")
                            print(f"    Transaction ID: {txn.get('transactionId', 'N/A')}")
                            print(f"    Type: {txn.get('type', 'N/A')}")
                            print(f"    Amount: ${txn.get('amount', 0):.2f}")
                            print(f"    Status: {txn.get('status', 'N/A')}")
                            if txn.get('fromAccount'):
                                print(f"    From: {txn['fromAccount']} → To: {txn.get('toAccount', 'N/A')}")
                            print()
                        print(f"{'='*60}\n")
                    else:
                        print("\n📜 No transaction history found\n")
                        
                    # If this is history-only mode, exit after showing history
                    if not args.from_account or not args.to_account or args.amount is None:
                        return 0
                        
                except Exception as e:
                    logger.error(f"Could not retrieve transaction history: {e}")
                    if not args.from_account or not args.to_account or args.amount is None:
                        return 1

            # Skip transfer operations if we're in history-only mode
            if not args.from_account or not args.to_account or args.amount is None:
                return 0

            # Check balances if requested
            if args.check_balance:
                logger.info("Checking account balances...")
                try:
                    from_balance = await transfer_service.get_balance(args.from_account)
                    to_balance = await transfer_service.get_balance(args.to_account)
                    
                    print(f"\n📊 Account Balances:")
                    print(f"  From ({args.from_account}): ${from_balance.get('balance', 0):.2f}")
                    print(f"  To   ({args.to_account}): ${to_balance.get('balance', 0):.2f}\n")
                except Exception as e:
                    logger.warning(f"Could not retrieve balances: {e}")

            # Validate accounts if requested
            if args.validate:
                logger.info("Validating accounts...")
                from_valid = await transfer_service.validate_account(args.from_account)
                to_valid = await transfer_service.validate_account(args.to_account)

                if not from_valid:
                    logger.error(f"✗ Invalid source account: {args.from_account}")
                    return 1

                if not to_valid:
                    logger.error(f"✗ Invalid destination account: {args.to_account}")
                    return 1

                logger.info("✓ All accounts validated successfully")

            # Create transfer request
            transfer_request = TransferRequest(
                from_account=args.from_account,
                to_account=args.to_account,
                amount=Decimal(str(args.amount)),
            )

            logger.info(f"Initiating transfer: {transfer_request}")

            # Execute transfer
            response = await transfer_service.transfer(transfer_request)

            # Display results
            print("\n" + "=" * 60)
            print("✅ TRANSFER SUCCESSFUL!")
            print("=" * 60)
            print(f"Transaction ID:    {response.transaction_id}")
            print(f"Status:            {response.status}")
            print(f"From Account:      {response.from_account}")
            print(f"To Account:        {response.to_account}")
            print(f"Amount:            ${response.amount:.2f}")
            print(f"Timestamp:         {response.timestamp}")
            if response.message:
                print(f"Message:           {response.message}")
            if response.bonus_points:
                print(f"Bonus Points:      {response.bonus_points}")
            if response.permission_level:
                print(f"Permission Level:  {response.permission_level}")
            if response.new_from_balance:
                print(f"New From Balance:  ${response.new_from_balance:.2f}")
            print("=" * 60 + "\n")

            logger.info(f"Transfer completed successfully: {response.transaction_id}")
            return 0

    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        print(f"\n❌ Error: {e}\n", file=sys.stderr)
        return 1

    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        print(f"\n❌ Connection Error: {e}", file=sys.stderr)
        print("Please ensure the banking server is running at http://localhost:8123\n")
        return 1

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected Error: {e}\n", file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print("\n⚠ Operation cancelled by user\n")
        sys.exit(130)
