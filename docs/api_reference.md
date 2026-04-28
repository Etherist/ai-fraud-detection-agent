# API Reference

## Base URL

When running locally:
```
http://localhost:8000
```

Production URL will be deployed to:
```
https://ai-fraud-detection-sme.onrender.com  (or similar)
```

---

## Authentication

**Current (Demo):** None (open endpoints)

**Production (Planned):** JWT Bearer tokens or OAuth2

---

## Endpoints

### Health Check

#### `GET /health`

Check if the API is operational.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-04-28T14:32:10.123456",
  "version": "1.0.0"
}
```

---

### Frontend

#### `GET /`

Serves the HTML frontend (single-page application).

**Response:** `text/html`

---

### File Upload

#### `POST /upload/`

Upload bank statement and tax return for analysis. Accepts multipart form data.

**Request:**
- Content-Type: `multipart/form-data`
- Fields:
  - `bank_statement` (file, required): CSV or PDF
  - `tax_return` (file, required): CSV or PDF

**Response (202 Accepted):**
```json
{
  "task_id": "a1b2c3d4",
  "status": "processing"
}
```

**Example cURL:**
```bash
curl -X POST \
  -F "bank_statement=@statement.csv" \
  -F "tax_return=@tax.pdf" \
  http://localhost:8000/upload/
```

**Error Responses:**
- `400 Bad Request`: Invalid file format, file too large
- `413 Payload Too Large`: Exceeds 10MB limit
- `500 Internal Server Error`: Processing failed (see `error` field)

---

### Get Results

#### `GET /results/{task_id}`

Retrieve analysis results for a completed task.

**Path Parameters:**
- `task_id` (string, required): Task identifier returned from `/upload/`

**Response (Processing):**
```json
{
  "status": "processing"
}
```

**Response (Completed):**
```json
{
  "task_id": "a1b2c3d4",
  "status": "completed",
  "risk_score": 85,
  "category": "High",
  "anomalies": [
    {
      "type": "round_dollar",
      "transaction_id": 3,
      "amount": 10000.00,
      "severity": "high",
      "message": "Round-dollar transaction: $10,000.00"
    },
    {
      "type": "outlier",
      "transaction_id": 5,
      "amount": 250000.00,
      "severity": "high",
      "message": "Statistically unusual transaction amount: $250,000.00"
    }
  ],
  "aml_alerts": [
    {
      "type": "high_risk_jurisdiction",
      "transaction_id": 10,
      "jurisdiction": "ZW",
      "severity": "high",
      "message": "Transaction linked to high-risk jurisdiction: ZW"
    }
  ],
  "apra_fields": {
    "asset_classification": "Substandard",
    "impairment_provision": 7500.00,
    "regulatory_code": "APS222-002",
    "collateral_value": 500000.00,
    "loan_to_value_ratio": 0.8,
    "requires_manual_review": true,
    "review_priority": "High"
  },
  "report_url": "/reports/audit_a1b2c3d4_20250428.pdf",
  "processed_at": "2025-04-28T14:32:15.123456",
  "business_details": {
    "business_name": "Acme Pty Ltd",
    "abn": "123456789"
  },
  "summary": {
    "total_transactions": 10,
    "anomaly_count": 2,
    "aml_alert_count": 1
  }
}
```

**Error Responses:**
- `404 Not Found`: Task ID does not exist
- `500 Internal Server Error`: Processing failed (check `status: "failed"`)

---

### Download Report

#### `GET /reports/{filename}`

Download a generated PDF or Markdown report.

**Path Parameters:**
- `filename` (string, required): Report filename

**Response:**
- For PDF: `application/pdf`
- For Markdown: `text/markdown`

**Example:**
```bash
curl -O http://localhost:8000/reports/audit_a1b2c3d4_20250428.pdf
```

---

### Sample Data (Demo)

#### `GET /api/sample-data`

Get pre-loaded sample transaction data for demo purposes.

**Response:**
```json
{
  "sample": [
    {
      "transaction_id": 1,
      "date": "2025-07-01",
      "amount": 50000.00,
      "description": "Invoice #123",
      "business_name": "Acme Pty Ltd",
      "abn": "123456789",
      "counterparty_jurisdiction": "AU"
    },
    ...
  ]
}
```

---

## Data Models

### Request Models

#### `AnalysisRequest`
```json
{
  "business_name": "Acme Pty Ltd (optional)",
  "abn": "123456789 (optional)",
  "upload_id": "temp_file_id (optional)"
}
```

### Response Models

#### `AnalysisResult` (Full Response)
```json
{
  "task_id": "string",
  "status": "completed",
  "risk_score": 0-100,
  "category": "Low|Medium|High",
  "anomalies": [...],
  "aml_alerts": [...],
  "apra_fields": {...},
  "report_url": "/reports/...",
  "processed_at": "ISO 8601 timestamp",
  "business_details": {...},
  "summary": {
    "total_transactions": int,
    "anomaly_count": int,
    "aml_alert_count": int
  }
}
```

#### `Anomaly`
```json
{
  "type": "round_dollar|outlier|high_value",
  "transaction_id": int,
  "amount": float,
  "severity": "low|medium|high",
  "message": "string explanation"
}
```

#### `AMLAlert`
```json
{
  "type": "high_risk_jurisdiction|watchlist_entity|...",
  "transaction_id": int|null,
  "severity": "medium|high",
  "message": "string explanation",
  "detail": "string (optional)"
}
```

#### `APRAFields`
```json
{
  "asset_classification": "Standard|Substandard|Doubtful|Loss",
  "impairment_provision": float,
  "regulatory_code": "APS222-001|002|003|004",
  "collateral_value": float,
  "loan_to_value_ratio": 0.0 - 1.0,
  "requires_manual_review": boolean,
  "review_priority": "Low|Medium|High",
  "apra_reporting_category": "STANDARD_RISK|ELEVATED_RISK|HIGH_IMPAIRMENT|CRITICAL_AML"
}
```

---

## Error Handling

### Standard Error Format
```json
{
  "detail": "Human-readable error message",
  "error_code": "VALIDATION_ERROR",  // optional
  "field": "bank_statement"  // optional
}
```

### Common HTTP Status Codes

| Code | Meaning | Cause |
|------|---------|-------|
| 200 | OK | Request successful |
| 202 | Accepted | Upload queued for async processing |
| 400 | Bad Request | Missing file, invalid format |
| 404 | Not Found | Task ID not found |
| 413 | Payload Too Large | File exceeds size limit |
| 500 | Internal Server Error | Processing exception |

---

## Rate Limiting

**Current:** None (demo)

**Planned:** 100 requests/hour per IP for demo deployment

---

## CORS

Enabled for all origins (`*`). Configure in production for specific domains.

---

## OpenAPI Schema

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **JSON Schema:** http://localhost:8000/openapi.json

---

## SDK / Client Examples

### Python (requests)
```python
import requests

