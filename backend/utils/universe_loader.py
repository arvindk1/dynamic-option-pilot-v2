"""
Universe Loader - Load stock universes from data files
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class UniverseLoader:
    def __init__(self, data_path: str = None):
        """Initialize universe loader with data path."""
        if data_path is None:
            # Default to backend/data/universes
            current_dir = Path(__file__).parent.parent
            data_path = current_dir / "data" / "universes"

        self.data_path = Path(data_path)
        self._cache = {}

    def load_universe(self, universe_name: str) -> List[str]:
        """Load a specific universe from file."""
        if universe_name in self._cache:
            return self._cache[universe_name]

        universe_file = self.data_path / f"{universe_name}.txt"

        if not universe_file.exists():
            logger.warning(f"Universe file not found: {universe_file}")
            return []

        return self._load_from_file(universe_file, universe_name)

    def load_universe_symbols(self, file_path: str) -> List[str]:
        """Load universe symbols from a file path (supports both relative and absolute paths)."""
        # Handle different path formats
        if file_path.startswith("backend/"):
            # Remove backend/ prefix since we're already in backend/
            file_path = file_path[8:]

        # Convert to Path object
        universe_file = Path(file_path)

        # If relative path, make it relative to backend/ directory
        if not universe_file.is_absolute():
            backend_dir = Path(__file__).parent.parent
            universe_file = backend_dir / universe_file

        if not universe_file.exists():
            logger.warning(f"Universe file not found: {universe_file}")
            return []

        cache_key = f"file:{file_path}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        return self._load_from_file(universe_file, cache_key)

    def _load_from_file(self, universe_file: Path, cache_key: str) -> List[str]:
        """Common method to load symbols from a file."""
        symbols = []
        try:
            with open(universe_file, "r") as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if line and not line.startswith("#"):
                        # Extract symbol (first word before any comment)
                        symbol = line.split()[0]
                        if symbol and symbol not in symbols:
                            symbols.append(symbol.upper())

            self._cache[cache_key] = symbols
            logger.info(f"Loaded {len(symbols)} symbols from {universe_file.name}")
            return symbols

        except Exception as e:
            logger.error(f"Error loading universe from {universe_file}: {e}")
            return []

    def get_top20_stocks(self) -> List[str]:
        """Get the TOP 20 most liquid large cap stocks."""
        return self.load_universe("top20")

    def get_mag7_stocks(self) -> List[str]:
        """Get the MAG 7 tech giants."""
        # Extract first 7 symbols from top20 (they're MAG7)
        top20 = self.get_top20_stocks()
        return top20[:7] if len(top20) >= 7 else top20

    def get_all_universes(self) -> Dict[str, List[str]]:
        """Get all available universes."""
        universes = {}

        if not self.data_path.exists():
            logger.warning(f"Universe data path does not exist: {self.data_path}")
            return universes

        # Find all .txt files in the universes directory
        for universe_file in self.data_path.glob("*.txt"):
            universe_name = universe_file.stem
            symbols = self.load_universe(universe_name)
            if symbols:
                universes[universe_name] = symbols

        return universes

    def clear_cache(self):
        """Clear the universe cache."""
        self._cache.clear()


# Global instance
_universe_loader = None


def get_universe_loader() -> UniverseLoader:
    """Get global universe loader instance."""
    global _universe_loader
    if _universe_loader is None:
        _universe_loader = UniverseLoader()
    return _universe_loader
