"""Yahoo Finance data provider plugin for the new architecture."""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import pandas as pd
import yfinance as yf
import asyncio
import logging
from dataclasses import dataclass

from core.orchestrator.base_plugin import DataProviderPlugin, PluginMetadata, PluginType, PluginConfig
from core.interfaces.data_provider_interface import IDataProvider

logger = logging.getLogger(__name__)


@dataclass
class CachedData:
    """Cached data container with timestamp."""
    data: Any
    timestamp: datetime
    expires_at: datetime


@dataclass
class MarketData:
    """Market data structure."""
    symbol: str
    price: float
    volume: int
    timestamp: datetime
    atr: float
    vix: float
    change: float = 0.0
    change_percent: float = 0.0


@dataclass
class OptionChain:
    """Option chain data structure."""
    symbol: str
    underlying_price: float
    timestamp: datetime
    calls: pd.DataFrame
    puts: pd.DataFrame


class YFinanceProvider(DataProviderPlugin, IDataProvider):
    """Yahoo Finance data provider with intelligent caching."""
    
    def __init__(self, config: PluginConfig = None):
        super().__init__(config)
        
        # Symbol mapping for Yahoo Finance compatibility
        self.symbol_map = {
            'SPX': '^GSPC',  # S&P 500 Index
            '$SPX': '^GSPC',
            '^SPX': '^GSPC',
            'VIX': '^VIX',   # VIX Index
            '^VIX': '^VIX',
            'RUT': '^RUT',   # Russell 2000
            '^RUT': '^RUT',
            'NDX': '^NDX'    # NASDAQ 100
        }
        
        # Industry-standard refresh intervals
        self.refresh_intervals = {
            'market_data': 5,      # 5 seconds for real-time quotes
            'option_chains': 30,   # 30 seconds for option chains
            'historical': 300,     # 5 minutes for historical data
            'vix': 5,             # 5 seconds for volatility index
            'extended_hours': 60,  # 1 minute outside market hours
            'market_closed': 900   # 15 minutes when market is closed
        }
        
        # Cache storage
        self.cache: Dict[str, CachedData] = {}
        
        # Rate limiting
        self.last_request_time = {}
        self.min_request_interval = 0.1  # 100ms between requests
        
        # Degraded mode flag for handling yfinance issues
        self._degraded_mode = False
    
    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="yfinance_provider",
            version="2.0.0",
            plugin_type=PluginType.DATA_PROVIDER,
            description="Yahoo Finance data provider with intelligent caching",
            author="Dynamic Option Pilot",
            dependencies=[],
            config_schema={
                'type': 'object',
                'properties': {
                    'rate_limit_ms': {'type': 'integer', 'default': 100},
                    'cache_enabled': {'type': 'boolean', 'default': True}
                }
            }
        )
    
    async def initialize(self) -> bool:
        """Initialize the plugin."""
        try:
            self._logger.info("🚀 Yahoo Finance provider initializing")
            
            # TEMPORARY WORKAROUND: Skip yfinance initialization due to library cache issues
            # This allows the system to continue working without yfinance dependency
            try:
                # Quick test to see if yfinance is working
                test_ticker = yf.Ticker("SPY")
                test_hist = test_ticker.history(period="1d", timeout=5)
                
                if not test_hist.empty:
                    self._logger.info("✅ Yahoo Finance working normally")
                    return True
                else:
                    raise Exception("No historical data returned")
                    
            except Exception as yf_error:
                self._logger.warning(f"⚠️ YFinance library issue detected: {yf_error}")
                self._logger.warning("🔧 YFinance provider will use degraded mode (historical data only)")
                
                # Mark as initialized but with limited functionality
                self._degraded_mode = True
                return True  # Allow system to continue without full yfinance functionality
                
        except Exception as e:
            self._logger.error(f"❌ Yahoo Finance initialization failed: {e}")
            # Allow system to continue - other data providers (Alpaca) can handle market data
            self._logger.warning("🔄 System will continue with other data providers")
            self._degraded_mode = True
            return True
    
    async def cleanup(self) -> bool:
        """Clean up plugin resources."""
        try:
            self.cache.clear()
            self.last_request_time.clear()
            self._logger.info("✅ Yahoo Finance provider cleaned up")
            return True
        except Exception as e:
            self._logger.error(f"❌ Yahoo Finance cleanup failed: {e}")
            return False
    
    def _map_symbol(self, symbol: str) -> str:
        """Map symbol to Yahoo Finance compatible format."""
        clean_symbol = symbol.strip().upper()
        return self.symbol_map.get(clean_symbol, symbol)
    
    def _is_market_hours(self) -> bool:
        """Check if market is currently open (US Eastern Time)."""
        import pytz
        now = datetime.now(pytz.timezone('US/Eastern'))
        weekday = now.weekday()
        
        # Market closed on weekends
        if weekday >= 5:
            return False
        
        # Market hours: 9:30 AM - 4:00 PM ET
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now <= market_close
    
    def _get_cache_key(self, operation: str, symbol: str, **kwargs) -> str:
        """Generate cache key for operation."""
        key_parts = [operation, symbol]
        if kwargs:
            key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
        return "|".join(key_parts)
    
    def _get_refresh_interval(self, data_type: str) -> int:
        """Get appropriate refresh interval based on market conditions."""
        if not self._is_market_hours():
            return self.refresh_intervals.get('market_closed', 900)
        
        return self.refresh_intervals.get(data_type, 30)
    
    async def _get_cached_or_fetch(self, cache_key: str, data_type: str, fetch_func) -> Any:
        """Get data from cache or fetch fresh data."""
        if not self.config.settings.get('cache_enabled', True):
            return await fetch_func()
            
        now = datetime.now(timezone.utc)
        
        # Check cache first
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if now < cached.expires_at:
                self._logger.debug(f"📋 Cache HIT for {cache_key}")
                return cached.data

        # Rate limiting - non-blocking implementation
        rate_limit = self.config.settings.get('rate_limit_ms', 100) / 1000
        if cache_key in self.last_request_time:
            time_since_last = (now - self.last_request_time[cache_key]).total_seconds()
            if time_since_last < rate_limit:
                wait_time = rate_limit - time_since_last
                # Use asyncio.create_task to prevent event loop blocking
                await asyncio.create_task(asyncio.sleep(wait_time))

        # Fetch fresh data
        self._logger.debug(f"🌐 Cache MISS for {cache_key} - fetching fresh data")
        try:
            data = await fetch_func()
            refresh_interval = self._get_refresh_interval(data_type)
            expires_at = now + timedelta(seconds=refresh_interval)
            
            self.cache[cache_key] = CachedData(
                data=data,
                timestamp=now,
                expires_at=expires_at
            )
            self.last_request_time[cache_key] = now
            
            self._logger.debug(f"💾 Cached {cache_key} for {refresh_interval}s")
            return data
            
        except Exception as e:
            self._logger.error(f"❌ Failed to fetch {cache_key}: {e}")
            
            # Return stale cache if available
            if cache_key in self.cache:
                self._logger.warning(f"🕰️ Returning stale cache for {cache_key}")
                return self.cache[cache_key].data
            
            raise
    
    async def get_market_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get market data for a symbol."""
        cache_key = self._get_cache_key("market_data", symbol)
        yf_symbol = self._map_symbol(symbol)
        
        async def fetch_market_data():
            ticker = yf.Ticker(yf_symbol)
            
            # Get basic market data
            price = 0.0
            volume = 0
            change = 0.0
            change_percent = 0.0
            
            try:
                info = ticker.info
                
                # Priority: preMarketPrice > postMarketPrice > regularMarketPrice > currentPrice
                if info.get("preMarketPrice") and info.get("preMarketPrice") > 0:
                    price = info.get("preMarketPrice", 0.0)
                    change = info.get("preMarketChange", 0.0)
                    change_percent = info.get("preMarketChangePercent", 0.0)
                    volume = -1  # Special marker for no pre-market volume
                elif info.get("postMarketPrice") and info.get("postMarketPrice") > 0:
                    price = info.get("postMarketPrice", 0.0)
                    change = info.get("postMarketChange", 0.0)
                    change_percent = info.get("postMarketChangePercent", 0.0)
                    volume = -1  # Special marker for no post-market volume
                elif info.get("regularMarketPrice") and info.get("regularMarketPrice") > 0:
                    price = info.get("regularMarketPrice", 0.0)
                    change = info.get("regularMarketChange", 0.0)
                    change_percent = info.get("regularMarketChangePercent", 0.0)
                    volume = info.get("regularMarketVolume", info.get("volume", 0))
                elif info.get("currentPrice") and info.get("currentPrice") > 0:
                    price = info.get("currentPrice", 0.0)
                    volume = info.get("volume", 0)
                    
            except TypeError as te:
                if "datetime" in str(te) and "str" in str(te):
                    self._logger.warning(f"YFinance cache corruption for {symbol}, skipping info lookup")
                else:
                    self._logger.warning(f"Failed to get info for {symbol}: {te}")
            except Exception as e:
                self._logger.warning(f"Failed to get info for {symbol}: {e}")
            
            # Fallback to history if needed
            if price == 0.0 or (change == 0.0 and change_percent == 0.0):
                try:
                    hist = ticker.history(period="2d")
                    if not hist.empty:
                        current_price = float(hist["Close"].iloc[-1])
                        current_volume = int(hist["Volume"].iloc[-1]) if len(hist["Volume"]) > 0 else 0
                        
                        if price == 0.0:
                            price = current_price
                            volume = current_volume
                        
                        if len(hist) >= 2 and (change == 0.0 and change_percent == 0.0):
                            previous_close = float(hist["Close"].iloc[-2])
                            change = current_price - previous_close
                            change_percent = (change / previous_close * 100) if previous_close != 0 else 0.0
                            
                except Exception as e:
                    self._logger.warning(f"Failed to get history for {symbol}: {e}")
            
            # Calculate ATR and get VIX
            atr = await self._get_atr(symbol)
            vix = await self._get_vix()
            
            import pytz
            et_tz = pytz.timezone('US/Eastern')
            market_timestamp = datetime.now(et_tz)
            
            market_data = MarketData(
                symbol=symbol,
                price=float(price),
                volume=int(volume),
                timestamp=market_timestamp,
                atr=float(atr),
                vix=float(vix),
                change=float(change),
                change_percent=float(change_percent),
            )
            
            # Convert to dict for API compatibility
            return {
                'symbol': market_data.symbol,
                'price': market_data.price,
                'volume': market_data.volume,
                'timestamp': market_data.timestamp.isoformat(),
                'atr': market_data.atr,
                'vix': market_data.vix,
                'change': market_data.change,
                'change_percent': market_data.change_percent
            }
        
        return await self._get_cached_or_fetch(cache_key, 'market_data', fetch_market_data)
    
    async def get_options_chain(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get options chain for a symbol."""
        expiration = kwargs.get('expiration')
        if not expiration:
            raise ValueError("expiration date required for options chain")
            
        if isinstance(expiration, str):
            expiration = datetime.strptime(expiration, "%Y-%m-%d")
            
        cache_key = self._get_cache_key("option_chain", symbol, expiration=expiration.strftime("%Y-%m-%d"))
        yf_symbol = self._map_symbol(symbol)
        
        async def fetch_option_chain():
            ticker = yf.Ticker(yf_symbol)
            chain = ticker.option_chain(expiration.strftime("%Y-%m-%d"))
            calls = chain.calls
            puts = chain.puts
            
            # Get underlying price
            underlying_price = await self._get_underlying_price(symbol)
            
            option_chain = OptionChain(
                symbol=symbol,
                underlying_price=float(underlying_price),
                timestamp=datetime.now(timezone.utc),
                calls=calls,
                puts=puts,
            )
            
            # Convert to dict for API compatibility
            return {
                'symbol': option_chain.symbol,
                'underlying_price': option_chain.underlying_price,
                'timestamp': option_chain.timestamp.isoformat(),
                'calls': calls.to_dict('records'),
                'puts': puts.to_dict('records')
            }
        
        return await self._get_cached_or_fetch(cache_key, 'option_chains', fetch_option_chain)
    
    async def _get_underlying_price(self, symbol: str) -> float:
        """Get underlying price with caching."""
        cache_key = self._get_cache_key("underlying_price", symbol)
        yf_symbol = self._map_symbol(symbol)
        
        async def fetch_price():
            ticker = yf.Ticker(yf_symbol)
            try:
                info = ticker.info
                price = info.get("regularMarketPrice")
                if price is not None:
                    return float(price)
            except TypeError as te:
                if "datetime" in str(te) and "str" in str(te):
                    self._logger.debug(f"YFinance cache corruption for {symbol}, skipping info lookup")
                pass
            except:
                pass
            
            try:
                hist = ticker.history(period="1d")
                if not hist.empty:
                    return float(hist["Close"].iloc[-1])
            except:
                pass
            
            return 0.0
        
        return await self._get_cached_or_fetch(cache_key, 'market_data', fetch_price)
    
    async def _get_atr(self, symbol: str) -> float:
        """Get Average True Range with caching."""
        cache_key = self._get_cache_key("atr", symbol)
        yf_symbol = self._map_symbol(symbol)
        
        async def fetch_atr():
            try:
                ticker = yf.Ticker(yf_symbol)
                hist = ticker.history(period="20d")
                if len(hist) >= 14:
                    hist['high_low'] = hist['High'] - hist['Low']
                    hist['high_close'] = abs(hist['High'] - hist['Close'].shift())
                    hist['low_close'] = abs(hist['Low'] - hist['Close'].shift())
                    
                    hist['true_range'] = hist[['high_low', 'high_close', 'low_close']].max(axis=1)
                    atr = hist['true_range'].rolling(window=14).mean().iloc[-1]
                    
                    return float(atr) if not pd.isna(atr) else 0.0
            except Exception as e:
                self._logger.warning(f"Failed to calculate ATR for {symbol}: {e}")
            
            return 0.0
        
        return await self._get_cached_or_fetch(cache_key, 'historical', fetch_atr)
    
    async def _get_vix(self) -> float:
        """Get VIX with caching."""
        cache_key = self._get_cache_key("vix", "^VIX")
        
        async def fetch_vix():
            try:
                vix_ticker = yf.Ticker("^VIX")
                hist = vix_ticker.history(period="1d")
                if not hist.empty:
                    return float(hist["Close"].iloc[-1])
            except Exception as e:
                self._logger.warning(f"Failed to get VIX: {e}")
            
            return 20.0  # Default VIX level
        
        return await self._get_cached_or_fetch(cache_key, 'vix', fetch_vix)
    
    async def get_historical_data(self, symbol: str, **kwargs) -> List[Dict]:
        """Get historical data - returns list of dicts for compatibility."""
        period = kwargs.get('period', '1mo')
        days = kwargs.get('days')
        
        # Convert days to period if provided
        if days is not None:
            if days <= 5:
                period = "5d"
            elif days <= 30:
                period = "1mo"
            elif days <= 90:
                period = "3mo"
            elif days <= 180:
                period = "6mo"
            else:
                period = "1y"
        
        cache_key = self._get_cache_key("historical", symbol, period=period)
        yf_symbol = self._map_symbol(symbol)
        
        async def fetch_historical():
            try:
                data = yf.download(yf_symbol, period=period, progress=False)
                if data.empty:
                    return []
                
                result = []
                for date, row in data.iterrows():
                    result.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'open': float(row.get('Open', 0).iloc[0]) if hasattr(row.get('Open', 0), 'iloc') else float(row.get('Open', 0)),
                        'high': float(row.get('High', 0).iloc[0]) if hasattr(row.get('High', 0), 'iloc') else float(row.get('High', 0)),
                        'low': float(row.get('Low', 0).iloc[0]) if hasattr(row.get('Low', 0), 'iloc') else float(row.get('Low', 0)),
                        'close': float(row.get('Close', 0).iloc[0]) if hasattr(row.get('Close', 0), 'iloc') else float(row.get('Close', 0)),
                        'volume': int(row.get('Volume', 0).iloc[0]) if hasattr(row.get('Volume', 0), 'iloc') else int(row.get('Volume', 0))
                    })
                return result
            except Exception as e:
                self._logger.warning(f"Failed to get historical data for {symbol}: {e}")
                return []
        
        return await self._get_cached_or_fetch(cache_key, 'historical', fetch_historical)
    
    async def validate_symbol(self, symbol: str) -> bool:
        """Validate if symbol is supported by Yahoo Finance."""
        try:
            yf_symbol = self._map_symbol(symbol)
            ticker = yf.Ticker(yf_symbol)
            
            # Try to get info first
            try:
                info = ticker.info
                return info.get('regularMarketPrice') is not None or info.get('currentPrice') is not None
            except TypeError as te:
                if "datetime" in str(te) and "str" in str(te):
                    self._logger.debug(f"YFinance cache corruption for {symbol}, using history for validation")
                    # Use history as fallback validation
                    hist = ticker.history(period="1d")
                    return not hist.empty
                else:
                    raise te
                    
        except Exception as e:
            self._logger.warning(f"Symbol validation failed for {symbol}: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        now = datetime.now(timezone.utc)
        stats = {
            'total_cached_items': len(self.cache),
            'expired_items': 0,
            'fresh_items': 0,
            'cached_symbols': set(),
            'data_types': {}
        }
        
        for key, cached_data in self.cache.items():
            if now > cached_data.expires_at:
                stats['expired_items'] += 1
            else:
                stats['fresh_items'] += 1
            
            parts = key.split('|')
            if len(parts) >= 2:
                data_type, symbol = parts[0], parts[1]
                stats['cached_symbols'].add(symbol)
                stats['data_types'][data_type] = stats['data_types'].get(data_type, 0) + 1
        
        stats['cached_symbols'] = list(stats['cached_symbols'])
        return stats