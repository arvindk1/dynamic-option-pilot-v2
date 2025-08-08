"""
Technical Analyzer Service - Calculate technical indicators for scoring
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import yfinance as yf

logger = logging.getLogger(__name__)


class TechnicalAnalyzerService:
    """
    Calculate comprehensive technical indicators for opportunity scoring.
    Includes RSI, MACD, Bollinger Bands, trend analysis, and volatility metrics.
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = timedelta(hours=1)  # Cache for 1 hour
    
    async def analyze_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a symbol and return comprehensive technical indicators.
        Uses caching to avoid repeated API calls.
        """
        try:
            # Check cache first
            cache_key = f"{symbol}_technical"
            if cache_key in self.cache:
                cached_data, cached_time = self.cache[cache_key]
                if datetime.utcnow() - cached_time < self.cache_duration:
                    logger.debug(f"Using cached technical data for {symbol}")
                    return cached_data
            
            # Fetch fresh data
            logger.info(f"Calculating technical indicators for {symbol}")
            technical_data = await self._calculate_technical_indicators(symbol)
            
            if technical_data:
                # Cache the result
                self.cache[cache_key] = (technical_data, datetime.utcnow())
                return technical_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    async def _calculate_technical_indicators(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Calculate all technical indicators for a symbol."""
        try:
            # Fetch market data (90 days for moving averages)
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="3mo", interval="1d")
            
            if hist.empty or len(hist) < 20:
                logger.warning(f"Insufficient data for {symbol} technical analysis")
                return None
            
            # Current price
            current_price = hist['Close'].iloc[-1]
            
            # Calculate all indicators
            technical_data = {
                'symbol': symbol,
                'market_price': float(current_price),
                'calculated_at': datetime.utcnow().isoformat(),
                'data_quality': 'GOOD'
            }
            
            # RSI (14-period)
            technical_data['rsi'] = self._calculate_rsi(hist['Close'], 14)
            
            # MACD
            macd_data = self._calculate_macd(hist['Close'])
            technical_data.update(macd_data)
            
            # Bollinger Bands
            bb_data = self._calculate_bollinger_bands(hist['Close'], current_price)
            technical_data.update(bb_data)
            
            # Moving Averages
            ma_data = self._calculate_moving_averages(hist['Close'])
            technical_data.update(ma_data)
            
            # Trend Strength
            technical_data['trend_strength'] = self._calculate_trend_strength(
                ma_data['sma_20'], ma_data['sma_50'], ma_data['sma_200'], current_price
            )
            
            # Volume Analysis
            if 'Volume' in hist.columns:
                volume_data = self._calculate_volume_indicators(hist['Volume'])
                technical_data.update(volume_data)
            
            # Volatility Analysis
            volatility_data = self._calculate_volatility_indicators(hist['Close'])
            technical_data.update(volatility_data)
            
            # Support/Resistance Levels
            sr_data = self._calculate_support_resistance(hist['High'], hist['Low'], hist['Close'])
            technical_data.update(sr_data)
            
            return technical_data
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators for {symbol}: {e}")
            return None
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)."""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else 50.0
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return 50.0
    
    def _calculate_macd(self, prices: pd.Series) -> Dict[str, float]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        try:
            exp1 = prices.ewm(span=12).mean()
            exp2 = prices.ewm(span=26).mean()
            macd_line = exp1 - exp2
            signal_line = macd_line.ewm(span=9).mean()
            histogram = macd_line - signal_line
            
            return {
                'macd': float(macd_line.iloc[-1]) if not np.isnan(macd_line.iloc[-1]) else 0.0,
                'macd_signal': float(signal_line.iloc[-1]) if not np.isnan(signal_line.iloc[-1]) else 0.0,
                'macd_histogram': float(histogram.iloc[-1]) if not np.isnan(histogram.iloc[-1]) else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return {'macd': 0.0, 'macd_signal': 0.0, 'macd_histogram': 0.0}
    
    def _calculate_bollinger_bands(self, prices: pd.Series, current_price: float) -> Dict[str, float]:
        """Calculate Bollinger Bands and current position."""
        try:
            sma = prices.rolling(window=20).mean()
            std = prices.rolling(window=20).std()
            
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)
            
            # Calculate position within bands (0 = lower band, 1 = upper band)
            current_upper = float(upper_band.iloc[-1])
            current_lower = float(lower_band.iloc[-1])
            
            if current_upper != current_lower:
                position = (current_price - current_lower) / (current_upper - current_lower)
            else:
                position = 0.5
            
            return {
                'bollinger_upper': current_upper,
                'bollinger_lower': current_lower,
                'bollinger_position': max(0.0, min(1.0, position))
            }
            
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            return {'bollinger_upper': 0.0, 'bollinger_lower': 0.0, 'bollinger_position': 0.5}
    
    def _calculate_moving_averages(self, prices: pd.Series) -> Dict[str, float]:
        """Calculate various moving averages."""
        try:
            return {
                'sma_20': float(prices.rolling(window=20).mean().iloc[-1]),
                'sma_50': float(prices.rolling(window=50).mean().iloc[-1]),
                'sma_200': float(prices.rolling(window=200).mean().iloc[-1]) if len(prices) >= 200 else float(prices.mean()),
                'ema_12': float(prices.ewm(span=12).mean().iloc[-1]),
                'ema_26': float(prices.ewm(span=26).mean().iloc[-1])
            }
            
        except Exception as e:
            logger.error(f"Error calculating moving averages: {e}")
            return {'sma_20': 0.0, 'sma_50': 0.0, 'sma_200': 0.0, 'ema_12': 0.0, 'ema_26': 0.0}
    
    def _calculate_trend_strength(self, sma_20: float, sma_50: float, sma_200: float, current_price: float) -> float:
        """
        Calculate trend strength (0-100) based on moving average alignment.
        100 = strong uptrend, 0 = strong downtrend, 50 = neutral
        """
        try:
            score = 50.0  # Start neutral
            
            # Price vs moving averages (40 points)
            if current_price > sma_20:
                score += 10
            if current_price > sma_50:
                score += 15
            if current_price > sma_200:
                score += 15
            
            # Moving average alignment (60 points)
            if sma_20 > sma_50:
                score += 20  # Short-term above medium-term
            if sma_50 > sma_200:
                score += 20  # Medium-term above long-term
            if sma_20 > sma_200:
                score += 20  # Short-term above long-term
            
            return min(max(score, 0.0), 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating trend strength: {e}")
            return 50.0
    
    def _calculate_volume_indicators(self, volumes: pd.Series) -> Dict[str, float]:
        """Calculate volume-based indicators."""
        try:
            current_volume = volumes.iloc[-1]
            avg_volume_20 = volumes.rolling(window=20).mean().iloc[-1]
            
            return {
                'volume_sma_20': float(avg_volume_20),
                'volume_ratio': float(current_volume / avg_volume_20) if avg_volume_20 > 0 else 1.0
            }
            
        except Exception as e:
            logger.error(f"Error calculating volume indicators: {e}")
            return {'volume_sma_20': 0.0, 'volume_ratio': 1.0}
    
    def _calculate_volatility_indicators(self, prices: pd.Series) -> Dict[str, float]:
        """Calculate volatility-based indicators."""
        try:
            # Daily returns
            returns = prices.pct_change().dropna()
            
            # ATR (Average True Range) approximation using close prices
            high_low = prices.rolling(window=2).apply(lambda x: x.max() - x.min(), raw=False)
            atr = high_low.rolling(window=14).mean().iloc[-1]
            
            # Realized volatility (20-day)
            realized_vol = returns.rolling(window=20).std().iloc[-1] * np.sqrt(252)  # Annualized
            
            # Volatility rank (percentile over 252 days)
            vol_series = returns.rolling(window=20).std() * np.sqrt(252)
            vol_rank = 0.0
            if len(vol_series) >= 252:
                recent_vol = vol_series.iloc[-1]
                vol_rank = (vol_series.rank(pct=True).iloc[-1]) * 100
            else:
                vol_rank = 50.0  # Default to median when insufficient data
            
            return {
                'atr': float(atr) if not np.isnan(atr) else 0.0,
                'realized_volatility_20d': float(realized_vol) if not np.isnan(realized_vol) else 0.25,
                'volatility_rank': float(vol_rank) if not np.isnan(vol_rank) else 50.0
            }
            
        except Exception as e:
            logger.error(f"Error calculating volatility indicators: {e}")
            return {'atr': 0.0, 'realized_volatility_20d': 0.25, 'volatility_rank': 50.0}
    
    def _calculate_support_resistance(self, highs: pd.Series, lows: pd.Series, closes: pd.Series) -> Dict[str, float]:
        """
        Calculate support and resistance levels using pivot points and recent ranges.
        """
        try:
            # Use recent 20-day data for support/resistance
            recent_highs = highs.tail(20)
            recent_lows = lows.tail(20)
            current_price = closes.iloc[-1]
            
            # Resistance: Recent high points
            resistance_candidates = recent_highs.nlargest(3)
            resistance_level = resistance_candidates.mean()
            
            # Support: Recent low points  
            support_candidates = recent_lows.nsmallest(3)
            support_level = support_candidates.mean()
            
            # Level confidence based on how many times price tested these levels
            price_range = resistance_level - support_level
            level_confidence = 70.0  # Base confidence
            
            if price_range > 0:
                # Higher confidence if current price is within reasonable range
                price_position = (current_price - support_level) / price_range
                if 0.2 <= price_position <= 0.8:  # Not at extremes
                    level_confidence += 20.0
            
            return {
                'support_level': float(support_level),
                'resistance_level': float(resistance_level),
                'level_confidence': min(level_confidence, 100.0)
            }
            
        except Exception as e:
            logger.error(f"Error calculating support/resistance: {e}")
            return {'support_level': 0.0, 'resistance_level': 0.0, 'level_confidence': 50.0}
    
    async def analyze_symbols_batch(self, symbols: List[str], max_concurrent: int = 5) -> Dict[str, Dict[str, Any]]:
        """Analyze multiple symbols concurrently."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_with_limit(symbol):
            async with semaphore:
                return symbol, await self.analyze_symbol(symbol)
        
        tasks = [analyze_with_limit(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build results dictionary
        analysis_results = {}
        for result in results:
            if isinstance(result, tuple) and len(result) == 2:
                symbol, analysis = result
                if analysis:
                    analysis_results[symbol] = analysis
        
        logger.info(f"Successfully analyzed {len(analysis_results)}/{len(symbols)} symbols")
        return analysis_results
    
    def clear_cache(self):
        """Clear the technical analysis cache."""
        self.cache.clear()
        logger.info("Technical analysis cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'cached_symbols': len(self.cache),
            'cache_duration_hours': self.cache_duration.total_seconds() / 3600,
            'symbols_cached': list(self.cache.keys())
        }


# Global service instance
_technical_analyzer_service = None

def get_technical_analyzer_service() -> TechnicalAnalyzerService:
    """Get global technical analyzer service instance."""
    global _technical_analyzer_service
    if _technical_analyzer_service is None:
        _technical_analyzer_service = TechnicalAnalyzerService()
    return _technical_analyzer_service