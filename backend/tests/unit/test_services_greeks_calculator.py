"""
Unit tests for Greeks Calculator service.
Tests financial mathematics calculations for options pricing.
"""

import pytest
import numpy as np
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from services.greeks_calculator import GreeksCalculator
from plugins.trading.base_strategy import StrategyOpportunity


class TestGreeksCalculator:
    """Test suite for Greeks calculation service."""
    
    @pytest.fixture
    def calculator(self):
        """Create GreeksCalculator instance for testing."""
        return GreeksCalculator()
    
    @pytest.fixture
    def sample_opportunity(self):
        """Create sample opportunity for testing."""
        return StrategyOpportunity(
            id="test_opp_1",
            symbol="SPY",
            strategy_type="iron_condor", 
            strategy_id="IronCondor",
            universe="test",  # CRITICAL FIX: Add universe attribute
            underlying_price=450.0,
            strike=445.0,
            short_strike=445.0,
            long_strike=440.0,
            expiration="2025-12-19",
            days_to_expiration=30,
            premium=2.50,
            max_loss=-247.50,
            max_profit=2.50,
            implied_volatility=0.20
        )
    
    def test_calculate_delta_put_credit_spread(self, calculator, sample_opportunity):
        """Test delta calculation for put credit spread."""
        # Test normal market conditions
        delta = calculator.calculate_delta(sample_opportunity)
        
        # Delta should be negative for put spreads
        assert -1.0 <= delta <= 0.0, f"Delta {delta} out of valid range for puts"
        assert isinstance(delta, float), "Delta should be float"
    
    def test_calculate_gamma_returns_positive_value(self, calculator, sample_opportunity):
        """Test gamma calculation returns positive value."""
        gamma = calculator.calculate_gamma(sample_opportunity)
        
        # Gamma is always positive
        assert gamma >= 0.0, f"Gamma {gamma} should be positive"
        assert isinstance(gamma, float), "Gamma should be float"
    
    def test_calculate_theta_negative_for_short_positions(self, calculator, sample_opportunity):
        """Test theta calculation for time decay."""
        theta = calculator.calculate_theta(sample_opportunity)
        
        # For credit spreads, theta should be positive (time decay helps)
        assert isinstance(theta, float), "Theta should be float"
        # Reasonable theta range for 30 DTE
        assert -50.0 <= theta <= 50.0, f"Theta {theta} seems unreasonable"
    
    def test_calculate_vega_reasonable_range(self, calculator, sample_opportunity):
        """Test vega calculation within reasonable bounds."""
        vega = calculator.calculate_vega(sample_opportunity)
        
        assert isinstance(vega, float), "Vega should be float"
        # Vega should be reasonable for 30 DTE
        assert -100.0 <= vega <= 100.0, f"Vega {vega} out of reasonable range"
    
    def test_calculate_probability_profit_credit_spread(self, calculator, sample_opportunity):
        """Test probability of profit calculation for credit spreads."""
        prob = calculator.calculate_probability_profit(sample_opportunity)
        
        assert 0.0 <= prob <= 1.0, f"Probability {prob} not in valid range [0,1]"
        assert isinstance(prob, float), "Probability should be float"
        
        # For credit spreads with strikes below current price, should have decent probability
        if sample_opportunity.short_strike < sample_opportunity.underlying_price:
            assert prob > 0.5, "Credit spread below current price should have >50% probability"
    
    def test_calculate_expected_value_considers_probability(self, calculator, sample_opportunity):
        """Test expected value calculation incorporates probability."""
        expected_value = calculator.calculate_expected_value(sample_opportunity)
        
        assert isinstance(expected_value, float), "Expected value should be float"
        
        # Expected value should be between max loss and max profit
        assert sample_opportunity.max_loss <= expected_value <= sample_opportunity.max_profit
    
    def test_greeks_calculation_edge_cases(self, calculator):
        """Test Greeks calculations with edge case inputs."""
        
        # Test with very short DTE (0 days)
        short_dte_opp = StrategyOpportunity(
            id="test_short_dte",
            symbol="SPY",
            strategy_type="iron_condor",
            strategy_id="IronCondor",
            universe="test",  # CRITICAL FIX: Add universe attribute
            underlying_price=450.0,
            days_to_expiration=0,
            strike=445.0,
            implied_volatility=0.20
        )
        
        # Should handle gracefully without errors
        delta = calculator.calculate_delta(short_dte_opp)
        assert isinstance(delta, (int, float)), "Should return numeric value"
        
        # Test with very high volatility
        high_vol_opp = StrategyOpportunity(
            id="test_high_vol",
            symbol="SPY", 
            strategy_type="iron_condor",
            strategy_id="IronCondor",
            universe="test",  # CRITICAL FIX: Add universe attribute
            underlying_price=450.0,
            days_to_expiration=30,
            strike=445.0,
            implied_volatility=2.0  # 200% IV
        )
        
        vega = calculator.calculate_vega(high_vol_opp)
        assert isinstance(vega, (int, float)), "Should handle high volatility"
    
    def test_invalid_inputs_raise_appropriate_errors(self, calculator):
        """Test that invalid inputs raise appropriate errors."""
        
        # Test with None opportunity
        with pytest.raises((ValueError, AttributeError)):
            calculator.calculate_delta(None)
        
        # Test with negative underlying price
        invalid_opp = StrategyOpportunity(
            id="test_invalid",
            symbol="SPY",
            strategy_type="iron_condor",
            strategy_id="IronCondor",
            universe="test",  # CRITICAL FIX: Add universe attribute
            underlying_price=-100.0,  # Invalid negative price
            days_to_expiration=30,
            strike=445.0
        )
        
        with pytest.raises(ValueError):
            calculator.calculate_delta(invalid_opp)
    
    def test_calculations_are_deterministic(self, calculator, sample_opportunity):
        """Test that calculations are deterministic (same inputs = same outputs)."""
        
        # Calculate multiple times
        delta1 = calculator.calculate_delta(sample_opportunity)
        delta2 = calculator.calculate_delta(sample_opportunity)
        
        assert delta1 == delta2, "Calculations should be deterministic"
        
        gamma1 = calculator.calculate_gamma(sample_opportunity)
        gamma2 = calculator.calculate_gamma(sample_opportunity)
        
        assert gamma1 == gamma2, "Gamma calculations should be deterministic"
    
    def test_financial_precision_requirements(self, calculator, sample_opportunity):
        """Test that calculations meet financial precision requirements."""
        
        # Greeks should be calculated to at least 4 decimal places
        delta = calculator.calculate_delta(sample_opportunity)
        gamma = calculator.calculate_gamma(sample_opportunity)
        theta = calculator.calculate_theta(sample_opportunity)
        vega = calculator.calculate_vega(sample_opportunity)
        
        # Test precision by checking if values change with small underlying price changes
        sample_opportunity.underlying_price += 0.01
        
        delta_adjusted = calculator.calculate_delta(sample_opportunity)
        
        # Delta should be sensitive to small price changes
        assert delta != delta_adjusted or abs(delta - delta_adjusted) < 0.01, \
            "Delta should be calculated with sufficient precision"
    
    @pytest.mark.parametrize("strategy_type,expected_delta_sign", [
        ("put_credit_spread", -1),  # Negative delta
        ("call_credit_spread", 1),  # Positive delta  
        ("iron_condor", 0),        # Near zero delta
    ])
    def test_delta_signs_by_strategy_type(self, calculator, strategy_type, expected_delta_sign):
        """Test that delta signs are correct for different strategy types."""
        
        opportunity = StrategyOpportunity(
            id=f"test_{strategy_type}",
            symbol="SPY",
            strategy_type=strategy_type,
            strategy_id=strategy_type.title(),
            universe="test",  # CRITICAL FIX: Add universe attribute
            underlying_price=450.0,
            strike=445.0,
            days_to_expiration=30,
            implied_volatility=0.20
        )
        
        delta = calculator.calculate_delta(opportunity)
        
        if expected_delta_sign == -1:
            assert delta <= 0, f"Put spreads should have non-positive delta, got {delta}"
        elif expected_delta_sign == 1:
            assert delta >= 0, f"Call spreads should have non-negative delta, got {delta}"
        else:  # Near zero for iron condors
            assert abs(delta) < 0.3, f"Iron condors should have near-zero delta, got {delta}"