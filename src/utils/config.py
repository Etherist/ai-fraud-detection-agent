import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

# Tesseract OCR Configuration
TESSERACT_PATH = os.getenv("TESSERACT_PATH", "/usr/bin/tesseract")

# Mock API Endpoints
# Default: mock server runs on port 8001; main app on 8000
MOCK_ABR_API_URL = os.getenv("MOCK_ABR_API_URL", "http://localhost:8001/abr")
MOCK_ATO_API_URL = os.getenv("MOCK_ATO_API_URL", "http://localhost:8001/ato")

# Risk Score Thresholds
import json
RISK_THRESHOLDS_STR = os.getenv("RISK_SCORE_THRESHOLDS", '{"Low": 30, "Medium": 70, "High": 100}')
try:
    RISK_THRESHOLDS = json.loads(RISK_THRESHOLDS_STR)
    # Validate required keys
    required_keys = {"Low", "Medium", "High"}
    if not required_keys.issubset(RISK_THRESHOLDS.keys()):
        raise ValueError(f"Missing required keys: {required_keys - set(RISK_THRESHOLDS.keys())}")
except (json.JSONDecodeError, ValueError) as e:
    logger.error(f"Invalid RISK_SCORE_THRESHOLDS JSON: {e}. Using defaults.")
    RISK_THRESHOLDS = {"Low": 30, "Medium": 70, "High": 100}

# Anomaly Detection Parameters
ISOLATION_FOREST_CONTAMINATION = float(os.getenv("ISOLATION_FOREST_CONTAMINATION", "0.1"))
ROUND_DOLLAR_THRESHOLD = float(os.getenv("ROUND_DOLLAR_THRESHOLD", "1000"))
OUTLIER_AMOUNT_THRESHOLD = float(os.getenv("OUTLIER_AMOUNT_THRESHOLD", "50000"))

# File Upload Limits
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
ALLOWED_EXTENSIONS = [ext.strip() for ext in os.getenv("ALLOWED_EXTENSIONS", ".csv,.pdf").split(",")]

# APRA APS 222 Configuration
APRA_ASSET_CLASSIFICATIONS = ["Standard", "Substandard", "Doubtful", "Loss"]
IMPAIRMENT_RATES = {
    "Standard": 0.0,
    "Substandard": 0.05,
    "Doubtful": 0.25,
    "Loss": 1.0
}

# Reporting
REPORT_OUTPUT_DIR = os.getenv("REPORT_OUTPUT_DIR", "reports/")
DEFAULT_REPORT_FORMAT = os.getenv("DEFAULT_REPORT_FORMAT", "pdf")

# AML Watchlist Paths
AML_WATCHLIST_PATH = os.getenv("AML_WATCHLIST_PATH", "data/aml_watchlist.json")
SHELL_COMPANY_PATH = os.getenv("SHELL_COMPANY_PATH", "data/shell_company_addresses.json")

# Security (CORS)
# Comma-separated list of allowed origins. Default: http://localhost:8000 (secure).
# For demo, set ALLOWED_ORIGINS=* (insecure - allows any origin with credentials).
ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")]

# Ensure directories exist
Path(REPORT_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
