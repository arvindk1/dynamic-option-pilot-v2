"""Application configuration management."""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration."""

    url: str = "sqlite:///./app.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10


@dataclass
class DataProviderConfig:
    """Data provider configuration."""

    primary_provider: str = "yfinance_provider"
    fallback_providers: list = None
    cache_enabled: bool = True
    rate_limit_ms: int = 100

    def __post_init__(self):
        if self.fallback_providers is None:
            self.fallback_providers = []


@dataclass
class TradingConfig:
    """Trading configuration."""

    paper_trading: bool = True
    max_position_size: float = 1000.0
    max_portfolio_risk: float = 0.02  # 2%
    default_universe: list = None
    environment: str = "development"  # development, production, sandbox
    strategy_config_path: str = None

    def __post_init__(self):
        if self.default_universe is None:
            # Load default universe from external file
            try:
                from utils.universe_loader import get_universe_loader

                universe_loader = get_universe_loader()
                self.default_universe = universe_loader.load_universe_symbols(
                    "default_etfs.txt"
                )
            except Exception:
                # Final fallback only if external loading fails
                self.default_universe = [
                    "SPY",
                    "QQQ",
                    "IWM",
                    "AAPL",
                    "MSFT",
                    "GOOGL",
                    "AMZN",
                    "TSLA",
                ]
        if self.strategy_config_path is None:
            self.strategy_config_path = f"backend/config/strategies/{self.environment}"


@dataclass
class AnalysisConfig:
    """Analysis configuration."""

    rsi_period: int = 14
    ema_fast: int = 12
    ema_slow: int = 26
    macd_signal: int = 9
    atr_period: int = 14
    volatility_threshold: float = 0.75


@dataclass
class APIConfig:
    """API configuration."""

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: list = None
    max_request_size: int = 16 * 1024 * 1024  # 16MB

    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class FeaturesConfig:
    """Feature toggles for enabling/disabling core functions."""

    scans: bool = True
    sentiment: bool = True
    rsi_coupon: bool = True
    theta_crop: bool = True
    troubleshooting: bool = True


class Settings:
    """Application settings manager."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self._config_data: Dict[str, Any] = {}
        self._load_config()

        # Initialize configuration objects
        self.database = DatabaseConfig(**self._config_data.get("database", {}))
        self.data_providers = DataProviderConfig(
            **self._config_data.get("data_providers", {})
        )
        self.trading = TradingConfig(**self._config_data.get("trading", {}))
        self.analysis = AnalysisConfig(**self._config_data.get("analysis", {}))
        self.api = APIConfig(**self._config_data.get("api", {}))
        self.logging = LoggingConfig(**self._config_data.get("logging", {}))

        # Plugin configurations
        self.plugin_configs = self._config_data.get("plugins", {})
        # Feature toggles
        self.features = FeaturesConfig(**self._config_data.get("features", {}))

    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        # Check environment variable first
        if "CONFIG_PATH" in os.environ:
            return os.environ["CONFIG_PATH"]

        # Check for environment-specific config
        env = os.environ.get("ENVIRONMENT", "development")
        env_config = Path(__file__).parent / "environments" / f"{env}.yaml"
        if env_config.exists():
            return str(env_config)

        # Default to development config
        return str(Path(__file__).parent / "environments" / "development.yaml")

    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    self._config_data = yaml.safe_load(f) or {}
                logger.info(f"Loaded configuration from {self.config_path}")
            else:
                logger.warning(f"Configuration file not found: {self.config_path}")
                self._config_data = {}

            # Override with environment variables
            self._load_environment_overrides()

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self._config_data = {}

    def _load_environment_overrides(self):
        """Load configuration overrides from environment variables."""
        env_mappings = {
            "DATABASE_URL": ("database", "url"),
            "PAPER_TRADING": ("trading", "paper_trading"),
            "MAX_POSITION_SIZE": ("trading", "max_position_size"),
            "RSI_PERIOD": ("analysis", "rsi_period"),
            "API_HOST": ("api", "host"),
            "API_PORT": ("api", "port"),
            "LOG_LEVEL": ("logging", "level"),
            "ALPACA_API_KEY": ("plugins", "alpaca_provider", "api_key"),
            "ALPACA_SECRET_KEY": ("plugins", "alpaca_provider", "secret_key"),
        }

        for env_var, config_path in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Navigate to the nested config location
                current = self._config_data
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]

                # Convert value to appropriate type
                current[config_path[-1]] = self._convert_env_value(value)

    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable value to appropriate type."""
        # Boolean conversion
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # Integer conversion
        try:
            if "." not in value:
                return int(value)
        except ValueError:
            pass

        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value

    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """Get configuration for a specific plugin."""
        return self.plugin_configs.get(plugin_name, {})

    def reload(self):
        """Reload configuration from file."""
        self._load_config()
        logger.info("Configuration reloaded")

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "database": self.database.__dict__,
            "data_providers": self.data_providers.__dict__,
            "trading": self.trading.__dict__,
            "analysis": self.analysis.__dict__,
            "api": self.api.__dict__,
            "logging": self.logging.__dict__,
            "plugins": self.plugin_configs,
            "features": self.features.__dict__,
        }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get global settings instance."""
    return settings


def create_settings(config_path: Optional[str] = None) -> Settings:
    """Create a new settings instance."""
    return Settings(config_path)
