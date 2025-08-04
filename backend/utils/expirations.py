"""
Options Expiration Utilities - Generate and manage option expiration dates
Extracted from trading.py for better testability and reusability
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ExpirationType(Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    LEAP = "leap"


@dataclass
class OptionExpiration:
    """Structured option expiration information"""

    date: datetime
    dte: int  # Days to expiration
    exp_type: ExpirationType
    display: str
    is_standard: bool = True  # Standard vs non-standard expiration

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for API compatibility"""
        return {
            "date": self.date,
            "dte": self.dte,
            "type": self.exp_type.value,
            "display": self.display,
            "is_standard": self.is_standard,
        }


class ExpirationGenerator:
    """Generate option expiration dates based on market conventions"""

    @staticmethod
    def is_monthly_expiration(friday: date) -> bool:
        """Check if Friday is a monthly expiration (3rd Friday)"""
        # Monthly options expire on the 3rd Friday (day 15-21)
        return 15 <= friday.day <= 21

    @staticmethod
    def is_quarterly_expiration(friday: date) -> bool:
        """Check if Friday is a quarterly expiration (March, June, Sept, Dec)"""
        return friday.month in [
            3,
            6,
            9,
            12,
        ] and ExpirationGenerator.is_monthly_expiration(friday)

    @staticmethod
    def get_next_friday(from_date: date) -> date:
        """Get the next Friday from given date"""
        days_ahead = 4 - from_date.weekday()  # Friday is weekday 4
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return from_date + timedelta(days=days_ahead)

    @staticmethod
    def get_option_expirations(
        count: int = 6,
        min_dte: int = 1,
        max_dte: int = 60,
        include_monthly_only: bool = False,
    ) -> List[OptionExpiration]:
        """
        Generate realistic option expiration dates
        Extracted and enhanced from trading.py

        Args:
            count: Number of expirations to return
            min_dte: Minimum days to expiration
            max_dte: Maximum days to expiration
            include_monthly_only: Only include monthly expirations
        """
        base_date = datetime.now(timezone.utc)
        today = base_date.date()

        expirations = []
        current_date = today
        friday_count = 0

        while len(expirations) < count and friday_count < 20:  # Safety limit
            next_friday = ExpirationGenerator.get_next_friday(current_date)
            dte = (next_friday - today).days
            friday_count += 1

            # Skip if outside DTE range
            if dte < min_dte or dte > max_dte:
                current_date = next_friday + timedelta(days=1)
                continue

            # Determine expiration type
            is_monthly = ExpirationGenerator.is_monthly_expiration(next_friday)
            is_quarterly = ExpirationGenerator.is_quarterly_expiration(next_friday)

            if include_monthly_only and not is_monthly:
                current_date = next_friday + timedelta(days=1)
                continue

            if is_quarterly:
                exp_type = ExpirationType.QUARTERLY
            elif is_monthly:
                exp_type = ExpirationType.MONTHLY
            else:
                exp_type = ExpirationType.WEEKLY

            expiration = OptionExpiration(
                date=datetime.combine(next_friday, datetime.min.time()).replace(
                    tzinfo=timezone.utc
                ),
                dte=dte,
                exp_type=exp_type,
                display=next_friday.strftime("%m/%d/%Y"),
                is_standard=True,
            )

            expirations.append(expiration)
            current_date = next_friday + timedelta(days=1)

        return expirations

    @staticmethod
    def get_option_expirations_legacy() -> List[Dict[str, Any]]:
        """
        Legacy function for backward compatibility
        Returns same format as original get_option_expirations()
        """
        expirations = ExpirationGenerator.get_option_expirations()
        return [exp.to_dict() for exp in expirations]

    @staticmethod
    def filter_expirations_by_strategy(
        expirations: List[OptionExpiration],
        strategy_type: str,
        min_dte: Optional[int] = None,
        max_dte: Optional[int] = None,
    ) -> List[OptionExpiration]:
        """Filter expirations based on strategy requirements"""

        # Strategy-specific DTE preferences
        strategy_dte_ranges = {
            "CREDIT_SPREAD": (14, 45),
            "IRON_CONDOR": (21, 35),
            "NAKED_OPTION": (7, 30),
            "STRADDLE": (14, 45),
            "CALENDAR": (21, 60),
        }

        # Use strategy defaults or provided ranges
        if strategy_type in strategy_dte_ranges:
            default_min, default_max = strategy_dte_ranges[strategy_type]
            min_dte = min_dte or default_min
            max_dte = max_dte or default_max
        else:
            min_dte = min_dte or 7
            max_dte = max_dte or 45

        return [exp for exp in expirations if min_dte <= exp.dte <= max_dte]

    @staticmethod
    def get_expiration_by_dte_target(
        target_dte: int, tolerance: int = 3
    ) -> Optional[OptionExpiration]:
        """Find expiration closest to target DTE within tolerance"""
        expirations = ExpirationGenerator.get_option_expirations(count=12)

        closest = None
        min_diff = float("inf")

        for exp in expirations:
            diff = abs(exp.dte - target_dte)
            if diff <= tolerance and diff < min_diff:
                min_diff = diff
                closest = exp

        return closest


class ExpirationCalendar:
    """Manage expiration calendar and market schedules"""

    # Market holidays when options don't expire (simplified list)
    MARKET_HOLIDAYS_2025 = [
        date(2025, 1, 1),  # New Year's Day
        date(2025, 1, 20),  # MLK Day
        date(2025, 2, 17),  # Presidents Day
        date(2025, 4, 18),  # Good Friday
        date(2025, 5, 26),  # Memorial Day
        date(2025, 7, 4),  # Independence Day
        date(2025, 9, 1),  # Labor Day
        date(2025, 11, 27),  # Thanksgiving
        date(2025, 12, 25),  # Christmas
    ]

    @staticmethod
    def is_market_holiday(check_date: date) -> bool:
        """Check if date is a market holiday"""
        return check_date in ExpirationCalendar.MARKET_HOLIDAYS_2025

    @staticmethod
    def adjust_for_holidays(expiration_date: date) -> date:
        """Adjust expiration date if it falls on a holiday"""
        if ExpirationCalendar.is_market_holiday(expiration_date):
            # Move to previous trading day
            adjusted = expiration_date - timedelta(days=1)
            # If that's also a holiday or weekend, keep going back
            while adjusted.weekday() >= 5 or ExpirationCalendar.is_market_holiday(
                adjusted
            ):
                adjusted -= timedelta(days=1)
            return adjusted
        return expiration_date

    @staticmethod
    def get_trading_days_between(start_date: date, end_date: date) -> int:
        """Count trading days between two dates (excluding weekends and holidays)"""
        current = start_date
        trading_days = 0

        while current <= end_date:
            if (
                current.weekday() < 5  # Not weekend
                and not ExpirationCalendar.is_market_holiday(current)
            ):
                trading_days += 1
            current += timedelta(days=1)

        return trading_days
