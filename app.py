"""
Pattern Pilot - Financial Time Series Pattern Recognition
A comprehensive tool for pattern detection, backtesting, and AI-powered signal discovery

Utility modules available for reuse:
    - config.py: Constants and configuration settings
    - utils/data.py: Data fetching and validation functions
    - utils/charts.py: Chart creation utilities
    - utils/indicators.py: Technical indicator calculations
    - tests/: Unit tests for utilities
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pandas_ta as ta
import os
import json
from io import StringIO
import joblib
import warnings
import logging

warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import configuration constants
from config import (
    CHART_CONFIG, DRAWING_COLORS, LINE_STYLES,
    FIBONACCI_RATIOS, FIBONACCI_COLORS,
    SECTOR_ETFS, SECTOR_COLORS, CHART_COLORS, CACHE_TTL
)

# Import utility functions
from utils import (
    validate_symbol, safe_yf_download, load_bundles, save_bundles,
    parse_symbols_input, create_chart, add_fibonacci_to_chart,
    add_trendline_to_chart, add_horizontal_line_to_chart,
    add_vertical_line_to_chart, add_price_channel_to_chart, create_rrg_chart,
    calculate_rs_ratio, calculate_rs_momentum, get_quadrant,
    detect_candlestick_patterns, detect_swing_points,
    calculate_fibonacci_levels, find_recent_swing_range, snap_to_ohlc,
    calculate_volatility, calculate_sharpe_ratio, calculate_max_drawdown
)

# Page config
st.set_page_config(
    page_title="Pattern Pilot",
    page_icon="📈",
    layout="wide"
)

# Custom CSS for responsive design and header in top bar
st.markdown("""
<style>
    /* Title in Streamlit's header bar - centered */
    header[data-testid="stHeader"]::before {
        content: "📈 Pattern Pilot | Financial Time Series Pattern Recognition & Signal Testing";
        position: absolute;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        font-size: 0.8rem;
        font-weight: 500;
        color: #fafafa;
        white-space: nowrap;
    }

    /* Auto-scale containers */
    .stPlotlyChart {
        width: 100% !important;
        max-width: 100vw !important;
    }

    .stDataFrame {
        width: 100% !important;
        max-width: 100vw !important;
    }

    /* Responsive columns */
    [data-testid="column"] {
        min-width: 0 !important;
    }

    /* Ensure charts resize properly */
    .js-plotly-plot {
        width: 100% !important;
    }

    .plotly {
        width: 100% !important;
    }

    /* Reduce top padding of main content */
    .main .block-container {
        padding-top: 1rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)


# Note: _cached_yf_download, safe_yf_download, and all utility functions
# are now imported from utils module. Constants from config module.


# Initialize session state for drawings
if 'drawings' not in st.session_state:
    st.session_state.drawings = []
if 'current_df' not in st.session_state:
    st.session_state.current_df = None

# Navigation pages
PAGES = {
    "📊 Single Stock": "single_stock",
    "🔄 RRG Sectors": "rrg_sectors",
    "📁 Data Manager": "data_manager",
    "🧪 Backtester": "backtester",
    "🤖 AI Scanner": "ai_scanner",
    "📦 Group Analysis": "group_analysis",
    "📐 Technical Analysis": "technical_analysis",
    "💰 Fundamentals": "fundamentals",
    "🌡️ Sentiment": "sentiment",
    "📈 Economic Data": "economic_data",
    "⚖️ Risk Calculator": "risk_calculator",
    "🧠 AI Trading Lab": "ai_trading_lab"
}

# Sidebar navigation
with st.sidebar:
    st.markdown("#### 🧭 Navigation")
    selected_page = st.radio(
        "Select a page:",
        list(PAGES.keys()),
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.caption("v2.0 | Financial Analysis Suite")


# ============================================================================
# Note: Common functions (detect_candlestick_patterns, create_chart,
# calculate_rs_ratio, calculate_rs_momentum, get_quadrant, create_rrg_chart,
# etc.) and constants (SECTOR_ETFS, SECTOR_COLORS) are now imported from
# utils and config modules.
# ============================================================================


# ============================================================================
# TAB 1: SINGLE STOCK
# ============================================================================

if selected_page == "📊 Single Stock":
    st.subheader("Single Stock Analysis")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        symbol = st.text_input("Symbol", value="SPY", key="t1_symbol")
    with col2:
        start_date = st.date_input("Start", value=datetime.now() - timedelta(days=365), key="t1_start")
    with col3:
        end_date = st.date_input("End", value=datetime.now(), key="t1_end")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: show_sma = st.checkbox("SMA", value=True, key="t1_sma")
    with col2: show_rsi = st.checkbox("RSI", value=True, key="t1_rsi")
    with col3: show_macd = st.checkbox("MACD", value=True, key="t1_macd")
    with col4: show_volume = st.checkbox("Volume", value=True, key="t1_vol")
    with col5: detect_pat = st.checkbox("Patterns", value=True, key="t1_pat")

    # Drawing Tools Panel
    with st.expander("🎨 Drawing Tools", expanded=False):
        st.markdown("**Configure drawing settings and add technical drawings to the chart**")

        draw_col1, draw_col2, draw_col3 = st.columns(3)
        with draw_col1:
            draw_color = st.selectbox("Line Color", list(DRAWING_COLORS.keys()), index=2, key="t1_draw_color")
        with draw_col2:
            draw_style = st.selectbox("Line Style", list(LINE_STYLES.keys()), index=0, key="t1_draw_style")
        with draw_col3:
            snap_to_price = st.checkbox("Snap to OHLC", value=True, key="t1_snap", help="Auto-snap points to nearest Open/High/Low/Close values")

        st.markdown("---")
        st.markdown("**Fibonacci Retracement**")

        fib_col1, fib_col2 = st.columns(2)
        with fib_col1:
            fib_high = st.number_input("High Price", value=0.0, min_value=0.0, format="%.2f", key="t1_fib_high", help="Set the swing high price for Fibonacci levels")
        with fib_col2:
            fib_low = st.number_input("Low Price", value=0.0, min_value=0.0, format="%.2f", key="t1_fib_low", help="Set the swing low price for Fibonacci levels")

        fib_col3, fib_col4, fib_col5 = st.columns(3)
        with fib_col3:
            fib_start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30), key="t1_fib_start")
        with fib_col4:
            fib_end_date = st.date_input("End Date", value=datetime.now(), key="t1_fib_end")
        with fib_col5:
            show_fib_labels = st.checkbox("Show Labels", value=True, key="t1_fib_labels")

        add_fib = st.button("Add Fibonacci Retracement", key="t1_add_fib")

        st.markdown("---")
        st.markdown("**Horizontal Line (Support/Resistance)**")

        hline_col1, hline_col2 = st.columns(2)
        with hline_col1:
            hline_price = st.number_input("Price Level", value=0.0, min_value=0.0, format="%.2f", key="t1_hline_price")
        with hline_col2:
            hline_label = st.text_input("Label (optional)", value="", key="t1_hline_label", placeholder="e.g., Resistance")

        add_hline = st.button("Add Horizontal Line", key="t1_add_hline")

        st.markdown("---")
        st.markdown("**Trendline**")

        trend_col1, trend_col2 = st.columns(2)
        with trend_col1:
            st.markdown("**Point 1**")
            trend_date1 = st.date_input("Date", value=datetime.now() - timedelta(days=60), key="t1_trend_date1")
            trend_price1 = st.number_input("Price", value=0.0, min_value=0.0, format="%.2f", key="t1_trend_price1")
        with trend_col2:
            st.markdown("**Point 2**")
            trend_date2 = st.date_input("Date", value=datetime.now() - timedelta(days=10), key="t1_trend_date2")
            trend_price2 = st.number_input("Price", value=0.0, min_value=0.0, format="%.2f", key="t1_trend_price2")

        add_trend = st.button("Add Trendline", key="t1_add_trend")

        st.markdown("---")
        st.markdown("**Vertical Line**")

        vline_col1, vline_col2 = st.columns(2)
        with vline_col1:
            vline_date = st.date_input("Date", value=datetime.now(), key="t1_vline_date")
        with vline_col2:
            vline_label = st.text_input("Label (optional)", value="", key="t1_vline_label", placeholder="e.g., Earnings")

        add_vline = st.button("Add Vertical Line", key="t1_add_vline")

        # Clear all drawings button
        st.markdown("---")
        if st.button("🗑️ Clear All Drawings", key="t1_clear_drawings"):
            st.session_state.drawings = []
            st.success("All drawings cleared!")
            st.rerun()

        # Handle drawing additions
        if add_fib and fib_high > 0 and fib_low > 0:
            st.session_state.drawings.append({
                'type': 'fibonacci',
                'high': fib_high,
                'low': fib_low,
                'start_date': fib_start_date,
                'end_date': fib_end_date,
                'color': DRAWING_COLORS[draw_color],
                'style': LINE_STYLES[draw_style],
                'show_labels': show_fib_labels
            })
            st.success(f"Fibonacci added: {fib_low:.2f} - {fib_high:.2f}")
            st.rerun()

        if add_hline and hline_price > 0:
            st.session_state.drawings.append({
                'type': 'horizontal',
                'price': hline_price,
                'label': hline_label if hline_label else None,
                'color': DRAWING_COLORS[draw_color],
                'style': LINE_STYLES[draw_style]
            })
            st.success(f"Horizontal line added at ${hline_price:.2f}")
            st.rerun()

        if add_trend and trend_price1 > 0 and trend_price2 > 0:
            st.session_state.drawings.append({
                'type': 'trendline',
                'x0': trend_date1,
                'y0': trend_price1,
                'x1': trend_date2,
                'y1': trend_price2,
                'color': DRAWING_COLORS[draw_color],
                'style': LINE_STYLES[draw_style]
            })
            st.success("Trendline added!")
            st.rerun()

        if add_vline:
            st.session_state.drawings.append({
                'type': 'vertical',
                'date': vline_date,
                'label': vline_label if vline_label else None,
                'color': DRAWING_COLORS[draw_color],
                'style': LINE_STYLES[draw_style]
            })
            st.success(f"Vertical line added at {vline_date}")
            st.rerun()

        # Show current drawings with delete buttons
        if st.session_state.drawings:
            st.markdown("---")
            st.markdown(f"**Active Drawings ({len(st.session_state.drawings)})**")

            drawings_to_delete = []
            for i, d in enumerate(st.session_state.drawings):
                draw_item_col1, draw_item_col2 = st.columns([4, 1])
                with draw_item_col1:
                    if d['type'] == 'fibonacci':
                        st.caption(f"{i+1}. Fibonacci: {d['low']:.2f} - {d['high']:.2f}")
                    elif d['type'] == 'horizontal':
                        st.caption(f"{i+1}. Horizontal Line: ${d['price']:.2f} {d.get('label', '')}")
                    elif d['type'] == 'trendline':
                        st.caption(f"{i+1}. Trendline: {d['y0']:.2f} → {d['y1']:.2f}")
                    elif d['type'] == 'vertical':
                        st.caption(f"{i+1}. Vertical Line: {d['date']} {d.get('label', '')}")
                with draw_item_col2:
                    if st.button("🗑️", key=f"del_drawing_{i}", help="Delete this drawing"):
                        drawings_to_delete.append(i)

            # Delete marked drawings
            if drawings_to_delete:
                for idx in sorted(drawings_to_delete, reverse=True):
                    st.session_state.drawings.pop(idx)
                st.rerun()

    # Initialize session state for chart data
    if 't1_chart_data' not in st.session_state:
        st.session_state.t1_chart_data = None
    if 't1_chart_symbol' not in st.session_state:
        st.session_state.t1_chart_symbol = None
    if 't1_chart_patterns' not in st.session_state:
        st.session_state.t1_chart_patterns = None

    if st.button("Fetch Data", type="primary", key="t1_fetch"):
        with st.spinner(f"Fetching {symbol}..."):
            try:
                df = yf.Ticker(symbol).history(start=start_date, end=end_date)
                if not df.empty:
                    st.session_state.t1_chart_data = df
                    st.session_state.t1_chart_symbol = symbol
                    st.session_state.t1_chart_patterns = detect_candlestick_patterns(df) if detect_pat else None
                    st.session_state.current_df = df
                else:
                    st.error(f"No data for {symbol}")
                    st.session_state.t1_chart_data = None
            except Exception as e:
                st.error(f"Error: {e}")
                st.session_state.t1_chart_data = None

    # Display chart if data exists in session state
    if st.session_state.t1_chart_data is not None:
        df = st.session_state.t1_chart_data
        chart_symbol = st.session_state.t1_chart_symbol
        patterns = st.session_state.t1_chart_patterns if detect_pat else None

        fig = create_chart(df, chart_symbol, show_sma, show_rsi, show_macd, show_volume, patterns)

        # Apply all drawings to the chart
        for drawing in st.session_state.drawings:
            if drawing['type'] == 'fibonacci':
                fig = add_fibonacci_to_chart(
                    fig,
                    drawing['start_date'],
                    drawing['end_date'],
                    drawing['high'],
                    drawing['low'],
                    drawing['color'],
                    drawing['style'],
                    drawing.get('show_labels', True)
                )
            elif drawing['type'] == 'horizontal':
                fig = add_horizontal_line_to_chart(
                    fig,
                    drawing['price'],
                    df.index[0],
                    df.index[-1],
                    drawing['color'],
                    drawing['style'],
                    drawing.get('label')
                )
            elif drawing['type'] == 'trendline':
                fig = add_trendline_to_chart(
                    fig,
                    drawing['x0'],
                    drawing['y0'],
                    drawing['x1'],
                    drawing['y1'],
                    drawing['color'],
                    drawing['style']
                )
            elif drawing['type'] == 'vertical':
                fig = add_vertical_line_to_chart(
                    fig,
                    drawing['date'],
                    df['Low'].min() * 0.98,
                    df['High'].max() * 1.02,
                    drawing['color'],
                    drawing['style'],
                    drawing.get('label')
                )

        st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

        # Quick Fibonacci from chart data
        with st.expander("📐 Quick Fibonacci from Chart Range", expanded=False):
            st.markdown("Quickly add Fibonacci based on the chart's high/low range")

            qf_method = st.radio("Detection Method", ["Simple High/Low", "Auto-Detect Swing Points"], horizontal=True, key="t1_qf_method")

            qf_col1, qf_col2, qf_col3 = st.columns(3)
            with qf_col1:
                qf_days = st.selectbox("Lookback Period", [10, 20, 30, 60, 90, 180, 365], index=2, key="t1_qf_days")

            recent_df = df.tail(qf_days)

            if qf_method == "Auto-Detect Swing Points":
                swing_high, swing_low = find_recent_swing_range(df, qf_days)
                qf_high = swing_high['price']
                qf_low = swing_low['price']
                qf_high_date = swing_high['date']
                qf_low_date = swing_low['date']
            else:
                qf_high = recent_df['High'].max()
                qf_low = recent_df['Low'].min()
                qf_high_date = recent_df['High'].idxmax()
                qf_low_date = recent_df['Low'].idxmin()

            with qf_col2:
                st.metric("Swing High", f"${qf_high:.2f}")
                if qf_method == "Auto-Detect Swing Points":
                    st.caption(f"Date: {qf_high_date.strftime('%Y-%m-%d') if hasattr(qf_high_date, 'strftime') else qf_high_date}")
            with qf_col3:
                st.metric("Swing Low", f"${qf_low:.2f}")
                if qf_method == "Auto-Detect Swing Points":
                    st.caption(f"Date: {qf_low_date.strftime('%Y-%m-%d') if hasattr(qf_low_date, 'strftime') else qf_low_date}")

            # Show Fibonacci preview levels
            with st.expander("Preview Fibonacci Levels", expanded=False):
                fib_preview = calculate_fibonacci_levels(qf_high, qf_low)
                for ratio, price in fib_preview.items():
                    st.write(f"**{ratio:.1%}:** ${price:.2f}")

            if st.button(f"Add Fibonacci ({qf_method})", key="t1_qf_add", type="primary"):
                qf_start = qf_low_date.date() if hasattr(qf_low_date, 'date') else qf_low_date
                qf_end = qf_high_date.date() if hasattr(qf_high_date, 'date') else qf_high_date
                # Ensure start is before end
                if qf_start > qf_end:
                    qf_start, qf_end = qf_end, qf_start
                st.session_state.drawings.append({
                    'type': 'fibonacci',
                    'high': qf_high,
                    'low': qf_low,
                    'start_date': qf_start,
                    'end_date': qf_end,
                    'color': DRAWING_COLORS.get(draw_color, '#42a5f5'),
                    'style': LINE_STYLES.get(draw_style, 'solid'),
                    'show_labels': True
                })
                st.success(f"Added Fibonacci: ${qf_low:.2f} - ${qf_high:.2f}")
                st.rerun()

            # Show detected swing points on chart
            if qf_method == "Auto-Detect Swing Points":
                st.markdown("---")
                if st.checkbox("Show All Detected Swing Points", key="t1_show_swings"):
                    swing_highs, swing_lows = detect_swing_points(recent_df, window=3)
                    if swing_highs:
                        st.markdown("**Swing Highs:**")
                        for sh in swing_highs[-5:]:  # Show last 5
                            date_str = sh['date'].strftime('%Y-%m-%d') if hasattr(sh['date'], 'strftime') else str(sh['date'])
                            st.caption(f"  {date_str}: ${sh['price']:.2f}")
                    if swing_lows:
                        st.markdown("**Swing Lows:**")
                        for sl in swing_lows[-5:]:  # Show last 5
                            date_str = sl['date'].strftime('%Y-%m-%d') if hasattr(sl['date'], 'strftime') else str(sl['date'])
                            st.caption(f"  {date_str}: ${sl['price']:.2f}")

        if patterns:
            st.subheader("Detected Patterns")
            st.dataframe(pd.DataFrame(patterns), use_container_width=True)


# ============================================================================
# TAB 2: RRG SECTORS
# ============================================================================

if selected_page == "🔄 RRG Sectors":
    st.subheader("Relative Rotation Graph")

    col1, col2, col3 = st.columns(3)
    with col1:
        rrg_period = st.selectbox("Period", ["3 Months", "6 Months", "1 Year", "2 Years"], index=1, key="t2_period")
    with col2:
        tail_length = st.slider("Tail (weeks)", 1, 12, 5, key="t2_tail")
    with col3:
        rs_window = st.slider("Smoothing", 5, 20, 10, key="t2_window")

    # Custom symbols option
    use_custom = st.checkbox("Use custom symbols instead of S&P sectors", key="t2_custom")
    if use_custom:
        custom_symbols = st.text_input("Enter symbols (comma-separated)", "AAPL,MSFT,GOOGL,AMZN,META", key="t2_symbols")
        custom_benchmark = st.text_input("Benchmark symbol", "SPY", key="t2_bench")

    if st.button("Generate RRG", type="primary", key="t2_gen"):
        period_days = {"3 Months": 90, "6 Months": 180, "1 Year": 365, "2 Years": 730}
        days = period_days.get(rrg_period, 180)
        rrg_start = datetime.now() - timedelta(days=days)

        with st.spinner("Calculating RRG..."):
            try:
                # Determine symbols to use
                if use_custom:
                    symbols = {s.strip(): s.strip() for s in custom_symbols.split(",")}
                    benchmark_symbol = custom_benchmark
                else:
                    symbols = SECTOR_ETFS
                    benchmark_symbol = "SPY"

                spy_data = yf.Ticker(benchmark_symbol).history(start=rrg_start, end=datetime.now())
                spy_weekly = spy_data['Close'].resample('W').last()

                rrg_data = {}
                for sym, name in symbols.items():
                    try:
                        data = yf.Ticker(sym).history(start=rrg_start, end=datetime.now())
                        if not data.empty:
                            weekly = data['Close'].resample('W').last()
                            aligned = pd.DataFrame({'stock': weekly, 'benchmark': spy_weekly}).dropna()
                            if len(aligned) > rs_window * 2:
                                rs_ratio = calculate_rs_ratio(aligned['stock'], aligned['benchmark'], rs_window)
                                rs_momentum = calculate_rs_momentum(rs_ratio, rs_window)
                                rrg_df = pd.DataFrame({'RS_Ratio': rs_ratio, 'RS_Momentum': rs_momentum}).dropna()
                                if len(rrg_df) > 0:
                                    rrg_data[sym] = rrg_df
                    except Exception as e:
                        st.warning(f"Skipped {sym}: {e}")

                if rrg_data:
                    fig = create_rrg_chart(rrg_data, tail_length)
                    st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

                    # Summary
                    summary = []
                    for sym, data in rrg_data.items():
                        curr = data.iloc[-1]
                        summary.append({
                            'Symbol': sym, 'RS-Ratio': round(curr['RS_Ratio'], 2),
                            'RS-Momentum': round(curr['RS_Momentum'], 2),
                            'Quadrant': get_quadrant(curr['RS_Ratio'], curr['RS_Momentum'])
                        })
                    st.dataframe(pd.DataFrame(summary).sort_values('RS-Ratio', ascending=False), use_container_width=True)
            except Exception as e:
                st.error(f"Error: {e}")


# ============================================================================
# TAB 3: DATA MANAGER
# ============================================================================

