#!/bin/bash
# Pattern Pilot - Installation Script (Linux/macOS)
# Creates virtual environment and installs dependencies

set -e

echo "==================================="
echo "  Pattern Pilot - Installation"
echo "==================================="
echo

# Check Python availability
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found. Please install Python 3.9 or later."
    exit 1
fi

echo "Using Python: $PYTHON_CMD"
$PYTHON_CMD --version

# Create virtual environment
echo
echo "Creating virtual environment..."
$PYTHON_CMD -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo
echo "==================================="
echo "  Installation Complete!"
echo "==================================="
echo
echo "To run Pattern Pilot:"
echo "  ./run.sh"
echo
echo "Or manually:"
echo "  source venv/bin/activate"
echo "  streamlit run app.py"
