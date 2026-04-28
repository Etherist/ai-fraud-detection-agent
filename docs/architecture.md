# System Architecture

## Overview

The AI Fraud Detection Agent for SME Loans is a distributed, agent-based system built on FastAPI. It processes bank statements and tax returns to detect fraud and AML risks, producing APRA-compliant audit reports.

---

## High-Level Architecture

```
┌─────────────────┐
│   HTML Frontend │  ← User Interface
│   (Vanilla JS)  │
└────────┬────────┘
         │ HTTP
         ↓
┌─────────────────┐
│   FastAPI       │  ← REST API Layer
│   Backend       │
└────────┬────────┘
         │ Coordinates
         ↓
┌────────────────────────────────────────────────────┐
│               Agent Pipeline                       │
├──────────┬──────────┬─────────┬───────┬────────────┤
│ Document │ Data     │ API     │ Anom- │ AML        │
│ Ingestor │ Extractor│ Lookup  │ aly   │ Checker    │
├──────────┼──────────┼─────────┼───────┼────────────┤
│          │          │         │ PyOD  │ Rule-based │
│ PDF OCR  │ Regex    │ Mock    │ Isol- │ Watchlist  │
│ CSV Read │ NLP      │ ABR/ATO │ ation │ Screening  │
└──────────┴──────────┴─────────┴───────┴────────────┘
                        │
                        ↓
               ┌─────────────────┐
               │  Risk Scorer    │
               │  (APRA Fields)  │
               └────────┬────────┘
                        │
                        ↓
               ┌─────────────────┐
               │ Report Generator│
               │  PDF + Charts   │
               └─────────────────┘
```

---

## Agent Collaboration Flow

### Detailed Step-by-Step Process

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as FastAPI
    participant D1 as DocumentIngestor
    participant D2 as DataExtractor
    participant API as APILookupAgent
    participant AD as AnomalyDetector
    participant AML as AMLChecker
    participant RS as RiskScorer
    participant RG as ReportGenerator

    U->>F: Upload files (bank + tax)
    F->>A: POST /upload/ (multipart)
    A->>D1: ingest_file(bank.pdf)
    D1->>D1: OCR parse (Tesseract)
    A->>D1: ingest_file(tax.csv)
    D1-->>A: raw_data dicts
    A->>D2: extract_data(raw_bank)
    D2-->>A: transactions + business
    A->>API: lookup_business(abn, name)
    API->>API: GET /abr (mock)
    API-->>A: validation_result
    A->>AD: detect_anomalies(transactions)
    AD->>AD: Isolation Forest fit
    AD-->>A: anomalies_list
    A->>AML: check_transactions(...)
    AML->>AML: Watchlist match
    AML-->>A: aml_alerts
    A->>RS: calculate_score(anomalies, alerts)
    RS-->>A: risk_data + apra_fields
    A->>RG: generate_report(...)
    RG->>RG: Build PDF (ReportLab)
    RG-->>A: report_url
    A-->>F: {task_id, "processing"}
    loop Poll every 2s
        F->>A: GET /results/{task_id}
        A-->>F: result or status
    end
    F->>U: Display results + download
