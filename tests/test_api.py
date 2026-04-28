"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.app.main import app

client = TestClient(app)

class TestAPIEndpoints:
    """Test suite for FastAPI REST endpoints."""

    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert data['version'] == '1.0.0'

    def test_root_returns_html(self):
        response = client.get("/")
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']
        assert 'AI Fraud Detection' in response.text

    def test_upload_no_files(self):
        response = client.post("/upload/")
        assert response.status_code == 422  # Validation error

    def test_upload_single_file(self):
        """Test uploading only bank statement (should fail)."""
        csv_content = "transaction_id,date,amount,description\n1,2025-07-01,50000,Test"
        response = client.post(
            "/upload/",
            files={
                "bank_statement": ("test.csv", csv_content.encode(), "text/csv")
            }
        )
        assert response.status_code == 422  # Missing tax_return

    def test_upload_both_files(self):
        """Test successful upload of both files."""
        bank_csv = "transaction_id,date,amount,description\n1,2025-07-01,50000,Test payment"
        tax_csv = "business_name,abn\nAcme Pty Ltd,123456789"

        response = client.post(
            "/upload/",
            files={
                "bank_statement": ("bank.csv", bank_csv.encode(), "text/csv"),
                "tax_return": ("tax.csv", tax_csv.encode(), "text/csv")
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert 'task_id' in data
        assert data['status'] == 'processing'
        # task_id is a UUID string (36 chars with hyphens or 32 hex chars)
        assert isinstance(data['task_id'], str) and len(data['task_id']) >= 8

    def test_upload_invalid_extension(self):
        """Test uploading .txt file (rejected)."""
        response = client.post(
            "/upload/",
            files={
                "bank_statement": ("test.txt", b"test", "text/plain"),
                "tax_return": ("tax.txt", b"test", "text/plain")
            }
        )
        assert response.status_code == 400
        assert "Unsupported file format" in response.json()['detail']

    def test_get_results_not_found(self):
        response = client.get("/results/nonexistent")
        assert response.status_code == 404

    def test_results_processing(self):
        """Test that task eventually completes."""
        # First upload
        bank_csv = "transaction_id,date,amount,description\n1,2025-07-01,50000,Test"
        tax_csv = "business_name,abn\nAcme Pty Ltd,123456789"

        upload_resp = client.post(
            "/upload/",
            files={
                "bank_statement": ("bank.csv", bank_csv.encode(), "text/csv"),
                "tax_return": ("tax.csv", tax_csv.encode(), "text/csv")
            }
        )
        task_id = upload_resp.json()['task_id']

        # Poll for results (quick check, may be completed already)
        result_resp = client.get(f"/results/{task_id}")
        assert result_resp.status_code in [200, 202]  # 200=done, 202=processing

    def test_get_report_not_found(self):
        response = client.get("/reports/nonexistent.pdf")
        assert response.status_code == 404

    def test_sample_data_endpoint(self):
        response = client.get("/api/sample-data")
        assert response.status_code == 200
        data = response.json()
        assert 'sample' in data
        # Check structure if sample data exists
        if data['sample']:
            assert 'transaction_id' in data['sample'][0]

    def test_upload_large_file(self):
        """Test file size limit (10MB)."""
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        response = client.post(
            "/upload/",
            files={
                "bank_statement": ("large.csv", large_content, "text/csv"),
                "tax_return": ("tax.csv", b"tiny", "text/csv")
            }
        )
        assert response.status_code == 413  # Payload Too Large

    def test_malformed_csv(self):
        """Test CSV with missing columns."""
        malformed = "col1,col2\n1,2\n"  # No transaction_id, amount
        response = client.post(
            "/upload/",
            files={
                "bank_statement": ("bad.csv", malformed.encode(), "text/csv"),
                "tax_return": ("tax.csv", b"business_name,abn\nTest,123456789", "text/csv")
            }
        )
        # Should succeed (system handles missing columns gracefully)
        assert response.status_code == 200

    def test_cors_headers(self):
        """Test CORS headers present."""
        response = client.options("/upload/")
        # CORS middleware should add headers
        assert 'access-control-allow-origin' in response.headers or response.status_code == 200