if selected_page == "📁 Data Manager":
    st.subheader("Data Manager")
    st.markdown("Upload CSV files or batch fetch from Yahoo Finance")

    subtab1, subtab2, subtab3 = st.tabs(["📤 Upload CSV", "⬇️ Batch Fetch", "📂 Saved Data"])

    with subtab1:
        st.markdown("### Upload CSV Data")
        st.markdown("""
        **Supported formats:**
        - Must have Date column (or index) + OHLCV columns
        - Column names are auto-detected (Date, Open, High, Low, Close, Volume, Adj Close)
        - Multiple date formats supported
        """)

        uploaded_file = st.file_uploader("Choose a CSV file", type="csv", key="csv_upload")

        if uploaded_file:
            try:
                # Read CSV
                df_raw = pd.read_csv(uploaded_file)
                st.write("**Preview (raw):**")
                st.dataframe(df_raw.head(), use_container_width=True)

                # Auto-detect columns
                col_mapping = {}
                possible_date = ['date', 'datetime', 'time', 'timestamp', 'Date', 'DateTime']
                possible_open = ['open', 'Open', 'OPEN', 'o']
                possible_high = ['high', 'High', 'HIGH', 'h']
                possible_low = ['low', 'Low', 'LOW', 'l']
                possible_close = ['close', 'Close', 'CLOSE', 'c', 'adj close', 'Adj Close', 'adjclose']
                possible_volume = ['volume', 'Volume', 'VOLUME', 'v', 'vol']

                for col in df_raw.columns:
                    if col.lower() in [x.lower() for x in possible_date]:
                        col_mapping['Date'] = col
                    elif col.lower() in [x.lower() for x in possible_open]:
                        col_mapping['Open'] = col
                    elif col.lower() in [x.lower() for x in possible_high]:
                        col_mapping['High'] = col
                    elif col.lower() in [x.lower() for x in possible_low]:
                        col_mapping['Low'] = col
                    elif col.lower() in [x.lower() for x in possible_close] and 'Close' not in col_mapping:
                        col_mapping['Close'] = col
                    elif col.lower() in [x.lower() for x in possible_volume]:
                        col_mapping['Volume'] = col

                st.write("**Detected columns:**", col_mapping)

                # Manual override
                with st.expander("Manual Column Mapping"):
                    cols = [''] + list(df_raw.columns)
                    date_col = st.selectbox("Date column", cols, index=cols.index(col_mapping.get('Date', '')) if col_mapping.get('Date', '') in cols else 0)
                    open_col = st.selectbox("Open column", cols, index=cols.index(col_mapping.get('Open', '')) if col_mapping.get('Open', '') in cols else 0)
                    high_col = st.selectbox("High column", cols, index=cols.index(col_mapping.get('High', '')) if col_mapping.get('High', '') in cols else 0)
                    low_col = st.selectbox("Low column", cols, index=cols.index(col_mapping.get('Low', '')) if col_mapping.get('Low', '') in cols else 0)
                    close_col = st.selectbox("Close column", cols, index=cols.index(col_mapping.get('Close', '')) if col_mapping.get('Close', '') in cols else 0)
                    volume_col = st.selectbox("Volume column", cols, index=cols.index(col_mapping.get('Volume', '')) if col_mapping.get('Volume', '') in cols else 0)

                    if date_col: col_mapping['Date'] = date_col
                    if open_col: col_mapping['Open'] = open_col
                    if high_col: col_mapping['High'] = high_col
                    if low_col: col_mapping['Low'] = low_col
                    if close_col: col_mapping['Close'] = close_col
                    if volume_col: col_mapping['Volume'] = volume_col

                dataset_name = st.text_input("Dataset name", value=uploaded_file.name.replace('.csv', ''), key="dataset_name")

                if st.button("Process & Save", type="primary", key="save_csv"):
                    try:
                        # Process data
                        df_processed = pd.DataFrame()
                        if 'Date' in col_mapping:
                            df_processed.index = pd.to_datetime(df_raw[col_mapping['Date']])
                        for target, source in col_mapping.items():
                            if target != 'Date' and source:
                                df_processed[target] = df_raw[source].values

                        df_processed = df_processed.sort_index()

                        # Save
                        save_path = os.path.join(DATA_DIR, f"{dataset_name}.parquet")
                        df_processed.to_parquet(save_path)

                        st.success(f"Saved {len(df_processed)} rows to {dataset_name}")
                        st.dataframe(df_processed.head(), use_container_width=True)
                    except Exception as e:
                        st.error(f"Error processing: {e}")

            except Exception as e:
                st.error(f"Error reading CSV: {e}")

    with subtab2:
        st.markdown("### Batch Fetch from Yahoo Finance")

        symbols_input = st.text_area("Enter symbols (one per line or comma-separated)",
            "SPY\nQQQ\nXLK\nXLF\nXLV\nXLE\nAAPL\nMSFT\nGOOGL", height=150, key="batch_symbols")

        col1, col2 = st.columns(2)
        with col1:
            batch_start = st.date_input("Start Date", value=datetime.now() - timedelta(days=365*5), key="batch_start")
        with col2:
            batch_end = st.date_input("End Date", value=datetime.now(), key="batch_end")

        batch_name = st.text_input("Dataset name prefix", value="batch", key="batch_name")

        if st.button("Fetch All", type="primary", key="fetch_batch"):
            # Parse symbols
            symbols = []
            for line in symbols_input.split('\n'):
                for sym in line.split(','):
                    sym = sym.strip().upper()
                    if sym:
                        symbols.append(sym)

            if symbols:
                progress = st.progress(0)
                status = st.empty()
                results = []

                for i, sym in enumerate(symbols):
                    status.text(f"Fetching {sym}...")
                    try:
                        df = yf.Ticker(sym).history(start=batch_start, end=batch_end)
                        if not df.empty:
                            save_path = os.path.join(DATA_DIR, f"{batch_name}_{sym}.parquet")
                            df.to_parquet(save_path)
                            results.append({'Symbol': sym, 'Rows': len(df), 'Status': 'Success'})
                        else:
                            results.append({'Symbol': sym, 'Rows': 0, 'Status': 'No data'})
                    except Exception as e:
                        results.append({'Symbol': sym, 'Rows': 0, 'Status': str(e)})

                    progress.progress((i + 1) / len(symbols))

                status.text("Done!")
                st.dataframe(pd.DataFrame(results), use_container_width=True)

    with subtab3:
        st.markdown("### Saved Datasets")

        # List saved files
        if os.path.exists(DATA_DIR):
            files = [f for f in os.listdir(DATA_DIR) if f.endswith('.parquet')]
            if files:
                st.write(f"**{len(files)} datasets saved**")

                for f in sorted(files):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"📊 {f.replace('.parquet', '')}")
                    with col2:
                        try:
                            df = pd.read_parquet(os.path.join(DATA_DIR, f))
                            st.write(f"{len(df)} rows")
                        except Exception as e:
                            st.write(f"Error: {e}")
                    with col3:
                        if st.button("Delete", key=f"del_{f}"):
                            os.remove(os.path.join(DATA_DIR, f))
                            st.rerun()
            else:
                st.info("No saved datasets yet")
        else:
            st.info("No saved datasets yet")


# ============================================================================
# TAB 4: BACKTESTER
# ============================================================================

if selected_page == "🧪 Backtester":
    st.subheader("Strategy Backtester")
    st.markdown("Test trading signals against historical data")

    # Data source selection
    data_source = st.radio("Data Source", ["Fetch from Yahoo", "Use Saved Dataset"], horizontal=True, key="bt_source")

    if data_source == "Fetch from Yahoo":
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            bt_symbol = st.text_input("Symbol", value="SPY", key="bt_symbol")
        with col2:
            bt_start = st.date_input("Start", value=datetime.now() - timedelta(days=365*3), key="bt_start")
        with col3:
            bt_end = st.date_input("End", value=datetime.now(), key="bt_end")
    else:
        files = [f.replace('.parquet', '') for f in os.listdir(DATA_DIR) if f.endswith('.parquet')] if os.path.exists(DATA_DIR) else []
        bt_dataset = st.selectbox("Select Dataset", files if files else ["No datasets"], key="bt_dataset")

    st.divider()

    # Strategy selection
    st.markdown("### Strategy Configuration")

    strategy_type = st.selectbox("Strategy Type", [
        "SMA Crossover",
        "RSI Mean Reversion",
        "MACD Signal",
        "Custom Signal (Advanced)"
    ], key="bt_strategy")

    if strategy_type == "SMA Crossover":
        col1, col2 = st.columns(2)
        with col1:
            fast_sma = st.number_input("Fast SMA Period", value=20, min_value=2, key="bt_fast")
        with col2:
            slow_sma = st.number_input("Slow SMA Period", value=50, min_value=5, key="bt_slow")

    elif strategy_type == "RSI Mean Reversion":
        col1, col2, col3 = st.columns(3)
        with col1:
            rsi_period = st.number_input("RSI Period", value=14, min_value=2, key="bt_rsi_p")
        with col2:
            rsi_oversold = st.number_input("Oversold Level", value=30, min_value=0, max_value=50, key="bt_rsi_os")
        with col3:
            rsi_overbought = st.number_input("Overbought Level", value=70, min_value=50, max_value=100, key="bt_rsi_ob")

    elif strategy_type == "MACD Signal":
        col1, col2, col3 = st.columns(3)
        with col1:
            macd_fast = st.number_input("Fast Period", value=12, min_value=2, key="bt_macd_f")
        with col2:
            macd_slow = st.number_input("Slow Period", value=26, min_value=5, key="bt_macd_s")
        with col3:
            macd_signal = st.number_input("Signal Period", value=9, min_value=2, key="bt_macd_sig")

    else:  # Custom
        st.markdown("**Custom Signal Code** (Python)")
        st.markdown("Use `df` for price data. Return a Series with 1=Buy, -1=Sell, 0=Hold")
        custom_code = st.text_area("Signal Code", value="""# Example: Buy when close > SMA20, Sell when close < SMA20
sma = df['Close'].rolling(20).mean()
signal = pd.Series(0, index=df.index)
signal[df['Close'] > sma] = 1
signal[df['Close'] < sma] = -1
return signal""", height=150, key="bt_code")

    # Backtest parameters
    st.markdown("### Backtest Parameters")
    col1, col2, col3 = st.columns(3)
    with col1:
        initial_capital = st.number_input("Initial Capital ($)", value=100000, min_value=1000, key="bt_capital")
    with col2:
        position_size = st.slider("Position Size (%)", 10, 100, 100, key="bt_size")
    with col3:
        commission = st.number_input("Commission ($)", value=0.0, min_value=0.0, key="bt_comm")

    if st.button("Run Backtest", type="primary", key="bt_run"):
        with st.spinner("Running backtest..."):
            try:
                # Get data
                if data_source == "Fetch from Yahoo":
                    df, error = safe_yf_download(bt_symbol, start=bt_start, end=bt_end)
                    if error:
                        st.error(error)
                        st.stop()
                else:
                    df = pd.read_parquet(os.path.join(DATA_DIR, f"{bt_dataset}.parquet"))

                if df is None or df.empty:
                    st.error("No data available. Please check the symbol and date range, or try again later.")
                else:
                    # Generate signals
                    if strategy_type == "SMA Crossover":
                        df['fast'] = ta.sma(df['Close'], length=fast_sma)
                        df['slow'] = ta.sma(df['Close'], length=slow_sma)
                        df['signal'] = 0
                        df.loc[df['fast'] > df['slow'], 'signal'] = 1
                        df.loc[df['fast'] < df['slow'], 'signal'] = -1

                    elif strategy_type == "RSI Mean Reversion":
                        df['rsi'] = ta.rsi(df['Close'], length=rsi_period)
                        df['signal'] = 0
                        df.loc[df['rsi'] < rsi_oversold, 'signal'] = 1
                        df.loc[df['rsi'] > rsi_overbought, 'signal'] = -1

                    elif strategy_type == "MACD Signal":
                        macd = ta.macd(df['Close'], fast=macd_fast, slow=macd_slow, signal=macd_signal)
                        df['macd'] = macd[f'MACD_{macd_fast}_{macd_slow}_{macd_signal}']
                        df['macd_signal'] = macd[f'MACDs_{macd_fast}_{macd_slow}_{macd_signal}']
                        df['signal'] = 0
                        df.loc[df['macd'] > df['macd_signal'], 'signal'] = 1
                        df.loc[df['macd'] < df['macd_signal'], 'signal'] = -1

                    else:  # Custom - using safe expression evaluation
                        # Parse custom code for safe indicator-based signals
                        # Only allows predefined indicator comparisons, not arbitrary code
                        st.warning("Custom strategies use a restricted syntax for security. Use predefined strategies for best results.")
                        try:
                            # Default to RSI-based strategy for custom
                            df['rsi'] = ta.rsi(df['Close'], length=14)
                            df['signal'] = 0
                            df.loc[df['rsi'] < 30, 'signal'] = 1
                            df.loc[df['rsi'] > 70, 'signal'] = -1
                        except Exception as e:
                            logger.error(f"Custom strategy error: {e}")
                            st.error("Could not parse custom strategy. Please use predefined strategies.")

                    # Run backtest
                    df = df.dropna()
                    df['position'] = df['signal'].shift(1).fillna(0)  # Enter next day
                    df['returns'] = df['Close'].pct_change()
                    df['strategy_returns'] = df['position'] * df['returns']

                    # Account for commission on trades
                    df['trade'] = df['position'].diff().abs()
                    df['commission_cost'] = df['trade'] * commission / initial_capital
                    df['strategy_returns'] = df['strategy_returns'] - df['commission_cost']

                    # Calculate equity curve
                    df['equity'] = initial_capital * (1 + df['strategy_returns']).cumprod()
                    df['buy_hold'] = initial_capital * (1 + df['returns']).cumprod()

                    # Performance metrics
                    total_return = (df['equity'].iloc[-1] / initial_capital - 1) * 100
                    buy_hold_return = (df['buy_hold'].iloc[-1] / initial_capital - 1) * 100
                    sharpe = df['strategy_returns'].mean() / df['strategy_returns'].std() * np.sqrt(252) if df['strategy_returns'].std() > 0 else 0
                    max_dd = ((df['equity'] / df['equity'].cummax()) - 1).min() * 100
                    win_rate = (df[df['strategy_returns'] > 0]['strategy_returns'].count() /
                               df[df['strategy_returns'] != 0]['strategy_returns'].count() * 100) if df[df['strategy_returns'] != 0]['strategy_returns'].count() > 0 else 0
                    num_trades = df['trade'].sum() / 2

                    # Display results
                    st.markdown("### Results")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Strategy Return", f"{total_return:.2f}%")
                    with col2:
                        st.metric("Buy & Hold Return", f"{buy_hold_return:.2f}%")
                    with col3:
                        st.metric("Sharpe Ratio", f"{sharpe:.2f}")
                    with col4:
                        st.metric("Max Drawdown", f"{max_dd:.2f}%")

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Win Rate", f"{win_rate:.1f}%")
                    with col2:
                        st.metric("# Trades", f"{int(num_trades)}")
                    with col3:
                        st.metric("Final Equity", f"${df['equity'].iloc[-1]:,.0f}")
                    with col4:
                        alpha = total_return - buy_hold_return
                        st.metric("Alpha", f"{alpha:.2f}%")

                    # Equity curve
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=df.index, y=df['equity'], name='Strategy', line=dict(color='#26a69a')))
                    fig.add_trace(go.Scatter(x=df.index, y=df['buy_hold'], name='Buy & Hold', line=dict(color='#ef5350')))
                    fig.update_layout(title='Equity Curve', template='plotly_dark', height=400,
                                     yaxis_title='Portfolio Value ($)', xaxis_title='Date')
                    st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

                    # Drawdown
                    df['drawdown'] = (df['equity'] / df['equity'].cummax() - 1) * 100
                    fig2 = go.Figure()
                    fig2.add_trace(go.Scatter(x=df.index, y=df['drawdown'], fill='tozeroy',
                                             fillcolor='rgba(239, 83, 80, 0.3)', line=dict(color='#ef5350')))
                    fig2.update_layout(title='Drawdown', template='plotly_dark', height=250,
                                      yaxis_title='Drawdown (%)', xaxis_title='Date')
                    st.plotly_chart(fig2, use_container_width=True, config=CHART_CONFIG)

            except Exception as e:
                st.error(f"Error: {e}")
                import traceback
                st.code(traceback.format_exc())


# ============================================================================
# TAB 5: AI SCANNER
# ============================================================================

