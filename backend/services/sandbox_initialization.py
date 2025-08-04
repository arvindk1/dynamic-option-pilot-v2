"""
Sandbox Strategy Initialization Service
Properly connects JSON strategy configs to sandbox system
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from services.sandbox_service import get_sandbox_service
from services.universe_loader import get_universe_loader
from utils.config_mappers import convert_json_to_sandbox_config

logger = logging.getLogger(__name__)


async def initialize_sandbox_from_json_strategies():
    """
    Initialize sandbox strategies from JSON configuration files
    This bridges the gap between live strategy JSON files and sandbox testing
    """
    try:
        # Get paths
        backend_dir = Path(__file__).parent.parent
        strategies_dir = backend_dir / "config" / "strategies" / "development"

        if not strategies_dir.exists():
            logger.warning(f"Strategies directory not found: {strategies_dir}")
            return

        sandbox_service = get_sandbox_service()
        universe_loader = get_universe_loader()

        # Load each JSON strategy file
        for json_file in strategies_dir.glob("*.json"):
            try:
                with open(json_file, "r") as f:
                    strategy_config = json.load(f)

                strategy_name = strategy_config.get("strategy_name", json_file.stem)
                strategy_id = strategy_config.get(
                    "strategy_type", json_file.stem.lower()
                )

                # Convert JSON config to sandbox format
                sandbox_config = convert_json_to_sandbox_config(
                    strategy_config, universe_loader
                )

                # Check if sandbox strategy already exists
                existing_strategies = await sandbox_service.get_user_strategies()
                strategy_exists = any(
                    s.name == strategy_name for s in existing_strategies
                )

                if not strategy_exists:
                    # Create new sandbox strategy
                    config = await sandbox_service.create_strategy_config(
                        strategy_id=strategy_id,
                        name=strategy_name,
                        config_data=sandbox_config,
                        user_id="default_user",
                    )
                    logger.info(
                        f"Created sandbox strategy: {strategy_name} from {json_file.name}"
                    )
                else:
                    # Update existing strategy with latest JSON config
                    existing_strategy = next(
                        s for s in existing_strategies if s.name == strategy_name
                    )
                    updated_config = await sandbox_service.update_strategy_config(
                        existing_strategy.id, {"config_data": sandbox_config}
                    )
                    logger.info(
                        f"Updated sandbox strategy: {strategy_name} from {json_file.name}"
                    )

            except Exception as e:
                logger.error(f"Failed to process strategy file {json_file}: {e}")

    except Exception as e:
        logger.error(f"Failed to initialize sandbox from JSON strategies: {e}")


# Conversion logic moved to utils/config_mappers.py


async def sync_sandbox_strategy_with_json(strategy_id: str, json_file_path: str):
    """
    Sync a specific sandbox strategy with its JSON file
    """
    try:
        with open(json_file_path, "r") as f:
            json_config = json.load(f)

        universe_loader = get_universe_loader()
        sandbox_config = convert_json_to_sandbox_config(json_config, universe_loader)

        sandbox_service = get_sandbox_service()

        # Update the strategy
        updated = await sandbox_service.update_strategy_config(
            strategy_id, {"config_data": sandbox_config}
        )

        if updated:
            logger.info(
                f"Successfully synced sandbox strategy {strategy_id} with JSON file"
            )
            return True
        else:
            logger.error(f"Failed to sync sandbox strategy {strategy_id}")
            return False

    except Exception as e:
        logger.error(f"Error syncing sandbox strategy with JSON: {e}")
        return False


if __name__ == "__main__":
    import os
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    import asyncio

    asyncio.run(initialize_sandbox_from_json_strategies())
