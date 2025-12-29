"""
Technical indicators and analysis utilities for Pattern Pilot
"""

from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np

from config import FIBONACCI_RATIOS


def calculate_fibonacci_levels(
    high_price: float,
    low_price: float,
    direction: str = 'retracement'
) -> Dict[float, float]:
    """
    Calculate Fibonacci retracement or extension levels.

    Args:
        high_price: Swing high price
        low_price: Swing low price
        direction: 'retracement' for retracement levels, 'extension' for extensions

    Returns:
        Dictionary mapping Fibonacci ratio to price level

    Example:
        >>> levels = calculate_fibonacci_levels(100, 80)
        >>> levels[0.618]  # 61.8% retracement
        87.64
    """
    diff = high_price - low_price
    levels = {}

    for ratio in FIBONACCI_RATIOS:
        if direction == 'retracement':
            # Retracement: from high going down
            level = high_price - (diff * ratio)
        else:
            # Extension: from low going up beyond high
            level = low_price + (diff * ratio)
        levels[ratio] = level

    return levels


def calculate_rs_ratio(
    stock_prices: pd.Series,
    benchmark_prices: pd.Series,
    window: int = 10
) -> pd.Series:
    """
    Calculate Relative Strength Ratio for RRG.

    Args:
        stock_prices: Series of stock closing prices
        benchmark_prices: Series of benchmark closing prices
        window: Rolling window for SMA calculation

    Returns:
        Series of RS-Ratio values normalized around 100
    """
    rs = stock_prices / benchmark_prices * 100
    rs_sma = rs.rolling(window=window).mean()
    return 100 + ((rs / rs_sma - 1) * 100)


def calculate_rs_momentum(
    rs_ratio: pd.Series,
    window: int = 10
) -> pd.Series:
    """
    Calculate Relative Strength Momentum for RRG.

    Args:
        rs_ratio: Series of RS-Ratio values
        window: Rolling window for calculation

    Returns:
        Series of RS-Momentum values normalized around 100
    """
    rs_ratio_sma = rs_ratio.rolling(window=window).mean()
    return 100 + ((rs_ratio / rs_ratio_sma - 1) * 100)


def get_quadrant(rs_ratio: float, rs_momentum: float) -> str:
    """
    Determine RRG quadrant based on RS-Ratio and RS-Momentum.

    Args:
        rs_ratio: Current RS-Ratio value
        rs_momentum: Current RS-Momentum value

    Returns:
        Quadrant name: 'Leading', 'Weakening', 'Lagging', or 'Improving'
    """
    if rs_ratio >= 100 and rs_momentum >= 100:
        return "Leading"
    elif rs_ratio >= 100:
        return "Weakening"
    elif rs_momentum < 100:
        return "Lagging"
    else:
        return "Improving"