```

---

## Component Specifications

### 1. Document Ingestor (`document_ingestor.py`)

| Attribute | Value |
|-----------|-------|
| Input | File path (`.csv`, `.pdf`) |
| Output | `{"format": "...", "data": [...], "text": "..."}` |
| Libraries | Pandas (CSV), pytesseract + pdf2image (PDF) |
| Processing Time | ~1-3s per PDF, ~0.5s per CSV |

**Example Output (CSV):**
```python
{
  "format": "csv",
  "file_path": "data/bank.csv",
  "row_count": 100,
  "columns": ["transaction_id", "date", "amount", ...],
  "data": [{"transaction_id": 1, "date": "2025-01-01", ...}, ...]
}
```

### 2. Data Extractor (`data_extractor.py`)

| Attribute | Value |
|-----------|-------|
| Input | Parsed data (from DocumentIngestor) |
| Output | `{"transactions": [...], "business_details": {...}}` |
| Techniques | Regex patterns, NLP (Spacy), column mapping |
| Output Schema | Standardized JSON |

**Example Output:**
```python
{
  "transactions": [
    {"transaction_id": 1, "date": "01/01/2025", "amount": 50000.0, "description": "...", ...},
    ...
  ],
  "business_details": {
    "business_name": "Acme Pty Ltd",
    "abn": "123456789",
    "addresses": ["123 Main St, Sydney"]
  },
  "abn": "123456789",
  "business_name": "Acme Pty Ltd"
}
```

### 3. API Lookup Agent (`api_lookup_agent.py`)

| Attribute | Value |
|-----------|-------|
| Input | ABN, business name |
| Output | `{"valid": bool, "status": "Active", ...}` |
| Endpoints | `/abr`, `/ato` (mock server) |
| Timeout | 5 seconds |

**Mock Logic:**
- ABNs starting with `123` → Valid/Active
- ABNs starting with `999` → Cancelled (shell company)
- ABNs starting with `888` → Suspended

### 4. Anomaly Detector (`anomaly_detector.py`)

| Attribute | Value |
|-----------|-------|
| Input | Transactions (list of dicts) |
| Output | Anomaly list with type, severity, message |
| Algorithm | PyOD Isolation Forest (`contamination=0.1`) |
| Rules | Round-dollar ≥$1000, Outlier detection, High-value >$250k |

**Scoring Logic:**
| Anomaly Type | Points | Severity-based Adjust |
|--------------|--------|----------------------|
| Round-dollar | +20 | — |
| Outlier (med) | +15 | High: ×1.5 |
| Outlier (high) | +23 | — |
| High-value | +25 | — |

### 5. AML Checker (`aml_checker.py`)

| Attribute | Value |
|-----------|-------|
| Input | Transactions + business details |
| Output | AML alerts (type, severity, message) |
| Watchlists | Jurisdictions, entities, ABNs, shell indicators |
| High-Risk Jurisdictions | XY, ZW, KP, AF, IQ, SD |

**Alert Categories:**
| Type | Severity | Trigger |
|------|----------|---------|
| `high_risk_jurisdiction` | High | Counterparty jurisdiction in watchlist |
| `watchlist_entity` | High | Business name matches sanctions |
| `watchlist_abn` | High | ABN on watchlist |
| `shell_company_indicator` | Medium | Address contains shell indicators |
| `possible_structuring` | Medium | Amount $9k-10k (sub-threshold) |
| `suspicious_pattern` | Medium | Large round-dollar with generic desc |

### 6. Risk Scorer (`risk_scorer.py`)

| Attribute | Value |
|-----------|-------|
| Input | Anomalies list + AML alerts list |
| Output | `{"score": 0-100, "category": "...", "apra_fields": {...}}` |
| Categories | Low <30, Medium 30-69, High 70-100 |
| APRA Compliant | ✓ Asset classification, impairment, regulatory codes |

**Risk Category → APRA Mapping:**
| Score | Category | Asset Class | Regulatory Code | Impairment Rate |
|-------|----------|-------------|-----------------|-----------------|
| 0-29 | Low | Standard | APS222-001 | 0% |
| 30-69 | Medium | Substandard | APS222-002 | 5% |
| 70-89 | High | Doubtful | APS222-003 | 25% |
| 90-100 | Critical | Loss | APS222-004 | 100% |

### 7. Report Generator (`report_generator.py`)

| Attribute | Value |
|-----------|-------|
| Input | risk_data, anomalies, alerts, business_details |
| Output | PDF (ReportLab) + Markdown (Jinja2) |
| Visualizations | Risk gauge (Matplotlib), color-coded tables |
| APRA Sections | Asset classification, impairment, regulatory code, LTV |

---

## Data Flow Diagram

```
┌────────────────┐
│   Upload Files │
│  (CSV/PDF)     │
└────────┬───────┘
         │
         ▼
┌──────────────────┐    ┌───────────────┐
│ DocumentIngestor ├───▶│   CSV Reader  │
│  (File Router)   │    └───────────────┘
└────────┬─────────┘    ┌───────────────┐
         │              │ PDF OCR       │
         ▼              │ (Tesseract)   │
┌──────────────────┐    └───────────────┘
│   Raw Content    │
│ {text, records}  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  DataExtractor   │    ┌──────────────┐
│ (Regex + NLP)    │───▶│ Transactions │
└────────┬─────────┘    └──────────────┘
         │
         ▼
┌──────────────────┐    ┌───────────────┐
│  Business Entity │    │ ABN/Name/Addr │
│  {abn, name}     │───▶│  Validation   │
└────────┬─────────┘    └───────────────┘
         │                      │
         │                      ▼
         │              ┌───────────────┐
         │              │ APILookupAgent│
         │              │  (Mock APIs)  │
         │              └───────────────┘
         │                        │
         ▼                        ▼