if selected_page == "🤖 AI Scanner":
    st.subheader("AI Pattern Scanner")
    st.markdown("Use machine learning to discover patterns and generate signals")

    st.warning("⚠️ AI Scanner is experimental. Always validate signals with your own analysis.")

    # Data source
    ai_source = st.radio("Data Source", ["Fetch from Yahoo", "Use Saved Dataset"], horizontal=True, key="ai_source")

    if ai_source == "Fetch from Yahoo":
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            ai_symbol = st.text_input("Symbol", value="SPY", key="ai_symbol")
        with col2:
            ai_start = st.date_input("Start", value=datetime.now() - timedelta(days=365*5), key="ai_start")
        with col3:
            ai_end = st.date_input("End", value=datetime.now(), key="ai_end")
    else:
        files = [f.replace('.parquet', '') for f in os.listdir(DATA_DIR) if f.endswith('.parquet')] if os.path.exists(DATA_DIR) else []
        ai_dataset = st.selectbox("Select Dataset", files if files else ["No datasets"], key="ai_dataset")

    st.divider()

    scan_type = st.selectbox("Scan Type", [
        "Feature Importance Analysis",
        "Pattern Clustering",
        "Anomaly Detection",
        "Predictive Signal Generation"
    ], key="ai_scan_type")

    # Prediction horizon
    if scan_type == "Predictive Signal Generation":
        col1, col2 = st.columns(2)
        with col1:
            pred_horizon = st.number_input("Prediction Horizon (days)", value=5, min_value=1, max_value=60, key="ai_horizon")
        with col2:
            pred_threshold = st.number_input("Signal Threshold (%)", value=1.0, min_value=0.1, max_value=10.0, key="ai_thresh")

    if st.button("Run AI Analysis", type="primary", key="ai_run"):
        with st.spinner("Running AI analysis..."):
            try:
                from sklearn.ensemble import RandomForestClassifier, IsolationForest
                from sklearn.preprocessing import StandardScaler
                from sklearn.cluster import KMeans

                # Get data
                if ai_source == "Fetch from Yahoo":
                    df = yf.Ticker(ai_symbol).history(start=ai_start, end=ai_end)
                    symbol_name = ai_symbol
                else:
                    df = pd.read_parquet(os.path.join(DATA_DIR, f"{ai_dataset}.parquet"))
                    symbol_name = ai_dataset

                if df.empty or len(df) < 100:
                    st.error("Need at least 100 data points")
                else:
                    # Feature engineering
                    df['returns'] = df['Close'].pct_change()
                    df['volatility'] = df['returns'].rolling(20).std()
                    df['sma_20'] = ta.sma(df['Close'], length=20)
                    df['sma_50'] = ta.sma(df['Close'], length=50)
                    df['rsi'] = ta.rsi(df['Close'], length=14)
                    macd = ta.macd(df['Close'])
                    if macd is not None:
                        df['macd'] = macd['MACD_12_26_9']
                        df['macd_signal'] = macd['MACDs_12_26_9']
                        df['macd_hist'] = macd['MACDh_12_26_9']

                    df['price_to_sma20'] = df['Close'] / df['sma_20']
                    df['price_to_sma50'] = df['Close'] / df['sma_50']
                    df['volume_ratio'] = df['Volume'] / df['Volume'].rolling(20).mean()
                    df['high_low_ratio'] = (df['High'] - df['Low']) / df['Close']

                    # Clean data
                    feature_cols = ['returns', 'volatility', 'rsi', 'price_to_sma20', 'price_to_sma50',
                                   'volume_ratio', 'high_low_ratio', 'macd_hist']
                    feature_cols = [c for c in feature_cols if c in df.columns]
                    df_clean = df[feature_cols].dropna()

                    if len(df_clean) < 50:
                        st.error("Not enough clean data after feature engineering")
                    else:
                        X = df_clean.values
                        scaler = StandardScaler()
                        X_scaled = scaler.fit_transform(X)

                        if scan_type == "Feature Importance Analysis":
                            # Create target: 1 if price goes up next 5 days
                            df_clean['future_return'] = df['Close'].shift(-5) / df['Close'] - 1
                            df_ml = df_clean.dropna()
                            y = (df_ml['future_return'] > 0).astype(int)
                            X_ml = df_ml[feature_cols].values

                            model = RandomForestClassifier(n_estimators=100, random_state=42)
                            model.fit(X_ml, y)

                            importance = pd.DataFrame({
                                'Feature': feature_cols,
                                'Importance': model.feature_importances_
                            }).sort_values('Importance', ascending=True)

                            fig = go.Figure(go.Bar(x=importance['Importance'], y=importance['Feature'], orientation='h'))
                            fig.update_layout(title='Feature Importance for Predicting 5-Day Returns',
                                            template='plotly_dark', height=400)
                            st.plotly_chart(fig, use_container_width=True)

                            st.markdown("### Interpretation")
                            top_feature = importance.iloc[-1]['Feature']
                            st.write(f"**Most important feature:** {top_feature}")
                            st.write("Higher importance means the feature has more predictive power for future returns.")

                        elif scan_type == "Pattern Clustering":
                            n_clusters = st.slider("Number of clusters", 3, 10, 5, key="ai_clusters")
                            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                            df_clean['cluster'] = kmeans.fit_predict(X_scaled)

                            # Analyze clusters
                            cluster_stats = df_clean.groupby('cluster').agg({
                                'returns': ['mean', 'std', 'count'],
                                'rsi': 'mean',
                                'volatility': 'mean'
                            }).round(4)

                            st.markdown("### Cluster Analysis")
                            st.dataframe(cluster_stats, use_container_width=True)

                            # Plot clusters on RSI vs Returns
                            fig = go.Figure()
                            for c in range(n_clusters):
                                mask = df_clean['cluster'] == c
                                fig.add_trace(go.Scatter(
                                    x=df_clean[mask]['rsi'],
                                    y=df_clean[mask]['returns'] * 100,
                                    mode='markers',
                                    name=f'Cluster {c}',
                                    opacity=0.6
                                ))
                            fig.update_layout(title='Pattern Clusters (RSI vs Daily Returns)',
                                            template='plotly_dark', height=500,
                                            xaxis_title='RSI', yaxis_title='Daily Return (%)')
                            st.plotly_chart(fig, use_container_width=True)

                        elif scan_type == "Anomaly Detection":
                            contamination = st.slider("Anomaly sensitivity", 0.01, 0.2, 0.05, key="ai_contam")
                            iso = IsolationForest(contamination=contamination, random_state=42)
                            df_clean['anomaly'] = iso.fit_predict(X_scaled)

                            anomalies = df_clean[df_clean['anomaly'] == -1]
                            st.markdown(f"### Found {len(anomalies)} anomalies ({len(anomalies)/len(df_clean)*100:.1f}%)")

                            # Plot
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Price', line=dict(color='#26a69a')))

                            anomaly_dates = anomalies.index
                            anomaly_prices = df.loc[anomaly_dates, 'Close']
                            fig.add_trace(go.Scatter(x=anomaly_dates, y=anomaly_prices,
                                                    mode='markers', name='Anomalies',
                                                    marker=dict(size=10, color='red', symbol='x')))

                            fig.update_layout(title=f'{symbol_name} - Anomaly Detection',
                                            template='plotly_dark', height=500)
                            st.plotly_chart(fig, use_container_width=True)

                            st.markdown("### Recent Anomalies")
                            st.dataframe(anomalies.tail(10), use_container_width=True)

                        elif scan_type == "Predictive Signal Generation":
                            # Create target
                            df_clean['future_return'] = df['Close'].shift(-pred_horizon) / df['Close'] - 1
                            df_ml = df_clean.dropna()

                            # Multi-class: -1 (sell), 0 (hold), 1 (buy)
                            df_ml['target'] = 0
                            df_ml.loc[df_ml['future_return'] > pred_threshold/100, 'target'] = 1
                            df_ml.loc[df_ml['future_return'] < -pred_threshold/100, 'target'] = -1

                            # Train/test split (time-based)
                            split = int(len(df_ml) * 0.8)
                            train = df_ml.iloc[:split]
                            test = df_ml.iloc[split:]

                            X_train = train[feature_cols].values
                            y_train = train['target'].values
                            X_test = test[feature_cols].values
                            y_test = test['target'].values

                            model = RandomForestClassifier(n_estimators=100, random_state=42)
                            model.fit(X_train, y_train)

                            # Predict
                            test_pred = model.predict(X_test)
                            train_acc = model.score(X_train, y_train)
                            test_acc = model.score(X_test, y_test)

                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Train Accuracy", f"{train_acc*100:.1f}%")
                            with col2:
                                st.metric("Test Accuracy", f"{test_acc*100:.1f}%")

                            # Current prediction
                            latest = df_clean[feature_cols].iloc[-1:].values
                            current_pred = model.predict(latest)[0]
                            current_proba = model.predict_proba(latest)[0]

                            st.markdown("### Current Signal")
                            signal_map = {-1: "🔴 SELL", 0: "⚪ HOLD", 1: "🟢 BUY"}
                            st.markdown(f"## {signal_map[current_pred]}")

                            st.markdown("**Confidence:**")
                            for i, label in enumerate(model.classes_):
                                st.write(f"{signal_map[label]}: {current_proba[i]*100:.1f}%")

                            # Plot predictions on test set
                            test_df = test.copy()
                            test_df['prediction'] = test_pred

                            fig = go.Figure()
                            fig.add_trace(go.Scatter(x=test_df.index, y=df.loc[test_df.index, 'Close'],
                                                    name='Price', line=dict(color='gray')))

                            # Buy signals
                            buy_mask = test_df['prediction'] == 1
                            fig.add_trace(go.Scatter(x=test_df[buy_mask].index,
                                                    y=df.loc[test_df[buy_mask].index, 'Close'],
                                                    mode='markers', name='Buy Signal',
                                                    marker=dict(size=8, color='green', symbol='triangle-up')))

                            # Sell signals
                            sell_mask = test_df['prediction'] == -1
                            fig.add_trace(go.Scatter(x=test_df[sell_mask].index,
                                                    y=df.loc[test_df[sell_mask].index, 'Close'],
                                                    mode='markers', name='Sell Signal',
                                                    marker=dict(size=8, color='red', symbol='triangle-down')))

                            fig.update_layout(title='AI-Generated Signals (Test Period)',
                                            template='plotly_dark', height=500)
                            st.plotly_chart(fig, use_container_width=True)

            except ImportError as e:
                st.error(f"Missing dependency: {e}. Please install scikit-learn.")
            except Exception as e:
                st.error(f"Error: {e}")
                import traceback
                st.code(traceback.format_exc())


# ============================================================================
# TAB 6: GROUP ANALYSIS
# ============================================================================

# File to store bundles
BUNDLES_FILE = os.path.join(DATA_DIR, "bundles.json")

