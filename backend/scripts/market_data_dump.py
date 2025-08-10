#!/usr/bin/env python3
"""
Market Data Dump Script
Creates local cache of market data to avoid API rate limits
"""

import asyncio
import json
import os
from datetime import datetime, date
from pathlib import Path
import sys

# Add project root to path
sys.path.append('/home/arvindk/devl/dynamic-option-pilot-v2/backend')

from plugins.data.alpaca_provider import AlpacaProvider
from utils.universe_loader import get_universe_loader

class MarketDataDumper:
    def __init__(self):
        self.cache_dir = Path(__file__).parent.parent / "cache" / "market_data"
        self.today = date.today().isoformat()
        self.cache_path = self.cache_dir / self.today
        self.cache_path.mkdir(parents=True, exist_ok=True)
        
    async def dump_all_data(self):
        """Dump all market data for strategies"""
        print(f"🚀 Starting market data dump for {self.today}")
        
        # Get all symbols used by strategies
        universe_loader = get_universe_loader()
        symbols = set()
        
        # Add symbols from all universes
        symbols.update(universe_loader.get_top20_stocks())
        symbols.update(universe_loader.get_thetacrop_symbols())
        symbols.update(['SPY', 'QQQ', 'IWM', 'VIX'])  # Common options symbols
        
        symbols = sorted(list(symbols))
        print(f"📊 Dumping data for {len(symbols)} symbols: {symbols[:10]}...")
        
        # Initialize Alpaca provider
        alpaca = AlpacaProvider()
        
        # Dump data
        quotes_data = await self._dump_quotes(alpaca, symbols)
        options_data = await self._dump_options_chains(alpaca, symbols[:10])  # Limit to prevent rate limits
        
        print(f"✅ Data dump completed!")
        print(f"   📁 Quotes: {len(quotes_data)} symbols")
        print(f"   📁 Options: {len(options_data)} symbols")
        print(f"   📂 Cache location: {self.cache_path}")
        
    async def _dump_quotes(self, alpaca, symbols):
        """Dump stock quotes"""
        print("📈 Dumping stock quotes...")
        quotes_data = {}
        
        for i, symbol in enumerate(symbols, 1):
            try:
                quote = await alpaca.get_quote(symbol)
                quotes_data[symbol] = {
                    'symbol': symbol,
                    'price': quote.price,
                    'bid': getattr(quote, 'bid', quote.price * 0.999),
                    'ask': getattr(quote, 'ask', quote.price * 1.001),
                    'volume': getattr(quote, 'volume', 1000000),
                    'timestamp': datetime.now().isoformat(),
                    'cached_at': datetime.now().isoformat()
                }
                print(f"  ✅ {i:2d}/{len(symbols)} {symbol}: ${quote.price}")
                
                # Rate limiting delay
                if i % 10 == 0:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"  ❌ {symbol}: Error - {e}")
                # Create fallback data
                quotes_data[symbol] = {
                    'symbol': symbol,
                    'price': 100.0,  # Fallback price
                    'bid': 99.0,
                    'ask': 101.0,
                    'volume': 1000000,
                    'timestamp': datetime.now().isoformat(),
                    'cached_at': datetime.now().isoformat(),
                    'fallback': True
                }
        
        # Save to file
        quotes_file = self.cache_path / "quotes.json"
        with open(quotes_file, 'w') as f:
            json.dump(quotes_data, f, indent=2)
        
        print(f"💾 Saved quotes to {quotes_file}")
        return quotes_data
    
    async def _dump_options_chains(self, alpaca, symbols):
        """Dump options chains with Greeks"""
        print("⚡ Dumping options chains...")
        options_data = {}
        
        for i, symbol in enumerate(symbols, 1):
            try:
                print(f"  📊 {i}/{len(symbols)} {symbol}: Fetching options chain...")
                
                # Get options chain (with built-in Greeks)
                chain = await alpaca.get_options_chain(symbol)
                options_data[symbol] = {
                    'symbol': symbol,
                    'chain': chain,
                    'cached_at': datetime.now().isoformat()
                }
                
                # Count options
                calls = len(chain.get('calls', []))
                puts = len(chain.get('puts', []))
                print(f"    ✅ {calls} calls, {puts} puts")
                
                # Rate limiting delay
                await asyncio.sleep(2)  # Longer delay for options
                
            except Exception as e:
                print(f"  ❌ {symbol}: Options error - {e}")
                # Create fallback options data
                options_data[symbol] = {
                    'symbol': symbol,
                    'chain': {'calls': [], 'puts': []},
                    'cached_at': datetime.now().isoformat(),
                    'fallback': True
                }
        
        # Save to file
        options_file = self.cache_path / "options.json"
        with open(options_file, 'w') as f:
            json.dump(options_data, f, indent=2)
            
        print(f"💾 Saved options to {options_file}")
        return options_data

async def main():
    """Main function"""
    dumper = MarketDataDumper()
    await dumper.dump_all_data()

if __name__ == "__main__":
    asyncio.run(main())