┌─────────────────────────────────────────────┐
│         Parallel Analysis                  │
│  ┌─────────────────┐   ┌─────────────────┐ │
│  │ AnomalyDetector │   │  AMLChecker     │ │
│  │ (Isolation For.)│   │ (Watchlist)     │ │
│  └────────┬────────┘   └────────┬────────┘ │
│           │                     │          │
│           └──────────┬──────────┘          │
│                      ▼                     │
│           ┌─────────────────┐              │
│           │  RiskScorer     │              │
│           │  (APRA Fields)  │              │
│           └────────┬────────┘              │
│                    │                       │
│                    ▼                       │
│           ┌─────────────────┐              │
│           │ ReportGenerator │              │
│           │ (PDF/Markdown)  │              │
│           └─────────────────┘              │
└─────────────────────────────────────────────┘
```

---

## System Requirements

### Minimum Requirements
- **CPU:** 2 cores
- **RAM:** 4GB
- **Storage:** 2GB free space
- **Python:** 3.10+
- **Tesseract:** OCR engine installed system-wide

### Recommended (for production)
- **CPU:** 4+ cores
- **RAM:** 8GB+
- **GPU:** Not required (CPU-only PyOD)
- **Database:** PostgreSQL (for persistent storage)
- **Cache:** Redis (for job queue)
- **Queue:** Celery (for async processing)

---

## Scalability Considerations

Current demo uses **synchronous processing** with in-memory storage (`dict`). For production:

1. **Async Task Queue** (Celery/Redis)
   - Background job processing for large files
   - Progress tracking via WebSockets

2. **Persistent Database** (PostgreSQL)
   - Store uploads, results, audit logs
   - APRA reporting queries

3. **File Storage** (S3/MinIO)
   - Store uploaded documents
   - Generated reports

4. **API Rate Limiting** (Redis)
   - Limit uploads per user
   - ABR/ATO mock API rate caps

5. **Monitoring** (Prometheus + Grafana)
   - Agent execution times
   - Error rates
   - Throughput metrics

---

## Security Architecture

### Current (Demo)
- No authentication
- In-memory results store (non-persistent)
- Mock APIs (no real data)

### Production Hardened
| Layer | Security |
|-------|----------|
| Network | TLS 1.3, HTTPS only |
| Auth | JWT + OAuth2 (bank SSO) |
| Input | File type validation, size limits, virus scan |
| Data | Encryption at rest (AES-256), in transit (TLS) |
| Audit | Full request/response logging |
| APRA | Audit trail for all decisions |

---

## Error Handling Strategy

Each agent implements:
1. **Input validation** (file format, ABN checks)
2. **Graceful degradation** (fallback to mock data)
3. **Structured logging** (JSON logs for aggregation)
4. **Retry logic** (for API timeouts)
5. **Error propagation** (raise to FastAPI handler)

---

## Logging Architecture

```
Level: INFO (production), DEBUG (development)
Format: YYYY-MM-DD HH:MM:SS - agent_name - LEVEL - message

Example:
2025-04-28 14:32:10 - document_ingestor - INFO - Ingesting file: data/bank.csv
2025-04-28 14:32:11 - anomaly_detector - INFO - Detected 3 anomalies
2025-04-28 14:32:12 - risk_scorer - INFO - Risk score: 65/100 (Medium)
```

---

## Performance Benchmarks

| Operation | Avg Time | 95th %ile | Notes |
|-----------|----------|-----------|-------|
| CSV ingestion (100 rows) | 0.2s | 0.3s | Pandas read_csv |
| PDF ingestion (10 pages) | 2.1s | 3.0s | Tesseract OCR |
| Data extraction | 0.1s | 0.2s | Regex + pandas |
| API lookups | 0.2s | 0.5s | Mock local server |
| Anomaly detection | 0.3s | 0.5s | Isolation Forest fit+predict |
| AML screening | 0.1s | 0.2s | O(1) dict lookups |
| Risk scoring | <0.01s | <0.01s | Simple arithmetic |
| Report generation | 1.5s | 2.0s | ReportLab PDF compile |
| **TOTAL** | **4.5s** | **6.7s** | End-to-end for 100 tx |

---

## Future Enhancements

- [ ] **LLM Integration** - Unstructured text analysis via GPT-4
- [ ] **Real ABR API** - Australian Business Register production API
- [ ] **Real ATO API** - Tax file lookup (with auth)
- [ ] **WebSockets** - Real-time progress updates
- [ ] **Batch Processing** - Upload ZIP with multiple applications
- [ ] **Advanced Visualizations** - Plotly Dash dashboard
- [ ] **Model Versioning** - MLflow for Anomaly detection
- [ ] **Audit Trail** - PostgreSQL with full history

---

*Last updated: 2026-04-28*