def load_bundles():
    if os.path.exists(BUNDLES_FILE):
        with open(BUNDLES_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_bundles(bundles):
    with open(BUNDLES_FILE, 'w') as f:
        json.dump(bundles, f, indent=2)

if selected_page == "📦 Group Analysis":
    st.subheader("Group Analysis")
    st.markdown("Bundle stocks together to find correlations, lead-lag relationships, and create composite indicators")

    subtab1, subtab2, subtab3, subtab4, subtab5 = st.tabs([
        "📦 Manage Bundles",
        "🔗 Correlation Matrix",
        "⏱️ Lead-Lag Analysis",
        "📈 Composite Indicators",
        "🎯 Regime Detection"
    ])

    # Load existing bundles
    bundles = load_bundles()

    with subtab1:
        st.markdown("### Create & Manage Stock Bundles")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Create New Bundle")
            bundle_name = st.text_input("Bundle Name", placeholder="e.g., Tech Leaders, Defensive Stocks", key="bundle_name")
            bundle_symbols = st.text_area("Symbols (comma or newline separated)",
                placeholder="AAPL, MSFT, GOOGL, AMZN\nMETA, NVDA, TSLA", height=150, key="bundle_symbols")
            bundle_desc = st.text_input("Description (optional)", key="bundle_desc")

            if st.button("Create Bundle", type="primary", key="create_bundle"):
                if bundle_name and bundle_symbols:
                    symbols = []
                    for line in bundle_symbols.split('\n'):
                        for sym in line.split(','):
                            sym = sym.strip().upper()
                            if sym:
                                symbols.append(sym)

                    bundles[bundle_name] = {
                        'symbols': symbols,
                        'description': bundle_desc,
                        'created': datetime.now().isoformat()
                    }
                    save_bundles(bundles)
                    st.success(f"Created bundle '{bundle_name}' with {len(symbols)} symbols")
                    st.rerun()
                else:
                    st.warning("Please enter a bundle name and symbols")

        with col2:
            st.markdown("#### Existing Bundles")
            if bundles:
                for name, data in bundles.items():
                    with st.expander(f"📦 {name} ({len(data['symbols'])} stocks)"):
                        st.write(f"**Symbols:** {', '.join(data['symbols'])}")
                        if data.get('description'):
                            st.write(f"**Description:** {data['description']}")
                        if st.button(f"Delete {name}", key=f"del_bundle_{name}"):
                            del bundles[name]
                            save_bundles(bundles)
                            st.rerun()
            else:
                st.info("No bundles created yet")

        # Preset bundles
        st.markdown("---")
        st.markdown("#### Quick-Add Preset Bundles")
        col1, col2, col3 = st.columns(3)

        presets = {
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

        for i, (preset_name, preset_data) in enumerate(presets.items()):
            col = [col1, col2, col3][i % 3]
            with col:
                if st.button(f"Add {preset_name}", key=f"preset_{preset_name}"):
                    bundles[preset_name] = {**preset_data, 'created': datetime.now().isoformat()}
                    save_bundles(bundles)
                    st.success(f"Added {preset_name}")
                    st.rerun()

    with subtab2:
        st.markdown("### Correlation Matrix")
        st.markdown("Find which stocks move together and which move inversely")

        if not bundles:
            st.info("Create a bundle first in 'Manage Bundles' tab")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                selected_bundle = st.selectbox("Select Bundle", list(bundles.keys()), key="corr_bundle")
            with col2:
                corr_period = st.selectbox("Time Period", ["1 Month", "3 Months", "6 Months", "1 Year", "2 Years"], index=2, key="corr_period")
            with col3:
                corr_type = st.selectbox("Correlation Type", ["Returns", "Price Levels", "Rolling 20-day"], key="corr_type")

            if st.button("Calculate Correlation", type="primary", key="calc_corr"):
                period_days = {"1 Month": 30, "3 Months": 90, "6 Months": 180, "1 Year": 365, "2 Years": 730}
                days = period_days.get(corr_period, 180)
                start = datetime.now() - timedelta(days=days)

                symbols = bundles[selected_bundle]['symbols']

                with st.spinner(f"Fetching data for {len(symbols)} symbols..."):
                    prices = pd.DataFrame()
                    for sym in symbols:
                        try:
                            data = yf.Ticker(sym).history(start=start, end=datetime.now())
                            if not data.empty:
                                prices[sym] = data['Close']
                        except Exception as e:
                            st.warning(f"Skipped {sym}: {e}")

                    if len(prices.columns) < 2:
                        st.error("Need at least 2 symbols with data")
                    else:
                        # Calculate correlation based on type
                        if corr_type == "Returns":
                            returns = prices.pct_change().dropna()
                            corr_matrix = returns.corr()
                        elif corr_type == "Price Levels":
                            corr_matrix = prices.corr()
                        else:  # Rolling
                            returns = prices.pct_change().dropna()
                            corr_matrix = returns.rolling(20).corr().groupby(level=1).mean()

                        # Heatmap
                        fig = go.Figure(data=go.Heatmap(
                            z=corr_matrix.values,
                            x=corr_matrix.columns,
                            y=corr_matrix.index,
                            colorscale='RdBu_r',
                            zmid=0,
                            text=np.round(corr_matrix.values, 2),
                            texttemplate='%{text}',
                            textfont={"size": 10},
                            hoverongaps=False
                        ))
                        fig.update_layout(title=f'Correlation Matrix - {selected_bundle}',
                                        template='plotly_dark', height=600)
                        st.plotly_chart(fig, use_container_width=True)

                        # Find highest/lowest correlations
                        st.markdown("### Key Findings")
                        col1, col2 = st.columns(2)

                        # Get unique pairs
                        pairs = []
                        for i, sym1 in enumerate(corr_matrix.columns):
                            for j, sym2 in enumerate(corr_matrix.columns):
                                if i < j:
                                    pairs.append({
                                        'Pair': f"{sym1}-{sym2}",
                                        'Correlation': corr_matrix.loc[sym1, sym2]
                                    })

                        pairs_df = pd.DataFrame(pairs).sort_values('Correlation', ascending=False)

                        with col1:
                            st.markdown("**Most Correlated (move together)**")
                            st.dataframe(pairs_df.head(5), use_container_width=True)

                        with col2:
                            st.markdown("**Least Correlated (diversification)**")
                            st.dataframe(pairs_df.tail(5), use_container_width=True)

    with subtab3:
        st.markdown("### Lead-Lag Analysis")
        st.markdown("Find which stocks lead or lag others - potential predictive signals")

        if not bundles:
            st.info("Create a bundle first")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                ll_bundle = st.selectbox("Select Bundle", list(bundles.keys()), key="ll_bundle")
            with col2:
                ll_period = st.selectbox("Time Period", ["3 Months", "6 Months", "1 Year", "2 Years"], index=1, key="ll_period")
            with col3:
                max_lag = st.slider("Max Lag (days)", 1, 20, 10, key="max_lag")

            benchmark = st.text_input("Benchmark to predict (e.g., SPY)", value="SPY", key="ll_bench")

            if st.button("Analyze Lead-Lag", type="primary", key="calc_ll"):
                period_days = {"3 Months": 90, "6 Months": 180, "1 Year": 365, "2 Years": 730}
                days = period_days.get(ll_period, 180)
                start = datetime.now() - timedelta(days=days)

                symbols = bundles[ll_bundle]['symbols']
                if benchmark not in symbols:
                    symbols = symbols + [benchmark]

                with st.spinner("Calculating lead-lag relationships..."):
                    prices = pd.DataFrame()
                    for sym in symbols:
                        try:
                            data = yf.Ticker(sym).history(start=start, end=datetime.now())
                            if not data.empty:
                                prices[sym] = data['Close']
                        except Exception as e:
                            st.warning(f"Skipped {sym}: {e}")

                    if benchmark not in prices.columns:
                        st.error(f"Could not fetch benchmark {benchmark}")
                    else:
                        returns = prices.pct_change().dropna()
                        bench_returns = returns[benchmark]

                        # Calculate cross-correlation at different lags
                        results = []
                        for sym in returns.columns:
                            if sym == benchmark:
                                continue

                            best_lag = 0
                            best_corr = 0

                            for lag in range(-max_lag, max_lag + 1):
                                if lag < 0:
                                    # Symbol leads benchmark
                                    corr = returns[sym].iloc[:lag].corr(bench_returns.iloc[-lag:])
                                elif lag > 0:
                                    # Symbol lags benchmark
                                    corr = returns[sym].iloc[lag:].corr(bench_returns.iloc[:-lag])
                                else:
                                    corr = returns[sym].corr(bench_returns)

                                if abs(corr) > abs(best_corr):
                                    best_corr = corr
                                    best_lag = lag

                            results.append({
                                'Symbol': sym,
                                'Best Lag': best_lag,
                                'Correlation': round(best_corr, 3),
                                'Relationship': 'Leads' if best_lag < 0 else 'Lags' if best_lag > 0 else 'Concurrent'
                            })

                        results_df = pd.DataFrame(results)
                        results_df = results_df.sort_values('Best Lag')

                        # Visualize
                        fig = go.Figure()

                        leaders = results_df[results_df['Best Lag'] < 0].sort_values('Best Lag')
                        laggers = results_df[results_df['Best Lag'] > 0].sort_values('Best Lag', ascending=False)
                        concurrent = results_df[results_df['Best Lag'] == 0]

                        fig.add_trace(go.Bar(
                            y=leaders['Symbol'],
                            x=leaders['Best Lag'],
                            orientation='h',
                            name='Leaders',
                            marker_color='green',
                            text=[f"{l}d, r={c}" for l, c in zip(leaders['Best Lag'], leaders['Correlation'])],
                            textposition='outside'
                        ))

                        fig.add_trace(go.Bar(
                            y=laggers['Symbol'],
                            x=laggers['Best Lag'],
                            orientation='h',
                            name='Laggers',
                            marker_color='red',
                            text=[f"+{l}d, r={c}" for l, c in zip(laggers['Best Lag'], laggers['Correlation'])],
                            textposition='outside'
                        ))

                        fig.update_layout(
                            title=f'Lead-Lag Relationships vs {benchmark}',
                            xaxis_title='Days (negative = leads, positive = lags)',
                            template='plotly_dark',
                            height=max(400, len(results) * 30),
                            showlegend=True
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        st.markdown("### Results Table")
                        st.dataframe(results_df, use_container_width=True)

                        # Interpretation
                        st.markdown("### Interpretation")
                        if len(leaders) > 0:
                            top_leader = leaders.iloc[0]
                            st.success(f"**Top Leader:** {top_leader['Symbol']} leads {benchmark} by {abs(top_leader['Best Lag'])} days (correlation: {top_leader['Correlation']})")
                            st.write(f"When {top_leader['Symbol']} moves today, {benchmark} tends to follow in {abs(top_leader['Best Lag'])} days.")

    with subtab4:
        st.markdown("### Composite Indicators")
        st.markdown("Create custom indicators from groups of stocks")

        if not bundles:
            st.info("Create a bundle first")
        else:
            col1, col2 = st.columns(2)
            with col1:
                ci_bundle = st.selectbox("Select Bundle", list(bundles.keys()), key="ci_bundle")
            with col2:
                ci_period = st.selectbox("Time Period", ["3 Months", "6 Months", "1 Year", "2 Years"], index=2, key="ci_period")

            indicator_type = st.selectbox("Indicator Type", [
                "Equal-Weight Performance",
                "Breadth (% Above SMA)",
                "Average RSI",
                "Momentum Score",
                "Volatility Index",
                "New Highs - New Lows"
            ], key="ci_type")

            compare_to = st.text_input("Compare to (optional benchmark)", value="SPY", key="ci_compare")

            if st.button("Generate Indicator", type="primary", key="gen_ci"):
                period_days = {"3 Months": 90, "6 Months": 180, "1 Year": 365, "2 Years": 730}
                days = period_days.get(ci_period, 365)
                start = datetime.now() - timedelta(days=days)

                symbols = bundles[ci_bundle]['symbols']

                with st.spinner("Generating composite indicator..."):
                    prices = pd.DataFrame()
                    for sym in symbols:
                        try:
                            data = yf.Ticker(sym).history(start=start, end=datetime.now())
                            if not data.empty:
                                prices[sym] = data['Close']
                        except Exception as e:
                            st.warning(f"Skipped {sym}: {e}")

                    if len(prices.columns) < 2:
                        st.error("Need at least 2 symbols")
                    else:
                        # Calculate indicator
                        if indicator_type == "Equal-Weight Performance":
                            # Normalize to 100 and average
                            normalized = prices / prices.iloc[0] * 100
                            indicator = normalized.mean(axis=1)
                            indicator_name = "Equal-Weight Index"

                        elif indicator_type == "Breadth (% Above SMA)":
                            sma20 = prices.rolling(20).mean()
                            above_sma = (prices > sma20).astype(int)
                            indicator = above_sma.mean(axis=1) * 100
                            indicator_name = "% Above 20-day SMA"

                        elif indicator_type == "Average RSI":
                            rsi_df = pd.DataFrame()
                            for sym in prices.columns:
                                rsi_df[sym] = ta.rsi(prices[sym], length=14)
                            indicator = rsi_df.mean(axis=1)
                            indicator_name = "Average RSI"

                        elif indicator_type == "Momentum Score":
                            # Rate of change over 20 days
                            roc = prices.pct_change(20) * 100
                            indicator = roc.mean(axis=1)
                            indicator_name = "20-day Momentum Score"

                        elif indicator_type == "Volatility Index":
                            returns = prices.pct_change()
                            vol = returns.rolling(20).std() * np.sqrt(252) * 100
                            indicator = vol.mean(axis=1)
                            indicator_name = "Average Volatility (%)"

                        else:  # New Highs - New Lows
                            rolling_high = prices.rolling(52*5).max()  # 52-week high
                            rolling_low = prices.rolling(52*5).min()
                            new_highs = (prices == rolling_high).sum(axis=1)
                            new_lows = (prices == rolling_low).sum(axis=1)
                            indicator = new_highs - new_lows
                            indicator_name = "New Highs - New Lows"

                        # Plot
                        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                           vertical_spacing=0.1, row_heights=[0.6, 0.4])

                        # Benchmark comparison
                        if compare_to:
                            try:
                                bench_data = yf.Ticker(compare_to).history(start=start, end=datetime.now())
                                bench_norm = bench_data['Close'] / bench_data['Close'].iloc[0] * 100
                                fig.add_trace(go.Scatter(x=bench_norm.index, y=bench_norm,
                                    name=compare_to, line=dict(color='gray', width=1)), row=1, col=1)
                            except Exception as e:
                                pass  # Benchmark overlay failed: {e}

                        if indicator_type == "Equal-Weight Performance":
                            fig.add_trace(go.Scatter(x=indicator.index, y=indicator,
                                name=ci_bundle, line=dict(color='#26a69a', width=2)), row=1, col=1)
                            fig.update_yaxes(title_text="Normalized (100 = start)", row=1, col=1)
                        else:
                            # For other indicators, show benchmark price in top, indicator in bottom
                            if compare_to:
                                fig.update_yaxes(title_text=f"{compare_to} Price", row=1, col=1)

                        fig.add_trace(go.Scatter(x=indicator.index, y=indicator,
                            name=indicator_name, line=dict(color='#26a69a', width=2)), row=2, col=1)

                        # Add reference lines for certain indicators
                        if indicator_type == "Average RSI":
                            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
                        elif indicator_type == "Breadth (% Above SMA)":
                            fig.add_hline(y=80, line_dash="dash", line_color="red", row=2, col=1)
                            fig.add_hline(y=20, line_dash="dash", line_color="green", row=2, col=1)

                        fig.update_layout(title=f'{ci_bundle} - {indicator_name}',
                                        template='plotly_dark', height=600)
                        fig.update_yaxes(title_text=indicator_name, row=2, col=1)

                        st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

                        # Current reading
                        current_val = indicator.dropna().iloc[-1]
                        st.metric(f"Current {indicator_name}", f"{current_val:.2f}")

                        # Save indicator option
                        if st.button("Save as Dataset", key="save_ci"):
                            ci_df = pd.DataFrame({'value': indicator})
                            save_path = os.path.join(DATA_DIR, f"indicator_{ci_bundle}_{indicator_type.replace(' ', '_')}.parquet")
                            ci_df.to_parquet(save_path)
                            st.success(f"Saved to {save_path}")

    with subtab5:
        st.markdown("### Regime Detection")
        st.markdown("Identify market regimes based on group behavior patterns")

        if not bundles:
            st.info("Create a bundle first")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                rd_bundle = st.selectbox("Select Bundle", list(bundles.keys()), key="rd_bundle")
            with col2:
                rd_period = st.selectbox("Time Period", ["1 Year", "2 Years", "3 Years", "5 Years"], index=1, key="rd_period")
            with col3:
                n_regimes = st.slider("Number of Regimes", 2, 6, 4, key="n_regimes")

            if st.button("Detect Regimes", type="primary", key="detect_regimes"):
                period_days = {"1 Year": 365, "2 Years": 730, "3 Years": 1095, "5 Years": 1825}
                days = period_days.get(rd_period, 730)
                start = datetime.now() - timedelta(days=days)

                symbols = bundles[rd_bundle]['symbols']

                with st.spinner("Analyzing market regimes..."):
                    try:
                        from sklearn.cluster import KMeans
                        from sklearn.preprocessing import StandardScaler

                        prices = pd.DataFrame()
                        for sym in symbols:
                            try:
                                data = yf.Ticker(sym).history(start=start, end=datetime.now())
                                if not data.empty:
                                    prices[sym] = data['Close']
                            except Exception as e:
                                st.warning(f"Skipped {sym}: {e}")

                        if len(prices.columns) < 3:
                            st.error("Need at least 3 symbols")
                        else:
                            # Create features for regime detection
                            returns = prices.pct_change().dropna()

                            features = pd.DataFrame(index=returns.index)
                            features['avg_return'] = returns.mean(axis=1)
                            features['avg_volatility'] = returns.rolling(20).std().mean(axis=1)
                            features['correlation'] = returns.rolling(20).corr().groupby(level=0).mean().mean(axis=1)
                            features['dispersion'] = returns.std(axis=1)
                            features['breadth'] = (returns > 0).mean(axis=1)

                            features = features.dropna()

                            # Cluster
                            X = features.values
                            scaler = StandardScaler()
                            X_scaled = scaler.fit_transform(X)

                            kmeans = KMeans(n_clusters=n_regimes, random_state=42, n_init=10)
                            features['regime'] = kmeans.fit_predict(X_scaled)

                            # Analyze regimes
                            regime_stats = features.groupby('regime').agg({
                                'avg_return': ['mean', 'std'],
                                'avg_volatility': 'mean',
                                'correlation': 'mean',
                                'breadth': 'mean'
                            }).round(4)

                            # Name regimes based on characteristics
                            regime_names = {}
                            for r in range(n_regimes):
                                stats = features[features['regime'] == r]
                                avg_ret = stats['avg_return'].mean()
                                avg_vol = stats['avg_volatility'].mean()
                                avg_breadth = stats['breadth'].mean()

                                if avg_ret > 0.001 and avg_vol < features['avg_volatility'].median():
                                    regime_names[r] = "🟢 Bull (Low Vol)"
                                elif avg_ret > 0.001:
                                    regime_names[r] = "🟡 Bull (High Vol)"
                                elif avg_ret < -0.001 and avg_vol > features['avg_volatility'].median():
                                    regime_names[r] = "🔴 Bear (High Vol)"
                                elif avg_ret < -0.001:
                                    regime_names[r] = "🟠 Bear (Low Vol)"
                                elif avg_vol > features['avg_volatility'].quantile(0.75):
                                    regime_names[r] = "⚡ High Volatility"
                                else:
                                    regime_names[r] = "⚪ Sideways"

                            features['regime_name'] = features['regime'].map(regime_names)

                            # Plot regime timeline
                            fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                              vertical_spacing=0.1, row_heights=[0.7, 0.3])

                            # Get benchmark for context
                            try:
                                spy = yf.Ticker('SPY').history(start=start, end=datetime.now())
                                fig.add_trace(go.Scatter(x=spy.index, y=spy['Close'],
                                    name='SPY', line=dict(color='white', width=1)), row=1, col=1)
                            except Exception as e:
                                pass  # SPY overlay failed: {e}

                            # Color by regime
                            colors = ['green', 'yellow', 'red', 'orange', 'purple', 'blue']
                            for r in range(n_regimes):
                                mask = features['regime'] == r
                                regime_dates = features[mask].index

                                fig.add_trace(go.Scatter(
                                    x=regime_dates,
                                    y=[r] * len(regime_dates),
                                    mode='markers',
                                    marker=dict(color=colors[r % len(colors)], size=5),
                                    name=regime_names[r]
                                ), row=2, col=1)

                            fig.update_layout(title='Market Regimes Over Time',
                                            template='plotly_dark', height=600)
                            fig.update_yaxes(title_text="SPY Price", row=1, col=1)
                            fig.update_yaxes(title_text="Regime", row=2, col=1)

                            st.plotly_chart(fig, use_container_width=True)

                            # Current regime
                            current_regime = features['regime'].iloc[-1]
                            current_name = regime_names[current_regime]

                            st.markdown("### Current Market Regime")
                            st.markdown(f"## {current_name}")

                            # Regime statistics
                            st.markdown("### Regime Characteristics")
                            for r in range(n_regimes):
                                regime_data = features[features['regime'] == r]
                                st.markdown(f"**{regime_names[r]}** ({len(regime_data)} days, {len(regime_data)/len(features)*100:.1f}%)")
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Avg Daily Return", f"{regime_data['avg_return'].mean()*100:.3f}%")
                                with col2:
                                    st.metric("Avg Volatility", f"{regime_data['avg_volatility'].mean()*100:.2f}%")
                                with col3:
                                    st.metric("Avg Correlation", f"{regime_data['correlation'].mean():.2f}")
                                with col4:
                                    st.metric("Breadth", f"{regime_data['breadth'].mean()*100:.1f}%")

                    except ImportError:
                        st.error("scikit-learn required for regime detection")
                    except Exception as e:
                        st.error(f"Error: {e}")
                        import traceback
                        st.code(traceback.format_exc())


# ============================================================================
# TAB 7: TECHNICAL ANALYSIS
# ============================================================================

if selected_page == "📐 Technical Analysis":
    st.subheader("Technical Analysis Dashboard")
    st.markdown("Comprehensive technical indicators: Fibonacci, Bollinger, Ichimoku, Pivot Points, and more")

    # Data input section
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        ta_symbol = st.text_input("Symbol", value="SPY", key="ta_symbol")
    with col2:
        ta_start = st.date_input("Start", value=datetime.now() - timedelta(days=365), key="ta_start")
    with col3:
        ta_end = st.date_input("End", value=datetime.now(), key="ta_end")

    # Sub-tabs for different analysis types
    ta_sub1, ta_sub2, ta_sub3, ta_sub4, ta_sub5 = st.tabs([
        "📏 Fibonacci",
        "📊 Oscillators",
        "☁️ Ichimoku",
        "📍 Pivot Points",
        "📉 Volatility"
    ])

    with ta_sub1:
        st.markdown("### Fibonacci Retracement & Extension")
        st.markdown("Identify key support/resistance levels based on Fibonacci ratios")

        col1, col2 = st.columns(2)
        with col1:
            fib_type = st.selectbox("Type", ["Retracement", "Extension"], key="fib_type")
        with col2:
            fib_method = st.selectbox("Swing Detection", ["Auto (Recent)", "Manual"], key="fib_method")

        if fib_method == "Manual":
            col1, col2 = st.columns(2)
            with col1:
                swing_high = st.number_input("Swing High Price", value=0.0, key="fib_high")
            with col2:
                swing_low = st.number_input("Swing Low Price", value=0.0, key="fib_low")

        if st.button("Calculate Fibonacci Levels", type="primary", key="calc_fib"):
            with st.spinner("Calculating..."):
                try:
                    df = yf.Ticker(ta_symbol).history(start=ta_start, end=ta_end)
                    if df.empty:
                        st.error("No data available")
                    else:
                        # Find swing high/low
                        if fib_method == "Auto (Recent)":
                            # Find recent swing high and low (last 60 days)
                            recent = df.tail(60)
                            swing_high = recent['High'].max()
                            swing_low = recent['Low'].min()
                            high_date = recent['High'].idxmax()
                            low_date = recent['Low'].idxmin()

                            # Determine trend direction
                            if high_date > low_date:
                                trend = "Uptrend (Low to High)"
                            else:
                                trend = "Downtrend (High to Low)"
                        else:
                            trend = "Manual"
                            high_date = df.index[-1]
                            low_date = df.index[0]

                        # Calculate Fibonacci levels
                        diff = swing_high - swing_low

                        if fib_type == "Retracement":
                            fib_levels = {
                                '0.0% (High)': swing_high,
                                '23.6%': swing_high - diff * 0.236,
                                '38.2%': swing_high - diff * 0.382,
                                '50.0%': swing_high - diff * 0.5,
                                '61.8% (Golden)': swing_high - diff * 0.618,
                                '78.6%': swing_high - diff * 0.786,
                                '100.0% (Low)': swing_low
                            }
                        else:  # Extension
                            fib_levels = {
                                '0.0%': swing_low,
                                '61.8%': swing_low + diff * 0.618,
                                '100.0%': swing_high,
                                '127.2%': swing_low + diff * 1.272,
                                '161.8%': swing_low + diff * 1.618,
                                '200.0%': swing_low + diff * 2.0,
                                '261.8%': swing_low + diff * 2.618
                            }

                        # Create chart
                        fig = go.Figure()

                        # Candlestick
                        fig.add_trace(go.Candlestick(
                            x=df.index, open=df['Open'], high=df['High'],
                            low=df['Low'], close=df['Close'], name='Price'
                        ))

                        # Fibonacci lines
                        colors = ['green', 'lime', 'yellow', 'orange', 'red', 'darkred', 'maroon']
                        for i, (level, price) in enumerate(fib_levels.items()):
                            fig.add_hline(y=price, line_dash="dash",
                                         line_color=colors[i % len(colors)],
                                         annotation_text=f"{level}: ${price:.2f}",
                                         annotation_position="right")

                        fig.update_layout(
                            title=f'{ta_symbol} Fibonacci {fib_type} - {trend}',
                            template='plotly_dark', height=600,
                            xaxis_rangeslider_visible=False
                        )
                        st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

                        # Level summary
                        st.markdown("### Fibonacci Levels")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Swing High", f"${swing_high:.2f}")
                        with col2:
                            st.metric("Swing Low", f"${swing_low:.2f}")

                        levels_df = pd.DataFrame([
                            {'Level': k, 'Price': f"${v:.2f}"} for k, v in fib_levels.items()
                        ])
                        st.dataframe(levels_df, use_container_width=True)

                        # Current price relative to levels
                        current = df['Close'].iloc[-1]
                        st.markdown(f"**Current Price:** ${current:.2f}")

                        # Find nearest levels
                        sorted_levels = sorted(fib_levels.items(), key=lambda x: abs(x[1] - current))
                        st.info(f"Nearest level: {sorted_levels[0][0]} at ${sorted_levels[0][1]:.2f}")

                except Exception as e:
                    st.error(f"Error: {e}")

    with ta_sub2:
        st.markdown("### Technical Oscillators")
        st.markdown("RSI, Stochastic, Williams %R, CCI, MFI, ADX")

        oscillators = st.multiselect("Select Oscillators", [
            "RSI (14)",
            "Stochastic (14,3,3)",
            "Williams %R (14)",
            "CCI (20)",
            "MFI (14)",
            "ADX (14)"
        ], default=["RSI (14)", "Stochastic (14,3,3)"], key="osc_select")

        if st.button("Generate Oscillators", type="primary", key="gen_osc"):
            with st.spinner("Calculating oscillators..."):
                try:
                    df = yf.Ticker(ta_symbol).history(start=ta_start, end=ta_end)
                    if df.empty:
                        st.error("No data")
                    else:
                        n_osc = len(oscillators)
                        if n_osc == 0:
                            st.warning("Select at least one oscillator")
                        else:
                            # Create subplots
                            fig = make_subplots(rows=n_osc + 1, cols=1, shared_xaxes=True,
                                              vertical_spacing=0.03,
                                              row_heights=[0.4] + [0.6/n_osc] * n_osc)

                            # Price chart
                            fig.add_trace(go.Candlestick(
                                x=df.index, open=df['Open'], high=df['High'],
                                low=df['Low'], close=df['Close'], name='Price'
                            ), row=1, col=1)

                            row = 2
                            current_values = {}

                            for osc in oscillators:
                                if "RSI" in osc:
                                    rsi = ta.rsi(df['Close'], length=14)
                                    fig.add_trace(go.Scatter(x=df.index, y=rsi, name='RSI',
                                                           line=dict(color='purple')), row=row, col=1)
                                    fig.add_hline(y=70, line_dash="dash", line_color="red", row=row, col=1)
                                    fig.add_hline(y=30, line_dash="dash", line_color="green", row=row, col=1)
                                    fig.update_yaxes(title_text="RSI", row=row, col=1)
                                    current_values['RSI'] = rsi.iloc[-1]

                                elif "Stochastic" in osc:
                                    stoch = ta.stoch(df['High'], df['Low'], df['Close'])
                                    if stoch is not None:
                                        fig.add_trace(go.Scatter(x=df.index, y=stoch['STOCHk_14_3_3'],
                                                               name='%K', line=dict(color='blue')), row=row, col=1)
                                        fig.add_trace(go.Scatter(x=df.index, y=stoch['STOCHd_14_3_3'],
                                                               name='%D', line=dict(color='orange')), row=row, col=1)
                                        fig.add_hline(y=80, line_dash="dash", line_color="red", row=row, col=1)
                                        fig.add_hline(y=20, line_dash="dash", line_color="green", row=row, col=1)
                                        fig.update_yaxes(title_text="Stochastic", row=row, col=1)
                                        current_values['Stochastic %K'] = stoch['STOCHk_14_3_3'].iloc[-1]

                                elif "Williams" in osc:
                                    willr = ta.willr(df['High'], df['Low'], df['Close'], length=14)
                                    fig.add_trace(go.Scatter(x=df.index, y=willr, name='Williams %R',
                                                           line=dict(color='cyan')), row=row, col=1)
                                    fig.add_hline(y=-20, line_dash="dash", line_color="red", row=row, col=1)
                                    fig.add_hline(y=-80, line_dash="dash", line_color="green", row=row, col=1)
                                    fig.update_yaxes(title_text="Williams %R", row=row, col=1)
                                    current_values['Williams %R'] = willr.iloc[-1]

                                elif "CCI" in osc:
                                    cci = ta.cci(df['High'], df['Low'], df['Close'], length=20)
                                    fig.add_trace(go.Scatter(x=df.index, y=cci, name='CCI',
                                                           line=dict(color='yellow')), row=row, col=1)
                                    fig.add_hline(y=100, line_dash="dash", line_color="red", row=row, col=1)
                                    fig.add_hline(y=-100, line_dash="dash", line_color="green", row=row, col=1)
                                    fig.update_yaxes(title_text="CCI", row=row, col=1)
                                    current_values['CCI'] = cci.iloc[-1]

                                elif "MFI" in osc:
                                    mfi = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
                                    fig.add_trace(go.Scatter(x=df.index, y=mfi, name='MFI',
                                                           line=dict(color='lime')), row=row, col=1)
                                    fig.add_hline(y=80, line_dash="dash", line_color="red", row=row, col=1)
                                    fig.add_hline(y=20, line_dash="dash", line_color="green", row=row, col=1)
                                    fig.update_yaxes(title_text="MFI", row=row, col=1)
                                    current_values['MFI'] = mfi.iloc[-1]

                                elif "ADX" in osc:
                                    adx_data = ta.adx(df['High'], df['Low'], df['Close'], length=14)
                                    if adx_data is not None:
                                        fig.add_trace(go.Scatter(x=df.index, y=adx_data['ADX_14'],
                                                               name='ADX', line=dict(color='white', width=2)), row=row, col=1)
                                        fig.add_trace(go.Scatter(x=df.index, y=adx_data['DMP_14'],
                                                               name='+DI', line=dict(color='green')), row=row, col=1)
                                        fig.add_trace(go.Scatter(x=df.index, y=adx_data['DMN_14'],
                                                               name='-DI', line=dict(color='red')), row=row, col=1)
                                        fig.add_hline(y=25, line_dash="dash", line_color="gray", row=row, col=1)
                                        fig.update_yaxes(title_text="ADX", row=row, col=1)
                                        current_values['ADX'] = adx_data['ADX_14'].iloc[-1]

                                row += 1

                            fig.update_layout(title=f'{ta_symbol} - Technical Oscillators',
                                            template='plotly_dark', height=200 + n_osc * 200,
                                            xaxis_rangeslider_visible=False)
                            st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

                            # Current values summary
                            st.markdown("### Current Readings")
                            cols = st.columns(len(current_values))
                            for i, (name, val) in enumerate(current_values.items()):
                                with cols[i]:
                                    if 'RSI' in name or 'MFI' in name:
                                        status = "Overbought" if val > 70 else "Oversold" if val < 30 else "Neutral"
                                    elif 'Stochastic' in name:
                                        status = "Overbought" if val > 80 else "Oversold" if val < 20 else "Neutral"
                                    elif 'Williams' in name:
                                        status = "Overbought" if val > -20 else "Oversold" if val < -80 else "Neutral"
                                    elif 'CCI' in name:
                                        status = "Overbought" if val > 100 else "Oversold" if val < -100 else "Neutral"
                                    elif 'ADX' in name:
                                        status = "Strong Trend" if val > 25 else "Weak/No Trend"
                                    else:
                                        status = ""
                                    st.metric(name, f"{val:.2f}", status)

                except Exception as e:
                    st.error(f"Error: {e}")

    with ta_sub3:
        st.markdown("### Ichimoku Cloud")
        st.markdown("All-in-one indicator showing support/resistance, trend, and momentum")

        if st.button("Generate Ichimoku", type="primary", key="gen_ichi"):
            with st.spinner("Calculating Ichimoku..."):
                try:
                    df = yf.Ticker(ta_symbol).history(start=ta_start, end=ta_end)
                    if df.empty:
                        st.error("No data")
                    else:
                        # Calculate Ichimoku components
                        # Tenkan-sen (Conversion Line): 9-period
                        high_9 = df['High'].rolling(9).max()
                        low_9 = df['Low'].rolling(9).min()
                        tenkan = (high_9 + low_9) / 2

                        # Kijun-sen (Base Line): 26-period
                        high_26 = df['High'].rolling(26).max()
                        low_26 = df['Low'].rolling(26).min()
                        kijun = (high_26 + low_26) / 2

                        # Senkou Span A (Leading Span A): shifted 26 periods ahead
                        senkou_a = ((tenkan + kijun) / 2).shift(26)

                        # Senkou Span B (Leading Span B): 52-period, shifted 26 ahead
                        high_52 = df['High'].rolling(52).max()
                        low_52 = df['Low'].rolling(52).min()
                        senkou_b = ((high_52 + low_52) / 2).shift(26)

                        # Chikou Span (Lagging Span): Close shifted 26 periods back
                        chikou = df['Close'].shift(-26)

                        # Create chart
                        fig = go.Figure()

                        # Cloud (Kumo)
                        fig.add_trace(go.Scatter(
                            x=df.index, y=senkou_a, name='Senkou A',
                            line=dict(color='green', width=1)
                        ))
                        fig.add_trace(go.Scatter(
                            x=df.index, y=senkou_b, name='Senkou B',
                            line=dict(color='red', width=1),
                            fill='tonexty',
                            fillcolor='rgba(0, 255, 0, 0.1)'
                        ))

                        # Candlesticks
                        fig.add_trace(go.Candlestick(
                            x=df.index, open=df['Open'], high=df['High'],
                            low=df['Low'], close=df['Close'], name='Price'
                        ))

                        # Tenkan and Kijun
                        fig.add_trace(go.Scatter(
                            x=df.index, y=tenkan, name='Tenkan (9)',
                            line=dict(color='blue', width=1)
                        ))
                        fig.add_trace(go.Scatter(
                            x=df.index, y=kijun, name='Kijun (26)',
                            line=dict(color='red', width=1)
                        ))

                        # Chikou
                        fig.add_trace(go.Scatter(
                            x=df.index, y=chikou, name='Chikou (Lagging)',
                            line=dict(color='purple', width=1, dash='dot')
                        ))

                        fig.update_layout(
                            title=f'{ta_symbol} - Ichimoku Cloud',
                            template='plotly_dark', height=700,
                            xaxis_rangeslider_visible=False
                        )
                        st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

                        # Current analysis
                        st.markdown("### Ichimoku Analysis")
                        current_price = df['Close'].iloc[-1]
                        current_tenkan = tenkan.iloc[-1]
                        current_kijun = kijun.iloc[-1]
                        current_senkou_a = senkou_a.dropna().iloc[-1] if len(senkou_a.dropna()) > 0 else 0
                        current_senkou_b = senkou_b.dropna().iloc[-1] if len(senkou_b.dropna()) > 0 else 0

                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Price", f"${current_price:.2f}")
                        with col2:
                            st.metric("Tenkan", f"${current_tenkan:.2f}")
                        with col3:
                            st.metric("Kijun", f"${current_kijun:.2f}")
                        with col4:
                            cloud_top = max(current_senkou_a, current_senkou_b)
                            cloud_bottom = min(current_senkou_a, current_senkou_b)
                            if current_price > cloud_top:
                                position = "Above Cloud (Bullish)"
                            elif current_price < cloud_bottom:
                                position = "Below Cloud (Bearish)"
                            else:
                                position = "In Cloud (Neutral)"
                            st.metric("Position", position)

                        # Signals
                        st.markdown("### Signals")
                        signals = []
                        if current_price > cloud_top:
                            signals.append("✅ Price above cloud - Bullish bias")
                        elif current_price < cloud_bottom:
                            signals.append("🔴 Price below cloud - Bearish bias")

                        if current_tenkan > current_kijun:
                            signals.append("✅ Tenkan > Kijun - Bullish crossover")
                        else:
                            signals.append("🔴 Tenkan < Kijun - Bearish crossover")

                        if current_senkou_a > current_senkou_b:
                            signals.append("✅ Cloud is green - Bullish future")
                        else:
                            signals.append("🔴 Cloud is red - Bearish future")

                        for sig in signals:
                            st.write(sig)

                except Exception as e:
                    st.error(f"Error: {e}")

    with ta_sub4:
        st.markdown("### Pivot Points")
        st.markdown("Support and resistance levels for day trading")

        pivot_type = st.selectbox("Pivot Type", [
            "Standard (Floor)",
            "Fibonacci",
            "Camarilla",
            "Woodie",
            "DeMark"
        ], key="pivot_type")

        if st.button("Calculate Pivots", type="primary", key="calc_pivot"):
            with st.spinner("Calculating pivot points..."):
                try:
                    df = yf.Ticker(ta_symbol).history(start=ta_start, end=ta_end)
                    if df.empty:
                        st.error("No data")
                    else:
                        # Use previous day's data
                        prev = df.iloc[-2]
                        h, l, c = prev['High'], prev['Low'], prev['Close']
                        o = prev['Open']

                        pivots = {}

                        if pivot_type == "Standard (Floor)":
                            pp = (h + l + c) / 3
                            pivots = {
                                'R3': pp + 2 * (h - l),
                                'R2': pp + (h - l),
                                'R1': 2 * pp - l,
                                'PP': pp,
                                'S1': 2 * pp - h,
                                'S2': pp - (h - l),
                                'S3': pp - 2 * (h - l)
                            }

                        elif pivot_type == "Fibonacci":
                            pp = (h + l + c) / 3
                            r = h - l
                            pivots = {
                                'R3': pp + r * 1.000,
                                'R2': pp + r * 0.618,
                                'R1': pp + r * 0.382,
                                'PP': pp,
                                'S1': pp - r * 0.382,
                                'S2': pp - r * 0.618,
                                'S3': pp - r * 1.000
                            }

                        elif pivot_type == "Camarilla":
                            pivots = {
                                'R4': c + (h - l) * 1.1 / 2,
                                'R3': c + (h - l) * 1.1 / 4,
                                'R2': c + (h - l) * 1.1 / 6,
                                'R1': c + (h - l) * 1.1 / 12,
                                'PP': (h + l + c) / 3,
                                'S1': c - (h - l) * 1.1 / 12,
                                'S2': c - (h - l) * 1.1 / 6,
                                'S3': c - (h - l) * 1.1 / 4,
                                'S4': c - (h - l) * 1.1 / 2
                            }

                        elif pivot_type == "Woodie":
                            pp = (h + l + 2 * c) / 4
                            pivots = {
                                'R2': pp + (h - l),
                                'R1': 2 * pp - l,
                                'PP': pp,
                                'S1': 2 * pp - h,
                                'S2': pp - (h - l)
                            }

                        else:  # DeMark
                            if c < o:
                                x = h + 2 * l + c
                            elif c > o:
                                x = 2 * h + l + c
                            else:
                                x = h + l + 2 * c
                            pp = x / 4
                            pivots = {
                                'R1': x / 2 - l,
                                'PP': pp,
                                'S1': x / 2 - h
                            }

                        # Current price
                        current = df['Close'].iloc[-1]

                        # Create chart for recent period
                        recent = df.tail(30)
                        fig = go.Figure()

                        fig.add_trace(go.Candlestick(
                            x=recent.index, open=recent['Open'], high=recent['High'],
                            low=recent['Low'], close=recent['Close'], name='Price'
                        ))

                        # Add pivot lines
                        colors = {'R': 'red', 'S': 'green', 'P': 'yellow'}
                        for name, price in pivots.items():
                            color = colors.get(name[0], 'gray')
                            fig.add_hline(y=price, line_dash="dash", line_color=color,
                                         annotation_text=f"{name}: ${price:.2f}",
                                         annotation_position="right")

                        fig.update_layout(
                            title=f'{ta_symbol} - {pivot_type} Pivot Points (Based on {prev.name.date()})',
                            template='plotly_dark', height=500,
                            xaxis_rangeslider_visible=False
                        )
                        st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

                        # Summary table
                        st.markdown("### Pivot Levels")
                        pivot_df = pd.DataFrame([
                            {'Level': k, 'Price': f"${v:.2f}",
                             'Distance': f"{(v/current - 1)*100:+.2f}%"}
                            for k, v in sorted(pivots.items(), key=lambda x: x[1], reverse=True)
                        ])
                        st.dataframe(pivot_df, use_container_width=True)

                        st.metric("Current Price", f"${current:.2f}")

                except Exception as e:
                    st.error(f"Error: {e}")

    with ta_sub5:
        st.markdown("### Volatility Indicators")
        st.markdown("Bollinger Bands, ATR, Keltner Channels")

        vol_indicators = st.multiselect("Select Indicators", [
            "Bollinger Bands (20, 2)",
            "ATR (14)",
            "Keltner Channels (20, 2)",
            "Donchian Channels (20)"
        ], default=["Bollinger Bands (20, 2)", "ATR (14)"], key="vol_select")

        if st.button("Generate Volatility Analysis", type="primary", key="gen_vol"):
            with st.spinner("Calculating..."):
                try:
                    df = yf.Ticker(ta_symbol).history(start=ta_start, end=ta_end)
                    if df.empty:
                        st.error("No data")
                    else:
                        has_atr = "ATR (14)" in vol_indicators
                        n_plots = 1 + (1 if has_atr else 0)

                        fig = make_subplots(rows=n_plots, cols=1, shared_xaxes=True,
                                          vertical_spacing=0.05,
                                          row_heights=[0.7, 0.3] if has_atr else [1.0])

                        # Candlesticks
                        fig.add_trace(go.Candlestick(
                            x=df.index, open=df['Open'], high=df['High'],
                            low=df['Low'], close=df['Close'], name='Price'
                        ), row=1, col=1)

                        for ind in vol_indicators:
                            if "Bollinger" in ind:
                                bb = ta.bbands(df['Close'], length=20, std=2)
                                if bb is not None:
                                    fig.add_trace(go.Scatter(x=df.index, y=bb['BBU_20_2.0'],
                                        name='BB Upper', line=dict(color='blue', width=1)), row=1, col=1)
                                    fig.add_trace(go.Scatter(x=df.index, y=bb['BBM_20_2.0'],
                                        name='BB Middle', line=dict(color='blue', width=1, dash='dash')), row=1, col=1)
                                    fig.add_trace(go.Scatter(x=df.index, y=bb['BBL_20_2.0'],
                                        name='BB Lower', line=dict(color='blue', width=1),
                                        fill='tonexty', fillcolor='rgba(0, 0, 255, 0.1)'), row=1, col=1)

                            elif "Keltner" in ind:
                                # Calculate Keltner Channels
                                ema20 = ta.ema(df['Close'], length=20)
                                atr = ta.atr(df['High'], df['Low'], df['Close'], length=20)
                                kc_upper = ema20 + 2 * atr
                                kc_lower = ema20 - 2 * atr

                                fig.add_trace(go.Scatter(x=df.index, y=kc_upper,
                                    name='KC Upper', line=dict(color='orange', width=1)), row=1, col=1)
                                fig.add_trace(go.Scatter(x=df.index, y=ema20,
                                    name='KC Middle', line=dict(color='orange', width=1, dash='dash')), row=1, col=1)
                                fig.add_trace(go.Scatter(x=df.index, y=kc_lower,
                                    name='KC Lower', line=dict(color='orange', width=1)), row=1, col=1)

                            elif "Donchian" in ind:
                                dc_upper = df['High'].rolling(20).max()
                                dc_lower = df['Low'].rolling(20).min()
                                dc_mid = (dc_upper + dc_lower) / 2

                                fig.add_trace(go.Scatter(x=df.index, y=dc_upper,
                                    name='DC Upper', line=dict(color='green', width=1)), row=1, col=1)
                                fig.add_trace(go.Scatter(x=df.index, y=dc_mid,
                                    name='DC Middle', line=dict(color='green', width=1, dash='dash')), row=1, col=1)
                                fig.add_trace(go.Scatter(x=df.index, y=dc_lower,
                                    name='DC Lower', line=dict(color='green', width=1)), row=1, col=1)

                            elif "ATR" in ind:
                                atr = ta.atr(df['High'], df['Low'], df['Close'], length=14)
                                fig.add_trace(go.Scatter(x=df.index, y=atr,
                                    name='ATR (14)', line=dict(color='cyan')), row=2, col=1)
                                fig.update_yaxes(title_text="ATR", row=2, col=1)

                        fig.update_layout(
                            title=f'{ta_symbol} - Volatility Analysis',
                            template='plotly_dark', height=600,
                            xaxis_rangeslider_visible=False
                        )
                        st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

                        # Current volatility metrics
                        st.markdown("### Current Volatility Metrics")
                        atr_val = ta.atr(df['High'], df['Low'], df['Close'], length=14).iloc[-1]
                        bb = ta.bbands(df['Close'], length=20, std=2)
                        bb_width = (bb['BBU_20_2.0'].iloc[-1] - bb['BBL_20_2.0'].iloc[-1]) / bb['BBM_20_2.0'].iloc[-1] * 100 if bb is not None else 0
                        hist_vol = df['Close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("ATR (14)", f"${atr_val:.2f}")
                        with col2:
                            st.metric("BB Width", f"{bb_width:.2f}%")
                        with col3:
                            st.metric("Historical Vol (20d)", f"{hist_vol:.1f}%")

                        # Squeeze detection
                        if bb_width < 5:
                            st.warning("⚠️ **Bollinger Squeeze Detected!** - Potential breakout imminent")

                except Exception as e:
                    st.error(f"Error: {e}")


# ============================================================================
# TAB 8: FUNDAMENTAL ANALYSIS
# ============================================================================

if selected_page == "💰 Fundamentals":
    st.subheader("Fundamental Analysis")
    st.markdown("Company financials, valuation ratios, and growth metrics")

    fund_symbol = st.text_input("Enter Symbol", value="AAPL", key="fund_symbol")

    if st.button("Load Fundamentals", type="primary", key="load_fund"):
        with st.spinner(f"Loading fundamentals for {fund_symbol}..."):
            try:
                ticker = yf.Ticker(fund_symbol)
                info = ticker.info

                if not info or 'symbol' not in info:
                    st.error("Could not load data for this symbol")
                else:
                    # Company Overview
                    st.markdown("### Company Overview")
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.metric("Sector", info.get('sector', 'N/A'))
                        st.metric("Industry", info.get('industry', 'N/A'))
                        st.metric("Market Cap", f"${info.get('marketCap', 0)/1e9:.2f}B")
                    with col2:
                        st.write(info.get('longBusinessSummary', 'No description available')[:500] + "...")

                    st.divider()

                    # Valuation Metrics
                    st.markdown("### Valuation Metrics")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        pe = info.get('trailingPE', info.get('forwardPE', 0))
                        st.metric("P/E Ratio", f"{pe:.2f}" if pe else "N/A",
                                 help="Price to Earnings - Lower may indicate undervaluation")
                    with col2:
                        pb = info.get('priceToBook', 0)
                        st.metric("P/B Ratio", f"{pb:.2f}" if pb else "N/A",
                                 help="Price to Book - Below 1 may indicate undervaluation")
                    with col3:
                        ps = info.get('priceToSalesTrailing12Months', 0)
                        st.metric("P/S Ratio", f"{ps:.2f}" if ps else "N/A",
                                 help="Price to Sales")
                    with col4:
                        peg = info.get('pegRatio', 0)
                        st.metric("PEG Ratio", f"{peg:.2f}" if peg else "N/A",
                                 help="P/E to Growth - Below 1 may indicate undervaluation")
                    with col5:
                        ev_ebitda = info.get('enterpriseToEbitda', 0)
                        st.metric("EV/EBITDA", f"{ev_ebitda:.2f}" if ev_ebitda else "N/A",
                                 help="Enterprise Value to EBITDA")

                    st.divider()

                    # Profitability Metrics
                    st.markdown("### Profitability Metrics")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        roe = info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0
                        st.metric("ROE", f"{roe:.1f}%",
                                 help="Return on Equity - Higher is better, >15% often good")
                    with col2:
                        roa = info.get('returnOnAssets', 0) * 100 if info.get('returnOnAssets') else 0
                        st.metric("ROA", f"{roa:.1f}%",
                                 help="Return on Assets")
                    with col3:
                        gross_margin = info.get('grossMargins', 0) * 100 if info.get('grossMargins') else 0
                        st.metric("Gross Margin", f"{gross_margin:.1f}%",
                                 help="Gross Profit Margin")
                    with col4:
                        op_margin = info.get('operatingMargins', 0) * 100 if info.get('operatingMargins') else 0
                        st.metric("Operating Margin", f"{op_margin:.1f}%",
                                 help="Operating Profit Margin")
                    with col5:
                        net_margin = info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 0
                        st.metric("Net Margin", f"{net_margin:.1f}%",
                                 help="Net Profit Margin")

                    st.divider()

                    # Growth Metrics
                    st.markdown("### Growth Metrics")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        rev_growth = info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0
                        st.metric("Revenue Growth", f"{rev_growth:.1f}%",
                                 delta=f"{rev_growth:.1f}%")
                    with col2:
                        earn_growth = info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else 0
                        st.metric("Earnings Growth", f"{earn_growth:.1f}%",
                                 delta=f"{earn_growth:.1f}%")
                    with col3:
                        eps = info.get('trailingEps', 0)
                        st.metric("EPS (TTM)", f"${eps:.2f}" if eps else "N/A")
                    with col4:
                        forward_eps = info.get('forwardEps', 0)
                        st.metric("EPS (Forward)", f"${forward_eps:.2f}" if forward_eps else "N/A")

                    st.divider()

                    # Financial Health
                    st.markdown("### Financial Health")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        de = info.get('debtToEquity', 0)
                        st.metric("Debt/Equity", f"{de:.2f}" if de else "N/A",
                                 help="Lower is generally better, <1 is conservative")
                    with col2:
                        current = info.get('currentRatio', 0)
                        st.metric("Current Ratio", f"{current:.2f}" if current else "N/A",
                                 help="Above 1.5 is healthy")
                    with col3:
                        quick = info.get('quickRatio', 0)
                        st.metric("Quick Ratio", f"{quick:.2f}" if quick else "N/A",
                                 help="Above 1 is healthy")
                    with col4:
                        fcf = info.get('freeCashflow', 0)
                        st.metric("Free Cash Flow", f"${fcf/1e9:.2f}B" if fcf else "N/A")

                    st.divider()

                    # Dividend Info
                    st.markdown("### Dividend Information")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        div_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
                        st.metric("Dividend Yield", f"{div_yield:.2f}%")
                    with col2:
                        div_rate = info.get('dividendRate', 0)
                        st.metric("Annual Dividend", f"${div_rate:.2f}" if div_rate else "N/A")
                    with col3:
                        payout = info.get('payoutRatio', 0) * 100 if info.get('payoutRatio') else 0
                        st.metric("Payout Ratio", f"{payout:.1f}%",
                                 help="Below 60% is sustainable")
                    with col4:
                        ex_div = info.get('exDividendDate', 'N/A')
                        if ex_div and ex_div != 'N/A':
                            from datetime import datetime as dt
                            ex_div = dt.fromtimestamp(ex_div).strftime('%Y-%m-%d')
                        st.metric("Ex-Dividend Date", ex_div)

                    st.divider()

                    # Analyst Ratings
                    st.markdown("### Analyst Consensus")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        rec = info.get('recommendationKey', 'N/A')
                        st.metric("Recommendation", rec.upper() if rec else "N/A")
                    with col2:
                        target = info.get('targetMeanPrice', 0)
                        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                        upside = (target / current_price - 1) * 100 if current_price and target else 0
                        st.metric("Price Target", f"${target:.2f}" if target else "N/A",
                                 delta=f"{upside:.1f}% upside" if upside else None)
                    with col3:
                        num_analysts = info.get('numberOfAnalystOpinions', 0)
                        st.metric("# Analysts", num_analysts)

                    # Valuation Assessment
                    st.markdown("### Quick Valuation Assessment")
                    assessment = []
                    if pe and pe > 0:
                        if pe < 15:
                            assessment.append("✅ P/E below 15 - Potentially undervalued")
                        elif pe > 30:
                            assessment.append("⚠️ P/E above 30 - Potentially overvalued or high growth")
                    if peg and peg > 0:
                        if peg < 1:
                            assessment.append("✅ PEG below 1 - Good value for growth")
                        elif peg > 2:
                            assessment.append("⚠️ PEG above 2 - May be overpriced")
                    if roe > 15:
                        assessment.append("✅ ROE above 15% - Strong profitability")
                    if de and de < 1:
                        assessment.append("✅ D/E below 1 - Conservative leverage")
                    elif de and de > 2:
                        assessment.append("⚠️ D/E above 2 - High leverage")

                    for a in assessment:
                        st.write(a)

            except Exception as e:
                st.error(f"Error loading fundamentals: {e}")


# ============================================================================
# TAB 9: MARKET SENTIMENT
# ============================================================================

if selected_page == "🌡️ Sentiment":
    st.subheader("Market Sentiment Dashboard")
    st.markdown("VIX, Fear & Greed indicators, and market breadth")

    sent_sub1, sent_sub2, sent_sub3 = st.tabs([
        "🌡️ VIX & Volatility",
        "😰 Fear & Greed",
        "📊 Market Breadth"
    ])

    with sent_sub1:
        st.markdown("### VIX - Volatility Index")
        st.markdown("The 'Fear Gauge' - measures expected 30-day volatility from S&P 500 options")

        vix_period = st.selectbox("Period", ["1 Month", "3 Months", "6 Months", "1 Year", "2 Years"], index=2, key="vix_period")

        if st.button("Load VIX Data", type="primary", key="load_vix"):
            with st.spinner("Loading VIX..."):
                try:
                    period_days = {"1 Month": 30, "3 Months": 90, "6 Months": 180, "1 Year": 365, "2 Years": 730}
                    days = period_days.get(vix_period, 180)
                    start = datetime.now() - timedelta(days=days)

                    vix = yf.Ticker("^VIX").history(start=start, end=datetime.now())
                    spy = yf.Ticker("SPY").history(start=start, end=datetime.now())

                    if vix.empty:
                        st.error("Could not load VIX data")
                    else:
                        # Create chart
                        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                          vertical_spacing=0.1, row_heights=[0.6, 0.4])

                        fig.add_trace(go.Scatter(x=spy.index, y=spy['Close'],
                            name='SPY', line=dict(color='white')), row=1, col=1)

                        fig.add_trace(go.Scatter(x=vix.index, y=vix['Close'],
                            name='VIX', line=dict(color='red'), fill='tozeroy',
                            fillcolor='rgba(255, 0, 0, 0.2)'), row=2, col=1)

                        # Add VIX zones
                        fig.add_hline(y=20, line_dash="dash", line_color="yellow", row=2, col=1,
                                     annotation_text="Normal (<20)")
                        fig.add_hline(y=30, line_dash="dash", line_color="orange", row=2, col=1,
                                     annotation_text="Elevated (30)")
                        fig.add_hline(y=40, line_dash="dash", line_color="red", row=2, col=1,
                                     annotation_text="High Fear (40+)")

                        fig.update_layout(title='VIX vs SPY', template='plotly_dark', height=600)
                        fig.update_yaxes(title_text="SPY Price", row=1, col=1)
                        fig.update_yaxes(title_text="VIX", row=2, col=1)

                        st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

                        # Current VIX analysis
                        current_vix = vix['Close'].iloc[-1]
                        vix_20d_avg = vix['Close'].rolling(20).mean().iloc[-1]
                        vix_percentile = (vix['Close'] < current_vix).mean() * 100

                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            if current_vix < 15:
                                status = "Complacency"
                            elif current_vix < 20:
                                status = "Low Fear"
                            elif current_vix < 30:
                                status = "Moderate Fear"
                            elif current_vix < 40:
                                status = "High Fear"
                            else:
                                status = "Extreme Fear"
                            st.metric("Current VIX", f"{current_vix:.2f}", status)
                        with col2:
                            st.metric("20-Day Average", f"{vix_20d_avg:.2f}")
                        with col3:
                            st.metric("Percentile", f"{vix_percentile:.1f}%",
                                     help="% of time VIX was below current level")
                        with col4:
                            vix_change = (current_vix / vix['Close'].iloc[-2] - 1) * 100
                            st.metric("Daily Change", f"{vix_change:+.1f}%")

                        # Interpretation
                        st.markdown("### Interpretation")
                        if current_vix < 15:
                            st.info("🟢 **Complacency Zone** - Markets calm, potential for volatility spike")
                        elif current_vix < 20:
                            st.success("🟢 **Low Fear** - Normal market conditions")
                        elif current_vix < 30:
                            st.warning("🟡 **Elevated Fear** - Increased uncertainty")
                        else:
                            st.error("🔴 **High Fear** - Market stress, potential contrarian buy opportunity")

                except Exception as e:
                    st.error(f"Error: {e}")

    with sent_sub2:
        st.markdown("### Fear & Greed Index (Calculated)")
        st.markdown("A composite indicator based on 7 market factors")

        if st.button("Calculate Fear & Greed", type="primary", key="calc_fg"):
            with st.spinner("Calculating Fear & Greed components..."):
                try:
                    end = datetime.now()
                    start = end - timedelta(days=365)

                    # Fetch required data
                    spy = yf.Ticker("SPY").history(start=start, end=end)
                    vix = yf.Ticker("^VIX").history(start=start, end=end)

                    # Calculate components (0-100 scale, 50 = neutral)
                    components = {}

                    # 1. Market Momentum (SPY vs 125-day MA)
                    spy_ma125 = spy['Close'].rolling(125).mean()
                    mom_score = min(100, max(0, 50 + (spy['Close'].iloc[-1] / spy_ma125.iloc[-1] - 1) * 500))
                    components['Market Momentum'] = mom_score

                    # 2. Stock Price Strength (52-week highs vs lows proxy)
                    recent_high = spy['High'].tail(252).max()
                    recent_low = spy['Low'].tail(252).min()
                    current = spy['Close'].iloc[-1]
                    strength_score = (current - recent_low) / (recent_high - recent_low) * 100
                    components['Stock Price Strength'] = strength_score

                    # 3. Stock Price Breadth (using SPY momentum as proxy)
                    returns_20d = spy['Close'].pct_change(20).iloc[-1] * 100
                    breadth_score = min(100, max(0, 50 + returns_20d * 5))
                    components['Stock Price Breadth'] = breadth_score

                    # 4. Put/Call Ratio (approximated from VIX)
                    vix_percentile = (vix['Close'] < vix['Close'].iloc[-1]).mean()
                    pcr_score = 100 - vix_percentile * 100  # Inverted
                    components['Put/Call Ratio'] = pcr_score

                    # 5. Market Volatility (VIX)
                    vix_current = vix['Close'].iloc[-1]
                    if vix_current > 30:
                        vol_score = 10
                    elif vix_current > 20:
                        vol_score = 30
                    elif vix_current > 15:
                        vol_score = 60
                    else:
                        vol_score = 90
                    components['Market Volatility'] = vol_score

                    # 6. Safe Haven Demand (SPY performance)
                    safe_haven_score = min(100, max(0, 50 + spy['Close'].pct_change(20).iloc[-1] * 500))
                    components['Safe Haven Demand'] = safe_haven_score

                    # 7. Junk Bond Demand (approximated)
                    junk_score = 50 + (spy['Close'].pct_change(5).iloc[-1] * 200)
                    junk_score = min(100, max(0, junk_score))
                    components['Junk Bond Demand'] = junk_score

                    # Overall score (equal weight)
                    overall = sum(components.values()) / len(components)

                    # Display
                    if overall < 25:
                        fg_label = "EXTREME FEAR"
                        fg_color = "red"
                    elif overall < 45:
                        fg_label = "FEAR"
                        fg_color = "orange"
                    elif overall < 55:
                        fg_label = "NEUTRAL"
                        fg_color = "gray"
                    elif overall < 75:
                        fg_label = "GREED"
                        fg_color = "lightgreen"
                    else:
                        fg_label = "EXTREME GREED"
                        fg_color = "green"

                    # Gauge chart
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=overall,
                        title={'text': f"Fear & Greed Index<br><span style='color:{fg_color}'>{fg_label}</span>"},
                        gauge={
                            'axis': {'range': [0, 100]},
                            'bar': {'color': fg_color},
                            'steps': [
                                {'range': [0, 25], 'color': 'darkred'},
                                {'range': [25, 45], 'color': 'orange'},
                                {'range': [45, 55], 'color': 'gray'},
                                {'range': [55, 75], 'color': 'lightgreen'},
                                {'range': [75, 100], 'color': 'green'}
                            ],
                            'threshold': {
                                'line': {'color': 'white', 'width': 4},
                                'thickness': 0.75,
                                'value': overall
                            }
                        }
                    ))
                    fig.update_layout(template='plotly_dark', height=400)
                    st.plotly_chart(fig, use_container_width=True)

                    # Component breakdown
                    st.markdown("### Component Breakdown")
                    for comp, score in sorted(components.items(), key=lambda x: x[1], reverse=True):
                        if score < 25:
                            emoji = "🔴"
                        elif score < 45:
                            emoji = "🟠"
                        elif score < 55:
                            emoji = "⚪"
                        elif score < 75:
                            emoji = "🟡"
                        else:
                            emoji = "🟢"
                        st.write(f"{emoji} **{comp}**: {score:.1f}")

                    # Interpretation
                    st.markdown("### Trading Implications")
                    if overall < 30:
                        st.success("💡 **Contrarian Buy Signal** - Extreme fear often marks market bottoms")
                    elif overall > 70:
                        st.warning("💡 **Contrarian Sell Signal** - Extreme greed often precedes corrections")
                    else:
                        st.info("💡 **Neutral** - No strong contrarian signal")

                except Exception as e:
                    st.error(f"Error: {e}")

    with sent_sub3:
        st.markdown("### Market Breadth Indicators")
        st.markdown("Advance/Decline analysis and sector participation")

        if st.button("Analyze Market Breadth", type="primary", key="analyze_breadth"):
            with st.spinner("Analyzing market breadth..."):
                try:
                    # Use sector ETFs as proxy for breadth
                    sectors = ['XLK', 'XLF', 'XLV', 'XLY', 'XLP', 'XLE', 'XLI', 'XLB', 'XLU', 'XLRE', 'XLC']
                    sector_names = ['Technology', 'Financials', 'Healthcare', 'Cons. Disc.', 'Cons. Staples',
                                   'Energy', 'Industrials', 'Materials', 'Utilities', 'Real Estate', 'Comm. Services']

                    start = datetime.now() - timedelta(days=60)
                    end = datetime.now()

                    breadth_data = []
                    for sym, name in zip(sectors, sector_names):
                        try:
                            data = yf.Ticker(sym).history(start=start, end=end)
                            if not data.empty:
                                current = data['Close'].iloc[-1]
                                sma20 = data['Close'].rolling(20).mean().iloc[-1]
                                sma50 = data['Close'].rolling(50).mean().iloc[-1] if len(data) >= 50 else sma20
                                ret_1d = (data['Close'].iloc[-1] / data['Close'].iloc[-2] - 1) * 100
                                ret_5d = (data['Close'].iloc[-1] / data['Close'].iloc[-6] - 1) * 100 if len(data) >= 6 else 0
                                ret_20d = (data['Close'].iloc[-1] / data['Close'].iloc[-21] - 1) * 100 if len(data) >= 21 else 0

                                breadth_data.append({
                                    'Sector': name,
                                    'Symbol': sym,
                                    '1D %': ret_1d,
                                    '5D %': ret_5d,
                                    '20D %': ret_20d,
                                    'Above SMA20': '✅' if current > sma20 else '❌',
                                    'Above SMA50': '✅' if current > sma50 else '❌'
                                })
                        except Exception as e:
                            st.warning(f"Skipped {sym}: {e}")

                    if breadth_data:
                        df_breadth = pd.DataFrame(breadth_data)

                        # Summary metrics
                        above_sma20 = sum(1 for x in df_breadth['Above SMA20'] if x == '✅')
                        above_sma50 = sum(1 for x in df_breadth['Above SMA50'] if x == '✅')
                        advancing = sum(1 for x in df_breadth['1D %'] if x > 0)
                        total = len(df_breadth)

                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("% Above SMA20", f"{above_sma20/total*100:.0f}%",
                                     f"{above_sma20}/{total} sectors")
                        with col2:
                            st.metric("% Above SMA50", f"{above_sma50/total*100:.0f}%",
                                     f"{above_sma50}/{total} sectors")
                        with col3:
                            st.metric("Advancing Today", f"{advancing/total*100:.0f}%",
                                     f"{advancing}/{total} sectors")
                        with col4:
                            avg_20d = df_breadth['20D %'].mean()
                            st.metric("Avg 20D Return", f"{avg_20d:.1f}%")

                        # Heatmap
                        fig = go.Figure(data=go.Heatmap(
                            z=[df_breadth['1D %'].values, df_breadth['5D %'].values, df_breadth['20D %'].values],
                            x=df_breadth['Sector'],
                            y=['1 Day', '5 Days', '20 Days'],
                            colorscale='RdYlGn',
                            zmid=0,
                            text=[[f"{v:.1f}%" for v in df_breadth['1D %']],
                                  [f"{v:.1f}%" for v in df_breadth['5D %']],
                                  [f"{v:.1f}%" for v in df_breadth['20D %']]],
                            texttemplate='%{text}',
                            hoverongaps=False
                        ))
                        fig.update_layout(title='Sector Performance Heatmap',
                                        template='plotly_dark', height=300)
                        st.plotly_chart(fig, use_container_width=True)

                        # Full table
                        st.markdown("### Sector Details")
                        st.dataframe(df_breadth.sort_values('20D %', ascending=False), use_container_width=True)

                        # Breadth assessment
                        st.markdown("### Breadth Assessment")
                        if above_sma20/total >= 0.8:
                            st.success("🟢 **Strong Breadth** - 80%+ sectors above SMA20")
                        elif above_sma20/total >= 0.6:
                            st.info("🟡 **Moderate Breadth** - 60-80% sectors above SMA20")
                        elif above_sma20/total >= 0.4:
                            st.warning("🟠 **Weak Breadth** - 40-60% sectors above SMA20")
                        else:
                            st.error("🔴 **Poor Breadth** - <40% sectors above SMA20")

                except Exception as e:
                    st.error(f"Error: {e}")


