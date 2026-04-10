@echo off
echo ========================================
echo   ETL Validation Framework - Web Server
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install requirements if needed
echo Installing/Updating dependencies...
pip install -r backend/requirements.txt -q

echo.
echo Starting FastAPI server...
echo.
echo Access the web interface at: http://localhost:8000
echo API documentation at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

cd backend
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
