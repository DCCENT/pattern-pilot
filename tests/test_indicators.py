"""
Unit tests for technical indicator utilities
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from utils.indicators import (
    calculate_fibonacci_levels,
    calculate_rs_ratio,
    calculate_rs_momentum,
    get_quadrant,
    detect_candlestick_patterns,
    detect_swing_points,
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_volatility
)


class TestFibonacciLevels:
    """Tests for calculate_fibonacci_levels function"""

    def test_retracement_levels(self):
        """Test Fibonacci retracement calculation"""
        levels = calculate_fibonacci_levels(100, 80, direction='retracement')

        # 0% should be at high
        assert levels[0] == 100

        # 100% should be at low
        assert levels[1.0] == 80

        # 50% should be midpoint
        assert levels[0.5] == 90

        # 61.8% (golden ratio)
        assert abs(levels[0.618] - 87.64) < 0.01

    def test_extension_levels(self):
        """Test Fibonacci extension calculation"""
        levels = calculate_fibonacci_levels(100, 80, direction='extension')

        # 0% should be at low
        assert levels[0] == 80

        # 100% should be at high
        assert levels[1.0] == 100

        # 161.8% extension
        assert abs(levels[1.618] - 112.36) < 0.01

    def test_handles_equal_prices(self):
        """Test when high equals low"""
        levels = calculate_fibonacci_levels(100, 100)
        # All levels should be the same
        for level in levels.values():
            assert level == 100


class TestRRGCalculations:
    """Tests for RRG-related calculations"""

    def test_rs_ratio(self):
        """Test RS-Ratio calculation"""
        stock = pd.Series([100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120])
        benchmark = pd.Series([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110])

        rs_ratio = calculate_rs_ratio(stock, benchmark, window=5)

        # Should be normalized around 100
        # Stock outperforming should have RS > 100
        assert rs_ratio.iloc[-1] > 100

    def test_rs_momentum(self):
        """Test RS-Momentum calculation"""
        rs_ratio = pd.Series([99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109])

        momentum = calculate_rs_momentum(rs_ratio, window=5)

        # Increasing RS-Ratio should result in positive momentum
        assert momentum.iloc[-1] > 100

    def test_get_quadrant_leading(self):
        """Test quadrant detection for Leading"""
        assert get_quadrant(105, 105) == "Leading"

    def test_get_quadrant_weakening(self):
        """Test quadrant detection for Weakening"""
        assert get_quadrant(105, 95) == "Weakening"

    def test_get_quadrant_lagging(self):
        """Test quadrant detection for Lagging"""
        assert get_quadrant(95, 95) == "Lagging"

    def test_get_quadrant_improving(self):
        """Test quadrant detection for Improving"""
        assert get_quadrant(95, 105) == "Improving"


class TestCandlestickPatterns:
    """Tests for candlestick pattern detection"""

    def create_candle_df(self, candles):
        """Helper to create DataFrame from candle specifications"""
        dates = pd.date_range(start='2024-01-01', periods=len(candles), freq='D')
        df = pd.DataFrame(candles, columns=['Open', 'High', 'Low', 'Close'], index=dates)
        return df

    def test_detects_doji(self):
        """Test Doji pattern detection"""
        # Doji: open and close nearly equal
        candles = [
            [100, 105, 95, 102],  # Previous candle
            [101, 106, 96, 103],  # Previous candle
            [100, 105, 95, 100.1],  # Doji - tiny body
        ]
        df = self.create_candle_df(candles)
        patterns = detect_candlestick_patterns(df)

        doji_patterns = [p for p in patterns if p['pattern'] == 'Doji']
        assert len(doji_patterns) > 0

    def test_detects_hammer(self):
        """Test Hammer pattern detection"""
        # Hammer: long lower shadow, small body at top
        candles = [
            [100, 105, 95, 98],   # Previous
            [99, 104, 94, 97],    # Previous
            [95, 96, 90, 96],  # Hammer - body=1, range=6, lower_shadow=5, upper_shadow=0
        ]
        df = self.create_candle_df(candles)
        patterns = detect_candlestick_patterns(df)

        hammer_patterns = [p for p in patterns if p['pattern'] == 'Hammer']
        assert len(hammer_patterns) > 0
        assert hammer_patterns[0]['type'] == 'bullish'

    def test_returns_empty_for_insufficient_data(self):
        """Test that function handles insufficient data"""
        candles = [
            [100, 105, 95, 102],  # Only one candle
        ]
        df = self.create_candle_df(candles)
        patterns = detect_candlestick_patterns(df)

        # Should not crash, may return empty
        assert isinstance(patterns, list)


class TestSwingPoints:
    """Tests for swing point detection"""

    def test_detects_swing_high(self):
        """Test swing high detection"""
        dates = pd.date_range(start='2024-01-01', periods=11, freq='D')
        df = pd.DataFrame({
            'High': [100, 102, 104, 106, 110, 106, 104, 102, 100, 98, 96],
            'Low': [95, 97, 99, 101, 105, 101, 99, 97, 95, 93, 91],
        }, index=dates)

        highs, lows = detect_swing_points(df, window=3)

        # Should detect swing high at index 4 (price 110)
        assert len(highs) > 0
        high_prices = [h['price'] for h in highs]
        assert 110 in high_prices

    def test_detects_swing_low(self):
        """Test swing low detection"""
        dates = pd.date_range(start='2024-01-01', periods=11, freq='D')
        df = pd.DataFrame({
            'High': [100, 98, 96, 94, 90, 94, 96, 98, 100, 102, 104],
            'Low': [95, 93, 91, 89, 85, 89, 91, 93, 95, 97, 99],
        }, index=dates)

        highs, lows = detect_swing_points(df, window=3)

        # Should detect swing low at index 4 (price 85)
        assert len(lows) > 0
        low_prices = [l['price'] for l in lows]
        assert 85 in low_prices


class TestPerformanceMetrics:
    """Tests for performance calculation functions"""

    def test_max_drawdown(self):
        """Test maximum drawdown calculation"""
        equity = pd.Series([100, 110, 105, 90, 100, 95, 110])
        mdd = calculate_max_drawdown(equity)

        # Max drawdown should be from 110 to 90 = -18.18%
        expected = (90 - 110) / 110
        assert abs(mdd - expected) < 0.01

    def test_max_drawdown_no_drawdown(self):
        """Test max drawdown when always increasing"""
        equity = pd.Series([100, 110, 120, 130, 140])
        mdd = calculate_max_drawdown(equity)

        assert mdd == 0

    def test_sharpe_ratio(self):
        """Test Sharpe ratio calculation"""
        # Consistent positive returns
        returns = pd.Series([0.01] * 100)  # 1% daily returns
        sharpe = calculate_sharpe_ratio(returns)

        # Should be positive for positive returns
        assert sharpe > 0

    def test_sharpe_ratio_zero_std(self):
        """Test Sharpe ratio when no variance"""
        returns = pd.Series([0.01] * 10)
        # All same returns means zero std
        sharpe = calculate_sharpe_ratio(returns)

        # Should handle without error
        assert isinstance(sharpe, float)

    def test_volatility(self):
        """Test volatility calculation"""
        prices = pd.Series([100, 102, 98, 104, 96, 106, 94, 108])
        vol = calculate_volatility(prices, window=5, annualize=False)

        # Volatility should be positive
        assert vol.iloc[-1] > 0

    def test_volatility_annualized(self):
        """Test annualized volatility"""
        prices = pd.Series([100, 102, 98, 104, 96, 106, 94, 108])
        vol_daily = calculate_volatility(prices, window=5, annualize=False)
        vol_annual = calculate_volatility(prices, window=5, annualize=True)

        # Annualized should be ~15.87x daily (sqrt(252))
        ratio = vol_annual.iloc[-1] / vol_daily.iloc[-1]
        assert abs(ratio - np.sqrt(252)) < 0.1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