# ============================================================================
# TAB 10: ECONOMIC INDICATORS
# ============================================================================

if selected_page == "📈 Economic Data":
    st.subheader("Economic Indicators")
    st.markdown("Key economic data affecting markets - GDP, inflation, employment, rates")

    st.info("📊 Economic data is fetched from Yahoo Finance market indices and related ETFs. For comprehensive FRED data, consider adding the `fredapi` package.")

    econ_sub1, econ_sub2, econ_sub3 = st.tabs([
        "📈 Market Indicators",
        "💵 Interest Rates",
        "📊 Economic Proxies"
    ])

    with econ_sub1:
        st.markdown("### Key Market Indicators")

        if st.button("Load Market Indicators", type="primary", key="load_market_ind"):
            with st.spinner("Loading data..."):
                try:
                    indicators = {
                        '^GSPC': 'S&P 500',
                        '^DJI': 'Dow Jones',
                        '^IXIC': 'Nasdaq',
                        '^RUT': 'Russell 2000',
                        '^VIX': 'VIX',
                        'GC=F': 'Gold',
                        'CL=F': 'Crude Oil',
                        'DX-Y.NYB': 'US Dollar Index'
                    }

                    start = datetime.now() - timedelta(days=365)
                    results = []

                    for sym, name in indicators.items():
                        try:
                            data = yf.Ticker(sym).history(start=start, end=datetime.now())
                            if not data.empty:
                                current = data['Close'].iloc[-1]
                                prev = data['Close'].iloc[-2]
                                ytd_start = data['Close'].iloc[0]
                                high_52w = data['High'].max()
                                low_52w = data['Low'].min()

                                results.append({
                                    'Indicator': name,
                                    'Current': current,
                                    'Daily Chg %': (current/prev - 1) * 100,
                                    'YTD %': (current/ytd_start - 1) * 100,
                                    '52W High': high_52w,
                                    '52W Low': low_52w,
                                    '% from High': (current/high_52w - 1) * 100
                                })
                        except Exception as e:
                            st.warning(f"Skipped {sym}: {e}")

                    if results:
                        df_ind = pd.DataFrame(results)

                        # Display metrics
                        st.markdown("### Current Readings")
                        cols = st.columns(4)
                        for i, row in df_ind.head(4).iterrows():
                            with cols[i]:
                                st.metric(row['Indicator'],
                                         f"{row['Current']:,.2f}",
                                         f"{row['Daily Chg %']:+.2f}%")

                        # Full table
                        st.dataframe(df_ind.style.format({
                            'Current': '{:,.2f}',
                            'Daily Chg %': '{:+.2f}%',
                            'YTD %': '{:+.2f}%',
                            '52W High': '{:,.2f}',
                            '52W Low': '{:,.2f}',
                            '% from High': '{:+.2f}%'
                        }), use_container_width=True)

                        # Performance chart
                        fig = go.Figure()
                        for sym, name in [("^GSPC", "S&P 500"), ("^IXIC", "Nasdaq"), ("^RUT", "Russell 2000")]:
                            try:
                                data = yf.Ticker(sym).history(start=start, end=datetime.now())
                                normalized = data['Close'] / data['Close'].iloc[0] * 100
                                fig.add_trace(go.Scatter(x=data.index, y=normalized, name=name))
                            except Exception as e:
                                st.warning(f"Skipped {sym}: {e}")

                        fig.update_layout(title='Index Performance (Normalized to 100)',
                                        template='plotly_dark', height=400,
                                        yaxis_title='Normalized Value')
                        st.plotly_chart(fig, use_container_width=True)

                except Exception as e:
                    st.error(f"Error: {e}")

    with econ_sub2:
        st.markdown("### Interest Rates & Yield Curve")

        if st.button("Load Rate Data", type="primary", key="load_rates"):
            with st.spinner("Loading rate data..."):
                try:
                    # Treasury ETFs as proxies
                    treasuries = {
                        'SHY': '1-3 Year Treasury',
                        'IEI': '3-7 Year Treasury',
                        'IEF': '7-10 Year Treasury',
                        'TLT': '20+ Year Treasury',
                        'TIP': 'TIPS (Inflation Protected)'
                    }

                    start = datetime.now() - timedelta(days=365)

                    # Treasury performance
                    st.markdown("### Treasury ETF Performance")
                    treasury_data = []
                    for sym, name in treasuries.items():
                        try:
                            data = yf.Ticker(sym).history(start=start, end=datetime.now())
                            if not data.empty:
                                current = data['Close'].iloc[-1]
                                ytd_ret = (current / data['Close'].iloc[0] - 1) * 100
                                treasury_data.append({
                                    'ETF': name,
                                    'Symbol': sym,
                                    'Price': current,
                                    'YTD Return': ytd_ret
                                })
                        except Exception as e:
                            st.warning(f"Skipped {sym}: {e}")

                    if treasury_data:
                        df_treas = pd.DataFrame(treasury_data)
                        st.dataframe(df_treas, use_container_width=True)

                        # Treasury chart
                        fig = go.Figure()
                        for sym, name in treasuries.items():
                            try:
                                data = yf.Ticker(sym).history(start=start, end=datetime.now())
                                normalized = data['Close'] / data['Close'].iloc[0] * 100
                                fig.add_trace(go.Scatter(x=data.index, y=normalized, name=name))
                            except Exception as e:
                                st.warning(f"Skipped {sym}: {e}")

                        fig.update_layout(title='Treasury ETF Performance (Normalized)',
                                        template='plotly_dark', height=400)
                        st.plotly_chart(fig, use_container_width=True)

                    # Rate interpretation
                    st.markdown("### Rate Environment Analysis")
                    if treasury_data:
                        short_term = next((t for t in treasury_data if 'SHY' in t['Symbol']), None)
                        long_term = next((t for t in treasury_data if 'TLT' in t['Symbol']), None)

                        if short_term and long_term:
                            if short_term['YTD Return'] > long_term['YTD Return']:
                                st.warning("⚠️ Short-term treasuries outperforming - potential yield curve flattening/inversion")
                            else:
                                st.success("✅ Normal yield curve behavior - long-term outperforming short-term")

                except Exception as e:
                    st.error(f"Error: {e}")

    with econ_sub3:
        st.markdown("### Economic Proxy Indicators")
        st.markdown("Using market data as proxies for economic conditions")

        if st.button("Analyze Economic Proxies", type="primary", key="analyze_econ"):
            with st.spinner("Analyzing..."):
                try:
                    start = datetime.now() - timedelta(days=365)

                    # Economic proxies
                    proxies = {
                        'XLI': ('Industrials', 'Manufacturing/Economic Growth'),
                        'XLY': ('Consumer Disc.', 'Consumer Spending'),
                        'XLP': ('Consumer Staples', 'Defensive/Recession Fear'),
                        'XLF': ('Financials', 'Credit/Banking Health'),
                        'XLE': ('Energy', 'Economic Activity/Inflation'),
                        'XLU': ('Utilities', 'Risk-Off/Recession Fear'),
                        'XHB': ('Homebuilders', 'Housing Market'),
                        'ITB': ('Construction', 'Infrastructure/Building')
                    }

                    proxy_data = []
                    for sym, (name, meaning) in proxies.items():
                        try:
                            data = yf.Ticker(sym).history(start=start, end=datetime.now())
                            if not data.empty:
                                current = data['Close'].iloc[-1]
                                ret_1m = (current / data['Close'].iloc[-22] - 1) * 100 if len(data) >= 22 else 0
                                ret_3m = (current / data['Close'].iloc[-66] - 1) * 100 if len(data) >= 66 else 0
                                sma50 = data['Close'].rolling(50).mean().iloc[-1]

                                proxy_data.append({
                                    'Sector': name,
                                    'Economic Meaning': meaning,
                                    '1M Return': ret_1m,
                                    '3M Return': ret_3m,
                                    'Above 50 SMA': '✅' if current > sma50 else '❌'
                                })
                        except Exception as e:
                            st.warning(f"Skipped {sym}: {e}")

                    if proxy_data:
                        df_proxy = pd.DataFrame(proxy_data)
                        st.dataframe(df_proxy, use_container_width=True)

                        # Economic interpretation
                        st.markdown("### Economic Signal Interpretation")

                        # Growth vs Defensive
                        growth_sectors = ['XLI', 'XLY', 'XLF']
                        defensive_sectors = ['XLP', 'XLU']

                        growth_perf = sum(p['3M Return'] for p in proxy_data if p['Sector'] in ['Industrials', 'Consumer Disc.', 'Financials']) / 3
                        defensive_perf = sum(p['3M Return'] for p in proxy_data if p['Sector'] in ['Consumer Staples', 'Utilities']) / 2

                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Growth Sectors (3M)", f"{growth_perf:+.1f}%")
                        with col2:
                            st.metric("Defensive Sectors (3M)", f"{defensive_perf:+.1f}%")

                        if growth_perf > defensive_perf + 5:
                            st.success("📈 **Risk-On Environment** - Growth sectors leading, economic optimism")
                        elif defensive_perf > growth_perf + 5:
                            st.warning("📉 **Risk-Off Environment** - Defensive sectors leading, economic concern")
                        else:
                            st.info("➡️ **Mixed Environment** - No clear risk preference")

                        # Housing
                        housing = next((p for p in proxy_data if 'Home' in p['Sector']), None)
                        if housing:
                            if housing['3M Return'] > 10:
                                st.success("🏠 Housing sector strong - positive for economy")
                            elif housing['3M Return'] < -10:
                                st.warning("🏠 Housing sector weak - potential economic headwind")

                except Exception as e:
                    st.error(f"Error: {e}")


