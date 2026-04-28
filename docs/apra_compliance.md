# APRA APS 222 Compliance

## Overview

This document details how the AI Fraud Detection Agent aligns with **APRA APS 222 – Credit Risk Management** requirements for Australian Prudential Regulation Authority compliance.

---

## APS 222 Overview

APRA APS 222 sets prudential standards for credit risk management in Australian financial institutions. Key requirements:
- **Asset classification** based on credit quality
- **Impairment provisioning** for expected credit losses
- **Risk grading** and reporting categories
- **Collateral valuation** and LTV ratios
- **Regular review** of impaired assets

---

## Alignment Map

| APS 222 Requirement | Agent Implementation | Location |
|---------------------|---------------------|----------|
| Asset classification | `RiskScorer._calculate_apra_fields()` | `src/agents/risk_scorer.py` |
| Impairment provision calculation | `RiskScorer._calculate_apair_provision()` | `src/agents/risk_scorer.py:145-180` |
| Regulatory code assignment | `RiskScorer._get_apra_code()` | `src/agents/risk_scorer.py:210-225` |
| LTV calculation | `ReportGenerator._calculate_ltv()` | `src/agents/report_generator.py:320-340` |
| Manual review trigger | `APRAFields.requires_manual_review` | Report output |
| Reporting category | `APRAFields.apra_reporting_category` | Report output |

---

## APRA Asset Classifications

### Classification Criteria

| Classification | Risk Score Range | Criteria | Impairment Rate | Regulatory Code |
|---------------|------------------|----------|-----------------|-----------------|
| **Standard** | 0 - 29 | Low risk, no concern | 0% | APS222-001 |
| **Substandard** | 30 - 69 | Potential weaknesses, requires monitoring | 5% | APS222-002 |
| **Doubtful** | 70 - 89 | High probability of loss, significant risk | 25% | APS222-003 |
| **Loss** | 90 - 100 | Evidence of impairment, likely unrecoverable | 100% | APS222-004 |

### Implementation

The `RiskScorer` agent calculates asset classification as follows:

```python
def _calculate_apra_fields(self, score, anomalies, aml_alerts):
    if score >= 90:
        asset_class = "Loss"
    elif score >= 70:
        asset_class = "Doubtful"
    elif score >= 30:
        asset_class = "Substandard"
    else:
        asset_class = "Standard"

    impairment_rate = IMPAIRMENT_RATES[asset_class]  # 0.0, 0.05, 0.25, 1.0
    suspicious_amount = sum(a['amount'] for a in anomalies if a['severity'] == 'high')
    impairment_provision = suspicious_amount * impairment_rate
```

---

## Impairment Provisioning

APRA requires **expected credit loss (ECL)** provisioning based on classification:

### Formula
```
Impairment Provision = Suspicious Amount × Impairment Rate

Where:
- Suspicious Amount = sum of high-severity anomaly amounts
- Impairment Rate = per classification table above
```

**Example:**
- Risk Score: 85 (Doubtful)
- High-severity anomalies total: $100,000
- Impairment rate: 25%
- **Provision = $100,000 × 0.25 = $25,000**

---

## Regulatory Codes

Each APRA classification maps to a specific regulatory code for reporting:

| Code | Classification | APS Reference | Reporting Frequency |
|------|---------------|---------------|-------------------|
| APS222-001 | Standard | Paragraph 22 | Monthly |
| APS222-002 | Substandard | Paragraph 23 | Monthly |
| APS222-003 | Doubtful | Paragraph 24 | Monthly |
| APS222-004 | Loss | Paragraph 25 | Monthly |

These codes are automatically included in generated PDF reports.

---

## Loan-to-Value (LTV) Ratio

### Calculation
```
LTV = Total Exposure / Collateral Value
```

**Implementation:**
```python
total_exposure = sum(tx['amount'] for tx in anomalies if tx['type'] in ['high_value', 'outlier'])
collateral_value = total_exposure * 0.5  # Mock: assume 50% collateral
ltv = min(total_exposure / collateral_value, 1.0)
```

**APRA Limits:**
- **Standard:** LTV ≤ 70%
- **Substandard:** LTV 70-85%
- **Doubtful:** LTV > 85%
- **Loss:** LTV > 100% (undercollateralized)

Our mock implementation uses a fixed 50% collateral ratio for simplicity. Production would integrate with property valuation APIs.

---

## Credit Risk Grading

### Risk Score Breakdown

