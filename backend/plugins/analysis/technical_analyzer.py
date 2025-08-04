"""Technical analysis plugin for market indicators and signals."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from core.orchestrator.base_plugin import (
    AnalysisPlugin,
    PluginConfig,
    PluginMetadata,
    PluginType,
)


def compute_ema(series: pd.Series, period: int) -> pd.Series:
    """Compute Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Compute Relative Strength Index."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(0)
    rsi[avg_loss == 0] = 100
    return rsi


def compute_macd(
    series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> pd.DataFrame:
    """Compute Moving Average Convergence Divergence."""
    ema_fast = compute_ema(series, fast)
    ema_slow = compute_ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = compute_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "hist": histogram})


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Compute Average True Range."""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)

    tr = pd.concat(
        [
            (high - low),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = tr.rolling(window=period, min_periods=period).mean()
    return atr


def compute_bollinger_bands(
    series: pd.Series, period: int = 20, std_dev: float = 2
) -> pd.DataFrame:
    """Compute Bollinger Bands."""
    sma = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return pd.DataFrame(
        {
            "sma": sma,
            "upper_band": upper_band,
            "lower_band": lower_band,
            "bandwidth": (upper_band - lower_band) / sma,
        }
    )


def compute_stochastic(
    df: pd.DataFrame, k_period: int = 14, d_period: int = 3
) -> pd.DataFrame:
    """Compute Stochastic Oscillator."""
    high = df["high"]
    low = df["low"]
    close = df["close"]

    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()

    k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d_percent = k_percent.rolling(window=d_period).mean()

    return pd.DataFrame({"k_percent": k_percent, "d_percent": d_percent})


def determine_volatility_regime(atr_series: pd.Series, threshold: float = 0.75) -> str:
    """Classify volatility regime based on ATR percentile."""
    if len(atr_series) < 20:
        return "UNKNOWN"
    percentile = atr_series.rank(pct=True).iloc[-1]
    if percentile >= 0.8:
        return "HIGH_VOLATILITY"
    elif percentile <= 0.2:
        return "LOW_VOLATILITY"
    else:
        return "NORMAL_VOLATILITY"


class TechnicalAnalyzer(AnalysisPlugin):
    """Technical analysis plugin for market indicators and signals."""

    def __init__(self, config: PluginConfig = None):
        super().__init__(config)

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="technical_analyzer",
            version="2.0.0",
            plugin_type=PluginType.ANALYSIS,
            description="Technical analysis plugin for market indicators and signals",
            author="Dynamic Option Pilot",
            dependencies=[],
            config_schema={
                "type": "object",
                "properties": {
                    "rsi_period": {"type": "integer", "default": 14},
                    "ema_fast": {"type": "integer", "default": 12},
                    "ema_slow": {"type": "integer", "default": 26},
                    "macd_signal": {"type": "integer", "default": 9},
                    "atr_period": {"type": "integer", "default": 14},
                    "bb_period": {"type": "integer", "default": 20},
                    "bb_std_dev": {"type": "number", "default": 2.0},
                    "high_vol_threshold": {"type": "number", "default": 0.75},
                },
            },
        )

    async def initialize(self) -> bool:
        """Initialize the technical analyzer."""
        try:
            self._logger.info("🚀 Technical analyzer initializing")
            # Validate configuration parameters
            settings = self.config.settings or {}

            # Check for valid periods
            if settings.get("rsi_period", 14) < 2:
                self._logger.error("RSI period must be >= 2")
                return False

            if settings.get("ema_fast", 12) >= settings.get("ema_slow", 26):
                self._logger.error("Fast EMA period must be less than slow EMA period")
                return False

            self._logger.info("✅ Technical analyzer initialized")
            return True
        except Exception as e:
            self._logger.error(f"❌ Technical analyzer initialization failed: {e}")
            return False

    async def cleanup(self) -> bool:
        """Clean up technical analyzer resources."""
        try:
            self._logger.info("✅ Technical analyzer cleaned up")
            return True
        except Exception as e:
            self._logger.error(f"❌ Technical analyzer cleanup failed: {e}")
            return False

    async def analyze(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Perform technical analysis on the provided data."""
        price_data = data.get("price_data")
        if not price_data or (
            isinstance(price_data, pd.DataFrame) and price_data.empty
        ):
            return self._get_default_analysis()

        # Convert list to DataFrame if needed
        if isinstance(price_data, list):
            price_data = pd.DataFrame(price_data)

        try:
            # Get configuration
            settings = self.config.settings or {}

            # Calculate all indicators
            analysis_result = await self._calculate_all_indicators(price_data, settings)

            # Add market regime analysis
            analysis_result.update(
                await self._analyze_market_regime(price_data, settings)
            )

            # Add signal analysis
            analysis_result.update(
                await self._analyze_signals(price_data, analysis_result, settings)
            )

            return analysis_result

        except Exception as e:
            self._logger.error(f"Technical analysis failed: {e}")
            return self._get_default_analysis()

    async def _calculate_all_indicators(
        self, price_data: pd.DataFrame, settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate all technical indicators."""
        if "close" not in price_data.columns:
            return self._get_default_analysis()

        close = price_data["close"]

        # RSI
        rsi_period = settings.get("rsi_period", 14)
        rsi_series = compute_rsi(close, rsi_period)

        # MACD
        ema_fast = settings.get("ema_fast", 12)
        ema_slow = settings.get("ema_slow", 26)
        macd_signal = settings.get("macd_signal", 9)
        macd_df = compute_macd(close, ema_fast, ema_slow, macd_signal)

        # EMAs
        ema_short = compute_ema(close, ema_fast)
        ema_long = compute_ema(close, ema_slow)

        # ATR
        atr_period = settings.get("atr_period", 14)
        if all(col in price_data.columns for col in ["high", "low", "close"]):
            atr_series = compute_atr(price_data[["high", "low", "close"]], atr_period)
        else:
            atr_series = pd.Series([0.0] * len(close), index=close.index)

        # Bollinger Bands
        bb_period = settings.get("bb_period", 20)
        bb_std_dev = settings.get("bb_std_dev", 2.0)
        bb_df = compute_bollinger_bands(close, bb_period, bb_std_dev)

        # Stochastic (if OHLC data available)
        if all(col in price_data.columns for col in ["high", "low", "close"]):
            stoch_df = compute_stochastic(price_data[["high", "low", "close"]])
        else:
            stoch_df = pd.DataFrame({"k_percent": [50.0], "d_percent": [50.0]})

        # SMAs for additional analysis
        sma_20 = close.rolling(20).mean()
        sma_50 = close.rolling(50).mean()
        sma_200 = close.rolling(200).mean()

        return {
            "rsi": float(rsi_series.iloc[-1]) if not rsi_series.empty else 50.0,
            "macd": float(macd_df["macd"].iloc[-1]) if not macd_df.empty else 0.0,
            "macd_signal": (
                float(macd_df["signal"].iloc[-1]) if not macd_df.empty else 0.0
            ),
            "macd_histogram": (
                float(macd_df["hist"].iloc[-1]) if not macd_df.empty else 0.0
            ),
            "ema_short": float(ema_short.iloc[-1]) if not ema_short.empty else 0.0,
            "ema_long": float(ema_long.iloc[-1]) if not ema_long.empty else 0.0,
            "atr": float(atr_series.iloc[-1]) if not atr_series.empty else 0.0,
            "bb_upper": float(bb_df["upper_band"].iloc[-1]) if not bb_df.empty else 0.0,
            "bb_middle": float(bb_df["sma"].iloc[-1]) if not bb_df.empty else 0.0,
            "bb_lower": float(bb_df["lower_band"].iloc[-1]) if not bb_df.empty else 0.0,
            "bb_bandwidth": (
                float(bb_df["bandwidth"].iloc[-1]) if not bb_df.empty else 0.0
            ),
            "stoch_k": (
                float(stoch_df["k_percent"].iloc[-1]) if not stoch_df.empty else 50.0
            ),
            "stoch_d": (
                float(stoch_df["d_percent"].iloc[-1]) if not stoch_df.empty else 50.0
            ),
            "sma_20": float(sma_20.iloc[-1]) if not sma_20.empty else 0.0,
            "sma_50": float(sma_50.iloc[-1]) if not sma_50.empty else 0.0,
            "sma_200": float(sma_200.iloc[-1]) if not sma_200.empty else 0.0,
            "current_price": float(close.iloc[-1]) if not close.empty else 0.0,
        }

    async def _analyze_market_regime(
        self, price_data: pd.DataFrame, settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze market regime and volatility."""
        if "close" not in price_data.columns:
            return {"volatility_regime": "UNKNOWN", "trend": "UNKNOWN"}

        # Volatility regime
        if all(col in price_data.columns for col in ["high", "low", "close"]):
            atr_series = compute_atr(price_data[["high", "low", "close"]])
            volatility_regime = determine_volatility_regime(
                atr_series, settings.get("high_vol_threshold", 0.75)
            )
        else:
            volatility_regime = "UNKNOWN"

        # Trend analysis
        close = price_data["close"]
        if len(close) >= 20:
            sma_20 = close.rolling(20).mean()
            if len(close) >= 50:
                sma_50 = close.rolling(50).mean()
                current_price = close.iloc[-1]
                sma_20_current = sma_20.iloc[-1]
                sma_50_current = sma_50.iloc[-1]

                if current_price > sma_20_current > sma_50_current:
                    trend = "STRONG_BULLISH"
                elif current_price > sma_20_current and sma_20_current < sma_50_current:
                    trend = "WEAK_BULLISH"
                elif current_price < sma_20_current < sma_50_current:
                    trend = "STRONG_BEARISH"
                elif current_price < sma_20_current and sma_20_current > sma_50_current:
                    trend = "WEAK_BEARISH"
                else:
                    trend = "SIDEWAYS"
            else:
                trend = "INSUFFICIENT_DATA"
        else:
            trend = "INSUFFICIENT_DATA"

        return {"volatility_regime": volatility_regime, "trend": trend}

    async def _analyze_signals(
        self,
        price_data: pd.DataFrame,
        indicators: Dict[str, Any],
        settings: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze trading signals based on technical indicators."""
        signals = {
            "rsi_oversold": indicators.get("rsi", 50) < 30,
            "rsi_overbought": indicators.get("rsi", 50) > 70,
            "macd_bullish": indicators.get("macd", 0)
            > indicators.get("macd_signal", 0),
            "macd_bearish": indicators.get("macd", 0)
            < indicators.get("macd_signal", 0),
            "price_above_ema_short": indicators.get("current_price", 0)
            > indicators.get("ema_short", 0),
            "price_above_ema_long": indicators.get("current_price", 0)
            > indicators.get("ema_long", 0),
            "bb_squeeze": indicators.get("bb_bandwidth", 0) < 0.1,  # Low volatility
            "bb_expansion": indicators.get("bb_bandwidth", 0) > 0.3,  # High volatility
            "stoch_oversold": indicators.get("stoch_k", 50) < 20,
            "stoch_overbought": indicators.get("stoch_k", 50) > 80,
        }

        # Composite signals
        bullish_signals = sum(
            [
                signals["rsi_oversold"],
                signals["macd_bullish"],
                signals["price_above_ema_short"],
                signals["price_above_ema_long"],
                signals["stoch_oversold"],
            ]
        )

        bearish_signals = sum(
            [
                signals["rsi_overbought"],
                signals["macd_bearish"],
                not signals["price_above_ema_short"],
                not signals["price_above_ema_long"],
                signals["stoch_overbought"],
            ]
        )

        # Overall signal strength
        if bullish_signals >= 3:
            overall_signal = "STRONG_BULLISH"
        elif bullish_signals >= 2:
            overall_signal = "WEAK_BULLISH"
        elif bearish_signals >= 3:
            overall_signal = "STRONG_BEARISH"
        elif bearish_signals >= 2:
            overall_signal = "WEAK_BEARISH"
        else:
            overall_signal = "NEUTRAL"

        signals.update(
            {
                "bullish_signals_count": bullish_signals,
                "bearish_signals_count": bearish_signals,
                "overall_signal": overall_signal,
            }
        )

        return {"signals": signals}

    async def calculate_rsi_coupon_signals(
        self, price_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Enhanced RSI analysis for coupon strategy."""
        if price_data is None or price_data.empty or "close" not in price_data.columns:
            return self._get_default_rsi_coupon_analysis()

        close = price_data["close"]

        # Calculate indicators
        rsi_14 = compute_rsi(close, 14).iloc[-1] if len(close) >= 14 else 50.0
        sma_50 = (
            close.rolling(50).mean().iloc[-1] if len(close) >= 50 else close.iloc[-1]
        )
        current_price = close.iloc[-1]

        # Signal validation
        rsi_oversold = rsi_14 < 30
        above_trend = current_price >= sma_50
        qualified = rsi_oversold and above_trend

        # Signal strength calculation
        signal_strength = (30 - rsi_14) / 30 if rsi_14 < 30 else 0

        # Exit signal monitoring
        rsi_exit_triggered = rsi_14 >= 50  # Mean reversion exit
        trend_break = current_price < sma_50  # Trend break exit

        exit_reasons = []
        if rsi_exit_triggered:
            exit_reasons.append("RSI_MEAN_REVERSION")
        if trend_break:
            exit_reasons.append("TREND_BREAK")

        return {
            "rsi_14": round(rsi_14, 1),
            "sma_50": round(sma_50, 2),
            "current_price": round(current_price, 2),
            "rsi_oversold": rsi_oversold,
            "above_trend": above_trend,
            "qualified_for_entry": qualified,
            "signal_strength": round(signal_strength, 2),
            "price_vs_sma_pct": (
                round((current_price / sma_50 - 1) * 100, 1) if sma_50 > 0 else 0.0
            ),
            "rsi_exit_triggered": rsi_exit_triggered,
            "trend_break": trend_break,
            "exit_reasons": exit_reasons,
        }

    async def get_support_resistance(
        self, symbol: str, price_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, float]:
        """Calculate support and resistance levels."""
        if price_data is None or price_data.empty:
            return {
                "support_1": 100.0,
                "resistance_1": 110.0,
                "support_2": 95.0,
                "resistance_2": 115.0,
            }

        try:
            if "high" in price_data.columns and "low" in price_data.columns:
                highs = price_data["high"]
                lows = price_data["low"]
                closes = price_data["close"]

                # Simple pivot point calculation
                recent_high = highs.rolling(20).max().iloc[-1]
                recent_low = lows.rolling(20).min().iloc[-1]
                current_close = closes.iloc[-1]

                # Calculate basic support/resistance levels
                pivot = (recent_high + recent_low + current_close) / 3
                resistance_1 = 2 * pivot - recent_low
                support_1 = 2 * pivot - recent_high
                resistance_2 = pivot + (recent_high - recent_low)
                support_2 = pivot - (recent_high - recent_low)

                return {
                    "support_1": round(support_1, 2),
                    "resistance_1": round(resistance_1, 2),
                    "support_2": round(support_2, 2),
                    "resistance_2": round(resistance_2, 2),
                    "pivot": round(pivot, 2),
                }
            else:
                # Fallback using only close prices
                close = price_data["close"]
                current_price = close.iloc[-1]
                std_dev = close.rolling(20).std().iloc[-1]

                return {
                    "support_1": round(current_price - std_dev, 2),
                    "resistance_1": round(current_price + std_dev, 2),
                    "support_2": round(current_price - 2 * std_dev, 2),
                    "resistance_2": round(current_price + 2 * std_dev, 2),
                    "pivot": round(current_price, 2),
                }
        except Exception as e:
            self._logger.error(f"Error calculating support/resistance: {e}")
            return {
                "support_1": 100.0,
                "resistance_1": 110.0,
                "support_2": 95.0,
                "resistance_2": 115.0,
                "pivot": 105.0,
            }

    def _get_default_analysis(self) -> Dict[str, Any]:
        """Return default analysis when data is insufficient."""
        return {
            "rsi": 50.0,
            "macd": 0.0,
            "macd_signal": 0.0,
            "macd_histogram": 0.0,
            "ema_short": 0.0,
            "ema_long": 0.0,
            "atr": 0.0,
            "bb_upper": 0.0,
            "bb_middle": 0.0,
            "bb_lower": 0.0,
            "bb_bandwidth": 0.0,
            "stoch_k": 50.0,
            "stoch_d": 50.0,
            "sma_20": 0.0,
            "sma_50": 0.0,
            "sma_200": 0.0,
            "current_price": 0.0,
            "volatility_regime": "UNKNOWN",
            "trend": "UNKNOWN",
            "signals": {
                "overall_signal": "NEUTRAL",
                "bullish_signals_count": 0,
                "bearish_signals_count": 0,
            },
        }

    def _get_default_rsi_coupon_analysis(self) -> Dict[str, Any]:
        """Return default RSI coupon analysis."""
        return {
            "rsi_14": 50.0,
            "sma_50": 0.0,
            "current_price": 0.0,
            "rsi_oversold": False,
            "above_trend": False,
            "qualified_for_entry": False,
            "signal_strength": 0.0,
            "price_vs_sma_pct": 0.0,
            "rsi_exit_triggered": False,
            "trend_break": False,
            "exit_reasons": [],
        }
