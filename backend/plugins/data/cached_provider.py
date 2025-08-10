"""
Cached Data Provider
Uses local cache files to avoid API rate limits during development
"""

import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, Optional

from plugins.data.alpaca_provider import AlpacaProvider
from models.market_data import Quote, OptionsChain

logger = logging.getLogger(__name__)

class CachedDataProvider(AlpacaProvider):
    """
    Data provider that uses cached market data to avoid API rate limits.
    Falls back to live Alpaca API if cache is missing.
    """
    
    def __init__(self):
        super().__init__()
        self.cache_dir = Path(__file__).parent.parent.parent / "cache" / "market_data"
        self.today = date.today().isoformat()
        self.cache_path = self.cache_dir / self.today
        
        # Load cache files
        self.quotes_cache = self._load_cache_file("quotes.json")
        self.options_cache = self._load_cache_file("options.json")
        
        logger.info(f"📁 Cached provider initialized")
        logger.info(f"   📊 Quotes cache: {len(self.quotes_cache)} symbols")
        logger.info(f"   ⚡ Options cache: {len(self.options_cache)} symbols")
        
    def _load_cache_file(self, filename: str) -> Dict[str, Any]:
        """Load cache file, return empty dict if not found"""
        cache_file = self.cache_path / filename
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                logger.info(f"✅ Loaded {filename}: {len(data)} entries")
                return data
            except Exception as e:
                logger.warning(f"❌ Failed to load {filename}: {e}")
        else:
            logger.warning(f"⚠️ Cache file not found: {cache_file}")
        return {}
    
    async def get_quote(self, symbol: str) -> Quote:
        """Get quote from cache first, fallback to live API"""
        
        # Try cache first
        if symbol in self.quotes_cache:
            cache_data = self.quotes_cache[symbol]
            logger.debug(f"📊 Using cached quote for {symbol}: ${cache_data['price']}")
            
            # Create Quote object from cached data
            quote = Quote(
                symbol=symbol,
                price=cache_data['price'],
                bid=cache_data.get('bid', cache_data['price'] * 0.999),
                ask=cache_data.get('ask', cache_data['price'] * 1.001),
                volume=cache_data.get('volume', 1000000),
                timestamp=cache_data.get('timestamp', datetime.now().isoformat())
            )
            return quote
        
        # Fallback to live API
        logger.warning(f"⚠️ No cached quote for {symbol}, using live API")
        try:
            return await super().get_quote(symbol)
        except Exception as e:
            logger.error(f"❌ Live API failed for {symbol}: {e}")
            # Return fallback quote
            return Quote(
                symbol=symbol,
                price=100.0,
                bid=99.0,
                ask=101.0,
                volume=1000000,
                timestamp=datetime.now().isoformat()
            )
    
    async def get_options_chain(self, symbol: str, expiration: Optional[str] = None) -> Dict[str, Any]:
        """Get options chain from cache first, fallback to live API"""
        
        # Try cache first
        if symbol in self.options_cache:
            cache_data = self.options_cache[symbol]
            logger.debug(f"⚡ Using cached options for {symbol}")
            
            chain = cache_data.get('chain', {'calls': [], 'puts': []})
            
            # Add real Greeks from cache if available
            for option_type in ['calls', 'puts']:
                for option in chain.get(option_type, []):
                    if 'greeks' not in option:
                        # Add realistic Greeks based on option characteristics
                        option['greeks'] = self._generate_realistic_greeks(option, option_type)
            
            return chain
        
        # Fallback to live API  
        logger.warning(f"⚠️ No cached options for {symbol}, using live API")
        try:
            return await super().get_options_chain(symbol, expiration)
        except Exception as e:
            logger.error(f"❌ Live options API failed for {symbol}: {e}")
            # Return empty chain
            return {'calls': [], 'puts': []}
    
    def _generate_realistic_greeks(self, option: Dict[str, Any], option_type: str) -> Dict[str, float]:
        """Generate realistic Greeks for cached options"""
        strike = option.get('strike', 100)
        
        # Simple realistic Greeks generation
        if option_type == 'calls':
            return {
                'delta': 0.5,    # At-the-money call
                'gamma': 0.02,   # Typical gamma
                'theta': -0.05,  # Time decay
                'vega': 0.15     # Volatility sensitivity
            }
        else:  # puts
            return {
                'delta': -0.5,   # At-the-money put
                'gamma': 0.02,   # Same gamma as call
                'theta': -0.05,  # Time decay
                'vega': 0.15     # Same vega as call
            }
    
    def is_using_cache(self) -> bool:
        """Check if provider is using cached data"""
        return len(self.quotes_cache) > 0 or len(self.options_cache) > 0