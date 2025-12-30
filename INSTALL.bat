@echo off
setlocal enabledelayedexpansion

:: Pattern Pilot - One-Click Installer
:: ====================================

:: IMPORTANT: Keep window open no matter what happens
:: This prevents the window from closing before user sees errors
if "%~1"=="" (
    cmd /k "%~f0" run
    exit /b
)

title Pattern Pilot Installer

:: Check if we're in the right directory (requirements.txt should exist)
:: This catches the common error of running from inside a ZIP file
if not exist "%~dp0requirements.txt" (
    echo.
    echo ========================================
    echo    ERROR: Required files not found!
    echo ========================================
    echo.
    echo This usually means:
    echo.
    echo   1. You're running this from INSIDE a ZIP file
    echo      FIX: Extract/unzip the folder first, then run INSTALL.bat
    echo.
    echo   2. Some files are missing from the download
    echo      FIX: Re-download from https://github.com/DCCENT/pattern-pilot
    echo.
    echo Current location: %~dp0
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo.
echo ========================================
echo     Pattern Pilot - One-Click Setup
echo ========================================
echo.

:: Change to script directory
cd /d "%~dp0"

:: Step 1: Check if venv already exists with working Python
echo [1/4] Checking Python environment...

if exist "venv\Scripts\python.exe" (
    echo    Found existing virtual environment
    set "PYTHON_CMD=venv\Scripts\python.exe"
    goto :venv_ready
)

:: Try to find Python using multiple methods
set "PYTHON_CMD="

:: Method 1: Check 'py' launcher (most reliable on Windows)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py"
    for /f "tokens=2" %%i in ('py --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo    Found Python !PYTHON_VERSION! via py launcher
    goto :python_found
)

:: Method 2: Check 'python' in PATH
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo    Found Python !PYTHON_VERSION! in PATH
    goto :python_found
)

:: Method 3: Check 'python3' in PATH
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python3"
    for /f "tokens=2" %%i in ('python3 --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo    Found Python !PYTHON_VERSION! in PATH
    goto :python_found
)

:: Method 4: Check common installation directories
for %%P in (
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%LocalAppData%\Programs\Python\Python310\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles%\Python310\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
) do (
    if exist %%P (
        set "PYTHON_CMD=%%~P"
        for /f "tokens=2" %%i in ('"%%~P" --version 2^>^&1') do set PYTHON_VERSION=%%i
        echo    Found Python !PYTHON_VERSION! at %%~P
        goto :python_found
    )
)

:: Python not found anywhere
echo.
echo ERROR: Python is not installed
echo.
echo Please install Python 3.10 or higher:
echo   1. Go to: https://www.python.org/downloads/
echo   2. Download Python 3.12 (or latest)
echo   3. IMPORTANT: Check "Add Python to PATH" during installation
echo   4. Run this installer again
echo.
echo Opening Python download page...
start https://www.python.org/downloads/
echo.
pause
exit /b 1

:python_found
:: Validate Python version (need 3.10+)
for /f "tokens=1,2 delims=." %%a in ("!PYTHON_VERSION!") do (
    set "PY_MAJOR=%%a"
    set "PY_MINOR=%%b"
)
if !PY_MAJOR! lss 3 (
    echo ERROR: Python 3.10+ required, found !PYTHON_VERSION!
    echo Please install Python 3.10 or higher from https://www.python.org/downloads/
    pause
    exit /b 1
)
if !PY_MAJOR! equ 3 if !PY_MINOR! lss 10 (
    echo ERROR: Python 3.10+ required, found !PYTHON_VERSION!
    echo Please install Python 3.10 or higher from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Step 2: Create virtual environment
echo.
echo [2/4] Setting up virtual environment...
if not exist "venv" (
    echo    Creating new virtual environment...
    %PYTHON_CMD% -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo    Virtual environment created
) else (
    echo    Virtual environment already exists
)

:venv_ready
:: Step 3: Install/verify dependencies
echo.
echo [3/4] Checking dependencies...
call venv\Scripts\activate.bat

:: Check if streamlit is already installed
pip show streamlit >nul 2>&1
if %errorlevel% equ 0 (
    echo    Dependencies already installed
) else (
    echo    Installing dependencies (this may take a few minutes)...
    pip install --upgrade pip
    if %errorlevel% neq 0 (
        echo ERROR: Failed to upgrade pip
        pause
        exit /b 1
    )
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Failed to install dependencies
        echo Please check your internet connection and try again.
        pause
        exit /b 1
    )
    echo    All dependencies installed
)

:: Step 4: Create desktop shortcut
echo.
echo [4/5] Creating desktop shortcut...

set "SHORTCUT=%USERPROFILE%\Desktop\Pattern Pilot.lnk"
set "TARGET=%~dp0run.bat"
set "SCRIPT_DIR=%~dp0"

:: Create shortcut using PowerShell script
powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%create_shortcut.ps1" -ShortcutPath "%SHORTCUT%" -TargetPath "%TARGET%" -WorkingDir "%SCRIPT_DIR%" >nul 2>&1

if exist "%SHORTCUT%" (
    echo    Desktop shortcut created
) else (
    echo    Could not create shortcut (non-critical)
)

:: Step 5: Check port and launch the app
echo.
echo [5/5] Starting Pattern Pilot...

:: Find an available port
set PORT=8501
:find_port
netstat -ano | findstr ":%PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo    Port %PORT% is in use, trying next...
    set /a PORT+=1
    if %PORT% gtr 8510 (
        echo ERROR: No available ports found between 8501-8510
        pause
        exit /b 1
    )
    goto find_port
)

echo.
echo ========================================
echo    Setup complete! Launching app...
echo ========================================
echo.
echo The app will open in your browser automatically.
echo If it doesn't, go to: http://localhost:%PORT%
echo.
echo Keep this window open while using the app.
echo Press Ctrl+C to stop the server.
echo.

:: Launch browser after a short delay, then start streamlit
start /b cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:%PORT%"
streamlit run app.py --server.port %PORT%

:: If we get here, the app was closed
echo.
echo Pattern Pilot has stopped.
pause