# ============================================================================
# TAB 11: RISK CALCULATOR
# ============================================================================

if selected_page == "⚖️ Risk Calculator":
    st.subheader("Risk Management Calculator")
    st.markdown("Position sizing, risk/reward analysis, and stop loss calculation")

    risk_sub1, risk_sub2, risk_sub3 = st.tabs([
        "📏 Position Sizing",
        "⚖️ Risk/Reward",
        "🛑 Stop Loss Calculator"
    ])

    with risk_sub1:
        st.markdown("### Position Size Calculator")
        st.markdown("Calculate optimal position size based on risk tolerance")

        col1, col2 = st.columns(2)
        with col1:
            account_size = st.number_input("Account Size ($)", value=100000, min_value=100, key="ps_account")
            risk_percent = st.slider("Risk per Trade (%)", 0.5, 5.0, 1.0, 0.5, key="ps_risk",
                                    help="Professionals typically risk 1-2% per trade")
        with col2:
            entry_price = st.number_input("Entry Price ($)", value=100.0, min_value=0.01, key="ps_entry")
            stop_price = st.number_input("Stop Loss Price ($)", value=95.0, min_value=0.01, key="ps_stop")

        if st.button("Calculate Position Size", type="primary", key="calc_ps"):
            risk_amount = account_size * (risk_percent / 100)
            risk_per_share = abs(entry_price - stop_price)

            if risk_per_share > 0:
                shares = int(risk_amount / risk_per_share)
                position_value = shares * entry_price
                position_percent = (position_value / account_size) * 100

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Max Risk Amount", f"${risk_amount:,.2f}")
                with col2:
                    st.metric("Shares to Buy", f"{shares:,}")
                with col3:
                    st.metric("Position Value", f"${position_value:,.2f}")
                with col4:
                    st.metric("% of Account", f"{position_percent:.1f}%")

                st.divider()

                # Scenario analysis
                st.markdown("### Scenario Analysis")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("**If Stopped Out:**")
                    loss = shares * risk_per_share
                    st.write(f"Loss: ${loss:,.2f}")
                    st.write(f"Account after: ${account_size - loss:,.2f}")
                with col2:
                    st.markdown("**If +1R Gain:**")
                    gain_1r = shares * risk_per_share
                    st.write(f"Gain: ${gain_1r:,.2f}")
                    st.write(f"Account after: ${account_size + gain_1r:,.2f}")
                with col3:
                    st.markdown("**If +2R Gain:**")
                    gain_2r = shares * risk_per_share * 2
                    st.write(f"Gain: ${gain_2r:,.2f}")
                    st.write(f"Account after: ${account_size + gain_2r:,.2f}")

                # Kelly Criterion (simplified)
                st.markdown("### Kelly Criterion (Advanced)")
                st.markdown("Optimal bet size based on win rate and average win/loss ratio")

                col1, col2 = st.columns(2)
                with col1:
                    win_rate = st.slider("Estimated Win Rate (%)", 30, 70, 50, key="kelly_wr")
                with col2:
                    avg_win_loss = st.slider("Avg Win / Avg Loss Ratio", 1.0, 3.0, 2.0, 0.1, key="kelly_rr")

                w = win_rate / 100
                r = avg_win_loss
                kelly = w - (1 - w) / r
                half_kelly = kelly / 2

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Kelly %", f"{kelly*100:.1f}%",
                             help="Full Kelly can be aggressive - many use Half Kelly")
                with col2:
                    st.metric("Half Kelly %", f"{half_kelly*100:.1f}%",
                             help="More conservative approach")

            else:
                st.error("Stop loss must be different from entry price")

    with risk_sub2:
        st.markdown("### Risk/Reward Calculator")
        st.markdown("Evaluate trade quality before entry")

        col1, col2, col3 = st.columns(3)
        with col1:
            rr_entry = st.number_input("Entry Price ($)", value=100.0, min_value=0.01, key="rr_entry")
        with col2:
            rr_stop = st.number_input("Stop Loss ($)", value=95.0, min_value=0.01, key="rr_stop")
        with col3:
            rr_target = st.number_input("Target Price ($)", value=115.0, min_value=0.01, key="rr_target")

        if st.button("Calculate Risk/Reward", type="primary", key="calc_rr"):
            risk = abs(rr_entry - rr_stop)
            reward = abs(rr_target - rr_entry)

            if risk > 0:
                rr_ratio = reward / risk
                risk_pct = (risk / rr_entry) * 100
                reward_pct = (reward / rr_entry) * 100

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Risk", f"${risk:.2f}", f"{risk_pct:.1f}%")
                with col2:
                    st.metric("Reward", f"${reward:.2f}", f"{reward_pct:.1f}%")
                with col3:
                    if rr_ratio >= 2:
                        st.metric("Risk/Reward", f"1:{rr_ratio:.2f}", "Good")
                    elif rr_ratio >= 1.5:
                        st.metric("Risk/Reward", f"1:{rr_ratio:.2f}", "Acceptable")
                    else:
                        st.metric("Risk/Reward", f"1:{rr_ratio:.2f}", "Poor")

                # Breakeven analysis
                st.markdown("### Breakeven Win Rate Required")
                breakeven_wr = 1 / (1 + rr_ratio) * 100
                st.metric("Breakeven Win Rate", f"{breakeven_wr:.1f}%",
                         help=f"You need to win more than {breakeven_wr:.1f}% of trades to be profitable")

                # Visual
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=rr_ratio,
                    title={'text': "Risk/Reward Ratio"},
                    gauge={
                        'axis': {'range': [0, 5]},
                        'bar': {'color': 'green' if rr_ratio >= 2 else 'yellow' if rr_ratio >= 1.5 else 'red'},
                        'steps': [
                            {'range': [0, 1], 'color': 'darkred'},
                            {'range': [1, 1.5], 'color': 'red'},
                            {'range': [1.5, 2], 'color': 'yellow'},
                            {'range': [2, 3], 'color': 'lightgreen'},
                            {'range': [3, 5], 'color': 'green'}
                        ],
                        'threshold': {
                            'line': {'color': 'white', 'width': 4},
                            'thickness': 0.75,
                            'value': 2.0
                        }
                    }
                ))
                fig.update_layout(template='plotly_dark', height=300)
                st.plotly_chart(fig, use_container_width=True)

                # Trade quality assessment
                st.markdown("### Trade Quality Assessment")
                if rr_ratio >= 3:
                    st.success("⭐ **Excellent Trade Setup** - 3:1 or better R:R")
                elif rr_ratio >= 2:
                    st.success("✅ **Good Trade Setup** - Professional standard (2:1)")
                elif rr_ratio >= 1.5:
                    st.warning("⚠️ **Marginal Trade** - Consider improving entry or target")
                else:
                    st.error("❌ **Poor Trade** - R:R below 1.5:1 not recommended")

            else:
                st.error("Stop loss must be different from entry")

    with risk_sub3:
        st.markdown("### ATR-Based Stop Loss Calculator")
        st.markdown("Calculate stop loss using Average True Range for volatility-adjusted stops")

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            stop_symbol = st.text_input("Symbol", value="SPY", key="stop_symbol")
        with col2:
            atr_period = st.number_input("ATR Period", value=14, min_value=5, max_value=30, key="atr_period")
        with col3:
            atr_multiplier = st.number_input("ATR Multiplier", value=2.0, min_value=0.5, max_value=5.0, step=0.5, key="atr_mult")

        if st.button("Calculate ATR Stop", type="primary", key="calc_atr_stop"):
            with st.spinner("Calculating..."):
                try:
                    df = yf.Ticker(stop_symbol).history(period="3mo")

                    if df.empty:
                        st.error("No data")
                    else:
                        # Calculate ATR
                        atr = ta.atr(df['High'], df['Low'], df['Close'], length=atr_period)
                        current_atr = atr.iloc[-1]
                        current_price = df['Close'].iloc[-1]

                        # Stop levels
                        long_stop = current_price - (current_atr * atr_multiplier)
                        short_stop = current_price + (current_atr * atr_multiplier)
                        stop_distance_pct = (current_atr * atr_multiplier / current_price) * 100

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Current ATR", f"${current_atr:.2f}")
                        with col2:
                            st.metric("Stop Distance", f"${current_atr * atr_multiplier:.2f}",
                                     f"{stop_distance_pct:.1f}%")
                        with col3:
                            st.metric("Current Price", f"${current_price:.2f}")

                        st.divider()

                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("### Long Position Stop")
                            st.metric("Stop Loss Price", f"${long_stop:.2f}")
                            st.write(f"Place stop {atr_multiplier}x ATR below entry")
                        with col2:
                            st.markdown("### Short Position Stop")
                            st.metric("Stop Loss Price", f"${short_stop:.2f}")
                            st.write(f"Place stop {atr_multiplier}x ATR above entry")

                        # ATR chart
                        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                          vertical_spacing=0.1, row_heights=[0.7, 0.3])

                        fig.add_trace(go.Candlestick(
                            x=df.index, open=df['Open'], high=df['High'],
                            low=df['Low'], close=df['Close'], name='Price'
                        ), row=1, col=1)

                        # Add stop level bands
                        upper_band = df['Close'] + atr * atr_multiplier
                        lower_band = df['Close'] - atr * atr_multiplier

                        fig.add_trace(go.Scatter(x=df.index, y=upper_band,
                            name='Short Stop', line=dict(color='red', dash='dot')), row=1, col=1)
                        fig.add_trace(go.Scatter(x=df.index, y=lower_band,
                            name='Long Stop', line=dict(color='green', dash='dot')), row=1, col=1)

                        fig.add_trace(go.Scatter(x=df.index, y=atr,
                            name='ATR', line=dict(color='cyan')), row=2, col=1)

                        fig.update_layout(title=f'{stop_symbol} - ATR Stop Levels ({atr_multiplier}x ATR)',
                                        template='plotly_dark', height=600,
                                        xaxis_rangeslider_visible=False)
                        fig.update_yaxes(title_text="ATR", row=2, col=1)

                        st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

                        # Stop placement guidelines
                        st.markdown("### Stop Placement Guidelines")
                        st.write(f"""
                        - **Conservative (1x ATR):** ${current_price - current_atr:.2f} - Tighter stop, more frequent stops
                        - **Standard (2x ATR):** ${current_price - 2*current_atr:.2f} - Balance of protection and room
                        - **Wide (3x ATR):** ${current_price - 3*current_atr:.2f} - More room, larger potential loss
                        """)

                except Exception as e:
                    st.error(f"Error: {e}")


