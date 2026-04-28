"""Tests for end-to-end CLI and integration."""

import pytest
import subprocess
import sys
import os
from pathlib import Path

class TestCLI:
    """Test suite for CLI interface."""

    def test_cli_help(self):
        """Test CLI help output."""
        result = subprocess.run(
            [sys.executable, "-m", "src.app.cli", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "--bank-statement" in result.stdout
        assert "--tax-return" in result.stdout

    def test_cli_missing_args(self):
        """Test CLI with missing required args."""
        result = subprocess.run(
            [sys.executable, "-m", "src.app.cli"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
        assert "required" in result.stderr.lower()

    def test_cli_nonexistent_files(self, tmp_path):
        """Test CLI with nonexistent files."""
        output = tmp_path / "output.pdf"
        result = subprocess.run(
            [
                sys.executable, "-m", "src.app.cli",
                "--bank-statement", "/nonexistent/bank.csv",
                "--tax-return", "/nonexistent/tax.csv",
                "--output", str(output)
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert "not found" in result.stderr.lower() or "Error" in result.stderr

    # Note: Full integration test would require running the full pipeline
    # Skipped in CI unless all deps installed

class TestIntegration:
    """End-to-end integration tests."""

    @pytest.mark.skipif(
        not os.path.exists("data/sample_bank_statements.csv"),
        reason="Sample data not generated"
    )
    def test_full_pipeline_imports(self):
        """Test that all agents can be imported."""
        try:
            from src.agents.document_ingestor import DocumentIngestor
            from src.agents.data_extractor import DataExtractor
            from src.agents.api_lookup_agent import APILookupAgent
            from src.agents.anomaly_detector import AnomalyDetector
            from src.agents.aml_checker import AMLChecker
            from src.agents.risk_scorer import RiskScorer
            from src.agents.report_generator import ReportGenerator
            from src.app.main import app
            assert True
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    def test_agents_have_required_methods(self):
        """Verify each agent class has required methods."""
        from src.agents.document_ingestor import DocumentIngestor
        from src.agents.data_extractor import DataExtractor
        from src.agents.anomaly_detector import AnomalyDetector
        from src.agents.aml_checker import AMLChecker
        from src.agents.risk_scorer import RiskScorer

        assert hasattr(DocumentIngestor, 'ingest_file')
        assert hasattr(DataExtractor, 'extract')
        assert hasattr(AnomalyDetector, 'detect_anomalies')
        assert hasattr(AMLChecker, 'check_transactions')
        assert hasattr(RiskScorer, 'calculate_score')

    def test_api_model_structure(self):
        """Test Pydantic models are well-formed."""
        from src.app.models import AnalysisResult, APRAFields

        # Verify APRAFields required fields
        apra = APRAFields(
            asset_classification="Standard",
            impairment_provision=0.0,
            regulatory_code="APS222-001",
            collateral_value=100000.0,
            loan_to_value_ratio=0.5,
            requires_manual_review=False,
            review_priority="Low",
            apra_reporting_category="STANDARD_RISK"
        )
        assert apra.asset_classification == "Standard"
