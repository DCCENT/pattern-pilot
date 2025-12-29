"""
Chart creation and drawing utilities for Pattern Pilot
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas_ta as ta

from config import CHART_COLORS, FIBONACCI_COLORS


def create_chart(
    df: pd.DataFrame,
    symbol: str,
    show_sma: bool = True,
    show_rsi: bool = True,
    show_macd: bool = True,
    show_volume: bool = True,
    patterns: Optional[List[Dict[str, Any]]] = None
) -> go.Figure:
    """
    Create an interactive candlestick chart with optional indicators.

    Args:
        df: DataFrame with OHLCV data
        symbol: Stock ticker symbol for title
        show_sma: Whether to display SMA lines
        show_rsi: Whether to display RSI subplot
        show_macd: Whether to display MACD subplot
        show_volume: Whether to display volume subplot
        patterns: List of detected candlestick patterns to annotate

    Returns:
        Plotly Figure object
    """
    # Calculate number of subplots needed
    rows = 1
    row_heights = [0.6]
    if show_volume:
        rows += 1
        row_heights.append(0.15)
    if show_rsi:
        rows += 1
        row_heights.append(0.15)
    if show_macd:
        rows += 1
        row_heights.append(0.15)

    # Normalize row heights
    total = sum(row_heights)
    row_heights = [h / total for h in row_heights]

    # Create subplots
    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights
    )

    # Main candlestick chart
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price',
        increasing_line_color=CHART_COLORS['bullish'],
        decreasing_line_color=CHART_COLORS['bearish']
    ), row=1, col=1)

    # Add SMAs
    if show_sma:
        df_copy = df.copy()
        df_copy['SMA20'] = ta.sma(df_copy['Close'], length=20)
        df_copy['SMA50'] = ta.sma(df_copy['Close'], length=50)
        fig.add_trace(go.Scatter(
            x=df_copy.index,
            y=df_copy['SMA20'],
            name='SMA 20',
            line=dict(color='orange', width=1)
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df_copy.index,
            y=df_copy['SMA50'],
            name='SMA 50',
            line=dict(color='blue', width=1)
        ), row=1, col=1)

    # Add pattern annotations
    if patterns:
        for p in patterns:
            pattern_type = p.get('type', 'neutral')
            color = CHART_COLORS.get(pattern_type, CHART_COLORS['neutral'])
            symbol_marker = 'triangle-up' if pattern_type == 'bullish' else \
                           'triangle-down' if pattern_type == 'bearish' else 'diamond'
            text_pos = 'top center' if pattern_type != 'bullish' else 'bottom center'

            fig.add_trace(go.Scatter(
                x=[p['date']],
                y=[p['price']],
                mode='markers+text',
                marker=dict(size=12, color=color, symbol=symbol_marker),
                text=[p['pattern']],
                textposition=text_pos,
                textfont=dict(size=9),
                showlegend=False
            ), row=1, col=1)

    current_row = 2

    # Volume subplot
    if show_volume:
        colors = [
            CHART_COLORS['bullish'] if c >= o else CHART_COLORS['bearish']
            for c, o in zip(df['Close'], df['Open'])
        ]
        fig.add_trace(go.Bar(
            x=df.index,
            y=df['Volume'],
            marker_color=colors,
            showlegend=False
        ), row=current_row, col=1)
        fig.update_yaxes(title_text="Volume", row=current_row, col=1)
        current_row += 1

    # RSI subplot
    if show_rsi:
        rsi = ta.rsi(df['Close'], length=14)
        fig.add_trace(go.Scatter(
            x=df.index,
            y=rsi,
            name='RSI',
            line=dict(color='purple', width=1)
        ), row=current_row, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=current_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=current_row, col=1)
        fig.update_yaxes(title_text="RSI", row=current_row, col=1)
        current_row += 1

    # MACD subplot
    if show_macd:
        macd = ta.macd(df['Close'])
        if macd is not None:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=macd['MACD_12_26_9'],
                name='MACD',
                line=dict(color='blue', width=1)
            ), row=current_row, col=1)
            fig.add_trace(go.Scatter(
                x=df.index,
                y=macd['MACDs_12_26_9'],
                name='Signal',
                line=dict(color='orange', width=1)
            ), row=current_row, col=1)
            colors = [
                CHART_COLORS['bullish'] if val >= 0 else CHART_COLORS['bearish']
                for val in macd['MACDh_12_26_9']
            ]
            fig.add_trace(go.Bar(
                x=df.index,
                y=macd['MACDh_12_26_9'],
                marker_color=colors,
                showlegend=False
            ), row=current_row, col=1)
            fig.update_yaxes(title_text="MACD", row=current_row, col=1)

    # Update layout
    fig.update_layout(
        title=f'{symbol} - Price Chart',
        template='plotly_dark',
        height=800,
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig


def add_fibonacci_to_chart(
    fig: go.Figure,
    start_date: Union[datetime, date, str],
    end_date: Union[datetime, date, str],
    high_price: float,
    low_price: float,
    color: str,
    line_style: str,
    show_labels: bool = True
) -> go.Figure:
    """
    Add Fibonacci retracement lines to a chart.

    Args:
        fig: Plotly figure to modify
        start_date: Start date for Fibonacci range
        end_date: End date for Fibonacci range
        high_price: Swing high price
        low_price: Swing low price
        color: Line color
        line_style: Line style (solid, dash, dot, etc.)
        show_labels: Whether to show price labels

    Returns:
        Modified Plotly figure
    """
    from .indicators import calculate_fibonacci_levels

    levels = calculate_fibonacci_levels(high_price, low_price)

    for i, (ratio, price) in enumerate(levels.items()):
        fib_color = FIBONACCI_COLORS[i] if i < len(FIBONACCI_COLORS) else color

        fig.add_shape(
            type="line",
            x0=start_date, x1=end_date,
            y0=price, y1=price,
            line=dict(color=fib_color, width=1, dash=line_style),
            row=1, col=1
        )

        if show_labels:
            fig.add_annotation(
                x=end_date, y=price,
                text=f"{ratio:.1%} (${price:.2f})",
                showarrow=False,
                xanchor="left",
                font=dict(size=10, color=fib_color),
                row=1, col=1
            )

    # Add the high-low range box
    fig.add_shape(
        type="rect",
        x0=start_date, x1=end_date,
        y0=low_price, y1=high_price,
        fillcolor="rgba(128, 128, 128, 0.1)",
        line=dict(color=color, width=1, dash=line_style),
        row=1, col=1
    )

    return fig


def add_trendline_to_chart(
    fig: go.Figure,
    x0: Union[datetime, date, str],
    y0: float,
    x1: Union[datetime, date, str],
    y1: float,
    color: str,
    line_style: str,
    extend: bool = False
) -> go.Figure:
    """
    Add a trendline to the chart.

    Args:
        fig: Plotly figure to modify
        x0: Start x-coordinate (date)
        y0: Start y-coordinate (price)
        x1: End x-coordinate (date)
        y1: End y-coordinate (price)
        color: Line color
        line_style: Line style
        extend: Whether to extend the line beyond endpoints

    Returns:
        Modified Plotly figure
    """
    fig.add_shape(
        type="line",
        x0=x0, y0=y0, x1=x1, y1=y1,
        line=dict(color=color, width=2, dash=line_style),
        row=1, col=1
    )
    return fig


def add_horizontal_line_to_chart(
    fig: go.Figure,
    y_val: float,
    x_start: Union[datetime, date, str],
    x_end: Union[datetime, date, str],
    color: str,
    line_style: str,
    label: Optional[str] = None
) -> go.Figure:
    """
    Add a horizontal line (support/resistance) to the chart.

    Args:
        fig: Plotly figure to modify
        y_val: Y-coordinate (price level)
        x_start: Start x-coordinate (date)
        x_end: End x-coordinate (date)
        color: Line color
        line_style: Line style
        label: Optional text label

    Returns:
        Modified Plotly figure
    """
    fig.add_shape(
        type="line",
        x0=x_start, y0=y_val, x1=x_end, y1=y_val,
        line=dict(color=color, width=2, dash=line_style),
        row=1, col=1
    )

    if label:
        fig.add_annotation(
            x=x_end, y=y_val,
            text=label,
            showarrow=False,
            xanchor="left",
            font=dict(size=10, color=color),
            row=1, col=1
        )

    return fig


def add_vertical_line_to_chart(
    fig: go.Figure,
    x_val: Union[datetime, date, str],
    y_min: float,
    y_max: float,
    color: str,
    line_style: str,
    label: Optional[str] = None
) -> go.Figure:
    """
    Add a vertical line to the chart.

    Args:
        fig: Plotly figure to modify
        x_val: X-coordinate (date)
        y_min: Minimum y-coordinate
        y_max: Maximum y-coordinate
        color: Line color
        line_style: Line style
        label: Optional text label

    Returns:
        Modified Plotly figure
    """
    fig.add_shape(
        type="line",
        x0=x_val, y0=y_min, x1=x_val, y1=y_max,
        line=dict(color=color, width=2, dash=line_style),
        row=1, col=1
    )

    if label:
        fig.add_annotation(
            x=x_val, y=y_max,
            text=label,
            showarrow=False,
            yanchor="bottom",
            font=dict(size=10, color=color),
            row=1, col=1
        )

    return fig


def add_price_channel_to_chart(
    fig: go.Figure,
    df: pd.DataFrame,
    start_idx: int,
    end_idx: int,
    color: str,
    line_style: str
) -> go.Figure:
    """
    Add a price channel (parallel lines along highs and lows).

    Args:
        fig: Plotly figure to modify
        df: DataFrame with OHLCV data
        start_idx: Start index for channel
        end_idx: End index for channel
        color: Line color
        line_style: Line style

    Returns:
        Modified Plotly figure
    """
    subset = df.iloc[start_idx:end_idx + 1]

    # Parse color for fill
    try:
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        fill_color = f"rgba({r}, {g}, {b}, 0.1)"
    except (ValueError, IndexError):
        fill_color = "rgba(128, 128, 128, 0.1)"

    # Upper channel line (connect highs)
    fig.add_trace(go.Scatter(
        x=subset.index,
        y=subset['High'],
        mode='lines',
        line=dict(color=color, width=1, dash=line_style),
        showlegend=False,
        name='Upper Channel'
    ), row=1, col=1)

    # Lower channel line (connect lows)
    fig.add_trace(go.Scatter(
        x=subset.index,
        y=subset['Low'],
        mode='lines',
        line=dict(color=color, width=1, dash=line_style),
        fill='tonexty',
        fillcolor=fill_color,
        showlegend=False,
        name='Lower Channel'
    ), row=1, col=1)

    return fig


def create_rrg_chart(
    rrg_data: Dict[str, pd.DataFrame],
    tail_length: int = 5,
    sector_colors: Optional[Dict[str, str]] = None,
    sector_names: Optional[Dict[str, str]] = None
) -> go.Figure:
    """
    Create a Relative Rotation Graph.

    Args:
        rrg_data: Dictionary of symbol -> DataFrame with RS_Ratio and RS_Momentum columns
        tail_length: Number of periods to show in the trail
        sector_colors: Optional mapping of symbol to color
        sector_names: Optional mapping of symbol to display name

    Returns:
        Plotly Figure object
    """
    from config import SECTOR_COLORS, SECTOR_ETFS

    if sector_colors is None:
        sector_colors = SECTOR_COLORS
    if sector_names is None:
        sector_names = SECTOR_ETFS

    fig = go.Figure()

    # Add quadrant backgrounds
    fig.add_shape(type="rect", x0=100, y0=100, x1=110, y1=110,
                  fillcolor="rgba(0, 255, 0, 0.1)", line=dict(width=0))
    fig.add_shape(type="rect", x0=100, y0=90, x1=110, y1=100,
                  fillcolor="rgba(255, 255, 0, 0.1)", line=dict(width=0))
    fig.add_shape(type="rect", x0=90, y0=90, x1=100, y1=100,
                  fillcolor="rgba(255, 0, 0, 0.1)", line=dict(width=0))
    fig.add_shape(type="rect", x0=90, y0=100, x1=100, y1=110,
                  fillcolor="rgba(0, 0, 255, 0.1)", line=dict(width=0))

    # Add quadrant labels
    fig.add_annotation(x=105, y=108, text="LEADING", showarrow=False,
                       font=dict(size=14, color="green"))
    fig.add_annotation(x=105, y=92, text="WEAKENING", showarrow=False,
                       font=dict(size=14, color="orange"))
    fig.add_annotation(x=95, y=92, text="LAGGING", showarrow=False,
                       font=dict(size=14, color="red"))
    fig.add_annotation(x=95, y=108, text="IMPROVING", showarrow=False,
                       font=dict(size=14, color="blue"))

    # Add center lines
    fig.add_hline(y=100, line_dash="dash", line_color="gray", line_width=1)
    fig.add_vline(x=100, line_dash="dash", line_color="gray", line_width=1)

    # Plot each symbol
    for symbol, data in rrg_data.items():
        if len(data) < 2:
            continue

        color = sector_colors.get(symbol, '#ffffff')
        name = sector_names.get(symbol, symbol)
        tail_data = data.tail(tail_length)

        # Trail
        fig.add_trace(go.Scatter(
            x=tail_data['RS_Ratio'],
            y=tail_data['RS_Momentum'],
            mode='lines',
            line=dict(color=color, width=2),
            name=name,
            showlegend=False,
            opacity=0.6
        ))

        # Current position
        current = data.iloc[-1]
        fig.add_trace(go.Scatter(
            x=[current['RS_Ratio']],
            y=[current['RS_Momentum']],
            mode='markers+text',
            marker=dict(size=15, color=color),
            text=[symbol],
            textposition='top center',
            textfont=dict(size=10, color=color),
            name=f"{name} ({symbol})"
        ))

    fig.update_layout(
        title="Relative Rotation Graph",
        template='plotly_dark',
        height=700,
        xaxis=dict(range=[90, 110], dtick=2, title="RS-Ratio"),
        yaxis=dict(range=[90, 110], dtick=2, title="RS-Momentum")
    )

    return fig