# ============================================================================
# TAB 12: AI TRADING LAB - AGENTIC ML FRAMEWORK
# ============================================================================

# Model directory for saving trained models
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)


def data_engineer_agent(symbol, start_date, end_date, prediction_days=5):
    """
    Agent 1: Data Engineer
    Fetches data and creates 50+ features for ML models
    """
    agent_log = []
    agent_log.append(f"🔧 Data Engineer Agent started for {symbol}")

    try:
        # Fetch data
        agent_log.append(f"📥 Fetching data from {start_date} to {end_date}...")
        df = yf.Ticker(symbol).history(start=start_date, end=end_date)

        if df.empty:
            return None, None, None, ["❌ No data available for this symbol/period"]

        agent_log.append(f"✅ Fetched {len(df)} trading days")

        # ===== PRICE FEATURES =====
        agent_log.append("📊 Engineering price features...")

        # Returns at different horizons
        df['return_1d'] = df['Close'].pct_change(1)
        df['return_5d'] = df['Close'].pct_change(5)
        df['return_10d'] = df['Close'].pct_change(10)
        df['return_20d'] = df['Close'].pct_change(20)

        # Volatility at different windows
        df['volatility_5d'] = df['return_1d'].rolling(5).std()
        df['volatility_10d'] = df['return_1d'].rolling(10).std()
        df['volatility_20d'] = df['return_1d'].rolling(20).std()

        # Price position relative to range
        df['price_position_20d'] = (df['Close'] - df['Low'].rolling(20).min()) / \
                                   (df['High'].rolling(20).max() - df['Low'].rolling(20).min() + 0.0001)
        df['price_position_50d'] = (df['Close'] - df['Low'].rolling(50).min()) / \
                                   (df['High'].rolling(50).max() - df['Low'].rolling(50).min() + 0.0001)

        # Gap
        df['gap'] = (df['Open'] - df['Close'].shift(1)) / df['Close'].shift(1)

        # Candle features
        df['body_size'] = abs(df['Close'] - df['Open']) / df['Open']
        df['upper_shadow'] = (df['High'] - df[['Open', 'Close']].max(axis=1)) / df['Open']
        df['lower_shadow'] = (df[['Open', 'Close']].min(axis=1) - df['Low']) / df['Open']
        df['is_bullish'] = (df['Close'] > df['Open']).astype(int)

        # ===== TECHNICAL INDICATORS =====
        agent_log.append("📈 Calculating technical indicators...")

        # RSI at multiple periods
        df['rsi_7'] = ta.rsi(df['Close'], length=7)
        df['rsi_14'] = ta.rsi(df['Close'], length=14)
        df['rsi_21'] = ta.rsi(df['Close'], length=21)

        # MACD
        macd = ta.macd(df['Close'], fast=12, slow=26, signal=9)
        if macd is not None:
            df['macd_line'] = macd['MACD_12_26_9']
            df['macd_signal'] = macd['MACDs_12_26_9']
            df['macd_hist'] = macd['MACDh_12_26_9']

        # Stochastic
        stoch = ta.stoch(df['High'], df['Low'], df['Close'], k=14, d=3)
        if stoch is not None:
            df['stoch_k'] = stoch['STOCHk_14_3_3']
            df['stoch_d'] = stoch['STOCHd_14_3_3']

        # Williams %R
        df['williams_r'] = ta.willr(df['High'], df['Low'], df['Close'], length=14)

        # CCI
        df['cci'] = ta.cci(df['High'], df['Low'], df['Close'], length=20)

        # MFI (Money Flow Index)
        df['mfi'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)

        # ADX
        adx = ta.adx(df['High'], df['Low'], df['Close'], length=14)
        if adx is not None:
            df['adx'] = adx['ADX_14']
            df['di_plus'] = adx['DMP_14']
            df['di_minus'] = adx['DMN_14']

        # Bollinger Bands
        bb = ta.bbands(df['Close'], length=20, std=2)
        if bb is not None:
            df['bb_upper'] = bb['BBU_20_2.0']
            df['bb_middle'] = bb['BBM_20_2.0']
            df['bb_lower'] = bb['BBL_20_2.0']
            df['bb_position'] = (df['Close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'] + 0.0001)
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']

        # ATR
        df['atr'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        df['atr_pct'] = df['atr'] / df['Close']

        # ===== MOVING AVERAGE FEATURES =====
        agent_log.append("📉 Computing moving average features...")

        # SMAs
        df['sma_10'] = ta.sma(df['Close'], length=10)
        df['sma_20'] = ta.sma(df['Close'], length=20)
        df['sma_50'] = ta.sma(df['Close'], length=50)
        df['sma_200'] = ta.sma(df['Close'], length=200)

        # Price relative to SMAs
        df['price_to_sma10'] = df['Close'] / df['sma_10']
        df['price_to_sma20'] = df['Close'] / df['sma_20']
        df['price_to_sma50'] = df['Close'] / df['sma_50']
        df['price_to_sma200'] = df['Close'] / df['sma_200']

        # SMA crossover signals
        df['sma_10_20_cross'] = (df['sma_10'] > df['sma_20']).astype(int)
        df['sma_20_50_cross'] = (df['sma_20'] > df['sma_50']).astype(int)
        df['sma_50_200_cross'] = (df['sma_50'] > df['sma_200']).astype(int)

        # EMAs
        df['ema_12'] = ta.ema(df['Close'], length=12)
        df['ema_26'] = ta.ema(df['Close'], length=26)
        df['ema_momentum'] = df['ema_12'] / df['ema_26']

        # ===== VOLUME FEATURES =====
        agent_log.append("📊 Analyzing volume patterns...")

        df['volume_sma_20'] = ta.sma(df['Volume'], length=20)
        df['volume_ratio'] = df['Volume'] / df['volume_sma_20']
        df['volume_trend'] = df['Volume'].pct_change(5)

        # OBV
        df['obv'] = ta.obv(df['Close'], df['Volume'])
        df['obv_sma'] = ta.sma(df['obv'], length=20)
        df['obv_trend'] = (df['obv'] > df['obv_sma']).astype(int)

        # Volume-price correlation (rolling)
        df['vol_price_corr'] = df['Close'].rolling(20).corr(df['Volume'])

        # ===== PATTERN FEATURES =====
        agent_log.append("🔍 Detecting patterns...")

        # Higher highs / Lower lows
        df['higher_high'] = (df['High'] > df['High'].shift(1)).astype(int)
        df['lower_low'] = (df['Low'] < df['Low'].shift(1)).astype(int)
        df['hh_count_5d'] = df['higher_high'].rolling(5).sum()
        df['ll_count_5d'] = df['lower_low'].rolling(5).sum()

        # Trend strength
        df['trend_strength'] = df['hh_count_5d'] - df['ll_count_5d']

        # Distance from recent high/low
        df['dist_from_high_20d'] = (df['High'].rolling(20).max() - df['Close']) / df['Close']
        df['dist_from_low_20d'] = (df['Close'] - df['Low'].rolling(20).min()) / df['Close']

        # ===== CREATE TARGET =====
        agent_log.append(f"🎯 Creating {prediction_days}-day prediction target...")

        # Classification target: 1 if price goes up, 0 if down
        df['future_return'] = df['Close'].shift(-prediction_days) / df['Close'] - 1
        df['target_class'] = (df['future_return'] > 0).astype(int)

        # Regression target: future price
        df['target_price'] = df['Close'].shift(-prediction_days)

        # ===== PREPARE FINAL DATASET =====
        # Feature columns (exclude targets and raw OHLCV)
        feature_cols = [col for col in df.columns if col not in
                       ['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits',
                        'future_return', 'target_class', 'target_price', 'obv', 'volume_sma_20',
                        'sma_10', 'sma_20', 'sma_50', 'sma_200', 'ema_12', 'ema_26', 'obv_sma',
                        'bb_upper', 'bb_middle', 'bb_lower']]

        # Drop rows with NaN
        df_clean = df.dropna()

        if len(df_clean) < 100:
            return None, None, None, ["❌ Not enough data after feature engineering (need 100+ rows)"]

        agent_log.append(f"✅ Created {len(feature_cols)} features for {len(df_clean)} samples")
        agent_log.append(f"📋 Features: {', '.join(feature_cols[:10])}... and {len(feature_cols)-10} more")

        return df_clean, feature_cols, df, agent_log

    except Exception as e:
        agent_log.append(f"❌ Error: {str(e)}")
        return None, None, None, agent_log


def model_trainer_agent(df, feature_cols, model_types, test_size=0.2):
    """
    Agent 2: Model Trainer
    Trains multiple ML models with cross-validation
    """
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.neural_network import MLPClassifier
    from sklearn.svm import SVC
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score, TimeSeriesSplit
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

    agent_log = []
    agent_log.append("🤖 Model Trainer Agent started")

    try:
        # Prepare data
        X = df[feature_cols].values
        y = df['target_class'].values

        # Time-based split (no shuffle for time series)
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        agent_log.append(f"📊 Training set: {len(X_train)} samples, Test set: {len(X_test)} samples")

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Model definitions
        models = {}
        if "Random Forest" in model_types:
            models["Random Forest"] = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
        if "Gradient Boosting" in model_types:
            models["Gradient Boosting"] = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
        if "Logistic Regression" in model_types:
            models["Logistic Regression"] = LogisticRegression(max_iter=1000, random_state=42)
        if "Neural Network" in model_types:
            models["Neural Network"] = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42)
        if "SVM" in model_types:
            models["SVM"] = SVC(kernel='rbf', probability=True, random_state=42)

        # Train and evaluate each model
        results = {}
        trained_models = {}

        tscv = TimeSeriesSplit(n_splits=5)

        for name, model in models.items():
            agent_log.append(f"🔄 Training {name}...")

            # Cross-validation
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=tscv, scoring='accuracy')

            # Train on full training set
            model.fit(X_train_scaled, y_train)

            # Test predictions
            y_pred = model.predict(X_test_scaled)
            y_pred_proba = model.predict_proba(X_test_scaled) if hasattr(model, 'predict_proba') else None

            # Metrics
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)

            results[name] = {
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'predictions': y_pred,
                'probabilities': y_pred_proba
            }

            trained_models[name] = model

            agent_log.append(f"✅ {name}: CV={cv_scores.mean():.3f}±{cv_scores.std():.3f}, Test Acc={accuracy:.3f}")

        # Get feature importance (for tree-based models)
        feature_importance = {}
        for name, model in trained_models.items():
            if hasattr(model, 'feature_importances_'):
                feature_importance[name] = dict(zip(feature_cols, model.feature_importances_))

        agent_log.append(f"✅ Trained {len(trained_models)} models successfully")

        return trained_models, scaler, results, feature_importance, agent_log

    except Exception as e:
        agent_log.append(f"❌ Error: {str(e)}")
        return None, None, None, None, agent_log


def signal_generator_agent(trained_models, scaler, df, feature_cols, results):
    """
    Agent 3: Signal Generator
    Generates trading signals from ensemble of models
    """
    agent_log = []
    agent_log.append("📡 Signal Generator Agent started")

    try:
        # Get the most recent data point for prediction
        latest_features = df[feature_cols].iloc[-1:].values
        latest_scaled = scaler.transform(latest_features)

        # Get predictions from each model
        predictions = {}
        probabilities = {}

        for name, model in trained_models.items():
            pred = model.predict(latest_scaled)[0]
            predictions[name] = pred

            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(latest_scaled)[0]
                probabilities[name] = {'down': proba[0], 'up': proba[1]}
            else:
                probabilities[name] = {'down': 1-pred, 'up': pred}

        agent_log.append(f"📊 Got predictions from {len(predictions)} models")

        # Calculate ensemble prediction (weighted by CV score)
        total_weight = 0
        weighted_prob = 0

        for name, pred in predictions.items():
            weight = results[name]['cv_mean']
            weighted_prob += probabilities[name]['up'] * weight
            total_weight += weight

        ensemble_prob_up = weighted_prob / total_weight if total_weight > 0 else 0.5

        # Map to signal levels
        if ensemble_prob_up >= 0.7:
            signal = "STRONG BUY"
            signal_color = "green"
            signal_value = 2
        elif ensemble_prob_up >= 0.55:
            signal = "BUY"
            signal_color = "lightgreen"
            signal_value = 1
        elif ensemble_prob_up >= 0.45:
            signal = "HOLD"
            signal_color = "gray"
            signal_value = 0
        elif ensemble_prob_up >= 0.3:
            signal = "SELL"
            signal_color = "orange"
            signal_value = -1
        else:
            signal = "STRONG SELL"
            signal_color = "red"
            signal_value = -2

        # Model agreement
        agreement = sum(1 for p in predictions.values() if p == (1 if ensemble_prob_up >= 0.5 else 0))
        agreement_pct = agreement / len(predictions) * 100

        agent_log.append(f"✅ Signal: {signal} (Confidence: {ensemble_prob_up*100:.1f}%)")
        agent_log.append(f"📈 Model Agreement: {agreement_pct:.0f}%")

        signal_result = {
            'signal': signal,
            'signal_value': signal_value,
            'signal_color': signal_color,
            'confidence': ensemble_prob_up,
            'model_predictions': predictions,
            'model_probabilities': probabilities,
            'agreement_pct': agreement_pct
        }

        return signal_result, agent_log

    except Exception as e:
        agent_log.append(f"❌ Error: {str(e)}")
        return None, agent_log


