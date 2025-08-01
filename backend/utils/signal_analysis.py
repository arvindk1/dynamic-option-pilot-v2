"""
Signal Analysis Utilities - Technical analysis and signal processing
Extracted from trading.py for better testability and reusability
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np


@dataclass
class TechnicalIndicators:
    """Container for technical indicator values"""
    rsi: float
    macd_line: float
    macd_signal: float
    macd_histogram: float
    bollinger_upper: float
    bollinger_lower: float
    bollinger_mid: float
    sma_20: float
    sma_50: float
    sma_200: float
    atr: float
    volume_sma: float


@dataclass
class MarketSignals:
    """Processed market signals from technical indicators"""
    rsi: float
    rsi_bias: str  # "BULLISH", "BEARISH", "NEUTRAL"
    rsi_strength: str  # "STRONG", "MODERATE", "WEAK"
    macd_signal: str  # "BUY", "SELL", "NEUTRAL"
    macd_bias: str  # "BULLISH", "BEARISH", "NEUTRAL"
    overall_bias: str  # Combined signal bias
    signal_strength: str  # Combined signal strength
    support_level: float
    resistance_level: float
    volatility_regime: str  # "HIGH", "NORMAL", "LOW"
    trend_direction: str  # "UP", "DOWN", "SIDEWAYS"


class SignalAnalyzer:
    """Technical signal analysis and processing"""
    
    @staticmethod
    def analyze_rsi(rsi: float) -> Tuple[str, str]:
        """Analyze RSI for bias and strength"""
        if rsi < 30:
            return "BULLISH", "STRONG"  # Oversold
        elif rsi < 40:
            return "BULLISH", "MODERATE"
        elif rsi > 70:
            return "BEARISH", "STRONG"  # Overbought
        elif rsi > 60:
            return "BEARISH", "MODERATE"
        else:
            return "NEUTRAL", "WEAK"
    
    @staticmethod
    def analyze_macd(macd_line: float, macd_signal: float) -> Tuple[str, str]:
        """Analyze MACD for bias and signal"""
        if macd_line > macd_signal:
            return "BULLISH", "BUY"
        elif macd_line < macd_signal:
            return "BEARISH", "SELL"
        else:
            return "NEUTRAL", "NEUTRAL"
    
    @staticmethod
    def detect_volatility_regime(atr: float, current_price: float, historical_atr: List[float]) -> str:
        """Detect current volatility regime"""
        atr_percent = (atr / current_price) * 100
        
        if len(historical_atr) >= 20:
            avg_atr = np.mean(historical_atr[-20:])
            if atr > avg_atr * 1.5:
                return "HIGH"
            elif atr < avg_atr * 0.7:
                return "LOW"
        
        # Fallback to absolute thresholds
        if atr_percent > 3.0:
            return "HIGH"
        elif atr_percent < 1.0:
            return "LOW"
        else:
            return "NORMAL"
    
    @staticmethod
    def detect_trend_direction(current_price: float, sma_20: float, sma_50: float, sma_200: float) -> str:
        """Detect overall trend direction"""
        if current_price > sma_20 > sma_50 > sma_200:
            return "UP"
        elif current_price < sma_20 < sma_50 < sma_200:
            return "DOWN"
        else:
            return "SIDEWAYS"
    
    @classmethod
    def analyze_advanced_signals(cls, indicators: Dict[str, Any], current_price: float) -> MarketSignals:
        """
        Analyze advanced technical signals for better trade selection
        Extracted from trading.py with enhancements
        """
        # Extract indicator values with defaults
        rsi = indicators.get('rsi', 50.0)
        macd_line = indicators.get('macd_line', 0.0)
        macd_signal_val = indicators.get('macd_signal', 0.0)
        sma_20 = indicators.get('sma_20', current_price)
        sma_50 = indicators.get('sma_50', current_price)
        sma_200 = indicators.get('sma_200', current_price)
        atr = indicators.get('atr', current_price * 0.02)
        
        # Analyze individual indicators
        rsi_bias, rsi_strength = cls.analyze_rsi(rsi)
        macd_bias, macd_signal_str = cls.analyze_macd(macd_line, macd_signal_val)
        
        # Combined signal analysis
        if rsi_bias == macd_bias and rsi_strength == "STRONG":
            overall_bias = rsi_bias
            signal_strength = "STRONG"
        elif rsi_bias == macd_bias:
            overall_bias = rsi_bias
            signal_strength = "MODERATE"
        else:
            overall_bias = "NEUTRAL"
            signal_strength = "WEAK"
        
        # Support/Resistance levels (simplified)
        support_level = current_price * 0.95
        resistance_level = current_price * 1.05
        
        # Enhanced analysis
        volatility_regime = cls.detect_volatility_regime(
            atr, current_price, indicators.get('historical_atr', [])
        )
        trend_direction = cls.detect_trend_direction(current_price, sma_20, sma_50, sma_200)
        
        return MarketSignals(
            rsi=rsi,
            rsi_bias=rsi_bias,
            rsi_strength=rsi_strength,
            macd_signal=macd_signal_str,
            macd_bias=macd_bias,
            overall_bias=overall_bias,
            signal_strength=signal_strength,
            support_level=support_level,
            resistance_level=resistance_level,
            volatility_regime=volatility_regime,
            trend_direction=trend_direction
        )
    
    @staticmethod
    def calculate_signal_confidence(signals: MarketSignals) -> float:
        """Calculate overall confidence score for signals (0.0 to 1.0)"""
        confidence = 0.5  # Base confidence
        
        # RSI contribution
        if signals.rsi_strength == "STRONG":
            confidence += 0.2
        elif signals.rsi_strength == "MODERATE":
            confidence += 0.1
        
        # MACD contribution  
        if signals.macd_bias == signals.rsi_bias:
            confidence += 0.15
        
        # Signal alignment
        if signals.overall_bias != "NEUTRAL":
            confidence += 0.1
            
        # Signal strength
        if signals.signal_strength == "STRONG":
            confidence += 0.15
        elif signals.signal_strength == "MODERATE":
            confidence += 0.05
        
        return round(min(1.0, max(0.0, confidence)), 2)


class ProbabilityCalculator:
    """Calculate probabilities for different trading strategies"""
    
    @staticmethod
    def calculate_probability_profit(signals: MarketSignals, delta_target: float, dte: int) -> float:
        """Calculate probability of profit based on signals"""
        base_prob = 0.5
        
        # Adjust for signal strength
        if signals.signal_strength == "STRONG":
            base_prob += 0.2
        elif signals.signal_strength == "MODERATE":
            base_prob += 0.1
        
        # Adjust for delta (closer to money = riskier)
        delta_adjustment = (0.5 - abs(delta_target)) * 0.3
        base_prob += delta_adjustment
        
        # Time decay benefit (more time = higher success for credit strategies)
        if dte > 30:
            base_prob += 0.05
        elif dte < 14:
            base_prob -= 0.05
            
        # Volatility regime impact
        if signals.volatility_regime == "HIGH":
            base_prob += 0.05  # Higher volatility helps credit strategies
        elif signals.volatility_regime == "LOW":
            base_prob -= 0.05
        
        return round(max(0.0, min(1.0, base_prob)), 3)
    
    @staticmethod
    def calculate_spread_probability_profit(signals: MarketSignals, delta_target: float, dte: int) -> float:
        """Calculate probability of profit for credit spreads specifically"""
        base_prob = ProbabilityCalculator.calculate_probability_profit(signals, delta_target, dte)
        
        # Credit spreads benefit from time decay and neutral markets
        if signals.overall_bias == "NEUTRAL":
            base_prob += 0.08
        elif signals.signal_strength == "WEAK":
            base_prob += 0.05  # Low volatility is good for credit spreads
            
        # OTM spreads have higher success rates but lower profits
        if abs(delta_target) < 0.2:
            base_prob += 0.1
        
        return round(max(0.0, min(1.0, base_prob)), 3)


def determine_trade_setup(signals: MarketSignals, dte: int) -> str:
    """Determine appropriate trade setup based on signals"""
    if signals.signal_strength == "STRONG":
        if signals.overall_bias == "BULLISH":
            return "BULLISH_MOMENTUM"
        elif signals.overall_bias == "BEARISH":
            return "BEARISH_MOMENTUM"
    
    if signals.volatility_regime == "HIGH":
        return "VOLATILITY_EXPANSION"
    elif signals.volatility_regime == "LOW" and dte > 21:
        return "VOLATILITY_CONTRACTION"
    
    if signals.overall_bias == "NEUTRAL":
        return "MEAN_REVERSION"
    
    return "NEUTRAL_INCOME"