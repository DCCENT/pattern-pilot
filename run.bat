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

:: Find an available port starting from 8501
set PORT=8501
:find_port
netstat -ano | findstr ":%PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo Port %PORT% is in use, trying next...
    set /a PORT+=1
    if %PORT% gtr 8510 (
        echo ERROR: No available ports found between 8501-8510
        pause
        exit /b 1
    )
    goto find_port
)

echo.
echo Starting Pattern Pilot...
echo.
echo App URL: http://localhost:%PORT%
echo Press Ctrl+C to stop.
echo.

start /b cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:%PORT%"
streamlit run app.py --server.port %PORT%
