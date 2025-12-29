"""
Pattern Pilot Configuration
Contains all constants, configuration settings, and static data
"""

from typing import Dict, List

# Valid stock symbol pattern (1-5 uppercase letters, or with common suffixes)
SYMBOL_PATTERN_REGEX = r'^[A-Z]{1,5}(\.[A-Z]{1,2})?$|^\^[A-Z]{2,6}$'

# Chart drawing tools configuration
CHART_CONFIG: Dict = {
    'modeBarButtonsToAdd': [
        'drawline',
        'drawopenpath',
        'drawcircle',
        'drawrect',
        'eraseshape'
    ],
    'displayModeBar': True,
    'displaylogo': False,
    'toImageButtonOptions': {
        'format': 'png',
        'filename': 'pattern_pilot_chart',
        'height': 800,
        'width': 1200,
        'scale': 2
    }
}

# Drawing tool colors
DRAWING_COLORS: Dict[str, str] = {
    'Red': '#ef5350',
    'Green': '#26a69a',
    'Blue': '#42a5f5',
    'Yellow': '#ffee58',
    'Orange': '#ffa726',
    'Purple': '#ab47bc',
    'Cyan': '#00bcd4',
    'Pink': '#ec407a',
    'White': '#ffffff',
    'Gold': '#ffd700'
}

# Line styles for drawing tools
LINE_STYLES: Dict[str, str] = {
    'Solid': 'solid',
    'Dash': 'dash',
    'Dot': 'dot',
    'Dash-Dot': 'dashdot',
    'Long Dash': 'longdash'
}

# Fibonacci ratios for retracement/extension
FIBONACCI_RATIOS: List[float] = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618]
FIBONACCI_COLORS: List[str] = [
    '#ef5350', '#ffa726', '#ffee58', '#66bb6a', '#26a69a',
    '#42a5f5', '#ab47bc', '#ec407a', '#ffffff'
]

# S&P 500 Sector ETFs
SECTOR_ETFS: Dict[str, str] = {
    'XLK': 'Technology',
    'XLF': 'Financials',
    'XLV': 'Health Care',
    'XLY': 'Consumer Discret.',
    'XLP': 'Consumer Staples',
    'XLE': 'Energy',
    'XLI': 'Industrials',
    'XLB': 'Materials',
    'XLU': 'Utilities',
    'XLRE': 'Real Estate',
    'XLC': 'Communication'
}

# Sector colors for RRG chart
SECTOR_COLORS: Dict[str, str] = {
    'XLK': '#00d4ff',
    'XLF': '#00ff88',
    'XLV': '#ff6b6b',
    'XLY': '#ffd93d',
    'XLP': '#6bcb77',
    'XLE': '#ff8c00',
    'XLI': '#9d4edd',
    'XLB': '#4ecdc4',
    'XLU': '#f8961e',
    'XLRE': '#577590',
    'XLC': '#f72585'
}

# Navigation pages
PAGES: Dict[str, str] = {
    "Single Stock": "single_stock",
    "RRG Sectors": "rrg_sectors",
    "Data Manager": "data_manager",
    "Backtester": "backtester",
    "AI Scanner": "ai_scanner",
    "Group Analysis": "group_analysis",
    "Technical Analysis": "technical_analysis",
    "Fundamentals": "fundamentals",
    "Sentiment": "sentiment",
    "Economic Data": "economic_data",
    "Risk Calculator": "risk_calculator",
    "AI Trading Lab": "ai_trading_lab"
}

# Preset stock bundles for Group Analysis
PRESET_BUNDLES: Dict[str, Dict] = {
    "FAANG+": {
        'symbols': ['META', 'AAPL', 'AMZN', 'NFLX', 'GOOGL', 'MSFT', 'NVDA', 'TSLA'],
        'description': 'Major tech giants'
    },
    "S&P Sectors": {
        'symbols': ['XLK', 'XLF', 'XLV', 'XLY', 'XLP', 'XLE', 'XLI', 'XLB', 'XLU', 'XLRE', 'XLC'],
        'description': 'S&P 500 sector ETFs'
    },
    "Market Indices": {
        'symbols': ['SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'EFA', 'EEM', 'TLT', 'GLD', 'USO'],
        'description': 'Major market and asset class ETFs'
    },
    "Financials": {
        'symbols': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'SCHW', 'AXP', 'V', 'MA'],
        'description': 'Major financial institutions'
    },
    "Semiconductors": {
        'symbols': ['NVDA', 'AMD', 'INTC', 'AVGO', 'QCOM', 'TXN', 'MU', 'AMAT', 'LRCX', 'KLAC'],
        'description': 'Semiconductor companies'
    },
    "Defensive": {
        'symbols': ['JNJ', 'PG', 'KO', 'PEP', 'WMT', 'MCD', 'VZ', 'T', 'SO', 'DUK'],
        'description': 'Defensive/low-beta stocks'
    }
}

# Economic indicators for FRED API
ECONOMIC_INDICATORS: Dict[str, Dict[str, str]] = {
    'GDP': {'series': 'GDP', 'name': 'Gross Domestic Product'},
    'UNRATE': {'series': 'UNRATE', 'name': 'Unemployment Rate'},
    'CPIAUCSL': {'series': 'CPIAUCSL', 'name': 'Consumer Price Index'},
    'FEDFUNDS': {'series': 'FEDFUNDS', 'name': 'Federal Funds Rate'},
    'DGS10': {'series': 'DGS10', 'name': '10-Year Treasury Rate'},
    'DGS2': {'series': 'DGS2', 'name': '2-Year Treasury Rate'},
    'T10Y2Y': {'series': 'T10Y2Y', 'name': '10Y-2Y Treasury Spread'},
    'VIXCLS': {'series': 'VIXCLS', 'name': 'VIX Volatility Index'},
}

# Candlestick pattern names and types
CANDLESTICK_PATTERNS: Dict[str, str] = {
    'doji': 'neutral',
    'hammer': 'bullish',
    'shooting_star': 'bearish',
    'bullish_engulfing': 'bullish',
    'bearish_engulfing': 'bearish',
    'morning_star': 'bullish',
    'evening_star': 'bearish',
}

# Default chart colors
CHART_COLORS: Dict[str, str] = {
    'bullish': '#26a69a',
    'bearish': '#ef5350',
    'neutral': '#ffeb3b',
    'background': 'plotly_dark',
}

# Cache TTL settings (in seconds)
CACHE_TTL: Dict[str, int] = {
    'price_data': 3600,      # 1 hour
    'fundamental_data': 86400,  # 24 hours
    'economic_data': 86400,   # 24 hours
}
