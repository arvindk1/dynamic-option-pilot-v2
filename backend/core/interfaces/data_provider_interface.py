"""
Unified Data Provider Interface
==============================
Clean, standardized interface for all data providers that supports
the engines pattern for strategies.
"""

import logging
from abc import ABC, abstractmethod
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class DataProviderType(Enum):
    """Supported data provider types."""

    YFINANCE = "yfinance"
    ALPACA = "alpaca"
    MOCK = "mock"


class Quote:
    """Standardized quote structure."""

    def __init__(
        self,
        symbol: str,
        price: float,
        volume: int,
        timestamp: datetime,
        bid: Optional[float] = None,
        ask: Optional[float] = None,
        change: float = 0.0,
        change_percent: float = 0.0,
        **kwargs,
    ):
        self.symbol = symbol
        self.price = price
        self.volume = volume
        self.timestamp = timestamp
        self.bid = bid
        self.ask = ask
        self.change = change
        self.change_percent = change_percent
        # Store additional fields for provider-specific data
        self.additional_data = kwargs

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API compatibility."""
        return {
            "symbol": self.symbol,
            "price": self.price,
            "volume": self.volume,
            "timestamp": (
                self.timestamp.isoformat()
                if isinstance(self.timestamp, datetime)
                else self.timestamp
            ),
            "bid": self.bid,
            "ask": self.ask,
            "change": self.change,
            "change_percent": self.change_percent,
            **self.additional_data,
        }


class OptionContract:
    """Standardized option contract structure."""

    def __init__(
        self,
        symbol: str,
        strike: float,
        expiration: date,
        option_type: str,
        bid: float,
        ask: float,
        last: float,
        volume: int,
        open_interest: int,
        delta: Optional[float] = None,
        gamma: Optional[float] = None,
        theta: Optional[float] = None,
        vega: Optional[float] = None,
        implied_volatility: Optional[float] = None,
        **kwargs,
    ):
        self.symbol = symbol
        self.strike = strike
        self.expiration = expiration
        self.option_type = option_type.lower()  # 'call' or 'put'
        self.bid = bid
        self.ask = ask
        self.last = last
        self.volume = volume
        self.open_interest = open_interest
        self.delta = delta
        self.gamma = gamma
        self.theta = theta
        self.vega = vega
        self.implied_volatility = implied_volatility
        self.additional_data = kwargs

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API compatibility."""
        return {
            "symbol": self.symbol,
            "strike": self.strike,
            "expiration": (
                self.expiration.isoformat()
                if isinstance(self.expiration, date)
                else self.expiration
            ),
            "option_type": self.option_type,
            "bid": self.bid,
            "ask": self.ask,
            "last": self.last,
            "volume": self.volume,
            "open_interest": self.open_interest,
            "delta": self.delta,
            "gamma": self.gamma,
            "theta": self.theta,
            "vega": self.vega,
            "implied_volatility": self.implied_volatility,
            **self.additional_data,
        }


