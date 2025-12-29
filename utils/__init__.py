"""
Pattern Pilot Utilities Package

This module exports all utility functions for use by app.py
"""

from .data import (
    validate_symbol,
    safe_yf_download,
    load_bundles,
    save_bundles,
    parse_symbols_input,
    get_ticker_info,
)

from .charts import (
    create_chart,
    add_fibonacci_to_chart,
    add_trendline_to_chart,
    add_horizontal_line_to_chart,
    add_vertical_line_to_chart,
    add_price_channel_to_chart,
    create_rrg_chart,
)

from .indicators import (
    calculate_rs_ratio,
    calculate_rs_momentum,
    get_quadrant,
    detect_candlestick_patterns,
    detect_swing_points,
    calculate_fibonacci_levels,
    find_recent_swing_range,
    snap_to_ohlc,
    calculate_correlation_matrix,
    calculate_volatility,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
)

__all__ = [
    # Data functions
    'validate_symbol',
    'safe_yf_download',
    'load_bundles',
    'save_bundles',
    'parse_symbols_input',
    'get_ticker_info',
    # Chart functions
    'create_chart',
    'add_fibonacci_to_chart',
    'add_trendline_to_chart',
    'add_horizontal_line_to_chart',
    'add_vertical_line_to_chart',
    'add_price_channel_to_chart',
    'create_rrg_chart',
    # Indicator functions
    'calculate_rs_ratio',
    'calculate_rs_momentum',
    'get_quadrant',
    'detect_candlestick_patterns',
    'detect_swing_points',
    'calculate_fibonacci_levels',
    'find_recent_swing_range',
    'snap_to_ohlc',
    'calculate_correlation_matrix',
    'calculate_volatility',
    'calculate_sharpe_ratio',
    'calculate_max_drawdown',
]
