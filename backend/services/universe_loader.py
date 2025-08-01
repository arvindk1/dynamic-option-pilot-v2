"""
Universe Loader Service - Load and manage trading symbol universes.

Provides organized symbol lists for different trading strategies:
- MAG7: Tech giants driving market sentiment
- TOP20: Most liquid large caps
- ETFs: Sector and broad market ETFs  
- Sector Leaders: Top stocks by sector
- RSI Tickers: Mean reversion candidates
"""

import logging
from pathlib import Path
from typing import List, Dict, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class UniverseInfo:
    """Information about a trading universe."""
    name: str
    description: str
    symbols: List[str]
    file_path: str

class UniverseLoader:
    """Load and manage trading symbol universes from files."""
    
    def __init__(self, universes_dir: str = None):
        """Initialize with path to universes directory."""
        if universes_dir is None:
            # Default to backend/data/universes
            current_dir = Path(__file__).parent
            self.universes_dir = current_dir.parent / "data" / "universes"
        else:
            self.universes_dir = Path(universes_dir)
            
        self._universes: Dict[str, UniverseInfo] = {}
        self._load_all_universes()
        
    def _load_all_universes(self):
        """Load all universe files from the directory."""
        try:
            if not self.universes_dir.exists():
                logger.warning(f"Universes directory not found: {self.universes_dir}")
                return
                
            # Load each .txt file as a universe
            for file_path in self.universes_dir.glob("*.txt"):
                universe_name = file_path.stem
                symbols = self._load_symbols_from_file(file_path)
                
                if symbols:
                    description = self._get_universe_description(universe_name)
                    self._universes[universe_name] = UniverseInfo(
                        name=universe_name,
                        description=description,
                        symbols=symbols,
                        file_path=str(file_path)
                    )
                    logger.info(f"Loaded universe '{universe_name}': {len(symbols)} symbols")
                    
        except Exception as e:
            logger.error(f"Error loading universes: {e}")
    
    def _load_symbols_from_file(self, file_path: Path) -> List[str]:
        """Load symbols from a text file, ignoring comments."""
        symbols = []
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        # Extract symbol (first word before any comment)
                        symbol = line.split()[0].upper()
                        if symbol:
                            symbols.append(symbol)
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            
        return symbols
    
    def _get_universe_description(self, name: str) -> str:
        """Get description for a universe based on its name."""
        descriptions = {
            'mag7': 'Magnificent Seven tech giants driving market sentiment',
            'top20': 'Top 20 most liquid large cap stocks for options trading',
            'etfs': 'Exchange traded funds with high options liquidity',
            'sector_leaders': 'Leading stocks by sector for targeted strategies',
            'rsi_tickers': 'Mean reversion candidates for RSI-based strategies'
        }
        return descriptions.get(name, f"Trading universe: {name}")
    
    def get_universe(self, name: str) -> List[str]:
        """Get symbols for a specific universe."""
        if name in self._universes:
            return self._universes[name].symbols.copy()
        else:
            logger.warning(f"Universe '{name}' not found")
            return []
    
    def get_universe_info(self, name: str) -> UniverseInfo:
        """Get full information about a universe."""
        return self._universes.get(name)
    
    def list_universes(self) -> List[str]:
        """List all available universe names."""
        return list(self._universes.keys())
    
    def get_all_universes(self) -> Dict[str, UniverseInfo]:
        """Get all universe information."""
        return self._universes.copy()
    
    def get_symbols_for_strategy(self, strategy: str) -> List[str]:
        """Get appropriate symbols for a specific strategy."""
        strategy_mappings = {
            'high_probability': ['top20', 'mag7'],
            'quick_scalp': ['mag7', 'etfs'],  # Most liquid for scalping
            'swing_trade': ['top20', 'sector_leaders'],
            'volatility_play': ['etfs', 'mag7'],  # High volatility names
            'theta_crop': ['etfs', 'top20'],  # Stable, high-premium names
            'rsi_coupon': ['rsi_tickers']  # Mean reversion candidates
        }
        
        universes = strategy_mappings.get(strategy, ['top20'])  # Default to top20
        all_symbols = set()
        
        for universe_name in universes:
            symbols = self.get_universe(universe_name)
            all_symbols.update(symbols)
            
        return list(all_symbols)
    
    def get_strategy_universe_priority(self, strategy: str) -> List[str]:
        """Get symbols prioritized for a strategy (most important first)."""
        symbols = self.get_symbols_for_strategy(strategy)
        
        # Strategy-specific prioritization
        if strategy == 'quick_scalp':
            # Prioritize most liquid (MAG7 first, then major ETFs)
            mag7 = self.get_universe('mag7')
            major_etfs = ['SPY', 'QQQ', 'IWM']
            other_symbols = [s for s in symbols if s not in mag7 and s not in major_etfs]
            return mag7 + major_etfs + other_symbols
            
        elif strategy == 'high_probability':
            # Prioritize stable, high-volume names
            top20 = self.get_universe('top20')
            other_symbols = [s for s in symbols if s not in top20]
            return top20 + other_symbols
            
        elif strategy == 'theta_crop':
            # Prioritize ETFs and stable large caps
            etfs = ['SPY', 'QQQ', 'IWM', 'XLK', 'XLF']
            stable_stocks = ['AAPL', 'MSFT', 'GOOGL', 'JPM', 'WMT']
            other_symbols = [s for s in symbols if s not in etfs and s not in stable_stocks]
            return etfs + stable_stocks + other_symbols
            
        else:
            return symbols

# Global instance
universe_loader = UniverseLoader()

def get_universe_loader() -> UniverseLoader:
    """Get the global universe loader instance."""
    return universe_loader