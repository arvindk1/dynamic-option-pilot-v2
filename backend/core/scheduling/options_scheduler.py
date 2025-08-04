"""
Options Trading Scheduler based on v1 scheduler.py pattern.

Provides strategy-specific scheduling intervals:
- High Probability: Every 3-5 minutes during market hours
- Quick Scalps: Every 1-2 minutes during peak hours (9:30-10:30 AM, 3:00-4:00 PM)
- Swing Trades: Every 10-15 minutes
- Volatility Plays: Every 2-3 minutes + event triggers
- Theta Crop: Every 5-10 minutes
"""

import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Any, Callable, Dict, List, Optional

import pytz
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from config.settings import get_settings
from core.orchestrator.plugin_registry import PluginRegistry
from models.database import get_db
from models.opportunity import ScanSession
from services.opportunity_cache import OpportunityCache, get_opportunity_cache

logger = logging.getLogger(__name__)


class MarketHours:
    """Market hours utility class."""

    def __init__(self, timezone: str = "US/Eastern"):
        self.timezone = pytz.timezone(timezone)
        self.market_open = time(9, 30)  # 9:30 AM ET
        self.market_close = time(16, 0)  # 4:00 PM ET
        self.peak_morning_start = time(9, 30)  # 9:30 AM ET
        self.peak_morning_end = time(10, 30)  # 10:30 AM ET
        self.peak_afternoon_start = time(15, 0)  # 3:00 PM ET
        self.peak_afternoon_end = time(16, 0)  # 4:00 PM ET

    def is_market_hours(self, dt: datetime = None) -> bool:
        """Check if current time is during market hours."""
        if dt is None:
            dt = datetime.now(self.timezone)
        elif dt.tzinfo is None:
            dt = self.timezone.localize(dt)
        else:
            dt = dt.astimezone(self.timezone)

        # Skip weekends
        if dt.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False

        current_time = dt.time()
        return self.market_open <= current_time <= self.market_close

    def is_peak_hours(self, dt: datetime = None) -> bool:
        """Check if current time is during peak trading hours."""
        if not self.is_market_hours(dt):
            return False

        if dt is None:
            dt = datetime.now(self.timezone)
        elif dt.tzinfo is None:
            dt = self.timezone.localize(dt)
        else:
            dt = dt.astimezone(self.timezone)

        current_time = dt.time()

        # Morning peak: 9:30-10:30 AM ET
        morning_peak = self.peak_morning_start <= current_time <= self.peak_morning_end

        # Afternoon peak: 3:00-4:00 PM ET
        afternoon_peak = (
            self.peak_afternoon_start <= current_time <= self.peak_afternoon_end
        )

        return morning_peak or afternoon_peak


