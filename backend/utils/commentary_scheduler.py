"""
Commentary Scheduler - Schedule automatic market commentary updates
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Optional

from services.market_commentary import get_market_commentary_service

logger = logging.getLogger(__name__)


class CommentaryScheduler:
    def __init__(self):
        self.commentary_service = get_market_commentary_service()
        self.scheduler_thread: Optional[threading.Thread] = None
        self.running = False
        self.last_update = None

    def start_scheduler(self):
        """Start the commentary update scheduler."""
        if self.running:
            logger.warning("Commentary scheduler already running")
            return

        self.running = True

        # Start scheduler thread
        self.scheduler_thread = threading.Thread(
            target=self._run_scheduler, daemon=True
        )
        self.scheduler_thread.start()

        logger.info("Commentary scheduler started with automatic updates")

    def stop_scheduler(self):
        """Stop the commentary scheduler."""
        self.running = False

        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)

        logger.info("Commentary scheduler stopped")

    def _run_scheduler(self):
        """Run the scheduler in a separate thread."""
        while self.running:
            try:
                current_time = datetime.utcnow()

                # Update every 30 minutes during market hours
                if (
                    self.last_update is None
                    or current_time - self.last_update > timedelta(minutes=30)
                ):
                    self._update_commentary("scheduled")
                    self.last_update = current_time

                # Check every 5 minutes
                time.sleep(300)  # 5 minutes
            except Exception as e:
                logger.error(f"Error in commentary scheduler: {e}")
                time.sleep(300)  # Continue after error

    def _update_commentary(self, update_type: str):
        """Update commentary with force refresh."""
        try:
            logger.info(f"Scheduled commentary update: {update_type}")

            # Force refresh to get latest data
            commentary = self.commentary_service.get_real_time_commentary(
                force_refresh=True
            )

            logger.info(
                f"Commentary updated for {commentary.get('display_date', 'unknown date')}"
            )
            logger.info(f"Session: {commentary.get('market_session', 'unknown')}")

            # Log earnings if available
            earnings = commentary.get("earnings_preview", [])
            if earnings:
                logger.info(f"Earnings preview includes {len(earnings)} companies")

        except Exception as e:
            logger.error(f"Failed to update commentary during {update_type}: {e}")

    def manual_update(self) -> dict:
        """Manually trigger a commentary update."""
        try:
            logger.info("Manual commentary update triggered")
            commentary = self.commentary_service.get_real_time_commentary(
                force_refresh=True
            )
            return {
                "status": "success",
                "message": "Commentary updated successfully",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "next_scheduled_update": commentary.get("next_update"),
            }
        except Exception as e:
            logger.error(f"Manual commentary update failed: {e}")
            return {
                "status": "error",
                "message": f"Failed to update commentary: {str(e)}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }


# Global scheduler instance
_commentary_scheduler: Optional[CommentaryScheduler] = None


def get_commentary_scheduler() -> CommentaryScheduler:
    """Get global commentary scheduler instance."""
    global _commentary_scheduler
    if _commentary_scheduler is None:
        _commentary_scheduler = CommentaryScheduler()
    return _commentary_scheduler


def start_commentary_scheduler():
    """Start the global commentary scheduler."""
    scheduler = get_commentary_scheduler()
    scheduler.start_scheduler()


def stop_commentary_scheduler():
    """Stop the global commentary scheduler."""
    if _commentary_scheduler:
        _commentary_scheduler.stop_scheduler()
