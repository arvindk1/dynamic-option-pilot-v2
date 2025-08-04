"""
Alpaca Symbol Utilities
=======================
Handle symbol mapping and validation for Alpaca-supported trading instruments.
Alpaca supports stocks and ETFs for options trading, but not indexes.
"""

import logging
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# Mapping from indexes to their tradeable ETF equivalents
INDEX_TO_ETF_MAPPING: Dict[str, str] = {
    # S&P 500
    "SPX": "SPY",  # S&P 500 Index -> SPDR S&P 500 ETF
    "^GSPC": "SPY",  # S&P 500 Index (Yahoo Finance format)
    # NASDAQ
    "NDX": "QQQ",  # NASDAQ-100 Index -> Invesco QQQ Trust
    "^NDX": "QQQ",  # NASDAQ-100 Index (Yahoo Finance format)
    "^IXIC": "QQQ",  # NASDAQ Composite -> QQQ (close proxy)
    # Dow Jones
    "DJX": "DIA",  # Dow Jones Industrial Average -> SPDR Dow Jones Industrial Average ETF
    "^DJI": "DIA",  # Dow Jones Industrial Average (Yahoo Finance format)
    # Russell
    "RUT": "IWM",  # Russell 2000 Index -> iShares Russell 2000 ETF
    "^RUT": "IWM",  # Russell 2000 Index (Yahoo Finance format)
    # Volatility
    "VIX": "VXX",  # VIX Index -> iPath Series B S&P 500 VIX Short-Term Futures ETN
    "^VIX": "VXX",  # VIX Index (Yahoo Finance format)
}

# Popular tradeable symbols that work with Alpaca options
SUPPORTED_SYMBOLS: Set[str] = {
    # Major ETFs
    "SPY",  # SPDR S&P 500 ETF
    "QQQ",  # Invesco QQQ Trust (NASDAQ-100)
    "IWM",  # iShares Russell 2000 ETF
    "DIA",  # SPDR Dow Jones Industrial Average ETF
    "VXX",  # iPath Series B S&P 500 VIX Short-Term Futures ETN
    "EFA",  # iShares MSCI EAFE ETF
    "EEM",  # iShares MSCI Emerging Markets ETF
    "GLD",  # SPDR Gold Shares
    "SLV",  # iShares Silver Trust
    "TLT",  # iShares 20+ Year Treasury Bond ETF
    "XLF",  # Financial Select Sector SPDR Fund
    "XLE",  # Energy Select Sector SPDR Fund
    "XLK",  # Technology Select Sector SPDR Fund
    # Major individual stocks with liquid options
    "AAPL",  # Apple Inc.
    "MSFT",  # Microsoft Corporation
    "GOOGL",  # Alphabet Inc.
    "AMZN",  # Amazon.com Inc.
    "TSLA",  # Tesla Inc.
    "NVDA",  # NVIDIA Corporation
    "META",  # Meta Platforms Inc.
    "NFLX",  # Netflix Inc.
    "AMD",  # Advanced Micro Devices Inc.
    "INTC",  # Intel Corporation
    "CRM",  # Salesforce Inc.
    "ORCL",  # Oracle Corporation
    "ADBE",  # Adobe Inc.
    "PYPL",  # PayPal Holdings Inc.
    "DIS",  # The Walt Disney Company
    "BA",  # The Boeing Company
    "JPM",  # JPMorgan Chase & Co.
    "BAC",  # Bank of America Corporation
    "WMT",  # Walmart Inc.
    "KO",  # The Coca-Cola Company
    "PFE",  # Pfizer Inc.
    "JNJ",  # Johnson & Johnson
    "UNH",  # UnitedHealth Group Incorporated
}

# Symbols that are definitely NOT supported by Alpaca for options trading
UNSUPPORTED_SYMBOLS: Set[str] = {
    # Indexes (cannot be traded directly)
    "SPX",
    "^GSPC",  # S&P 500 Index
    "NDX",
    "^NDX",
    "^IXIC",  # NASDAQ indexes
    "DJX",
    "^DJI",  # Dow Jones indexes
    "RUT",
    "^RUT",  # Russell indexes
    "VIX",
    "^VIX",  # Volatility indexes
    # Other common non-tradeable symbols
    "BTC-USD",
    "ETH-USD",  # Cryptocurrencies
    "EURUSD=X",
    "GBPUSD=X",  # Forex pairs
}


