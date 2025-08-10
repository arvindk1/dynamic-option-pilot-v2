"""Alpaca data provider plugin for the new architecture."""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import pandas as pd
import asyncio
import logging

from core.orchestrator.base_plugin import DataProviderPlugin, PluginMetadata, PluginType, PluginConfig
from core.interfaces.data_provider_interface import IDataProvider
from services.greeks_calculator import calculate_position_greeks

logger = logging.getLogger(__name__)

try:
    import alpaca_trade_api as tradeapi
    from alpaca_trade_api.rest import REST, TimeFrame
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    logger.warning("alpaca-trade-api not installed. Install with: pip install alpaca-trade-api")


class AlpacaProvider(DataProviderPlugin, IDataProvider):
    """Alpaca Markets data provider for real market data."""
    
    def __init__(self, config: PluginConfig = None):
        super().__init__(config)
        self.api_key = None
        self.secret_key = None
        self.base_url = None
        self.client = None
        self.paper = True  # Default to paper trading
    
    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="alpaca_provider",
            version="2.0.0",
            plugin_type=PluginType.DATA_PROVIDER,
            description="Alpaca Markets data provider for real-time market data",
            author="Dynamic Option Pilot",
            dependencies=[],
            config_schema={
                'type': 'object',
                'properties': {
                    'api_key': {'type': 'string'},
                    'secret_key': {'type': 'string'},
                    'paper_trading': {'type': 'boolean', 'default': True},
                    'base_url': {'type': 'string'}
                },
                'required': ['api_key', 'secret_key']
            }
        )
    
    async def initialize(self) -> bool:
        """Initialize the Alpaca provider."""
        if not ALPACA_AVAILABLE:
            self._logger.error("❌ alpaca-trade-api is required for Alpaca data plugin")
            return False
        
        try:
            # Get configuration
            settings = self.config.settings or {}
            
            self.api_key = settings.get('api_key')
            self.secret_key = settings.get('secret_key')
            self.paper = settings.get('paper_trading', True)
            
            # Set base URL based on paper trading mode
            if self.paper:
                self.base_url = 'https://paper-api.alpaca.markets'
            else:
                self.base_url = 'https://api.alpaca.markets'
            
            if not self.api_key or not self.secret_key:
                self._logger.error("❌ Alpaca API credentials not found")
                return False
            
            # Initialize Alpaca REST client
            self.client = REST(
                key_id=self.api_key,
                secret_key=self.secret_key,
                base_url=self.base_url,
                api_version='v2'
            )
            
            # Test connection
            account = self.client.get_account()
            self._logger.info(f"✅ Connected to Alpaca {'paper' if self.paper else 'live'} account: {account.id}")
            return True
            
        except Exception as e:
            self._logger.error(f"❌ Failed to connect to Alpaca API: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """Clean up Alpaca provider resources."""
        try:
            self.client = None
            self._logger.info("✅ Alpaca provider cleaned up")
            return True
        except Exception as e:
            self._logger.error(f"❌ Alpaca cleanup failed: {e}")
            return False
    
    async def get_market_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get real-time market data from Alpaca."""
        if not self.client:
            raise RuntimeError("Alpaca client not initialized")
        
        # Check for unsupported symbols
        unsupported_symbols = ['^VIX', 'VIX', '^SPX', '^RUT', '^NDX']
        if symbol.upper() in [s.upper() for s in unsupported_symbols]:
            raise ValueError(f"Symbol {symbol} not supported by Alpaca")
        
        try:
            # Get latest quote and trade
            latest_quote = self.client.get_latest_quote(symbol)
            latest_trade = self.client.get_latest_trade(symbol)
            
            # Get current price
            current_price = latest_trade.price if latest_trade else latest_quote.ask_price
            
            # Get historical data for ATR and change calculation
            historical_data = await self.get_historical_data(symbol, period="1M")
            atr = self._calculate_atr(pd.DataFrame(historical_data)) if len(historical_data) > 14 else 45.0
            
            # Calculate change and change percent from previous close
            change = 0.0
            change_percent = 0.0
            if len(historical_data) >= 2:
                previous_close = historical_data[-2]['close']
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100 if previous_close > 0 else 0.0
            
            # For VIX, try to get VIX data if symbol is SPY
            vix = 16.5  # Default
            if symbol.upper() in ['SPY']:
                try:
                    vix_quote = self.client.get_latest_quote('VIX')
                    vix = (vix_quote.bid_price + vix_quote.ask_price) / 2 if vix_quote else 16.5
                except:
                    pass
            
            return {
                'symbol': symbol,
                'price': float(current_price),
                'volume': int(latest_trade.size if latest_trade else 0),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'atr': float(atr),
                'vix': float(vix),
                'change': float(change),
                'change_percent': float(change_percent)
            }
            
        except Exception as e:
            self._logger.error(f"Error fetching market data for {symbol}: {e}")
            raise
    
    async def get_options_chain(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get options chain data from Alpaca."""
        expiration = kwargs.get('expiration')
        if not expiration:
            raise ValueError("expiration date required for options chain")
            
        if isinstance(expiration, str):
            expiration = datetime.strptime(expiration, "%Y-%m-%d")
        
        if not self.client:
            raise RuntimeError("Alpaca client not initialized")
        
        try:
            import requests
            
            headers = {
                'APCA-API-KEY-ID': self.api_key,
                'APCA-API-SECRET-KEY': self.secret_key
            }
            
            # Alpaca options API endpoint
            url = f'https://data.alpaca.markets/v1beta1/options/snapshots/{symbol}'
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Get underlying price
            market_data = await self.get_market_data(symbol)
            underlying_price = market_data['price']
            
            # Process option data
            calls_data = []
            puts_data = []
            
            if 'snapshots' in data:
                for contract_symbol, contract_data in data['snapshots'].items():
                    # Parse option symbol
                    option_info = self._parse_option_symbol(contract_symbol)
                    if not option_info:
                        continue
                    
                    # Filter by expiration date (within 1 day tolerance)
                    if abs((option_info['expiration'] - expiration).days) > 1:
                        continue
                    
                    # Extract option data
                    latest_quote = contract_data.get('latestQuote', {})
                    latest_trade = contract_data.get('latestTrade', {})
                    greeks = contract_data.get('impliedVolatility', {})
                    
                    option_data = {
                        "strike": option_info['strike'],
                        "bid": latest_quote.get('bidPrice', 0.0),
                        "ask": latest_quote.get('askPrice', 0.0),
                        "last": latest_trade.get('price', 0.0),
                        "volume": latest_trade.get('size', 0),
                        "open_interest": contract_data.get('openInterest', 0),
                        "delta": greeks.get('delta', 0.0),
                        "gamma": greeks.get('gamma', 0.0),
                        "theta": greeks.get('theta', 0.0),
                        "vega": greeks.get('vega', 0.0),
                        "implied_volatility": greeks.get('impliedVolatility', 0.0)
                    }
                    
                    if option_info['option_type'] == 'C':
                        calls_data.append(option_data)
                    else:
                        puts_data.append(option_data)
            
            # Sort by strike price
            calls_data.sort(key=lambda x: x['strike'])
            puts_data.sort(key=lambda x: x['strike'])
            
            return {
                'symbol': symbol,
                'underlying_price': float(underlying_price),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'calls': calls_data,
                'puts': puts_data
            }
            
        except Exception as e:
            self._logger.error(f"Error fetching options data for {symbol}: {e}")
            raise
    
    async def get_historical_data(self, symbol: str, **kwargs) -> List[Dict]:
        """Get historical price data from Alpaca."""
        if not self.client:
            raise RuntimeError("Alpaca client not initialized")
        
        period = kwargs.get('period', '1M')
        
        try:
            # Parse period
            if period == "1M":
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
                timeframe = TimeFrame.Day
            elif period == "1Y":
                start_date = datetime.now(timezone.utc) - timedelta(days=365)
                timeframe = TimeFrame.Day
            else:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
                timeframe = TimeFrame.Day
            
            # Get bars data
            bars = self.client.get_bars(
                symbol,
                timeframe,
                start=start_date.strftime('%Y-%m-%d'),
                asof=None,
                feed='iex'  # Use IEX feed for free data
            ).df
            
            if bars.empty:
                return []
            
            # Reset index and format data
            bars = bars.reset_index()
            
            result = []
            for _, row in bars.iterrows():
                result.append({
                    'date': row['timestamp'].strftime('%Y-%m-%d'),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['volume'])
                })
            
            return result
            
        except Exception as e:
            self._logger.error(f"Error fetching historical data for {symbol}: {e}")
            raise
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range."""
        if len(df) < period:
            return 45.0  # Default value
        
        try:
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift(1))
            low_close = abs(df['low'] - df['close'].shift(1))
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=period).mean().iloc[-1]
            
            return round(atr, 2)
        except:
            return 45.0
    
    def _parse_option_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Parse Alpaca option symbol format (e.g., AAPL240315C00172500)."""
        try:
            # Alpaca format: {underlying}{YYMMDD}{C|P}{8-digit strike}
            if len(symbol) < 15:
                return None
            
            # Find where the date starts (6 digits)
            underlying = ""
            date_start = -1
            for i in range(len(symbol) - 14):
                if symbol[i:i+6].isdigit():
                    underlying = symbol[:i]
                    date_start = i
                    break
            
            if date_start == -1:
                return None
            
            # Extract components
            date_str = symbol[date_start:date_start+6]  # YYMMDD
            option_type = symbol[date_start+6]  # C or P
            strike_str = symbol[date_start+7:date_start+15]  # 8 digits
            
            # Parse expiration date
            year = 2000 + int(date_str[:2])
            month = int(date_str[2:4])
            day = int(date_str[4:6])
            expiration = datetime(year, month, day)
            
            # Parse strike (divide by 1000 to get actual strike)
            strike = float(strike_str) / 1000.0
            
            return {
                'underlying': underlying,
                'expiration': expiration,
                'strike': strike,
                'option_type': option_type
            }
            
        except Exception:
            return None
    
    async def _add_greeks_to_positions(self, position_data: List[Dict[str, Any]]):
        """Add Greeks calculations to options positions"""
        try:
            # Group positions by underlying to get current prices
            underlyings = {}
            options_positions = []
            
            for position in position_data:
                if position.get('type') in ['CALL', 'PUT']:
                    underlying = position.get('underlying', position.get('symbol', '').replace('250829C00660000', '').replace('250829C00670000', '').replace('250829P00600000', '').replace('250829P00610000', ''))
                    
                    # Try to extract underlying from symbol if not already set
                    if not underlying and len(position.get('symbol', '')) > 3:
                        # For symbols like SPY250829C00660000, extract SPY
                        symbol = position.get('symbol', '')
                        for i, char in enumerate(symbol):
                            if char.isdigit():
                                underlying = symbol[:i]
                                break
                    
                    if underlying:
                        underlyings[underlying] = None  # Will fetch price
                        options_positions.append(position)
            
            # Fetch current prices for underlyings
            for underlying in underlyings.keys():
                try:
                    market_data = await self.get_market_data(underlying)
                    underlyings[underlying] = market_data.get('price', 0.0)
                except Exception as e:
                    self._logger.warning(f"Could not get price for {underlying}: {e}")
                    underlyings[underlying] = 0.0
            
            # Calculate Greeks for each options position
            for position in options_positions:
                underlying = position.get('underlying')
                if not underlying:
                    # Try to extract from symbol again
                    symbol = position.get('symbol', '')
                    for i, char in enumerate(symbol):
                        if char.isdigit():
                            underlying = symbol[:i]
                            break
                
                if underlying and underlying in underlyings:
                    underlying_price = underlyings[underlying]
                    if underlying_price > 0:
                        # Use implied volatility based on underlying (rough estimates)
                        iv_estimates = {
                            'SPY': 0.18,   # S&P 500 ETF
                            'QQQ': 0.25,   # NASDAQ ETF  
                            'IWM': 0.28,   # Russell 2000 ETF
                            'GLD': 0.20,   # Gold ETF
                            'TLT': 0.15,   # Treasury ETF
                        }
                        
                        implied_vol = iv_estimates.get(underlying, 0.22)  # Default 22% IV
                        
                        # Calculate Greeks using our calculator
                        position_with_greeks = calculate_position_greeks(
                            position, 
                            underlying_price, 
                            implied_vol
                        )
                        
                        # Update the original position with Greeks
                        position.update({
                            'delta': position_with_greeks.get('delta', 0.0),
                            'gamma': position_with_greeks.get('gamma', 0.0),
                            'theta': position_with_greeks.get('theta', 0.0),
                            'vega': position_with_greeks.get('vega', 0.0),
                            'rho': position_with_greeks.get('rho', 0.0)
                        })
                        
                        self._logger.debug(f"Calculated Greeks for {position.get('symbol')}: "
                                         f"Delta={position.get('delta'):.3f}")
            
        except Exception as e:
            self._logger.error(f"Error calculating Greeks: {e}")
            # Don't fail the entire position loading if Greeks calculation fails
    
    async def validate_symbol(self, symbol: str) -> bool:
        """Validate if symbol is supported by Alpaca."""
        if not self.client:
            return False
            
        # Check against known unsupported symbols first
        unsupported_symbols = ['^VIX', 'VIX', '^SPX', '^RUT', '^NDX']
        if symbol.upper() in [s.upper() for s in unsupported_symbols]:
            return False
        
        try:
            # Try to get a quote for the symbol to validate it exists
            latest_quote = self.client.get_latest_quote(symbol)
            return latest_quote is not None
        except Exception:
            # If we can't get a quote, assume symbol is invalid
            return False
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get all positions from Alpaca account."""
        if not self.client:
            self._logger.error("❌ Alpaca client not initialized")
            return []
        
        try:
            positions = self.client.list_positions()
            position_data = []
            
            for position in positions:
                # Convert position to our standard format
                position_dict = {
                    "id": position.symbol,  # Use symbol as ID for now
                    "symbol": position.symbol,
                    "quantity": float(position.qty),
                    "entry_price": float(position.avg_entry_price),
                    "current_price": float(position.current_price) if position.current_price else 0.0,
                    "market_value": float(position.market_value) if position.market_value else 0.0,
                    "pnl": float(getattr(position, 'unrealized_pl', 0.0)),
                    "pnl_percentage": float(getattr(position, 'unrealized_plpc', 0.0)) * 100,
                    "side": position.side,
                    "status": "OPEN" if float(position.qty) != 0 else "CLOSED",
                    "entry_date": datetime.now(timezone.utc).isoformat(),  # TODO: Get actual entry date from orders/activities
                    "type": "STOCK"  # Default to stock, will be enhanced for options
                }
                
                # Try to detect if this is an options position
                if len(position.symbol) > 6 and any(char in position.symbol for char in ['C', 'P']):
                    # This might be an options symbol
                    option_info = self._parse_option_symbol(position.symbol)
                    if option_info:
                        position_dict.update({
                            "type": "CALL" if option_info['option_type'] == 'C' else "PUT",
                            "strike": option_info['strike'],
                            "expiration": option_info['expiration'].isoformat(),
                            "underlying": option_info['underlying']
                        })
                
                position_data.append(position_dict)
            
            # Calculate Greeks for options positions
            await self._add_greeks_to_positions(position_data)
            
            self._logger.info(f"✅ Retrieved {len(position_data)} positions from Alpaca")
            return position_data
            
        except Exception as e:
            self._logger.error(f"❌ Error fetching positions from Alpaca: {e}")
            return []
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information from Alpaca."""
        if not self.client:
            self._logger.error("❌ Alpaca client not initialized")
            return {}
        
        try:
            account = self.client.get_account()
            
            return {
                "account_id": account.id,
                "account_balance": float(account.equity),
                "cash": float(account.cash),
                "buying_power": float(account.buying_power),
                "account_status": account.status,
                "total_pnl": 0.0,  # Will be calculated from positions
                "day_trade_count": getattr(account, 'daytrade_count', 0),
                "pattern_day_trader": getattr(account, 'pattern_day_trader', False),
                "trade_suspended_by_user": getattr(account, 'trade_suspended_by_user', False),
                "trading_blocked": getattr(account, 'trading_blocked', False),
                "transfers_blocked": getattr(account, 'transfers_blocked', False),
                "account_blocked": getattr(account, 'account_blocked', False),
                "created_at": account.created_at.isoformat() if hasattr(account, 'created_at') and account.created_at else None,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self._logger.error(f"❌ Error fetching account info from Alpaca: {e}")
            return {}