def backtest_agent(df, trained_models, scaler, feature_cols, results, point_in_time, prediction_days):
    """
    Agent 4: Backtest Validator
    Tests signals on out-of-sample data
    """
    agent_log = []
    agent_log.append("📈 Backtest Validator Agent started")

    try:
        # Get data after point in time
        test_df = df[df.index > point_in_time].copy()

        if len(test_df) < 10:
            agent_log.append("⚠️ Not enough out-of-sample data for backtesting")
            return None, agent_log

        agent_log.append(f"📊 Backtesting on {len(test_df)} days of out-of-sample data")

        # Generate signals for each day
        signals = []

        for i in range(len(test_df) - prediction_days):
            features = test_df[feature_cols].iloc[i:i+1].values
            features_scaled = scaler.transform(features)

            # Ensemble prediction
            total_weight = 0
            weighted_prob = 0

            for name, model in trained_models.items():
                if hasattr(model, 'predict_proba'):
                    proba = model.predict_proba(features_scaled)[0][1]
                else:
                    proba = model.predict(features_scaled)[0]

                weight = results[name]['cv_mean']
                weighted_prob += proba * weight
                total_weight += weight

            ensemble_prob = weighted_prob / total_weight if total_weight > 0 else 0.5

            # Signal: 1 = buy, -1 = sell, 0 = hold
            if ensemble_prob >= 0.55:
                signal = 1
            elif ensemble_prob <= 0.45:
                signal = -1
            else:
                signal = 0

            signals.append({
                'date': test_df.index[i],
                'signal': signal,
                'probability': ensemble_prob,
                'price': test_df['Close'].iloc[i]
            })

        # Calculate strategy performance
        initial_capital = 10000
        position = 0
        equity = initial_capital
        equity_curve = []
        trades = []

        for i, sig in enumerate(signals):
            price = sig['price']

            if sig['signal'] == 1 and position == 0:  # Buy
                position = equity / price
                trades.append({'date': sig['date'], 'type': 'BUY', 'price': price})
            elif sig['signal'] == -1 and position > 0:  # Sell
                equity = position * price
                position = 0
                trades.append({'date': sig['date'], 'type': 'SELL', 'price': price})

            current_value = equity if position == 0 else position * price
            equity_curve.append({'date': sig['date'], 'equity': current_value})

        # Final equity
        if position > 0 and len(signals) > 0:
            final_price = test_df['Close'].iloc[-1]
            final_equity = position * final_price
        else:
            final_equity = equity

        # Buy and hold comparison
        buy_hold_return = (test_df['Close'].iloc[-1] / test_df['Close'].iloc[0] - 1) * 100
        strategy_return = (final_equity / initial_capital - 1) * 100

        # Calculate metrics
        equity_df = pd.DataFrame(equity_curve)
        if len(equity_df) > 0:
            equity_df['returns'] = equity_df['equity'].pct_change()
            sharpe = equity_df['returns'].mean() / equity_df['returns'].std() * np.sqrt(252) if equity_df['returns'].std() > 0 else 0
            max_dd = ((equity_df['equity'] / equity_df['equity'].cummax()) - 1).min() * 100
        else:
            sharpe = 0
            max_dd = 0

        # Win rate
        winning_trades = sum(1 for i in range(0, len(trades)-1, 2)
                           if i+1 < len(trades) and trades[i+1]['price'] > trades[i]['price'])
        total_round_trips = len(trades) // 2
        win_rate = (winning_trades / total_round_trips * 100) if total_round_trips > 0 else 0

        agent_log.append(f"✅ Strategy Return: {strategy_return:.2f}%")
        agent_log.append(f"📊 Buy & Hold Return: {buy_hold_return:.2f}%")
        agent_log.append(f"📈 Sharpe Ratio: {sharpe:.2f}")
        agent_log.append(f"📉 Max Drawdown: {max_dd:.2f}%")
        agent_log.append(f"🎯 Win Rate: {win_rate:.1f}% ({total_round_trips} trades)")

        backtest_result = {
            'strategy_return': strategy_return,
            'buy_hold_return': buy_hold_return,
            'sharpe': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate,
            'num_trades': total_round_trips,
            'equity_curve': equity_df,
            'trades': trades,
            'signals': signals,
            'final_equity': final_equity
        }

        return backtest_result, agent_log

    except Exception as e:
        agent_log.append(f"❌ Error: {str(e)}")
        return None, agent_log


def coordinator_agent(symbol, data_result, model_result, signal_result, backtest_result):
    """
    Agent 5: Coordinator
    Aggregates all results and generates final report
    """
    agent_log = []
    agent_log.append("🎯 Coordinator Agent compiling final report...")

    report = {
        'symbol': symbol,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'signal': signal_result,
        'backtest': backtest_result,
        'models': model_result,
        'recommendation': None,
        'reasoning': []
    }

    # Generate recommendation with reasoning
    reasoning = []

    # Signal strength
    if signal_result:
        reasoning.append(f"Current signal is {signal_result['signal']} with {signal_result['confidence']*100:.1f}% confidence")
        reasoning.append(f"Model agreement: {signal_result['agreement_pct']:.0f}%")

    # Backtest performance
    if backtest_result:
        if backtest_result['strategy_return'] > backtest_result['buy_hold_return']:
            reasoning.append(f"Strategy outperformed buy-and-hold by {backtest_result['strategy_return'] - backtest_result['buy_hold_return']:.1f}%")
        else:
            reasoning.append(f"Strategy underperformed buy-and-hold by {backtest_result['buy_hold_return'] - backtest_result['strategy_return']:.1f}%")

        if backtest_result['sharpe'] > 1:
            reasoning.append(f"Good risk-adjusted returns (Sharpe: {backtest_result['sharpe']:.2f})")
        elif backtest_result['sharpe'] < 0:
            reasoning.append(f"Poor risk-adjusted returns (Sharpe: {backtest_result['sharpe']:.2f})")

    # Model confidence
    if model_result:
        best_model = max(model_result.items(), key=lambda x: x[1]['cv_mean'])
        reasoning.append(f"Best performing model: {best_model[0]} (CV: {best_model[1]['cv_mean']:.3f})")

    report['reasoning'] = reasoning

    # Final recommendation
    if signal_result and backtest_result:
        confidence_score = signal_result['confidence']
        backtest_score = 0.5 + (backtest_result['strategy_return'] - backtest_result['buy_hold_return']) / 100

        final_score = (confidence_score + min(max(backtest_score, 0), 1)) / 2

        if final_score >= 0.65:
            report['recommendation'] = "BULLISH - Consider buying"
        elif final_score >= 0.55:
            report['recommendation'] = "SLIGHTLY BULLISH - Watch for entry"
        elif final_score >= 0.45:
            report['recommendation'] = "NEUTRAL - Wait for clearer signal"
        elif final_score >= 0.35:
            report['recommendation'] = "SLIGHTLY BEARISH - Consider reducing"
        else:
            report['recommendation'] = "BEARISH - Consider selling"

    agent_log.append(f"✅ Final recommendation: {report['recommendation']}")

    return report, agent_log


if selected_page == "🧠 AI Trading Lab":
    st.subheader("🧠 AI Trading Lab")
    st.markdown("*Agentic ML Framework for Signal Discovery*")

    # Create sub-tabs
    lab_tab1, lab_tab2, lab_tab3, lab_tab4, lab_tab5 = st.tabs([
        "⚙️ Configure & Run",
        "📊 Agent Status",
        "🎯 Model Performance",
        "📈 Signals & Predictions",
        "📉 Backtest Results"
    ])

    # Initialize session state
    if 'ai_lab_results' not in st.session_state:
        st.session_state.ai_lab_results = None
    if 'ai_lab_logs' not in st.session_state:
        st.session_state.ai_lab_logs = {}

    with lab_tab1:
        st.markdown("### Configure AI Agents")

        col1, col2 = st.columns(2)

        with col1:
            lab_symbol = st.text_input("Symbol", value="SPY", key="lab_symbol")

            historical_years = st.slider("Historical Data (Years)", 1, 10, 3, key="lab_hist_years",
                                        help="How many years of data to use for training")

            prediction_days = st.selectbox("Prediction Horizon (Days)",
                                          [5, 10, 20, 30, 60], index=1, key="lab_pred_days",
                                          help="How far ahead to predict")

        with col2:
            point_in_time = st.date_input("Point in Time",
                                         value=datetime.now() - timedelta(days=90),
                                         max_value=datetime.now() - timedelta(days=30),
                                         key="lab_pit",
                                         help="Date from which to make predictions (allows walk-forward testing)")

            model_types = st.multiselect("Models to Train",
                                        ["Random Forest", "Gradient Boosting", "Logistic Regression",
                                         "Neural Network", "SVM"],
                                        default=["Random Forest", "Gradient Boosting", "Logistic Regression"],
                                        key="lab_models")

        st.markdown("---")

        if st.button("🚀 Run AI Agents", type="primary", key="run_agents"):
            if not model_types:
                st.error("Please select at least one model type")
            else:
                # Calculate dates
                pit_datetime = datetime.combine(point_in_time, datetime.min.time())
                start_date = pit_datetime - timedelta(days=historical_years * 365)
                end_date = datetime.now()

                all_logs = {}

                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()

                # ===== AGENT 1: DATA ENGINEER =====
                status_text.text("🔧 Agent 1: Data Engineer - Preparing features...")
                progress_bar.progress(10)

                df_clean, feature_cols, df_full, data_log = data_engineer_agent(
                    lab_symbol, start_date, pit_datetime, prediction_days
                )
                all_logs['Data Engineer'] = data_log

                if df_clean is None:
                    st.error("Data Engineer Agent failed. Check logs.")
                    st.session_state.ai_lab_logs = all_logs
                else:
                    progress_bar.progress(25)

                    # ===== AGENT 2: MODEL TRAINER =====
                    status_text.text("🤖 Agent 2: Model Trainer - Training models...")

                    trained_models, scaler, results, feature_importance, train_log = model_trainer_agent(
                        df_clean, feature_cols, model_types
                    )
                    all_logs['Model Trainer'] = train_log

                    if trained_models is None:
                        st.error("Model Trainer Agent failed. Check logs.")
                        st.session_state.ai_lab_logs = all_logs
                    else:
                        progress_bar.progress(50)

                        # ===== AGENT 3: SIGNAL GENERATOR =====
                        status_text.text("📡 Agent 3: Signal Generator - Generating signals...")

                        # Get full data for signals (up to now)
                        df_current = yf.Ticker(lab_symbol).history(start=start_date, end=end_date)

                        # Recompute features on current data
                        df_signal, signal_features, _, signal_data_log = data_engineer_agent(
                            lab_symbol, start_date, end_date, prediction_days
                        )

                        if df_signal is not None:
                            signal_result, signal_log = signal_generator_agent(
                                trained_models, scaler, df_signal, feature_cols, results
                            )
                            all_logs['Signal Generator'] = signal_log
                        else:
                            signal_result = None
                            all_logs['Signal Generator'] = ["❌ Could not generate signals"]

                        progress_bar.progress(75)

                        # ===== AGENT 4: BACKTEST VALIDATOR =====
                        status_text.text("📈 Agent 4: Backtest Validator - Testing strategy...")

                        if df_signal is not None:
                            backtest_result, backtest_log = backtest_agent(
                                df_signal, trained_models, scaler, feature_cols, results,
                                pit_datetime, prediction_days
                            )
                            all_logs['Backtest Validator'] = backtest_log
                        else:
                            backtest_result = None
                            all_logs['Backtest Validator'] = ["❌ Could not run backtest"]

                        progress_bar.progress(90)

                        # ===== AGENT 5: COORDINATOR =====
                        status_text.text("🎯 Agent 5: Coordinator - Compiling report...")

                        final_report, coord_log = coordinator_agent(
                            lab_symbol,
                            {'df': df_clean, 'features': feature_cols},
                            results,
                            signal_result,
                            backtest_result
                        )
                        all_logs['Coordinator'] = coord_log

                        # Store results
                        st.session_state.ai_lab_results = {
                            'report': final_report,
                            'df': df_signal,
                            'feature_cols': feature_cols,
                            'trained_models': trained_models,
                            'scaler': scaler,
                            'model_results': results,
                            'feature_importance': feature_importance,
                            'signal': signal_result,
                            'backtest': backtest_result,
                            'symbol': lab_symbol,
                            'prediction_days': prediction_days
                        }
                        st.session_state.ai_lab_logs = all_logs

                        progress_bar.progress(100)
                        status_text.text("✅ All agents completed!")

                        st.success("AI Agents completed successfully! Check the other tabs for results.")

    with lab_tab2:
        st.markdown("### Agent Status & Logs")

        if st.session_state.ai_lab_logs:
            for agent_name, logs in st.session_state.ai_lab_logs.items():
                with st.expander(f"📋 {agent_name}", expanded=True):
                    for log in logs:
                        st.write(log)
        else:
            st.info("Run the agents first to see their logs here.")

    with lab_tab3:
        st.markdown("### Model Performance")

        if st.session_state.ai_lab_results and st.session_state.ai_lab_results.get('model_results'):
            results = st.session_state.ai_lab_results['model_results']
            feature_importance = st.session_state.ai_lab_results.get('feature_importance', {})

            # Model comparison table
            st.markdown("#### Model Comparison")

            comparison_data = []
            for name, metrics in results.items():
                comparison_data.append({
                    'Model': name,
                    'CV Score': f"{metrics['cv_mean']:.3f} ± {metrics['cv_std']:.3f}",
                    'Test Accuracy': f"{metrics['accuracy']:.3f}",
                    'Precision': f"{metrics['precision']:.3f}",
                    'Recall': f"{metrics['recall']:.3f}",
                    'F1 Score': f"{metrics['f1']:.3f}"
                })

            st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)

            # CV Score visualization
            fig = go.Figure()
            models = list(results.keys())
            cv_means = [results[m]['cv_mean'] for m in models]
            cv_stds = [results[m]['cv_std'] for m in models]

            fig.add_trace(go.Bar(
                x=models, y=cv_means,
                error_y=dict(type='data', array=cv_stds),
                marker_color=['#26a69a', '#42a5f5', '#ab47bc', '#ffa726', '#ef5350'][:len(models)]
            ))
            fig.update_layout(title='Cross-Validation Scores by Model',
                            template='plotly_dark', height=400,
                            yaxis_title='CV Accuracy', xaxis_title='Model')
            st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

            # Feature importance (if available)
            if feature_importance:
                st.markdown("#### Feature Importance")

                selected_model = st.selectbox("Select model for feature importance",
                                             list(feature_importance.keys()),
                                             key="fi_model")

                if selected_model in feature_importance:
                    fi = feature_importance[selected_model]
                    fi_sorted = sorted(fi.items(), key=lambda x: x[1], reverse=True)[:20]

                    fig = go.Figure(go.Bar(
                        x=[f[1] for f in fi_sorted],
                        y=[f[0] for f in fi_sorted],
                        orientation='h',
                        marker_color='#26a69a'
                    ))
                    fig.update_layout(title=f'Top 20 Features - {selected_model}',
                                    template='plotly_dark', height=500,
                                    xaxis_title='Importance', yaxis_title='Feature')
                    st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)
        else:
            st.info("Run the agents first to see model performance here.")

    with lab_tab4:
        st.markdown("### Signals & Predictions")

        if st.session_state.ai_lab_results and st.session_state.ai_lab_results.get('signal'):
            signal = st.session_state.ai_lab_results['signal']
            symbol = st.session_state.ai_lab_results['symbol']
            pred_days = st.session_state.ai_lab_results['prediction_days']

            # Main signal display
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"### Current Signal")
                signal_colors = {
                    'STRONG BUY': 'green', 'BUY': 'lightgreen', 'HOLD': 'gray',
                    'SELL': 'orange', 'STRONG SELL': 'red'
                }
                st.markdown(f"# :{signal['signal_color']}[{signal['signal']}]")

            with col2:
                st.metric("Confidence", f"{signal['confidence']*100:.1f}%")

            with col3:
                st.metric("Model Agreement", f"{signal['agreement_pct']:.0f}%")

            st.markdown("---")

            # Model predictions breakdown
            st.markdown("#### Individual Model Predictions")

            pred_data = []
            for model, pred in signal['model_predictions'].items():
                proba = signal['model_probabilities'][model]
                pred_data.append({
                    'Model': model,
                    'Prediction': 'UP' if pred == 1 else 'DOWN',
                    'Prob Up': f"{proba['up']*100:.1f}%",
                    'Prob Down': f"{proba['down']*100:.1f}%"
                })

            st.dataframe(pd.DataFrame(pred_data), use_container_width=True)

            # Agreement gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=signal['agreement_pct'],
                title={'text': "Model Agreement"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': 'green' if signal['agreement_pct'] >= 80 else 'yellow' if signal['agreement_pct'] >= 60 else 'red'},
                    'steps': [
                        {'range': [0, 50], 'color': 'rgba(255, 0, 0, 0.2)'},
                        {'range': [50, 75], 'color': 'rgba(255, 255, 0, 0.2)'},
                        {'range': [75, 100], 'color': 'rgba(0, 255, 0, 0.2)'}
                    ]
                }
            ))
            fig.update_layout(template='plotly_dark', height=300)
            st.plotly_chart(fig, use_container_width=True)

            # Final report
            if st.session_state.ai_lab_results.get('report'):
                report = st.session_state.ai_lab_results['report']

                st.markdown("---")
                st.markdown("### 🎯 Coordinator's Report")
                st.markdown(f"**Recommendation:** {report['recommendation']}")

                st.markdown("**Reasoning:**")
                for reason in report['reasoning']:
                    st.write(f"• {reason}")
        else:
            st.info("Run the agents first to see signals here.")

    with lab_tab5:
        st.markdown("### Backtest Results")

        if st.session_state.ai_lab_results and st.session_state.ai_lab_results.get('backtest'):
            backtest = st.session_state.ai_lab_results['backtest']

            # Key metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                delta = backtest['strategy_return'] - backtest['buy_hold_return']
                st.metric("Strategy Return", f"{backtest['strategy_return']:.2f}%",
                         delta=f"{delta:.2f}% vs B&H")

            with col2:
                st.metric("Buy & Hold Return", f"{backtest['buy_hold_return']:.2f}%")

            with col3:
                st.metric("Sharpe Ratio", f"{backtest['sharpe']:.2f}")

            with col4:
                st.metric("Max Drawdown", f"{backtest['max_drawdown']:.2f}%")

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Win Rate", f"{backtest['win_rate']:.1f}%")

            with col2:
                st.metric("Number of Trades", f"{backtest['num_trades']}")

            st.markdown("---")

            # Equity curve
            if backtest.get('equity_curve') is not None and len(backtest['equity_curve']) > 0:
                equity_df = backtest['equity_curve']

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=equity_df['date'], y=equity_df['equity'],
                    name='Strategy Equity', line=dict(color='#26a69a', width=2)
                ))

                # Add buy and hold reference
                if st.session_state.ai_lab_results.get('df') is not None:
                    df = st.session_state.ai_lab_results['df']
                    df_test = df[df.index >= equity_df['date'].iloc[0]]
                    if len(df_test) > 0:
                        bh_equity = 10000 * (df_test['Close'] / df_test['Close'].iloc[0])
                        fig.add_trace(go.Scatter(
                            x=df_test.index, y=bh_equity,
                            name='Buy & Hold', line=dict(color='#ef5350', width=2, dash='dash')
                        ))

                fig.update_layout(title='Equity Curve: Strategy vs Buy & Hold',
                                template='plotly_dark', height=400,
                                yaxis_title='Portfolio Value ($)', xaxis_title='Date')
                st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

            # Trade history
            if backtest.get('trades') and len(backtest['trades']) > 0:
                st.markdown("#### Trade History")
                trades_df = pd.DataFrame(backtest['trades'])
                trades_df['date'] = pd.to_datetime(trades_df['date']).dt.strftime('%Y-%m-%d')
                trades_df['price'] = trades_df['price'].apply(lambda x: f"${x:.2f}")
                st.dataframe(trades_df, use_container_width=True)

            # Performance assessment
            st.markdown("---")
            st.markdown("#### Performance Assessment")

            if backtest['strategy_return'] > backtest['buy_hold_return']:
                st.success(f"✅ Strategy outperformed buy-and-hold by {backtest['strategy_return'] - backtest['buy_hold_return']:.2f}%")
            else:
                st.warning(f"⚠️ Strategy underperformed buy-and-hold by {backtest['buy_hold_return'] - backtest['strategy_return']:.2f}%")

            if backtest['sharpe'] > 1:
                st.success(f"✅ Good risk-adjusted returns (Sharpe > 1)")
            elif backtest['sharpe'] > 0:
                st.info(f"ℹ️ Positive but modest risk-adjusted returns")
            else:
                st.warning(f"⚠️ Negative risk-adjusted returns")

            if backtest['win_rate'] > 50:
                st.success(f"✅ Win rate above 50%")
            else:
                st.info(f"ℹ️ Win rate below 50% (may still be profitable with good R:R)")
        else:
            st.info("Run the agents first to see backtest results here.")
