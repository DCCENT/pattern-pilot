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

:: Activate and run
call venv\Scripts\activate.bat

echo.
echo Starting Pattern Pilot...
echo.
echo App URL: http://localhost:8501
echo Press Ctrl+C to stop.
echo.

start /b cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8501"
streamlit run app.py
