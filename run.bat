@echo off
:: Pattern Pilot - Quick Launcher
:: (Use INSTALL.bat for first-time setup)

title Pattern Pilot

cd /d "%~dp0"

:: Check if already installed
if not exist "venv\Scripts\streamlit.exe" (
    echo.
    echo Pattern Pilot is not installed yet.
    echo Running installer...
    echo.
    call INSTALL.bat
    exit /b
)

:: Verify core dependencies are working
call venv\Scripts\activate.bat
python -c "import streamlit; import yfinance; import pandas" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo Dependencies need to be reinstalled...
    echo.
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

:: Check if port 8501 is already in use
netstat -ano | findstr ":8501" >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo WARNING: Port 8501 is already in use.
    echo Another instance may be running. Close it first.
    echo.
    pause
    exit /b 1
)

echo.
echo Starting Pattern Pilot...
echo.
echo App URL: http://localhost:8501
echo Press Ctrl+C to stop.
echo.

start /b cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8501"
streamlit run app.py
