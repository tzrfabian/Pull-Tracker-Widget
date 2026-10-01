@echo off
setlocal

cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel% neq 0 (
    echo Python launcher not found. Install Python 3.9 or newer and try again.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -3 -m venv .venv
    if %errorlevel% neq 0 (
        echo Could not create the virtual environment.
        pause
        exit /b 1
    )
)

echo Installing dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Dependency installation failed.
    pause
    exit /b 1
)

echo Installation complete.
echo Start the widget with: .venv\Scripts\python.exe pull_tracker_widget.py
pause