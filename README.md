# Pattern Pilot

**Financial Time Series Pattern Recognition & Signal Testing**

A comprehensive tool for stock pattern detection, backtesting, and AI-powered signal discovery.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## Quick Start (Windows)

### First Time Setup
1. **Download** - Click the green `Code` button above, then `Download ZIP`
2. **Extract** - Right-click the ZIP file and select "Extract All"
3. **Install & Run** - Double-click `INSTALL.bat`
4. **Done!** - The app will open in your browser automatically

### After Installation
Just double-click `run.bat` to start the app.

---

## Features

### Analysis Tools
- **Single Stock Analysis** - Interactive candlestick charts with technical indicators
- **Multi-Stock Comparison** - Compare multiple stocks side by side
- **Pattern Scanner** - Scan for candlestick patterns across multiple symbols
- **Correlation Matrix** - Analyze stock correlations

### Technical Indicators
- Moving Averages (SMA, EMA)
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Volume Analysis

### Pattern Recognition
- Doji, Hammer, Engulfing patterns
- Morning/Evening Star
- Three White Soldiers / Three Black Crows
- And many more...

### Trading Tools
- **Strategy Backtester** - Test trading strategies on historical data
- **AI Trading Lab** - Machine learning-powered signal discovery
- **Sector Analysis** - Sector rotation and performance tracking
- **Options Flow** - Options data analysis

### Drawing Tools
- Fibonacci Retracement
- Trend Lines
- Support/Resistance Lines
- Custom annotations

---

## Requirements

- Windows 10 or higher
- Python 3.10 or higher ([Download Python](https://www.python.org/downloads/))
- Internet connection (for fetching stock data)

---

## Manual Installation

If the one-click installer doesn't work, follow these steps:

```bash
# 1. Open Command Prompt in the extracted folder

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the app
streamlit run app.py
```

---

## Docker (Advanced)

```bash
docker-compose up --build
```

Then open http://localhost:8501

---

## Troubleshooting

### "Python is not installed"
1. Download Python from https://www.python.org/downloads/
2. During installation, **check "Add Python to PATH"**
3. Restart your computer
4. Run `INSTALL.bat` again

### App won't start
1. Make sure no other app is using port 8501
2. Try running `INSTALL.bat` again to reinstall dependencies

### Data not loading
- Check your internet connection
- Some symbols may not be available on Yahoo Finance

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

## Credits

Built with:
- [Streamlit](https://streamlit.io/) - Web framework
- [yfinance](https://github.com/ranaroussi/yfinance) - Yahoo Finance API
- [Plotly](https://plotly.com/) - Interactive charts
- [pandas-ta](https://github.com/twopirllc/pandas-ta) - Technical analysis
