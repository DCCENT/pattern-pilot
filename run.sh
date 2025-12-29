#!/bin/bash
# Pattern Pilot - Run Script (Linux/macOS)
# Activates virtual environment and launches the application

set -e

echo "==================================="
echo "  Pattern Pilot - Starting..."
echo "==================================="
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running install.sh first..."
    ./install.sh
fi

# Activate virtual environment
source venv/bin/activate

# Launch Streamlit
echo "Launching Pattern Pilot..."
echo "Open your browser to: http://localhost:8501"
echo
echo "Press Ctrl+C to stop the server"
echo

streamlit run app.py