# Upload
files = {
    'bank_statement': open('statement.csv', 'rb'),
    'tax_return': open('tax.pdf', 'rb')
}
response = requests.post('http://localhost:8000/upload/', files=files)
task_id = response.json()['task_id']

# Poll
import time
while True:
    result = requests.get(f'http://localhost:8000/results/{task_id}').json()
    if result.get('status') == 'completed':
        print(f"Risk: {result['risk_score']}/100")
        break
    time.sleep(2)
```

### JavaScript (Browser Fetch)
```javascript
const formData = new FormData();
formData.append('bank_statement', fileInput1.files[0]);
formData.append('tax_return', fileInput2.files[0]);

const response = await fetch('/upload/', {
    method: 'POST',
    body: formData
});
const { task_id } = await response.json();

// Poll for results
const poll = setInterval(async () => {
    const res = await fetch(`/results/${task_id}`);
    const data = await res.json();
    if (data.status === 'completed') {
        clearInterval(poll);
        displayResults(data);
    }
}, 2000);
```

---

## Webhooks (Future)

Planned webhook notifications for completed analyses:
```json
{
  "event": "analysis.completed",
  "task_id": "a1b2c3d4",
  "risk_score": 85,
  "callback_url": "https://your-bank.com/hooks/fraud-detection"
}
```

---

*API Version: 1.0.0 | Last Updated: 2026-04-28*
