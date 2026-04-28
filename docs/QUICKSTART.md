# Quick Start Guide

Get the AI Fraud Detection Agent up and running in 5 minutes.

---

## Prerequisites

- **Python 3.10+** (check: `python3 --version`)
- **pip** package manager
- **Tesseract OCR** installed system-wide (for PDF parsing)

---

## Installation

### Option A: Automated (Linux/Mac)

```bash
git clone https://github.com/your-username/ai-fraud-detection-sme.git
cd ai-fraud-detection-sme
chmod +x start_demo.sh
./start_demo.sh
```

### Option B: Manual

```bash
# 1. Clone repo
git clone https://github.com/your-username/ai-fraud-detection-sme.git
cd ai-fraud-detection-sme

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Tesseract OCR
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr poppler-utils
# Mac:
brew install tesseract poppler
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

# 5. Generate sample data
python3 scripts/generate_sample_data.py

# 6. Create required directories
mkdir -p reports temp

# 7. Start mock API (Terminal 1)
python3 scripts/mock_api_server.py

# 8. Start main app (Terminal 2)
uvicorn src.app.main:app --reload
```

---

## Using the Demo

1. Open browser: http://localhost:8000
2. Upload `data/sample_bank_statements.csv` as Bank Statement
3. Upload `data/sample_tax_returns.csv` as Tax Return (or any CSV)
4. Click **"🔍 Analyze Application"**
5. Wait 3-5 seconds → View results

**Expected output:**
- Risk Score: **65/100 (Medium)**
- 3 anomalies detected
- 1 AML alert (high-risk jurisdiction)
- APRA Code: **APS222-002**

---

## CLI Mode

```bash
python3 src/app/cli.py \
  --bank-statement data/sample_bank_statements.csv \
  --tax-return data/sample_tax_returns.csv \
  --output reports/demo_result.pdf
```

---

## Alternative Demo: Jupyter Notebook

```bash
# Install jupyter
pip install jupyter

# Launch notebook
jupyter notebook notebooks/demo.ipynb
```

*(Notebook template not yet created – create cells demonstrating agent pipeline)*

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `tesseract: command not found` | Install Tesseract OCR (see Step 4) |
| `ModuleNotFoundError: No module named 'pdf2image'` | `pip install pdf2image` |
| Port 8000 in use | Change port: `uvicorn --port 8080` |
| Mock API errors | Ensure `mock_api_server.py` is running on port 8001 |
| PDF parsing slow | Use CSV instead of PDF for demo |

---

## Project Structure Overview

```
ai-fraud-detection-agent/
├── src/
│   ├── agents/       # 7 autonomous agents
│   ├── app/          # FastAPI backend + frontend
│   └── utils/        # Helpers + config
├── data/             # Sample CSV/JSON files
├── docs/             # Comprehensive documentation
├── tests/            # Pytest test suite
├── scripts/          # Utility scripts
├── reports/          # Generated PDFs (created at runtime)
└── requirements.txt  # Python dependencies
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest --cov=src tests/

# Single test file
pytest tests/test_anomaly_detector.py -v
```

---

## Architecture at a Glance

```
Upload → Ingest (PDF/CSV) → Extract (transactions) → API Lookup (ABR/ATO)
        ↓
    [Parallel Analysis]
        ↓         ↓
  Anomaly     AML
  Detector    Checker
        ↓         ↓
          Risk Scorer (APRA Fields)
                    ↓
             Report Generator (PDF)
```

---

## Sample Data Included

- `data/sample_bank_statements.csv` – 10 transactions with seeded fraud patterns
- `data/sample_tax_returns.csv` – One business tax return
- `data/aml_watchlist.json` – Mock high-risk jurisdictions & entities
- `data/shell_company_addresses.json` – Shell company red flags

---

## What's Next?

1. **Read the docs**: `docs/architecture.md` for deep dive
2. **Explore agents**: Review each agent in `src/agents/`
3. **Run tests**: Ensure everything works
4. **Customize**: Adjust thresholds in `.env`
5. **Deploy**: Push to GitHub + Render.com for live demo

---

## Common Commands

```bash
# Start everything (Linux/Mac)
./start_demo.sh

# Run a single agent manually (for debugging)
python3 -c "from src.agents.anomaly_detector import detect_anomalies; ..."

# View logs (real-time)
tail -f logs/app.log  # if logging to file

# Lint code
flake8 src/

# Format code
black src/
```

---

**Need help?** Check `docs/demo_guide.md` or open an issue on GitHub.
