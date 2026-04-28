"""FastAPI main application - RESTful backend for processing SME loan applications."""

import logging
import uuid
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src.agents.document_ingestor import DocumentIngestor
from src.agents.data_extractor import DataExtractor
from src.agents.api_lookup_agent import APILookupAgent
from src.agents.anomaly_detector import AnomalyDetector
from src.agents.aml_checker import AMLChecker
from src.agents.risk_scorer import RiskScorer
from src.agents.report_generator import ReportGenerator

from src.app.models import AnalysisResult, HealthCheck
from src.app.rate_limit import RateLimitMiddleware

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Fraud Detection Agent for SME Loans",
    description="Automated fraud and AML risk assessment for Australian lenders. "
                "Built with Vibe Coding & Agent Engineering. "
                "APRA APS 222 Compliant.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration from environment
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
allowed_origins = [origin.strip() for origin in allowed_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting (simple in-memory per IP)
app.add_middleware(RateLimitMiddleware)

# Mount static files (HTML frontend)
app.mount("/static", StaticFiles(directory="src/app/static"), name="static")

# In-memory storage for task results (demo only; use Redis/DB in production)
results_store: Dict[str, Dict[str, Any]] = {}

# Initialize agents
document_ingestor = DocumentIngestor()
data_extractor = DataExtractor()
api_lookup_agent = APILookupAgent()
anomaly_detector = AnomalyDetector(contamination=0.1)
aml_checker = AMLChecker()
risk_scorer = RiskScorer()
report_generator = ReportGenerator(output_dir="reports/")

logger.info("FastAPI application initialized with all agents")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve HTML frontend."""
    return FileResponse("src/app/static/index.html")


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )


@app.post("/upload/")
async def upload_files(
    bank_statement: UploadFile = File(..., description="Bank statement (CSV or PDF)"),
    tax_return: UploadFile = File(..., description="Tax return (CSV or PDF)")
):
    """
    Upload SME loan application documents for analysis.

    Accepts bank statements and tax returns in CSV or PDF format.
    Returns a task_id for polling results.
    """
    logger.info(f"File upload request: {bank_statement.filename}, {tax_return.filename}")

    # Validate file extensions
    allowed_exts = ['.csv', '.pdf']
    for file in [bank_statement, tax_return]:
        ext = Path(file.filename).suffix.lower()
        if ext not in allowed_exts:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {ext}. Allowed: {allowed_exts}"
            )

    # Generate unique task ID (full UUID for unguessability)
    task_id = str(uuid.uuid4())
    results_store[task_id] = {"status": "processing"}

    # Save uploaded files to temporary directory
    temp_dir = Path(tempfile.mkdtemp())
    bank_path = temp_dir / f"{task_id}_bank{Path(bank_statement.filename).suffix}"
    tax_path = temp_dir / f"{task_id}_tax{Path(tax_return.filename).suffix}"

    try:
        # Write bank statement
        with open(bank_path, "wb") as f:
            content = await bank_statement.read()
            f.write(content)

        # Write tax return
        with open(tax_path, "wb") as f:
            content = await tax_return.read()
            f.write(content)

        # Check file sizes before processing
        max_size_mb = 10
        for path, file_obj in [(bank_path, tax_path)]:
            file_size_mb = path.stat().st_size / (1024 * 1024)
            if file_size_mb > max_size_mb:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large: {file_size_mb:.1f}MB. Maximum: {max_size_mb}MB"
                )

        logger.info(f"Files saved: {bank_path}, {tax_path}")

        # Process files (synchronous for demo; use background tasks in production)
        result = process_files(bank_path, tax_path, task_id)
        results_store[task_id] = result

        return {"task_id": task_id, "status": "processing"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload processing failed: {e}", exc_info=True)
        results_store[task_id] = {
            "status": "failed",
            "error": str(e)
        }
        raise HTTPException(status_code=500, detail="Processing failed")
    finally:
        # Cleanup temporary files regardless of success/failure
        try:
            if bank_path.exists():
                bank_path.unlink()
            if tax_path.exists():
                tax_path.unlink()
            if temp_dir.exists():
                temp_dir.rmdir()
        except Exception as e:
            logger.warning(f"Failed to clean up temp files: {e}")


@app.options("/upload/")
async def upload_options():
    """CORS preflight handler for /upload/ endpoint."""
    return {"detail": "CORS preflight"}


@app.get("/results/{task_id}")
async def get_results(task_id: str):
    """
    Retrieve analysis results for a given task ID.

    Returns:
        AnalysisResult with risk score, anomalies, AML alerts, etc.
    """
    logger.info(f"Results request for task: {task_id}")

    if task_id not in results_store:
        raise HTTPException(status_code=404, detail="Task not found")

    result = results_store[task_id]

    if result.get("status") == "failed":
        raise HTTPException(status_code=500, detail=result.get("error", "Processing failed"))

    if result.get("status") != "completed":
        return {"status": "processing"}

    return result


@app.get("/reports/{filename}")
async def get_report(filename: str):
    """
    Download generated report file.

    Args:
        filename: Report filename (e.g., audit_abc123_20260428.pdf)
    """
    report_path = Path("reports") / filename
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(
        path=report_path,
        filename=filename,
        media_type="application/pdf" if filename.endswith('.pdf') else "text/markdown"
    )


@app.get("/api/sample-data")
async def get_sample_data():
    """Get sample transaction data for demo purposes."""
    import pandas as pd
    sample_path = Path("data/sample_bank_statements.csv")
    if sample_path.exists():
        df = pd.read_csv(sample_path)
        return {"sample": df.to_dict('records')}
    return {"sample": []}


def process_files(bank_path: Path, tax_path: Path, task_id: str) -> Dict[str, Any]:
    """
    End-to-end processing pipeline for SME loan analysis.

    Args:
        bank_path: Path to bank statement file
        tax_path: Path to tax return file
        task_id: Unique task identifier

    Returns:
        Complete analysis result dictionary
    """
    logger.info(f"Starting processing pipeline for task {task_id}")

    # Step 1: Ingest documents
    bank_raw = document_ingestor.ingest_file(str(bank_path))
    tax_raw = document_ingestor.ingest_file(str(tax_path))

    # Step 2: Extract structured data
    bank_data = data_extractor.extract(bank_raw)
    tax_data = data_extractor.extract(tax_raw)

    # Merge transaction data from bank statement
    transactions = bank_data.get('transactions', [])
    business_details = {
        'business_name': tax_data.get('business_name', bank_data.get('business_name', '')),
        'abn': tax_data.get('abn', bank_data.get('abn', '')),
        'addresses': tax_data.get('addresses', []) or bank_data.get('addresses', [])
    }

    logger.info(f"Extracted {len(transactions)} transactions, business: {business_details.get('business_name')}")

    # Step 3: API lookups (validate business) - run synchronously via asyncio
    abn = business_details.get('abn', '')
    business_name = business_details.get('business_name', '')
    abr_result = None
    ato_result = None

    if abn and business_name:
        # Use module-level sync wrappers that run async code
        from src.agents.api_lookup_agent import lookup_business, lookup_tax_return as lookup_tax_return_sync
        abr_result = lookup_business(abn, business_name)
        ato_result = lookup_tax_return_sync(abn)
        logger.info(f"API lookups completed: ABR valid={abr_result.get('valid')}, ATO found={ato_result.get('found')}")
    else:
        logger.warning("Skipping API lookups: ABN or business name missing")

    # Step 4: Anomaly detection
    anomalies = anomaly_detector.detect_anomalies(transactions)

    # Step 5: AML checking
    aml_alerts = aml_checker.check_transactions(transactions, business_details)

    # Step 6: Risk scoring with APRA fields
    risk_data = risk_scorer.calculate_score(anomalies, aml_alerts)

    # Step 7: Generate report
    report_result = report_generator.generate_report(
        risk_data=risk_data,
        anomalies=anomalies,
        aml_alerts=aml_alerts,
        business_details=business_details,
        task_id=task_id,
        format="pdf"
    )

    # Compile final result
    result = {
        "task_id": task_id,
        "status": "completed",
        "risk_score": risk_data["score"],
        "category": risk_data["category"],
        "anomalies": anomalies,
        "aml_alerts": aml_alerts,
        "apra_fields": risk_data["apra_fields"],
        "report_url": report_result["report_url"],
        "processed_at": datetime.now().isoformat(),
        "business_details": business_details,
        "summary": {
            "total_transactions": len(transactions),
            "anomaly_count": len(anomalies),
            "aml_alert_count": len(aml_alerts)
        }
    }

    logger.info(f"Processing completed for task {task_id}: score={risk_data['score']}, category={risk_data['category']}")
    return result


# Include CLI entry point
def cli_main():
    """Main entry point for CLI execution."""
    import sys
    sys.argv[0] = "src/app/cli.py"
    from src.app.cli import main
    main()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
