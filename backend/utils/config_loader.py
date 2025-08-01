"""Configuration loader utility for external YAML configurations."""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Utility for loading external configuration files."""
    
    def __init__(self, config_root: str = None):
        """Initialize config loader with root directory."""
        if config_root is None:
            # Default to backend/config relative to this file
            backend_dir = Path(__file__).parent.parent
            config_root = backend_dir / "config"
        
        self.config_root = Path(config_root)
        logger.info(f"ConfigLoader initialized with root: {self.config_root}")
    
    def load_strategy_config(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """Load strategy configuration from JSON or YAML file (JSON preferred)."""
        # Try JSON first (new preferred format), then YAML (legacy)
        config_files = [
            self.config_root / "strategies" / f"{strategy_id}.json",
            self.config_root / "strategies" / f"{strategy_id}.yaml"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        if config_file.suffix == '.json':
                            config = json.load(f)
                        else:
                            config = yaml.safe_load(f)
                    
                    logger.info(f"Loaded strategy config for {strategy_id} from {config_file.name}")
                    return config
                    
                except Exception as e:
                    logger.error(f"Failed to load strategy config {config_file}: {e}")
                    continue
        
        logger.error(f"No valid strategy config found for {strategy_id}")
        return None
    
    def load_universe_symbols(self, universe_name: str) -> Optional[list]:
        """Load universe symbols from text file."""
        universe_file = self.config_root.parent / "data" / "universes" / f"{universe_name}.txt"
        
        if not universe_file.exists():
            logger.error(f"Universe file not found: {universe_file}")
            return None
        
        try:
            symbols = []
            with open(universe_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if line and not line.startswith('#'):
                        # Extract symbol (first word before any comment)
                        symbol = line.split()[0] if line.split() else None
                        if symbol and symbol.isalpha():
                            symbols.append(symbol.upper())
            
            logger.info(f"Loaded {len(symbols)} symbols from universe {universe_name}")
            return symbols
            
        except Exception as e:
            logger.error(f"Failed to load universe {universe_name}: {e}")
            return None
    
    def get_config_path(self, *path_parts: str) -> Path:
        """Get path to config file/directory."""
        return self.config_root.joinpath(*path_parts)
    
    def list_strategy_configs(self) -> list:
        """List all available strategy configuration files."""
        strategies_dir = self.config_root / "strategies"
        
        if not strategies_dir.exists():
            return []
        
        config_files = []
        # Scan for both JSON and YAML files (JSON preferred)
        for file_path in list(strategies_dir.glob("*.json")) + list(strategies_dir.glob("*.yaml")):
            strategy_id = file_path.stem
            if strategy_id not in config_files:  # Avoid duplicates if both formats exist
                config_files.append(strategy_id)
        
        return config_files
    
    def list_universes(self) -> list:
        """List all available universe files."""
        universes_dir = self.config_root.parent / "data" / "universes"
        
        if not universes_dir.exists():
            return []
        
        universe_files = []
        for file_path in universes_dir.glob("*.txt"):
            universe_name = file_path.stem
            universe_files.append(universe_name)
        
        return universe_files


# Global config loader instance
_config_loader: Optional[ConfigLoader] = None


def initialize_config_loader(config_root: str = None) -> ConfigLoader:
    """Initialize the global config loader."""
    global _config_loader
    _config_loader = ConfigLoader(config_root)
    return _config_loader


def get_config_loader() -> Optional[ConfigLoader]:
    """Get the global config loader instance."""
    return _config_loader