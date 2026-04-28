"""
AI Fraud Detection Agent for SME Loans - Test Suite

Run with: pytest tests/ -v
"""

import pytest
import sys
import os
import time
import subprocess
import signal
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Test data paths
TEST_DATA_DIR = Path(__file__).parent / "test_data"
SAMPLE_BANK_CSV = TEST_DATA_DIR / "sample_bank_statements.csv"
SAMPLE_TAX_CSV = TEST_DATA_DIR / "sample_tax_returns.csv"

# Ensure test data exists
if not SAMPLE_BANK_CSV.exists() or not SAMPLE_TAX_CSV.exists():
    print("Generating test data...")
    generate_script = Path(__file__).parent.parent / "scripts" / "generate_sample_data.py"
    subprocess.run([sys.executable, str(generate_script)], check=True)

# Mock server process (for API lookup tests)
_mock_server_process = None

@pytest.fixture(scope="session", autouse=True)
def mock_server():
    """Start mock ABR/ATO API server for session and stop after all tests."""
    global _mock_server_process
    
    # Start mock server
    mock_script = Path(__file__).parent.parent / "scripts" / "mock_api_server.py"
    _mock_server_process = subprocess.Popen(
        [sys.executable, str(mock_script)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid
    )
    
    # Wait for server to be ready
    import urllib.request
    import urllib.error
    max_retries = 30
    for i in range(max_retries):
        try:
            urllib.request.urlopen("http://localhost:8001/health", timeout=1)
            break
        except (urllib.error.URLError, ConnectionRefusedError):
            if i == max_retries - 1:
                raise
            time.sleep(0.1)
    
    yield
    
    # Stop mock server
    if _mock_server_process:
        os.killpg(os.getpgid(_mock_server_process.pid), signal.SIGTERM)
        _mock_server_process.wait(timeout=5)
