#!/bin/bash
# Quick start script for AI Fraud Detection Agent demo

set -e

echo "=============================================="
echo "🚀 AI Fraud Detection Agent - Quick Start"
echo "=============================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3.10+ is required. Please install Python first."
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Install Tesseract if not present (Linux)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if ! command -v tesseract &> /dev/null; then
        echo "⚠️  Tesseract OCR not found. Installing via apt..."
        sudo apt-get update && sudo apt-get install -y tesseract-ocr poppler-utils
    fi
fi

# Generate sample data
echo "📄 Generating sample data..."
python3 scripts/generate_sample_data.py

# Create directories
mkdir -p reports temp

# Start mock API server in background
echo "🌐 Starting mock ABR/ATO API server..."
python3 scripts/mock_api_server.py &
MOCK_PID=$!
sleep 2

# Start main app
echo "🚀 Starting FastAPI application..."
echo ""
echo "=============================================="
echo "✅ System ready!"
echo "📊 Access at: http://localhost:8000"
echo "📚 API docs: http://localhost:8000/docs"
echo "🛑 Press Ctrl+C to stop"
echo "=============================================="
echo ""

# Cleanup on exit
trap "kill $MOCK_PID 2>/dev/null; exit" INT TERM

# Run main app
python3 -m uvicorn src.app.main:app --reload
