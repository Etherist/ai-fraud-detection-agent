.PHONY: help install test lint format clean run demo data

help:
	@echo "AI Fraud Detection Agent - Makefile Commands"
	@echo "==========================================="
	@echo ""
	@echo "  make install      - Install dependencies in venv"
	@echo "  make data         - Generate sample data files"
	@echo "  make demo         - Start demo (requires two terminals)"
	@echo "  make backend      - Start FastAPI backend only"
	@echo "  make mock-api     - Start mock ABR/ATO API server"
	@echo "  make test         - Run pytest with coverage"
	@echo "  make lint         - Run flake8 linter"
	@echo "  make format       - Auto-format with black"
	@echo "  make clean        - Remove temp files and caches"
	@echo "  make docs         - Build documentation with mkdocs"
	@echo ""

install:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

data:
	python3 scripts/generate_sample_data.py

backend:
	uvicorn src.app.main:app --reload

mock-api:
	python3 scripts/mock_api_server.py

demo:
	@echo "Starting demo..."
	@echo "1. Start mock API server in one terminal:"
	@echo "   $$ make mock-api"
	@echo ""
	@echo "2. In another terminal, start backend:"
	@echo "   $$ make backend"
	@echo ""
	@echo "3. Open http://localhost:8000"

test:
	pytest tests/ -v --cov=src --cov-report=term --cov-report=html

lint:
	flake8 src/ tests/ --max-line-length=88

format:
	black src/ tests/ --line-length 88

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache .coverage htmlcov
	rm -rf reports/*.pdf reports/*.md 2>/dev/null || true
	rm -rf temp/* 2>/dev/null || true

docs:
	mkdocs build

# Development: run all checks
check: lint format test
	@echo "✅ All checks passed!"
