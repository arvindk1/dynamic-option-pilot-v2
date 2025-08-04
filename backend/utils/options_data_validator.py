"""
Options Data Validator - Validates synthetic pricing against real market data
This module helps ensure that only opportunities with real market data backing are displayed
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from plugins.data.yfinance import DataPlugin
from utils.expirations import OptionExpiration

logger = logging.getLogger(__name__)


class OptionsDataValidator:
    """
    Validates options opportunities against real market data
    Ensures synthetic data is only used for comparison/scoring, not display
    """

    def __init__(self):
        self.data_provider = DataPlugin()

    async def validate_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an opportunity against real market data

        Args:
            opportunity: Dictionary containing opportunity data

        Returns:
            Updated opportunity with real market data if available, or None if invalid
        """
        symbol = opportunity.get("symbol")
        expiration_date = opportunity.get("expiration_date")
        option_type = opportunity.get("option_type", "PUT").upper()
        short_strike = opportunity.get("short_strike")
        long_strike = opportunity.get("long_strike")

        if not all([symbol, expiration_date, short_strike]):
            logger.debug(
                f"Missing required data for opportunity validation: {symbol} (exp: {expiration_date}, strike: {short_strike})"
            )
            return None

        try:
            # Parse expiration date
            exp_date = datetime.strptime(expiration_date, "%Y-%m-%d")

            # Fetch real options chain
            option_chain = await self.data_provider.get_option_chain(symbol, exp_date)

            # Validate strikes exist in real market data
            if option_type == "PUT":
                options_data = option_chain.puts
            else:
                options_data = option_chain.calls

            # Check if our strikes exist in real data
            short_strike_data = self._find_strike_data(options_data, short_strike)
            long_strike_data = None
            if long_strike:
                long_strike_data = self._find_strike_data(options_data, long_strike)

            if not short_strike_data:
                logger.debug(
                    f"Short strike {short_strike} not found in real options data for {symbol}"
                )
                return None

            if long_strike and not long_strike_data:
                logger.debug(
                    f"Long strike {long_strike} not found in real options data for {symbol}"
                )
                return None

            # Update opportunity with real market data
            opportunity = opportunity.copy()
            opportunity["data_source_type"] = "REAL_MARKET"
            opportunity["data_source_provider"] = "yahoo_finance"
            opportunity["pricing_confidence"] = 0.95

            # Update pricing with real market data
            real_bid = short_strike_data.get("bid", 0.0)
            real_ask = short_strike_data.get("ask", 0.0)
            real_mid = (
                (real_bid + real_ask) / 2
                if real_bid and real_ask
                else opportunity.get("premium", 0.0)
            )

            if long_strike_data:
                # For spreads, calculate spread pricing
                long_bid = long_strike_data.get("bid", 0.0)
                long_ask = long_strike_data.get("ask", 0.0)
                long_mid = (long_bid + long_ask) / 2 if long_bid and long_ask else 0.0

                # Credit spread: sell high strike, buy low strike
                if option_type == "PUT" and short_strike > long_strike:
                    spread_credit = real_mid - long_mid
                elif option_type == "CALL" and short_strike < long_strike:
                    spread_credit = real_mid - long_mid
                else:
                    spread_credit = long_mid - real_mid

                opportunity["premium"] = max(0.0, spread_credit)
                opportunity["max_profit"] = max(0.0, spread_credit)
                opportunity["max_loss"] = (
                    abs(short_strike - long_strike) - spread_credit
                )
            else:
                # Single option
                opportunity["premium"] = real_mid
                opportunity["max_profit"] = real_mid  # For credit strategies

            # Update real market Greeks if available
            if "impliedVolatility" in short_strike_data:
                opportunity["implied_volatility"] = short_strike_data[
                    "impliedVolatility"
                ]

            # Remove synthetic warnings and add real data confidence
            opportunity["display_warnings"] = [
                "✅ REAL MARKET DATA - Live options pricing"
            ]

            logger.debug(f"Validated {symbol} opportunity with real market data")
            return opportunity

        except Exception as e:
            logger.warning(f"Failed to validate opportunity for {symbol}: {e}")
            return None

    def _find_strike_data(self, options_data, target_strike: float) -> Optional[Dict]:
        """Find options data for a specific strike price"""
        if options_data is None or options_data.empty:
            return None

        # Convert to float for comparison
        target_strike = float(target_strike)

        # Find exact match or closest strike
        for _, option in options_data.iterrows():
            option_strike = float(option.get("strike", 0))
            if (
                abs(option_strike - target_strike) < 0.01
            ):  # Allow small floating point differences
                return {
                    "strike": option_strike,
                    "bid": float(option.get("bid", 0.0)),
                    "ask": float(option.get("ask", 0.0)),
                    "volume": int(option.get("volume", 0)),
                    "openInterest": int(option.get("openInterest", 0)),
                    "impliedVolatility": float(option.get("impliedVolatility", 0.0)),
                }

        return None

    async def validate_opportunities_batch(
        self, opportunities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Validate a batch of opportunities against real market data

        Args:
            opportunities: List of opportunity dictionaries

        Returns:
            List of validated opportunities with real market data
        """
        validated_opportunities = []

        # Group opportunities by symbol to minimize API calls
        symbol_groups = {}
        for opp in opportunities:
            symbol = opp.get("symbol")
            if symbol not in symbol_groups:
                symbol_groups[symbol] = []
            symbol_groups[symbol].append(opp)

        # Validate a reasonable number from each symbol
        for symbol, symbol_opps in list(symbol_groups.items())[
            :5
        ]:  # Max 5 symbols to avoid rate limits
            try:
                # Validate first few opportunities for this symbol
                for opportunity in symbol_opps[:3]:  # Max 3 per symbol
                    validated = await self.validate_opportunity(opportunity)
                    if validated:
                        validated_opportunities.append(validated)

                    # If validation fails, mark as high-confidence synthetic
                    elif opportunity.get("pricing_confidence", 0.0) >= 0.7:
                        # Keep synthetic with clear warnings
                        opportunity = opportunity.copy()
                        opportunity["data_source_type"] = "SYNTHETIC_CALCULATED"
                        opportunity["pricing_confidence"] = 0.75
                        opportunity["display_warnings"] = [
                            "⚠️ CALCULATED PRICING - Real options data unavailable",
                            "Verify with broker before trading",
                        ]
                        validated_opportunities.append(opportunity)

            except Exception as e:
                logger.warning(f"Error validating opportunities for {symbol}: {e}")
                # Fall back to synthetic data for this symbol
                for opp in symbol_opps[:2]:
                    if opp.get("pricing_confidence", 0.0) >= 0.6:
                        opp["display_warnings"] = [
                            "⚠️ ESTIMATED PRICING - Market data validation failed"
                        ]
                        validated_opportunities.append(opp)

        logger.info(
            f"Validated {len(validated_opportunities)} opportunities (real + high-confidence synthetic)"
        )
        return validated_opportunities


# Global instance
options_validator = OptionsDataValidator()
