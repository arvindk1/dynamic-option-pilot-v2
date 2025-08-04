"""Enhanced base strategy plugin for V1 strategy migration to V2 architecture."""

import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from core.orchestrator.base_plugin import (
    PluginConfig,
    PluginMetadata,
    PluginType,
    TradingStrategyPlugin,
)

logger = logging.getLogger(__name__)


@dataclass
class StrategyOpportunity:
    """Enhanced opportunity structure compatible with V1 strategies."""

    # Core identification
    id: str
    symbol: str
    strategy_type: str
    strategy_id: str

    # Trade structure
    option_type: Optional[str] = None
    strike: Optional[float] = None
    short_strike: Optional[float] = None
    long_strike: Optional[float] = None
    expiration: Optional[str] = None
    days_to_expiration: int = 0

    # Financial metrics
    premium: float = 0.0
    max_loss: float = 0.0
    max_profit: float = 0.0
    probability_profit: float = 0.0
    expected_value: float = 0.0

    # Greeks
    delta: float = 0.0
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    implied_volatility: Optional[float] = None

    # Market data
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    liquidity_score: float = 0.0
    underlying_price: float = 0.0

    # Technical analysis
    bias: str = "NEUTRAL"
    rsi: Optional[float] = None
    macd_signal: Optional[str] = None
    support_resistance: Optional[Dict[str, float]] = None

    # Strategy specific
    trade_setup: str = ""
    risk_level: str = "MEDIUM"
    confidence_intervals: Optional[Dict[str, Any]] = None
    value_at_risk: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    volatility_regime: Optional[str] = None

    # Scoring and metadata
    score: float = 0.0
    generated_at: Optional[datetime] = None
    market_conditions: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.utcnow()
        if self.market_conditions is None:
            self.market_conditions = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        data = asdict(self)
        # Convert datetime to ISO string
        if self.generated_at:
            data["generated_at"] = self.generated_at.isoformat()
        return data


@dataclass
class StrategyConfig:
    """Configuration for strategy plugins."""

    # Strategy identification
    strategy_id: str
    name: str
    category: str

    # Trading parameters
    min_dte: int = 15
    max_dte: int = 45
    min_probability: float = 0.50
    max_risk_per_trade: float = 500.0
    min_liquidity_score: float = 7.0

    # Universe settings
    symbols: List[str] = None
    max_opportunities: int = 10

    # Technical analysis
    use_technical_analysis: bool = True
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0

    # Risk management
    max_position_size: float = 0.05  # 5% of account
    stop_loss_threshold: float = -0.50  # 50% loss
    profit_target_threshold: float = 0.25  # 25% profit

    # Performance tracking
    track_performance: bool = True
    backtest_enabled: bool = False

    def __post_init__(self):
        if self.symbols is None:
            # Load symbols from external default universe
            try:
                from utils.universe_loader import get_universe_loader

                universe_loader = get_universe_loader()
                self.symbols = universe_loader.load_universe_symbols("default_etfs.txt")
            except Exception:
                self.symbols = [
                    "SPY",
                    "QQQ",
                    "IWM",
                ]  # Final fallback only if external loading fails