def detect_candlestick_patterns(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Detect common candlestick patterns in OHLC data.

    Args:
        df: DataFrame with Open, High, Low, Close columns

    Returns:
        List of dictionaries containing pattern information:
        - date: Pattern date
        - pattern: Pattern name
        - price: Reference price for annotation
        - type: 'bullish', 'bearish', or 'neutral'
    """
    patterns: List[Dict[str, Any]] = []
    df = df.copy()

    # Calculate candle components
    df['body'] = abs(df['Close'] - df['Open'])
    df['upper_shadow'] = df['High'] - df[['Open', 'Close']].max(axis=1)
    df['lower_shadow'] = df[['Open', 'Close']].min(axis=1) - df['Low']
    df['is_bullish'] = df['Close'] > df['Open']
    df['range'] = df['High'] - df['Low']

    for i in range(2, len(df)):
        date = df.index[i]
        row = df.iloc[i]
        prev = df.iloc[i - 1]
        # prev2 = df.iloc[i - 2]  # Available for 3-candle patterns

        # Doji: Very small body relative to range
        if row['range'] > 0 and row['body'] / row['range'] < 0.1:
            patterns.append({
                'date': date,
                'pattern': 'Doji',
                'price': row['High'],
                'type': 'neutral'
            })

        # Hammer: Long lower shadow, small upper shadow, small body at top
        elif (row['lower_shadow'] > 2 * row['body'] and
              row['upper_shadow'] < row['body'] and
              row['body'] > 0):
            patterns.append({
                'date': date,
                'pattern': 'Hammer',
                'price': row['Low'],
                'type': 'bullish'
            })

        # Shooting Star: Long upper shadow, small lower shadow, small body at bottom
        elif (row['upper_shadow'] > 2 * row['body'] and
              row['lower_shadow'] < row['body'] and
              row['body'] > 0):
            patterns.append({
                'date': date,
                'pattern': 'Shooting Star',
                'price': row['High'],
                'type': 'bearish'
            })

        # Bullish Engulfing: Bearish candle followed by larger bullish candle
        elif (not prev['is_bullish'] and
              row['is_bullish'] and
              row['Open'] < prev['Close'] and
              row['Close'] > prev['Open'] and
              row['body'] > prev['body']):
            patterns.append({
                'date': date,
                'pattern': 'Bullish Engulfing',
                'price': row['Low'],
                'type': 'bullish'
            })

        # Bearish Engulfing: Bullish candle followed by larger bearish candle
        elif (prev['is_bullish'] and
              not row['is_bullish'] and
              row['Open'] > prev['Close'] and
              row['Close'] < prev['Open'] and
              row['body'] > prev['body']):
            patterns.append({
                'date': date,
                'pattern': 'Bearish Engulfing',
                'price': row['High'],
                'type': 'bearish'
            })

    return patterns


def detect_swing_points(
    df: pd.DataFrame,
    window: int = 5
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Detect swing highs and lows for Fibonacci placement.

    Args:
        df: DataFrame with High and Low columns
        window: Number of bars on each side to confirm swing

    Returns:
        Tuple of (swing_highs, swing_lows) where each is a list of dicts:
        - date: Swing point date
        - price: Swing point price
        - index: DataFrame index position
    """
    swing_highs: List[Dict[str, Any]] = []
    swing_lows: List[Dict[str, Any]] = []

    highs = df['High'].values
    lows = df['Low'].values
    dates = df.index

    for i in range(window, len(df) - window):
        # Check for swing high
        is_swing_high = True
        for j in range(1, window + 1):
            if highs[i] <= highs[i - j] or highs[i] <= highs[i + j]:
                is_swing_high = False
                break
        if is_swing_high:
            swing_highs.append({
                'date': dates[i],
                'price': highs[i],
                'index': i
            })

        # Check for swing low
        is_swing_low = True
        for j in range(1, window + 1):
            if lows[i] >= lows[i - j] or lows[i] >= lows[i + j]:
                is_swing_low = False
                break
        if is_swing_low:
            swing_lows.append({
                'date': dates[i],
                'price': lows[i],
                'index': i
            })

    return swing_highs, swing_lows


def find_recent_swing_range(
    df: pd.DataFrame,
    lookback_days: int = 60
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Find the most recent significant swing high and low for Fibonacci.

    Args:
        df: DataFrame with OHLC data
        lookback_days: Number of days to look back

    Returns:
        Tuple of (swing_high_dict, swing_low_dict) with 'date' and 'price' keys
    """
    recent_df = df.tail(lookback_days)
    swing_highs, swing_lows = detect_swing_points(recent_df, window=3)

    if swing_highs and swing_lows:
        # Get the highest swing high and lowest swing low
        highest = max(swing_highs, key=lambda x: x['price'])
        lowest = min(swing_lows, key=lambda x: x['price'])
        return highest, lowest

    # Fallback to simple high/low
    high_idx = recent_df['High'].idxmax()
    low_idx = recent_df['Low'].idxmin()
    return (
        {'date': high_idx, 'price': recent_df.loc[high_idx, 'High']},
        {'date': low_idx, 'price': recent_df.loc[low_idx, 'Low']}
    )


def snap_to_ohlc(
    df: pd.DataFrame,
    x_val: Any,
    y_val: float,
    snap_enabled: bool = True
) -> float:
    """
    Snap a point to the nearest OHLC value.

    Args:
        df: DataFrame with OHLC data
        x_val: X-coordinate (date) to find nearest bar
        y_val: Y-coordinate (price) to snap
        snap_enabled: Whether snapping is enabled

    Returns:
        Snapped price value, or original if snapping disabled/fails
    """
    if not snap_enabled or df is None or df.empty:
        return y_val

    try:
        # Find the closest date
        if isinstance(x_val, str):
            x_val = pd.to_datetime(x_val)

        # Get the index as datetime for comparison
        idx = pd.to_datetime(df.index)
        distances = abs(idx - x_val)
        closest_idx = distances.argmin()
        row = df.iloc[closest_idx]

        # Find closest OHLC value
        ohlc_values = [row['Open'], row['High'], row['Low'], row['Close']]
        closest_val = min(ohlc_values, key=lambda x: abs(x - y_val))
        return closest_val

    except (IndexError, KeyError, TypeError, ValueError):
        return y_val


def calculate_correlation_matrix(
    prices: pd.DataFrame,
    method: str = 'returns'
) -> pd.DataFrame:
    """
    Calculate correlation matrix for a group of assets.

    Args:
        prices: DataFrame with symbols as columns and prices as values
        method: 'returns' for return correlation, 'price' for price levels

    Returns:
        Correlation matrix DataFrame
    """
    if method == 'returns':
        returns = prices.pct_change().dropna()
        return returns.corr()
    else:
        return prices.corr()


def calculate_volatility(
    prices: pd.Series,
    window: int = 20,
    annualize: bool = True
) -> pd.Series:
    """
    Calculate rolling volatility.

    Args:
        prices: Series of prices
        window: Rolling window size
        annualize: Whether to annualize (multiply by sqrt(252))

    Returns:
        Series of volatility values
    """
    returns = prices.pct_change()
    vol = returns.rolling(window=window).std()
    if annualize:
        vol = vol * np.sqrt(252)
    return vol


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0
) -> float:
    """
    Calculate Sharpe ratio.

    Args:
        returns: Series of returns
        risk_free_rate: Annual risk-free rate (default 0)

    Returns:
        Annualized Sharpe ratio
    """
    excess_returns = returns - risk_free_rate / 252
    if excess_returns.std() == 0:
        return 0.0
    return excess_returns.mean() / excess_returns.std() * np.sqrt(252)


def calculate_max_drawdown(equity: pd.Series) -> float:
    """
    Calculate maximum drawdown.

    Args:
        equity: Series of portfolio values

    Returns:
        Maximum drawdown as a decimal (e.g., 0.15 for 15%)
    """
    cummax = equity.cummax()
    drawdown = (equity - cummax) / cummax
    return drawdown.min()
