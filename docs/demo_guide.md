# Demo Guide

## Quick Start

This guide walks you through running the AI Fraud Detection Agent demo on your local machine.

---

## Prerequisites

- **Python 3.10+** installed
- **pip** package manager
- **Tesseract OCR** installed (for PDF support)
- **Git** (optional, for cloning)

---

## Step-by-Step Setup

### 1. Clone and Navigate

```bash
git clone https://github.com/your-username/ai-fraud-detection-sme.git
cd ai-fraud-detection-sme
```

### 2. Create Virtual Environment

```bash
# Linux/Mac
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Tesseract OCR

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install tesseract-ocr
sudo apt install poppler-utils  # for pdf2image (optional)
```

**Mac:**
```bash
brew install tesseract
brew install poppler
```

**Windows:**
Download from [UB Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH.

Verify:
```bash
tesseract --version
# Should output: tesseract 5.x.x
```

### 5. Start Mock API Server

The demo requires mock ABR/ATO APIs. Open a terminal:

```bash
python scripts/mock_api_server.py
```

You should see:
```
INFO:     Started server process [xxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

Leave this terminal running.

### 6. Start Main Application

Open a **new terminal** and run:

```bash
uvicorn src.app.main:app --reload
```

You should see:
```
INFO:     Will watch for changes in these directories: [...]
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 7. Open Frontend

Navigate to: http://localhost:8000

You should see the upload form.

---

## Running the Demo

### Method A: Upload Sample Files

1. Click "Choose File" under **Bank Statement**
   - Select: `data/sample_bank_statements.csv`
2. Click "Choose File" under **Tax Return**
   - For demo, you can use any CSV from `data/` (or create your own matching the format)
3. Click **"🔍 Analyze Application"**
4. Wait 3-5 seconds (spinner shows)

**Expected Result:**
- Risk Score: **65/100 (Medium)**
- Anomalies: 3 detected (2 round-dollar + 1 outlier)
- AML Alerts: 1 high-risk jurisdiction
- APRA Code: **APS222-002** (Substandard)
- Impairment Provision: ~$27,500

### Method B: CLI Demo

In a terminal:

```bash
python src/app/cli.py \
  --bank-statement data/sample_bank_statements.csv \
  --tax-return data/sample_tax_returns.csv \
  --output reports/demo_output.pdf \
  --format pdf
```

**Expected console output** (see README.md).

### Method C: API Call (cURL)

```bash
# Upload
curl -X POST -F "bank_statement=@data/sample_bank_statements.csv" \
            -F "tax_return=@data/sample_tax_returns.csv" \
            http://localhost:8000/upload/ > /tmp/task.json

# Extract task_id
TASK_ID=$(cat /tmp/task.json | grep -o '"task_id":"[^"]*"' | cut -d'"' -f4)

# Poll for results
for i in {1..30}; do
  curl http://localhost:8000/results/$TASK_ID | jq .
  sleep 2
done
```

---

## Understanding the Results

### Risk Score Breakdown

| Score Range | Category | Color | Interpretation |
|-------------|----------|-------|----------------|
| 0-29 | Low | 🟢 Green | Minimal risk, proceed |
| 30-69 | Medium | 🟠 Orange | Additional review recommended |
| 70-100 | High | 🔴 Red | Deny or require significant collateral |

### Anomaly Types Detected

| Type | Trigger | Points | Severity |
|-----|---------|--------|----------|
| `round_dollar` | Amount divisible by $1,000 (≥$1k) | +20 | High |
| `outlier` | Isolation Forest (statistical) | +15 (med) / +23 (high) | Medium/High |
| `high_value` | Single transaction >$250k | +25 | High |
| `suspicious_pattern` | Round-dollar + generic description | +15 | Medium |

### AML Alert Types

| Type | Trigger | Severity | Example |
|------|---------|----------|---------|
| `high_risk_jurisdiction` | Counterparty jurisdiction in watchlist | High | XY, ZW (sanctioned countries) |
| `watchlist_entity` | Business name matches AML watchlist | High | "Shell Corp", "Fake Biz" |
| `watchlist_abn` | ABN in sanctions list | High | ABN 999... |
| `shell_company_indicator` | Address contains shell phrase | Medium | "PO Box", "Virtual Office" |
| `possible_structuring` | Amount $9k-$10k (sub-reporting-threshold) | Medium | $9,800 deposit |

---

## Interpreting APRA Fields

The report includes these APRA-specific fields:

| Field | Example | Meaning |
|-------|---------|---------|
| `asset_classification` | Substandard | Credit quality grade (Standard/Substandard/Doubtful/Loss) |
| `regulatory_code` | APS222-002 | APRA reporting code for this classification |
| `impairment_provision` | $27,500.00 | Amount to set aside as expected loss |
| `collateral_value` | $500,000.00 | Value of pledged assets |
| `loan_to_value_ratio` | 0.8 (80%) | Exposure / Collateral |
| `requires_manual_review` | true | Must be reviewed by senior underwriter |
| `review_priority` | High | Urgency of review |

---

## Exploring the Code

### Agent Pipeline

Follow the processing flow in `src/app/main.py` → `process_files()`:

```python
# Step 1: Ingest
bank_raw = document_ingestor.ingest_file(bank_path)
tax_raw = document_ingestor.ingest_file(tax_path)

# Step 2: Extract
bank_data = data_extractor.extract(bank_raw)
transactions = bank_data['transactions']

# Step 3: API Lookups
abr = api_lookup_agent.lookup_business(abn, business_name)
ato = api_lookup_agent.lookup_tax_return(abn)

# Step 4: Anomaly Detection
anomalies = anomaly_detector.detect_anomalies(transactions)

# Step 5: AML Screening
aml_alerts = aml_checker.check_transactions(transactions, business_details)

# Step 6: Risk Scoring
risk_data = risk_scorer.calculate_score(anomalies, aml_alerts)

# Step 7: Report Generation
report = report_generator.generate_report(...)
```

### Viewing PDF Reports

Reports are saved to `reports/` directory:

```bash
ls -la reports/
# audit_a1b2c3d4_20250428.pdf
```

Open with any PDF viewer:
```bash
xdg-open reports/audit_*.pdf  # Linux
open reports/audit_*.pdf      # Mac
start reports/audit_*.pdf     # Windows
```

---

## Customizing the Demo

### Changing Thresholds

Edit `.env`:
```bash
RISK_SCORE_THRESHOLDS={"Low": 30, "Medium": 70, "High": 100}
ISOLATION_FOREST_CONTAMINATION=0.15  # More sensitive anomaly detection
ROUND_DOLLAR_THERSHOLD=1000  # Minimum for round-dollar flag
```

### Modifying Watchlists

Edit `data/aml_watchlist.json`:
```json
{
  "jurisdictions": ["XY", "ZW", "KP", "NEW_COUNTRY"],
  "entities": ["Shell Corp", "Fake Biz", "New Entity"],
  "abns": ["999999999", "111111111"]
}
```

Restart the app, re-run analysis.

### Adding New Anomaly Types

Extend `src/agents/anomaly_detector.py`:
```python
def detect_anomalies(self, transactions):
    anomalies = []
    for tx in transactions:
        # New rule: Weekend transactions
        if tx['date'].dayofweek >= 5:  # Sat/Sun
            anomalies.append({
                "type": "weekend_transaction",
                "severity": "medium",
                ...
            })
```

---

## Troubleshooting

### "TesseractNotFoundError"

**Issue:** Tesseract OCR not installed or not in PATH.

**Fix:**
```bash
# Check path
which tesseract

# If not found, install:
sudo apt install tesseract-ocr  # Ubuntu
# or brew install tesseract    # Mac
# or download installer for Windows
```

### "ModuleNotFoundError: No module named 'pdf2image'"

**Fix:** Install poppler-utils and pdf2image:
```bash
sudo apt install poppler-utils  # Linux
pip install pdf2image
```

### "Port 8000 already in use"

**Fix:** Use different port:
```bash
uvicorn src.app.main:app --reload --port 8080
```

### "File too large" error

**Fix:** Increase limit in `.env`:
```bash
MAX_FILE_SIZE_MB=20
```

### Mock API not responding

**Check:** Make sure `scripts/mock_api_server.py` is running on port 8001.
Default `MOCK_ABR_API_URL` in `.env` points to `http://localhost:8001/abr`.

**Fix:** Update `.env`:
```bash
MOCK_ABR_API_URL=http://localhost:8001/abr
MOCK_ATO_API_URL=http://localhost:8001/ato
```

---

## Performance Tips

1. **Use CSV over PDF** - CSV parsing is ~10x faster than PDF OCR
2. **Limit file size** - Large PDFs (>50 pages) will be slow
3. **Disable PDF OCR** if not needed: in `.env`, set `ENABLE_OCR=false` (future enhancement)
4. **Batch processing** - For multiple applications, implement Celery queue (production)

---

## Demo Presentation Tips

If presenting to employers/team:

1. **Start with the problem:** "SME loan fraud costs Australian banks $X annually"
2. **Show the architecture diagram** (docs/architecture.md)
3. **Live demo:**
   - Upload sample file
   - Watch results appear
   - Download PDF report
   - Highlight APRA fields
4. **Code walkthrough** (5 min):
   - Show agent modules (`src/agents/`)
   - Explain Isolation Forest (pyod)
   - Show APRA mapping in `risk_scorer.py`
5. **Q&A:**
   - What about real APIs? (Can integrate with ABR/ATO)
   - Accuracy? (Tunable thresholds, more data needed)
   - Scalability? (Add Celery, Redis, PostgreSQL)

---

## Next Steps

After demo:
1. **Push to GitHub** and enable GitHub Pages for docs
2. **Deploy to Render.com** (free tier)
3. **Add more sample files** with edge cases
4. **Write a blog post** about the Agent Engineering approach
5. **Add unit tests** (pytest) if presenting to technical audience

---

## Contact & Support

Issues? Open an issue on GitHub: https://github.com/your-username/ai-fraud-detection-sme/issues

---

*Enjoy the demo! 🚀*
