"""
Data models for the banking client.

Uses Python dataclasses for clean, immutable data structures.
All models include type hints and validation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class Account:
    """Represents a bank account."""

    account_number: str
    balance: Optional[Decimal] = None
    status: Optional[str] = None

    def __post_init__(self):
        """Validate account data."""
        if not self.account_number or not self.account_number.strip():
            raise ValueError("Account number cannot be empty")


@dataclass(frozen=True)
class TransferRequest:
    """Request model for fund transfers."""

    from_account: str
    to_account: str
    amount: Decimal

    def __post_init__(self):
        """Validate transfer request data."""
        if not self.from_account or not self.from_account.strip():
            raise ValueError("Source account cannot be empty")

        if not self.to_account or not self.to_account.strip():
            raise ValueError("Destination account cannot be empty")

        if self.from_account == self.to_account:
            raise ValueError("Source and destination accounts must be different")

        if self.amount <= 0:
            raise ValueError("Transfer amount must be positive")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "fromAccount": self.from_account,
            "toAccount": self.to_account,
            "amount": float(self.amount),
        }

    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.from_account} → {self.to_account}: ${self.amount:.2f}"


@dataclass(frozen=True)
class TransferResponse:
    """Response model for fund transfers."""

    transaction_id: str
    status: str
    from_account: str
    to_account: str
    amount: Decimal
    timestamp: str
    message: Optional[str] = None
    bonus_points: Optional[str] = None
    permission_level: Optional[str] = None
    new_from_balance: Optional[Decimal] = None
    new_to_balance: Optional[Decimal] = None

    @classmethod
    def from_dict(cls, data: dict) -> "TransferResponse":
        """Create instance from API response dictionary."""
        # Handle timestamp - use current time if not provided
        timestamp = data.get("timestamp") or data.get("issuedAt") or datetime.now().isoformat()
        
        return cls(
            transaction_id=data.get("transactionId", ""),
            status=data.get("status", "UNKNOWN"),
            from_account=data.get("fromAccount", ""),
            to_account=data.get("toAccount", ""),
            amount=Decimal(str(data.get("amount", 0))),
            timestamp=timestamp,
            message=data.get("message"),
            bonus_points=data.get("bonusPoints"),
            permission_level=data.get("permissionLevel"),
            new_from_balance=Decimal(str(data.get("newFromAccountBalance", 0))) if data.get("newFromAccountBalance") else None,
            new_to_balance=Decimal(str(data.get("newToAccountBalance", 0))) if data.get("newToAccountBalance") else None,
        )


@dataclass(frozen=True)
class AuthToken:
    """Authentication token model."""

    token: str
    expires_at: Optional[datetime] = None
    token_type: str = "Bearer"

    def is_expired(self) -> bool:
        """Check if token is expired."""
        if not self.expires_at:
            return False
        return datetime.now() >= self.expires_at

    def get_header_value(self) -> str:
        """Get formatted token for Authorization header."""
        return f"{self.token_type} {self.token}"


@dataclass
class AccountBalance:
    """Account balance information."""

    account_number: str
    balance: Decimal
    currency: str = "USD"
    last_updated: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_dict(cls, data: dict) -> "AccountBalance":
        """Create instance from API response dictionary."""
        return cls(
            account_number=data.get("accountNumber", ""),
            balance=Decimal(str(data.get("balance", 0))),
            currency=data.get("currency", "USD"),
        )
