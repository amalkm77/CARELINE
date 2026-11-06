@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" set "PYTHON=.venv\Scripts\python.exe"
if not defined PYTHON if exist "venv\Scripts\python.exe" set "PYTHON=venv\Scripts\python.exe"

if not defined PYTHON (
    echo CARELINE Python environment was not found.
    echo Create a virtual environment and install requirements.txt first.
    pause
    exit /b 1
)

"%PYTHON%" -c "import flask, flask_cors, vaderSentiment" >nul 2>nul
if errorlevel 1 (
    echo Installing CARELINE Python dependencies, including VADER sentiment analysis...
    "%PYTHON%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Dependency installation failed. Check your internet connection and try again.
        pause
        exit /b 1
    )
)

"%PYTHON%" backend\app.py
if errorlevel 1 (
    echo CARELINE could not start. Check the error above.
    pause
)
