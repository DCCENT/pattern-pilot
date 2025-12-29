"""
Data fetching and management utilities for Pattern Pilot
"""

import re
import os
import json
import logging
from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime

import pandas as pd
import yfinance as yf
import streamlit as st

from config import SYMBOL_PATTERN_REGEX, CACHE_TTL

# Setup logging
logger = logging.getLogger(__name__)

# Compile symbol pattern once
SYMBOL_PATTERN = re.compile(SYMBOL_PATTERN_REGEX)


def validate_symbol(symbol: str) -> bool:
    """
    Validate stock symbol format.

    Args:
        symbol: The stock symbol to validate (e.g., 'AAPL', 'SPY', '^GSPC')

    Returns:
        True if symbol matches valid format, False otherwise

    Examples:
        >>> validate_symbol('AAPL')
        True
        >>> validate_symbol('invalid!')
        False
    """
    if not symbol or not isinstance(symbol, str):
        return False
    symbol = symbol.strip().upper()
    return bool(SYMBOL_PATTERN.match(symbol))


@st.cache_data(ttl=CACHE_TTL.get('price_data', 3600), show_spinner=False)
def _cached_yf_download(
    symbol: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    period: Optional[str] = None
) -> pd.DataFrame:
    """
    Internal cached function for Yahoo Finance data.

    Args:
        symbol: Stock ticker symbol
        start: Start date string (YYYY-MM-DD)
        end: End date string (YYYY-MM-DD)
        period: Period string (e.g., '1y', '6mo', '1d')

    Returns:
        DataFrame with OHLCV data
    """
    ticker = yf.Ticker(symbol)
    if period:
        return ticker.history(period=period)
    else:
        return ticker.history(start=start, end=end)


def safe_yf_download(
    symbol: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    period: Optional[str] = None
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Safely fetch data from Yahoo Finance with error handling and caching.

    Args:
        symbol: Stock ticker symbol
        start: Start date for historical data
        end: End date for historical data
        period: Alternative to start/end - period string like '1y', '6mo'

    Returns:
        Tuple of (DataFrame or None, error_message or None)

    Example:
        >>> df, error = safe_yf_download('AAPL', period='1mo')
        >>> if error:
        ...     print(f"Error: {error}")
        ... else:
        ...     print(f"Got {len(df)} rows")
    """
    # Validate symbol
    if not validate_symbol(symbol):
        return None, f"Invalid symbol format: {symbol}"

    symbol = symbol.strip().upper()

    # Convert dates to strings for caching
    start_str = str(start) if start else None
    end_str = str(end) if end else None

    try:
        df = _cached_yf_download(symbol, start_str, end_str, period)

        if df is None or df.empty:
            return None, f"No data returned for {symbol}"
        return df, None

    except ConnectionError as e:
        logger.error(f"Network error fetching {symbol}: {e}")
        return None, "Network error. Please check your internet connection."
    except ValueError as e:
        logger.warning(f"Invalid data for {symbol}: {e}")
        return None, f"Invalid data for {symbol}. Please check the symbol."
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error fetching {symbol}: {error_msg}")
        if "NoneType" in error_msg:
            return None, f"Yahoo Finance API error for {symbol}. The service may be temporarily unavailable."
        return None, f"Failed to fetch {symbol}: {error_msg}"


def load_bundles(bundles_file: str) -> Dict[str, Dict[str, Any]]:
    """
    Load stock bundles from JSON file.

    Args:
        bundles_file: Path to the bundles JSON file

    Returns:
        Dictionary of bundle name -> bundle data
    """
    if os.path.exists(bundles_file):
        try:
            with open(bundles_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing bundles file: {e}")
            return {}
        except IOError as e:
            logger.error(f"Error reading bundles file: {e}")
            return {}
    return {}


def save_bundles(bundles: Dict[str, Dict[str, Any]], bundles_file: str) -> bool:
    """
    Save stock bundles to JSON file.

    Args:
        bundles: Dictionary of bundle name -> bundle data
        bundles_file: Path to the bundles JSON file

    Returns:
        True if saved successfully, False otherwise
    """
    try:
        with open(bundles_file, 'w') as f:
            json.dump(bundles, f, indent=2)
        return True
    except IOError as e:
        logger.error(f"Error saving bundles file: {e}")
        return False


def parse_symbols_input(symbols_input: str) -> List[str]:
    """
    Parse a string of symbols (comma or newline separated) into a list.

    Args:
        symbols_input: String containing symbols, separated by commas or newlines

    Returns:
        List of uppercase, stripped symbol strings

    Example:
        >>> parse_symbols_input("AAPL, MSFT\\nGOOGL")
        ['AAPL', 'MSFT', 'GOOGL']
    """
    symbols = []
    for line in symbols_input.split('\n'):
        for sym in line.split(','):
            sym = sym.strip().upper()
            if sym and validate_symbol(sym):
                symbols.append(sym)
    return symbols


def get_ticker_info(symbol: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Get company information for a ticker symbol.

    Args:
        symbol: Stock ticker symbol

    Returns:
        Tuple of (info dict or None, error message or None)
    """
    if not validate_symbol(symbol):
        return None, f"Invalid symbol format: {symbol}"

    try:
        ticker = yf.Ticker(symbol.strip().upper())
        info = ticker.info
        if not info or 'symbol' not in info:
            return None, f"Could not load data for {symbol}"
        return info, None
    except Exception as e:
        logger.error(f"Error fetching info for {symbol}: {e}")
        return None, str(e)