class OptionsScheduler:
    """
    Strategy-aware options trading scheduler based on v1 architecture.

    Manages different scanning intervals for each trading strategy:
    - Integrates with plugin registry (replaces v1 orchestrator)
    - Uses opportunity cache for performance
    - Provides market hours awareness
    - Supports event-driven triggers
    """

    def __init__(
        self, plugin_registry: PluginRegistry, opportunity_cache: OpportunityCache
    ):
        self.plugin_registry = plugin_registry
        self.opportunity_cache = opportunity_cache
        self.scheduler = AsyncIOScheduler(timezone="US/Eastern")
        self.market_hours = MarketHours()
        self.settings = get_settings()

        # Strategy configurations with intervals in minutes
        self.strategy_configs = {
            "high_probability": {
                "interval_minutes": 4,  # Every 3-5 minutes (using 4 as middle)
                "enabled": True,
                "market_hours_only": True,
                "symbols": ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "GOOGL", "AMZN"],
            },
            "quick_scalp": {
                "interval_minutes": 1.5,  # Every 1-2 minutes during peak hours
                "enabled": True,
                "peak_hours_only": True,  # Only during peak trading hours
                "symbols": ["SPY", "QQQ", "TSLA", "NVDA"],
            },
            "swing_trade": {
                "interval_minutes": 12,  # Every 10-15 minutes (using 12 as middle)
                "enabled": True,
                "market_hours_only": True,
                "symbols": [
                    "SPY",
                    "QQQ",
                    "IWM",
                    "AAPL",
                    "MSFT",
                    "GOOGL",
                    "AMZN",
                    "TSLA",
                    "NVDA",
                    "META",
                ],
            },
            "volatility_play": {
                "interval_minutes": 2.5,  # Every 2-3 minutes
                "enabled": True,
                "market_hours_only": True,
                "event_driven": True,  # Also triggered by volatility events
                "symbols": ["SPY", "QQQ", "VIX", "UVXY", "SQQQ"],
            },
            "theta_crop": {
                "interval_minutes": 7,  # Every 5-10 minutes (using 7 as middle)
                "enabled": True,
                "market_hours_only": True,
                "symbols": ["SPY", "QQQ", "IWM", "DIA"],
            },
        }

        # Job tracking
        self.active_jobs = {}
        self.scan_stats = {
            "total_scans": 0,
            "successful_scans": 0,
            "failed_scans": 0,
            "last_scan_time": None,
            "opportunities_found_today": 0,
        }

        # Add event listeners
        self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)

        logger.info("OptionsScheduler initialized with strategy-specific intervals")

    async def start(self):
        """Start the scheduler and configure all jobs."""
        try:
            # Schedule strategy-specific scanning jobs
            await self._schedule_strategy_jobs()

            # Schedule maintenance jobs
            await self._schedule_maintenance_jobs()

            # Start the scheduler
            self.scheduler.start()

            logger.info("OptionsScheduler started successfully")

        except Exception as e:
            logger.error(f"Failed to start OptionsScheduler: {e}")
            raise

    async def stop(self):
        """Stop the scheduler gracefully."""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)
            logger.info("OptionsScheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping OptionsScheduler: {e}")

    async def _schedule_strategy_jobs(self):
        """Schedule jobs for each trading strategy."""
        for strategy, config in self.strategy_configs.items():
            if not config.get("enabled", True):
                logger.info(f"Strategy {strategy} is disabled, skipping")
                continue

            # Create interval trigger
            interval_seconds = int(config["interval_minutes"] * 60)
            trigger = IntervalTrigger(seconds=interval_seconds)

            # Schedule the job
            job_id = f"scan_{strategy}"
            job = self.scheduler.add_job(
                func=self._scan_strategy,
                args=[strategy],
                trigger=trigger,
                id=job_id,
                name=f"Scan {strategy.replace('_', ' ').title()}",
                max_instances=1,  # Prevent overlapping scans
                coalesce=True,  # Combine missed executions
            )

            self.active_jobs[strategy] = job
            logger.info(
                f"Scheduled {strategy} scanning every {config['interval_minutes']} minutes"
            )

    async def _schedule_maintenance_jobs(self):
        """Schedule maintenance and cleanup jobs."""

        # Cache cleanup every 10 minutes
        self.scheduler.add_job(
            func=self._cleanup_cache,
            trigger=IntervalTrigger(minutes=10),
            id="cleanup_cache",
            name="Cache Cleanup",
            max_instances=1,
        )

        # Database maintenance every hour
        self.scheduler.add_job(
            func=self._database_maintenance,
            trigger=CronTrigger(minute=0),  # Every hour at minute 0
            id="database_maintenance",
            name="Database Maintenance",
            max_instances=1,
        )

        # Daily stats reset at market open
        self.scheduler.add_job(
            func=self._reset_daily_stats,
            trigger=CronTrigger(
                hour=9, minute=25, day_of_week="mon-fri"
            ),  # 5 min before market open
            id="reset_daily_stats",
            name="Reset Daily Stats",
            max_instances=1,
        )

        logger.info("Scheduled maintenance jobs")

    async def _scan_strategy(self, strategy: str):
        """
        Execute scanning for a specific strategy.
        Based on v1's market_open_tasks pattern but strategy-specific.
        """
        config = self.strategy_configs.get(strategy)
        if not config:
            logger.error(f"No configuration found for strategy: {strategy}")
            return

        # Check market hours requirements
        if config.get("market_hours_only") and not self.market_hours.is_market_hours():
            logger.debug(f"Skipping {strategy} scan - outside market hours")
            return

        if config.get("peak_hours_only") and not self.market_hours.is_peak_hours():
            logger.debug(f"Skipping {strategy} scan - outside peak hours")
            return

        scan_session_id = None

        try:
            self.scan_stats["total_scans"] += 1
            self.scan_stats["last_scan_time"] = datetime.utcnow()

            logger.info(f"Starting {strategy} scan")

            # Create scan session
            db_gen = get_db()
            db = next(db_gen)
            try:
                session = ScanSession(
                    strategy=strategy,
                    symbols_scanned=config.get("symbols", []),
                    scan_parameters=config,
                )
                db.add(session)
                db.commit()
                db.refresh(session)
                scan_session_id = session.id
            finally:
                db.close()

            # Get data plugin (replaces v1's orchestrator.get_plugin("data"))
            data_plugin = self.plugin_registry.get_plugin("yfinance_provider")
            if not data_plugin:
                raise Exception("Data provider plugin not available")

            # Scan for opportunities using the strategy
            opportunities = await self._perform_strategy_scan(
                strategy, config, data_plugin
            )

            # Update cache with results
            if opportunities:
                await self.opportunity_cache.add_opportunities(
                    opportunities, strategy, scan_session_id
                )
                self.scan_stats["opportunities_found_today"] += len(opportunities)
                logger.info(
                    f"{strategy} scan completed: {len(opportunities)} opportunities found"
                )
            else:
                logger.info(f"{strategy} scan completed: no opportunities found")

            # Update scan session
            db_gen = get_db()
            db = next(db_gen)
            try:
                session = (
                    db.query(ScanSession)
                    .filter(ScanSession.id == scan_session_id)
                    .first()
                )
                if session:
                    session.completed_at = datetime.utcnow()
                    session.opportunities_found = (
                        len(opportunities) if opportunities else 0
                    )
                    session.status = "COMPLETED"
                    db.commit()
            finally:
                db.close()

            self.scan_stats["successful_scans"] += 1

        except Exception as e:
            logger.error(f"Error scanning {strategy}: {e}")
            self.scan_stats["failed_scans"] += 1

            # Update scan session with error
            if scan_session_id:
                try:
                    db_gen = get_db()
                    db = next(db_gen)
                    try:
                        session = (
                            db.query(ScanSession)
                            .filter(ScanSession.id == scan_session_id)
                            .first()
                        )
                        if session:
                            session.completed_at = datetime.utcnow()
                            session.status = "FAILED"
                            session.error_message = str(e)
                            db.commit()
                    finally:
                        db.close()
                except Exception as db_error:
                    logger.error(f"Error updating scan session: {db_error}")

    async def _perform_strategy_scan(
        self, strategy: str, config: Dict[str, Any], data_plugin
    ) -> List[Dict[str, Any]]:
        """
        Perform the actual scanning logic for a strategy.
        This is where the strategy-specific opportunity detection would happen.
        """
        opportunities = []
        symbols = config.get("symbols", [])

        try:
            # For now, we'll return enhanced demo data based on strategy
            # In a real implementation, this would:
            # 1. Get market data for symbols
            # 2. Run strategy-specific analysis
            # 3. Identify trading opportunities
            # 4. Calculate metrics (probability of profit, expected value, etc.)

            # Example implementation for high_probability strategy:
            if strategy == "high_probability":
                for symbol in symbols[:3]:  # Limit to first 3 for demo
                    # Simulate getting market data
                    market_data = await data_plugin.get_market_data(symbol)
                    if market_data:
                        # Simulate finding an opportunity
                        opportunity = {
                            "id": f"{symbol}_{strategy}_{int(datetime.utcnow().timestamp())}",
                            "symbol": symbol,
                            "strategy_type": strategy,
                            "short_strike": market_data.get("price", 100) * 0.98,
                            "long_strike": market_data.get("price", 100) * 0.90,
                            "premium": 2.85 + (len(opportunities) * 0.10),
                            "max_loss": 715 + (len(opportunities) * 50),
                            "delta": -0.12,
                            "probability_profit": 0.78 - (len(opportunities) * 0.02),
                            "expected_value": 195.50 + (len(opportunities) * 10),
                            "days_to_expiration": 28,
                            "underlying_price": market_data.get("price", 100),
                            "liquidity_score": 9.2 - (len(opportunities) * 0.1),
                            "bias": "BULLISH",
                            "rsi": 45.3 + (len(opportunities) * 2),
                            "scan_timestamp": datetime.utcnow().isoformat(),
                            "is_live": True,
                        }
                        opportunities.append(opportunity)

            # Add similar logic for other strategies...
            elif strategy == "quick_scalp":
                # Quick scalp opportunities - smaller, faster trades
                for symbol in symbols[:2]:
                    market_data = await data_plugin.get_market_data(symbol)
                    if market_data:
                        opportunity = {
                            "id": f"{symbol}_{strategy}_{int(datetime.utcnow().timestamp())}",
                            "symbol": symbol,
                            "strategy_type": strategy,
                            "strike": market_data.get("price", 100) * 1.02,
                            "premium": 1.20 + (len(opportunities) * 0.05),
                            "max_loss": 120 + (len(opportunities) * 20),
                            "delta": 0.25,
                            "probability_profit": 0.55 - (len(opportunities) * 0.01),
                            "expected_value": 45.00 + (len(opportunities) * 5),
                            "days_to_expiration": 3,
                            "underlying_price": market_data.get("price", 100),
                            "liquidity_score": 8.5,
                            "bias": "NEUTRAL",
                            "rsi": 52.1,
                            "scan_timestamp": datetime.utcnow().isoformat(),
                            "is_live": True,
                        }
                        opportunities.append(opportunity)

        except Exception as e:
            logger.error(f"Error performing {strategy} scan: {e}")

        return opportunities

    async def _cleanup_cache(self):
        """Clean up expired cache entries."""
        try:
            await self.opportunity_cache.cleanup_expired()
            logger.debug("Cache cleanup completed")
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")

    async def _database_maintenance(self):
        """Perform database maintenance tasks."""
        try:
            # Clean up old scan sessions (keep last 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)

            db_gen = get_db()
            db = next(db_gen)
            try:
                old_sessions = (
                    db.query(ScanSession)
                    .filter(ScanSession.started_at < cutoff_time)
                    .all()
                )

                for session in old_sessions:
                    db.delete(session)

                db.commit()

                if old_sessions:
                    logger.info(
                        f"Database maintenance: cleaned up {len(old_sessions)} old scan sessions"
                    )
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error during database maintenance: {e}")

    async def _reset_daily_stats(self):
        """Reset daily statistics."""
        try:
            self.scan_stats["opportunities_found_today"] = 0
            logger.info("Daily stats reset for new trading day")
        except Exception as e:
            logger.error(f"Error resetting daily stats: {e}")

    def _job_executed(self, event):
        """Handle job execution events."""
        logger.debug(f"Job {event.job_id} executed successfully")

    def _job_error(self, event):
        """Handle job error events."""
        logger.error(f"Job {event.job_id} failed with exception: {event.exception}")

    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get comprehensive scheduler status."""
        return {
            "running": self.scheduler.running,
            "active_jobs": {
                strategy: {
                    "id": job.id,
                    "name": job.name,
                    "next_run": (
                        job.next_run_time.isoformat() if job.next_run_time else None
                    ),
                    "enabled": self.strategy_configs[strategy].get("enabled", True),
                }
                for strategy, job in self.active_jobs.items()
            },
            "scan_stats": self.scan_stats.copy(),
            "market_status": {
                "is_market_hours": self.market_hours.is_market_hours(),
                "is_peak_hours": self.market_hours.is_peak_hours(),
                "current_time_et": datetime.now(self.market_hours.timezone).isoformat(),
            },
        }

    async def trigger_manual_scan(self, strategy: str) -> bool:
        """Manually trigger a scan for a specific strategy."""
        try:
            if strategy not in self.strategy_configs:
                logger.error(f"Unknown strategy: {strategy}")
                return False

            logger.info(f"Manual scan triggered for {strategy}")
            await self._scan_strategy(strategy)
            return True

        except Exception as e:
            logger.error(f"Error in manual scan for {strategy}: {e}")
            return False


# Global scheduler instance
_options_scheduler: Optional[OptionsScheduler] = None


def get_options_scheduler() -> Optional[OptionsScheduler]:
    """Get global scheduler instance."""
    return _options_scheduler


def initialize_options_scheduler(
    plugin_registry: PluginRegistry, opportunity_cache: OpportunityCache
) -> OptionsScheduler:
    """Initialize global scheduler instance."""
    global _options_scheduler
    _options_scheduler = OptionsScheduler(plugin_registry, opportunity_cache)
    return _options_scheduler
