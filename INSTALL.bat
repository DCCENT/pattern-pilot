@echo off
setlocal enabledelayedexpansion

:: Pattern Pilot - One-Click Installer
:: ====================================

title Pattern Pilot Installer

:: Colors for output
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "CYAN=[96m"
set "RESET=[0m"

echo.
echo %CYAN%========================================%RESET%
echo %CYAN%    Pattern Pilot - One-Click Setup    %RESET%
echo %CYAN%========================================%RESET%
echo.

:: Change to script directory
cd /d "%~dp0"

:: Step 1: Check for Python
echo %YELLOW%[1/4]%RESET% Checking for Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo %RED%ERROR: Python is not installed or not in PATH%RESET%
    echo.
    echo %YELLOW%Please install Python 3.10 or higher:%RESET%
    echo   1. Go to: https://www.python.org/downloads/
    echo   2. Download Python 3.12 (or latest)
    echo   3. IMPORTANT: Check "Add Python to PATH" during installation
    echo   4. Restart your computer after installation
    echo   5. Run this installer again
    echo.
    echo Opening Python download page...
    start https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo %GREEN%   Found Python %PYTHON_VERSION%%RESET%

:: Step 2: Create virtual environment
echo.
echo %YELLOW%[2/4]%RESET% Setting up virtual environment...
if not exist "venv" (
    echo        Creating new virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo %RED%ERROR: Failed to create virtual environment%RESET%
        pause
        exit /b 1
    )
    echo %GREEN%   Virtual environment created%RESET%
) else (
    echo %GREEN%   Virtual environment already exists%RESET%
)

:: Step 3: Install dependencies
echo.
echo %YELLOW%[3/4]%RESET% Installing dependencies (this may take a few minutes)...
call venv\Scripts\activate.bat
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo %RED%ERROR: Failed to install dependencies%RESET%
    pause
    exit /b 1
)
echo %GREEN%   All dependencies installed%RESET%

:: Step 4: Launch the app
echo.
echo %YELLOW%[4/4]%RESET% Starting Pattern Pilot...
echo.
echo %GREEN%========================================%RESET%
echo %GREEN%   Setup complete! Launching app...    %RESET%
echo %GREEN%========================================%RESET%
echo.
echo %CYAN%The app will open in your browser automatically.%RESET%
echo %CYAN%If it doesn't, go to: http://localhost:8501%RESET%
echo.
echo %YELLOW%Keep this window open while using the app.%RESET%
echo %YELLOW%Press Ctrl+C to stop the server.%RESET%
echo.

:: Launch browser after a short delay, then start streamlit
start /b cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:8501"
streamlit run app.py

:: If we get here, the app was closed
echo.
echo %YELLOW%Pattern Pilot has stopped.%RESET%
pause
