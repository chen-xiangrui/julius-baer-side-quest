"""
Configuration management for the banking client.

Supports loading from JSON files and environment variables.
"""

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """
    Configuration for banking API client.

    Supports loading from:
    1. JSON configuration files
    2. Environment variables
    3. Default values
    """

    base_url: str = "http://localhost:8123"
    timeout: int = 30
    max_retries: int = 3
    log_level: str = "INFO"

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """
        Load configuration from file or environment.

        Priority (highest to lowest):
        1. Environment variables
        2. Configuration file (if provided)
        3. Default configuration file (config/settings.json)
        4. Default values

        Args:
            config_path: Optional path to configuration file

        Returns:
            Config: Configuration instance
        """
        config_data = {}

        # Try to load from file
        if config_path:
            config_data = cls._load_from_file(config_path)
        else:
            # Try default config location
            default_path = Path(__file__).parent / "config" / "settings.json"
            if default_path.exists():
                config_data = cls._load_from_file(str(default_path))

        # Override with environment variables
        if os.getenv("BANKING_API_URL"):
            config_data["base_url"] = os.getenv("BANKING_API_URL")

        if os.getenv("BANKING_API_TIMEOUT"):
            try:
                config_data["timeout"] = int(os.getenv("BANKING_API_TIMEOUT"))
            except ValueError:
                logger.warning("Invalid BANKING_API_TIMEOUT value, using default")

        if os.getenv("BANKING_API_MAX_RETRIES"):
            try:
                config_data["max_retries"] = int(os.getenv("BANKING_API_MAX_RETRIES"))
            except ValueError:
                logger.warning("Invalid BANKING_API_MAX_RETRIES value, using default")

        if os.getenv("LOG_LEVEL"):
            config_data["log_level"] = os.getenv("LOG_LEVEL")

        # Create config instance
        config = cls(**config_data)
        logger.info(f"Configuration loaded: base_url={config.base_url}")

        return config

    @staticmethod
    def _load_from_file(file_path: str) -> dict:
        """
        Load configuration from JSON file.

        Args:
            file_path: Path to JSON configuration file

        Returns:
            dict: Configuration data
        """
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                logger.info(f"Loaded configuration from: {file_path}")
                return data
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "base_url": self.base_url,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "log_level": self.log_level,
        }

    def save(self, file_path: str):
        """
        Save configuration to JSON file.

        Args:
            file_path: Path where to save the configuration
        """
        try:
            # Create directory if it doesn't exist
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
                logger.info(f"Configuration saved to: {file_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise
