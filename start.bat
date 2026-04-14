@echo off
REM Constitutional Helper - Windows Launcher
REM This script activates the virtual environment and starts the Streamlit app

echo ========================================
echo Constitutional Helper - Launching...
echo ========================================

REM Check if .venv exists
if not exist ".venv" (
    echo.
    echo Error: Virtual environment not found!
    echo Please run: python -m venv .venv
    echo Then run: .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Start Streamlit
echo.
echo Starting Constitutional Helper on http://localhost:8501
echo Press Ctrl+C to stop the server
echo.
streamlit run app.py

pause