class OptionChain:
    """Standardized option chain structure."""

    def __init__(
        self,
        symbol: str,
        underlying_price: float,
        expiration: date,
        calls: List[OptionContract],
        puts: List[OptionContract],
        timestamp: datetime,
        **kwargs,
    ):
        self.symbol = symbol
        self.underlying_price = underlying_price
        self.expiration = expiration
        self.calls = calls
        self.puts = puts
        self.timestamp = timestamp
        self.additional_data = kwargs

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API compatibility."""
        return {
            "symbol": self.symbol,
            "underlying_price": self.underlying_price,
            "expiration": (
                self.expiration.isoformat()
                if isinstance(self.expiration, date)
                else self.expiration
            ),
            "calls": [call.to_dict() for call in self.calls],
            "puts": [put.to_dict() for put in self.puts],
            "timestamp": (
                self.timestamp.isoformat()
                if isinstance(self.timestamp, datetime)
                else self.timestamp
            ),
            **self.additional_data,
        }


class IDataProvider(ABC):
    """
    Unified data provider interface for all data sources.

    This interface provides a clean, consistent API that all strategies can use
    regardless of the underlying data provider (YFinance, Alpaca, etc.).
    """

    @abstractmethod
    async def get_market_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        Get current market data for a symbol.

        Args:
            symbol: Stock/ETF symbol (e.g., 'SPY', 'AAPL')
            **kwargs: Provider-specific parameters

        Returns:
            Dict containing market data (price, volume, timestamp, etc.)
        """
        pass

    @abstractmethod
    async def get_options_chain(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        Get options chain for a symbol and expiration.

        Args:
            symbol: Underlying symbol
            **kwargs: Must include 'expiration' date, other provider-specific params

        Returns:
            Dict containing calls, puts, underlying price, timestamp
        """
        pass

    @abstractmethod
    async def get_historical_data(self, symbol: str, **kwargs) -> List[Dict]:
        """
        Get historical price data.

        Args:
            symbol: Stock/ETF symbol
            **kwargs: period, days, or other time range parameters

        Returns:
            List of dicts with OHLCV data
        """
        pass

    @abstractmethod
    async def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if symbol is supported by this provider.

        Args:
            symbol: Symbol to validate

        Returns:
            True if symbol is supported
        """
        pass

    # Convenience methods that return structured objects
    async def get_quote(self, symbol: str, **kwargs) -> Quote:
        """Get quote as structured Quote object."""
        market_data = await self.get_market_data(symbol, **kwargs)
        return Quote(
            symbol=market_data.get("symbol", symbol),
            price=market_data.get("price", 0.0),
            volume=market_data.get("volume", 0),
            timestamp=self._parse_timestamp(market_data.get("timestamp")),
            bid=market_data.get("bid"),
            ask=market_data.get("ask"),
            change=market_data.get("change", 0.0),
            change_percent=market_data.get("change_percent", 0.0),
            atr=market_data.get("atr"),
            vix=market_data.get("vix"),
        )

    async def get_option_chain_structured(
        self, symbol: str, expiration: date, **kwargs
    ) -> OptionChain:
        """Get option chain as structured OptionChain object."""
        chain_data = await self.get_options_chain(
            symbol, expiration=expiration, **kwargs
        )

        # Convert raw calls/puts data to OptionContract objects
        calls = []
        for call_data in chain_data.get("calls", []):
            calls.append(
                OptionContract(
                    symbol=call_data.get("contractSymbol", f"{symbol}C"),
                    strike=call_data.get("strike", 0.0),
                    expiration=expiration,
                    option_type="call",
                    bid=call_data.get("bid", 0.0),
                    ask=call_data.get("ask", 0.0),
                    last=call_data.get("lastPrice", call_data.get("last", 0.0)),
                    volume=call_data.get("volume", 0),
                    open_interest=call_data.get(
                        "openInterest", call_data.get("open_interest", 0)
                    ),
                    delta=call_data.get("delta"),
                    gamma=call_data.get("gamma"),
                    theta=call_data.get("theta"),
                    vega=call_data.get("vega"),
                    implied_volatility=call_data.get(
                        "impliedVolatility", call_data.get("implied_volatility")
                    ),
                )
            )

        puts = []
        for put_data in chain_data.get("puts", []):
            puts.append(
                OptionContract(
                    symbol=put_data.get("contractSymbol", f"{symbol}P"),
                    strike=put_data.get("strike", 0.0),
                    expiration=expiration,
                    option_type="put",
                    bid=put_data.get("bid", 0.0),
                    ask=put_data.get("ask", 0.0),
                    last=put_data.get("lastPrice", put_data.get("last", 0.0)),
                    volume=put_data.get("volume", 0),
                    open_interest=put_data.get(
                        "openInterest", put_data.get("open_interest", 0)
                    ),
                    delta=put_data.get("delta"),
                    gamma=put_data.get("gamma"),
                    theta=put_data.get("theta"),
                    vega=put_data.get("vega"),
                    implied_volatility=put_data.get(
                        "impliedVolatility", put_data.get("implied_volatility")
                    ),
                )
            )

        return OptionChain(
            symbol=chain_data.get("symbol", symbol),
            underlying_price=chain_data.get("underlying_price", 0.0),
            expiration=expiration,
            calls=calls,
            puts=puts,
            timestamp=self._parse_timestamp(chain_data.get("timestamp")),
        )

    def _parse_timestamp(self, timestamp_str: Optional[str]) -> datetime:
        """Parse timestamp string to datetime object."""
        if not timestamp_str:
            return datetime.now()

        if isinstance(timestamp_str, datetime):
            return timestamp_str

        try:
            # Handle ISO format
            if "T" in timestamp_str:
                return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            else:
                return datetime.fromisoformat(timestamp_str)
        except Exception:
            logger.warning(f"Failed to parse timestamp: {timestamp_str}")
            return datetime.now()


class DataProviderAdapter(IDataProvider):
    """
    Adapter that wraps existing V2 data provider plugins to implement
    the unified interface without breaking existing functionality.
    """

    def __init__(self, provider_plugin):
        self.provider = provider_plugin
        self._logger = logging.getLogger(
            f"{__name__}.{provider_plugin.__class__.__name__}"
        )

    async def get_market_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Delegate to underlying provider's get_market_data method."""
        return await self.provider.get_market_data(symbol, **kwargs)

    async def get_options_chain(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Delegate to underlying provider's get_options_chain method."""
        return await self.provider.get_options_chain(symbol, **kwargs)

    async def get_historical_data(self, symbol: str, **kwargs) -> List[Dict]:
        """Delegate to underlying provider's get_historical_data method."""
        return await self.provider.get_historical_data(symbol, **kwargs)

    async def validate_symbol(self, symbol: str) -> bool:
        """Delegate to underlying provider's validate_symbol method."""
        return await self.provider.validate_symbol(symbol)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics if supported by underlying provider."""
        if hasattr(self.provider, "get_cache_stats"):
            return self.provider.get_cache_stats()
        return {}

    @property
    def provider_name(self) -> str:
        """Get the name of the underlying provider."""
        if hasattr(self.provider, "metadata"):
            return self.provider.metadata.name
        return self.provider.__class__.__name__