class BaseStrategyPlugin(TradingStrategyPlugin):
    """Enhanced base class for V1 strategy migration with V2 integration."""

    def __init__(
        self, config: PluginConfig = None, strategy_config: StrategyConfig = None
    ):
        super().__init__(config)
        self.strategy_config = strategy_config
        self._performance_stats = {}
        self._universe_symbols = []

    @property
    @abstractmethod
    def strategy_metadata(self) -> StrategyConfig:
        """Return strategy-specific metadata."""
        pass

    @abstractmethod
    async def scan_opportunities(
        self, universe: List[str], **kwargs
    ) -> List[StrategyOpportunity]:
        """Scan for trading opportunities. Override TradingStrategyPlugin method."""
        pass

    @abstractmethod
    async def validate_opportunity(self, opportunity: StrategyOpportunity) -> bool:
        """Validate a trading opportunity. Enhanced from base class."""
        pass

    @abstractmethod
    def calculate_position_size(
        self, opportunity: StrategyOpportunity, account_size: float
    ) -> int:
        """Calculate appropriate position size for the opportunity."""
        pass

    @abstractmethod
    def calculate_risk_metrics(
        self, opportunity: StrategyOpportunity
    ) -> Dict[str, float]:
        """Calculate comprehensive risk metrics for the opportunity."""
        pass

    # V2 Integration Methods
    async def scan_opportunities_v2(
        self, universe: List[str], **kwargs
    ) -> List[Dict[str, Any]]:
        """V2 integration wrapper for scan_opportunities."""
        try:
            # Call enhanced scan method
            opportunities = await self.scan_opportunities(universe, **kwargs)

            # Convert to V2 format
            return [opp.to_dict() for opp in opportunities]

        except Exception as e:
            self._logger.error(f"Strategy scan failed: {e}")
            return []

    async def validate_opportunity_v2(self, opportunity: Dict[str, Any]) -> bool:
        """V2 integration wrapper for validate_opportunity."""
        try:
            # Convert from V2 format
            strategy_opp = self._dict_to_opportunity(opportunity)
            return await self.validate_opportunity(strategy_opp)
        except Exception as e:
            self._logger.error(f"Opportunity validation failed: {e}")
            return False

    # Helper Methods
    def _dict_to_opportunity(self, data: Dict[str, Any]) -> StrategyOpportunity:
        """Convert dictionary to StrategyOpportunity."""
        # Handle datetime conversion
        generated_at = data.get("generated_at")
        if isinstance(generated_at, str):
            generated_at = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))

        return StrategyOpportunity(
            id=data.get("id", ""),
            symbol=data.get("symbol", ""),
            strategy_type=data.get("strategy_type", ""),
            strategy_id=data.get(
                "strategy_id",
                self.strategy_config.strategy_id if self.strategy_config else "",
            ),
            option_type=data.get("option_type"),
            strike=data.get("strike"),
            short_strike=data.get("short_strike"),
            long_strike=data.get("long_strike"),
            expiration=data.get("expiration"),
            days_to_expiration=data.get("days_to_expiration", 0),
            premium=data.get("premium", 0.0),
            max_loss=data.get("max_loss", 0.0),
            max_profit=data.get("max_profit", 0.0),
            probability_profit=data.get("probability_profit", 0.0),
            expected_value=data.get("expected_value", 0.0),
            delta=data.get("delta", 0.0),
            gamma=data.get("gamma"),
            theta=data.get("theta"),
            vega=data.get("vega"),
            implied_volatility=data.get("implied_volatility"),
            volume=data.get("volume"),
            open_interest=data.get("open_interest"),
            liquidity_score=data.get("liquidity_score", 0.0),
            underlying_price=data.get("underlying_price", 0.0),
            bias=data.get("bias", "NEUTRAL"),
            rsi=data.get("rsi"),
            macd_signal=data.get("macd_signal"),
            support_resistance=data.get("support_resistance"),
            trade_setup=data.get("trade_setup", ""),
            risk_level=data.get("risk_level", "MEDIUM"),
            confidence_intervals=data.get("confidence_intervals"),
            value_at_risk=data.get("value_at_risk"),
            sharpe_ratio=data.get("sharpe_ratio"),
            volatility_regime=data.get("volatility_regime"),
            score=data.get("score", 0.0),
            generated_at=generated_at,
            market_conditions=data.get("market_conditions", {}),
        )

    def _calculate_score(self, opportunity: StrategyOpportunity) -> float:
        """Calculate composite score for opportunity ranking."""
        try:
            score = 0.0

            # Probability component (40% weight)
            prob_score = opportunity.probability_profit * 40

            # Expected value component (30% weight)
            ev_normalized = min(
                opportunity.expected_value / 200.0, 1.0
            )  # Normalize to $200 max
            ev_score = ev_normalized * 30

            # Liquidity component (20% weight)
            liquidity_score = (opportunity.liquidity_score / 10.0) * 20

            # Risk-adjusted component (10% weight)
            if opportunity.max_loss > 0:
                risk_reward = opportunity.max_profit / opportunity.max_loss
                risk_score = min(risk_reward, 2.0) / 2.0 * 10  # Cap at 2:1 ratio
            else:
                risk_score = 0

            score = prob_score + ev_score + liquidity_score + risk_score
            return round(score, 2)

        except Exception as e:
            self._logger.error(f"Score calculation failed: {e}")
            return 0.0

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get strategy performance statistics."""
        return {
            "strategy_id": (
                self.strategy_config.strategy_id if self.strategy_config else "unknown"
            ),
            "total_opportunities": self._performance_stats.get(
                "total_opportunities", 0
            ),
            "successful_trades": self._performance_stats.get("successful_trades", 0),
            "win_rate": self._performance_stats.get("win_rate", 0.0),
            "average_profit": self._performance_stats.get("average_profit", 0.0),
            "max_drawdown": self._performance_stats.get("max_drawdown", 0.0),
            "sharpe_ratio": self._performance_stats.get("sharpe_ratio", 0.0),
            "last_updated": datetime.utcnow().isoformat(),
        }

    def update_performance_stats(self, trade_result: Dict[str, Any]):
        """Update performance statistics after trade execution."""
        if not self.strategy_config or not self.strategy_config.track_performance:
            return

        try:
            # Update trade count
            self._performance_stats["total_opportunities"] = (
                self._performance_stats.get("total_opportunities", 0) + 1
            )

            # Update success metrics
            if trade_result.get("success", False):
                self._performance_stats["successful_trades"] = (
                    self._performance_stats.get("successful_trades", 0) + 1
                )

            # Calculate win rate
            total = self._performance_stats["total_opportunities"]
            successful = self._performance_stats["successful_trades"]
            self._performance_stats["win_rate"] = (
                successful / total if total > 0 else 0.0
            )

            # Update profit metrics
            profit = trade_result.get("profit", 0.0)
            current_avg = self._performance_stats.get("average_profit", 0.0)
            self._performance_stats["average_profit"] = (
                current_avg * (total - 1) + profit
            ) / total

        except Exception as e:
            self._logger.error(f"Performance stats update failed: {e}")

    async def health_check(self) -> bool:
        """Enhanced health check for strategy plugins."""
        base_health = await super().health_check()

        if not base_health:
            return False

        try:
            # Check strategy configuration
            if not self.strategy_config:
                self._logger.warning("Strategy configuration missing")
                return False

            # Check universe availability
            if not self._universe_symbols:
                self._logger.warning("No universe symbols configured")

            return True

        except Exception as e:
            self._logger.error(f"Strategy health check failed: {e}")
            return False


class V1StrategyMigrationMixin:
    """Mixin class to help with V1 strategy migration patterns."""

    def format_v1_opportunity(
        self, symbol: str, strategy_type: str, **kwargs
    ) -> StrategyOpportunity:
        """Format opportunity in V1 style for easier migration."""
        opportunity_id = (
            f"{strategy_type}_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        return StrategyOpportunity(
            id=opportunity_id,
            symbol=symbol,
            strategy_type=strategy_type,
            strategy_id=getattr(
                self, "strategy_config", StrategyConfig("unknown", "Unknown", "other")
            ).strategy_id,
            **kwargs,
        )

    def calculate_theta_decay_score(
        self, days_to_expiration: int, theta: float
    ) -> float:
        """Calculate theta decay score - common in V1 strategies."""
        if days_to_expiration <= 0 or theta >= 0:
            return 0.0

        # Higher score for more theta decay closer to expiration
        time_score = max(0, (45 - days_to_expiration) / 45.0)  # Peak at 0 DTE
        theta_score = min(abs(theta) / 5.0, 1.0)  # Normalize theta impact

        return time_score * theta_score * 100

    def calculate_rsi_score(self, rsi: Optional[float], bias: str) -> float:
        """Calculate RSI-based score - common in V1 technical strategies."""
        if rsi is None:
            return 0.0

        if bias.upper() == "BULLISH" and rsi < 40:
            return (40 - rsi) / 40 * 100  # Higher score for oversold in bullish bias
        elif bias.upper() == "BEARISH" and rsi > 60:
            return (rsi - 60) / 40 * 100  # Higher score for overbought in bearish bias

        return 0.0

    def validate_liquidity_requirements(
        self, opportunity: StrategyOpportunity, min_score: float = 7.0
    ) -> bool:
        """Validate liquidity requirements - common V1 pattern."""
        return opportunity.liquidity_score >= min_score

    def validate_probability_requirements(
        self, opportunity: StrategyOpportunity, min_prob: float = 0.50
    ) -> bool:
        """Validate probability requirements - common V1 pattern."""
        return opportunity.probability_profit >= min_prob
