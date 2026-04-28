@echo off
REM Quick start script for AI Fraud Detection Agent (Windows)

echo ==============================================
echo 🚀 AI Fraud Detection Agent - Quick Start
echo ==============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 3.10+ is required. Please install Python first.
    pause
    exit /b 1
)

echo ✓ Python found
echo.

REM Create virtual environment
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -q -r requirements.txt

REM Generate sample data
echo 📄 Generating sample data...
python scripts\generate_sample_data.py

REM Create directories
if not exist "reports" mkdir reports
if not exist "temp" mkdir temp

REM Start mock API server in new window
echo 🌐 Starting mock ABR/ATO API server...
start "Mock API Server" cmd /c "python scripts\mock_api_server.py"

REM Wait for server to start
timeout /t 3 >nul

REM Start main app
echo 🚀 Starting FastAPI application...
echo.
echo ==============================================
echo ✅ System ready!
echo 📊 Access at: http://localhost:8000
echo 📚 API docs: http://localhost:8000/docs
echo 🛑 Press Ctrl+C to stop
echo ==============================================
echo.

REM Run main app
python -m uvicorn src.app.main:app --reload