| Risk Factor | Points | Example |
|-------------|--------|---------|
| Round-dollar transaction | +20 | $50,000 (exactly) |
| Outlier (medium) | +15 | Statistical anomaly |
| Outlier (high, >$50k) | +23 | Severe statistical outlier |
| High-value transaction | +25 | >$250,000 single tx |
| AML high-severity alert | +40 | Sanctioned jurisdiction |
| AML medium alert | +15 | Structuring pattern |
| Shell company indicator | +25 | Known shell ABN |

**Thresholds:**
- **Low:** 0-29 points
- **Medium:** 30-69 points
- **High:** 70+ points

---

## AML Integration (AUSTRAC)

While APRA APS 222 focuses on credit risk, our system integrates **AML/CTF Act** requirements:

| AML Risk | APRA Impact | Action |
|----------|-------------|--------|
| High-risk jurisdiction match | ↑ Risk score +40 | Flag for immediate review |
| Watchlist entity match | ↑ Risk score +40 | Suspicious Matter Report (SMR) |
| Structuring pattern | ↑ Risk score +15 | Enhanced due diligence |
| Shell company | ↑ Risk score +25 | Deny loan, file SAR |

AML alerts trigger **automatic escalation** to compliance officers.

---

## Reporting Requirements

### Report Contents (Per APS 222)

1. **Executive Summary** (Page 1)
   - Overall risk score and category
   - Summary of key findings
   - Recommended action

2. **APRA Fields Table** (Page 2)
   - Asset classification
   - Regulatory code
   - Impairment provision amount
   - LTV ratio
   - Collateral value
   - Review priority

3. **Anomaly Details** (Page 3-4)
   - All flagged transactions
   - Risk drivers
   - Supporting evidence

4. **AML Alerts** (Page 5)
   - All AML red flags
   - Jurisdiction risks
   - Watchlist matches

5. **Appendices**
   - Business registration details (ABR validation)
   - Tax return consistency check (ATO)
   - Declaration of completeness

### Report Format

- **Primary:** PDF (ReportLab) - for submission to APRA
- **Secondary:** Markdown (Jinja2) - for internal review and version control

Each report includes:
- Unique report ID (task ID + timestamp)
- Generation timestamp
- Analyst signature placeholder
- Version history (future enhancement)

---

## Testing APRA Compliance

### Test Cases

| Test | Input | Expected APRA Code | Expected Asset Class |
|------|-------|-------------------|---------------------|
| Low-risk application | No anomalies | APS222-001 | Standard |
| Round-dollar transactions | 1× round-dollar | APS222-002 | Substandard |
| Outlier + AML alert | Outlier + high-risk jdx | APS222-003 | Doubtful |
| Multiple severe anomalies | 5+ high-severity | APS222-004 | Loss |
| Shell company ABN | Watchlist ABN | APS222-003 | Doubtful |

Run tests:
```bash
pytest tests/test_apra_compliance.py -v
```

---

## Audit Trail Requirements

APRA requires **audit trails** for all credit decisions. Our system logs:

1. **Input data hash** (SHA-256 of uploaded files)
2. **Agent decisions** (each agent's output timestamped)
3. **Score calculations** (point breakdown per anomaly)
4. **Manual override** (if risk team adjusts score)

Log format:
```json
{
  "timestamp": "2025-04-28T14:32:10.123456",
  "task_id": "a1b2c3d4",
  "agent": "risk_scorer",
  "action": "calculate_score",
  "inputs": {"anomaly_count": 3, "aml_count": 1},
  "outputs": {"score": 85, "category": "High"},
  "user": "system"  // or analyst_id
}
```

---

## Regulatory Submissions

### Monthly Reporting to APRA

Our system generates APS 222 reporting packages:
1. **Aggregate data** – Total exposure by asset class
2. **Loss experience** - Impairment provisions by portfolio
3. **Credit quality** – Risk grading distribution
4. **New impaired assets** – Additions to Substandard/Doubtful/Loss

Export format: CSV compatible with APRA's EFS system.

---

## Future Enhancements

- [ ] **Real APRA templates** - Pre-formatted APRA reporting forms
- [ ] **E-signature integration** - Digital sign-off by Credit Officer
- [ ] **Versioned reports** - Track report revisions over time
- [ ] **Audit log retention** - 7-year retention per APRA record-keeping rules
- [ ] **Access controls** - Role-based report access (analyst, manager, auditor)

---

**Compliance Status:** ✅ **APS 222-Aligned (Demo Mode)**

*Note: This is a demonstration system. Production deployment requires:*
1. *APRA pre-approval of scoring models*
2. *Full audit trail implementation*
3. *Independent validation of impairment calculations*
4. *Secure data storage and retention policies*

---

*Last reviewed: 2026-04-28*