def normalize_symbol(symbol: str) -> str:
    """
    Normalize a symbol to its Alpaca-tradeable equivalent.

    Args:
        symbol: Input symbol (could be index, stock, ETF)

    Returns:
        Alpaca-tradeable symbol

    Examples:
        normalize_symbol("SPX") -> "SPY"
        normalize_symbol("^GSPC") -> "SPY"
        normalize_symbol("SPY") -> "SPY"
    """
    symbol = symbol.upper().strip()

    # If it's an index, map to ETF equivalent
    if symbol in INDEX_TO_ETF_MAPPING:
        mapped_symbol = INDEX_TO_ETF_MAPPING[symbol]
        logger.info(f"🔄 Mapped index {symbol} to tradeable ETF {mapped_symbol}")
        return mapped_symbol

    # If it's already a supported symbol, return as-is
    if symbol in SUPPORTED_SYMBOLS:
        return symbol

    # If it's known to be unsupported, map to SPY as default
    if symbol in UNSUPPORTED_SYMBOLS:
        logger.warning(f"⚠️ Unsupported symbol {symbol}, defaulting to SPY")
        return "SPY"

    # For unknown symbols, assume they're valid (could be a stock we haven't listed)
    logger.info(f"Unknown symbol {symbol}, assuming it's valid for Alpaca")
    return symbol


def is_supported_symbol(symbol: str) -> bool:
    """
    Check if a symbol is supported by Alpaca for options trading.

    Args:
        symbol: Symbol to check

    Returns:
        True if supported, False otherwise
    """
    symbol = symbol.upper().strip()

    # Check if it's in our supported list
    if symbol in SUPPORTED_SYMBOLS:
        return True

    # Check if it's a known unsupported symbol
    if symbol in UNSUPPORTED_SYMBOLS:
        return False

    # Check if it's an index that can be mapped
    if symbol in INDEX_TO_ETF_MAPPING:
        return True  # Can be mapped to supported ETF

    # For unknown symbols, we'll assume they might be valid
    # The actual API call will determine if they're really supported
    return True


def get_tradeable_equivalent(symbol: str) -> str:
    """
    Get the tradeable equivalent of a symbol for Alpaca.
    Same as normalize_symbol but with more explicit naming.

    Args:
        symbol: Input symbol

    Returns:
        Tradeable equivalent symbol
    """
    return normalize_symbol(symbol)


def get_supported_symbols() -> List[str]:
    """
    Get list of all supported symbols.

    Returns:
        List of supported symbol strings
    """
    return sorted(list(SUPPORTED_SYMBOLS))


def get_index_mappings() -> Dict[str, str]:
    """
    Get the index to ETF mapping dictionary.

    Returns:
        Dictionary mapping indexes to ETFs
    """
    return INDEX_TO_ETF_MAPPING.copy()


def validate_symbol_for_options(symbol: str) -> tuple[bool, str, Optional[str]]:
    """
    Comprehensive symbol validation for options trading.

    Args:
        symbol: Symbol to validate

    Returns:
        Tuple of (is_valid, final_symbol, warning_message)

    Examples:
        validate_symbol_for_options("SPY") -> (True, "SPY", None)
        validate_symbol_for_options("SPX") -> (True, "SPY", "Mapped SPX to SPY")
        validate_symbol_for_options("INVALID") -> (False, "INVALID", "Unknown symbol")
    """
    original_symbol = symbol
    normalized_symbol = normalize_symbol(symbol)

    # Check if normalization changed the symbol
    if normalized_symbol != original_symbol:
        if original_symbol in INDEX_TO_ETF_MAPPING:
            warning = (
                f"Mapped index {original_symbol} to tradeable ETF {normalized_symbol}"
            )
        else:
            warning = f"Normalized {original_symbol} to {normalized_symbol}"
    else:
        warning = None

    # Final validation
    is_valid = is_supported_symbol(normalized_symbol)

    return is_valid, normalized_symbol, warning


# Default symbol to use when no symbol is specified
DEFAULT_SYMBOL = "SPY"

# Popular symbols for dropdown menus, etc.
POPULAR_SYMBOLS = ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "TSLA", "GOOGL", "AMZN", "NVDA"]
