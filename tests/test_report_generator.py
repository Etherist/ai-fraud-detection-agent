"""Tests for Report Generator."""

import pytest
import os
from pathlib import Path
from src.agents.report_generator import ReportGenerator, generate_pdf_report
from src.agents.risk_scorer import RiskScorer
from src.agents.anomaly_detector import AnomalyDetector
from src.agents.aml_checker import AMLChecker

class TestReportGenerator:
    """Test suite for ReportGenerator agent."""

    @pytest.fixture
    def sample_risk_data(self):
        scorer = RiskScorer()
        anomalies = [
            {"type": "round_dollar", "transaction_id": 1, "amount": 10000.00, "severity": "high", "message": "Test anomaly"}
        ]
        alerts = []
        return scorer.calculate_score(anomalies, alerts)

    @pytest.fixture
    def sample_anomalies(self):
        return [
            {"type": "round_dollar", "transaction_id": 1, "amount": 10000.00, "severity": "high", "message": "Round-dollar"},
            {"type": "outlier", "transaction_id": 2, "amount": 250000.00, "severity": "high", "message": "Outlier"},
        ]

    @pytest.fixture
    def sample_aml_alerts(self):
        return [
            {"type": "high_risk_jurisdiction", "transaction_id": 3, "severity": "high", "message": "High-risk jdx"},
        ]

    @pytest.fixture
    def business_details(self):
        return {
            "business_name": "Test Pty Ltd",
            "abn": "123456789",
            "addresses": ["123 Test St"]
        }

    @pytest.fixture
    def generator(self, tmp_path):
        return ReportGenerator(output_dir=str(tmp_path))

    def test_generator_initialization(self, generator):
        assert generator.output_dir is not None
        assert Path(generator.output_dir).exists()

    def test_generate_pdf_report(self, generator, sample_risk_data, sample_anomalies,
                                 sample_aml_alerts, business_details):
        task_id = "test123"
        result = generator.generate_report(
            risk_data=sample_risk_data,
            anomalies=sample_anomalies,
            aml_alerts=sample_aml_alerts,
            business_details=business_details,
            task_id=task_id,
            format="pdf"
        )

        assert result['format'] == 'pdf'
        assert Path(result['report_path']).exists()
        assert result['report_path'].endswith('.pdf')

    def test_generate_markdown_report(self, generator, sample_risk_data, sample_anomalies,
                                       sample_aml_alerts, business_details):
        task_id = "test456"
        result = generator.generate_report(
            risk_data=sample_risk_data,
            anomalies=sample_anomalies,
            aml_alerts=sample_aml_alerts,
            business_details=business_details,
            task_id=task_id,
            format="markdown"
        )

        assert result['format'] == 'markdown'
        assert result['report_path'].endswith('.markdown')
        assert Path(result['report_path']).exists()

        # Check content
        with open(result['report_path'], 'r') as f:
            content = f.read()
            assert 'Risk Score' in content
            assert 'APRA' in content

    def test_pdf_contains_apra_fields(self, sample_risk_data, sample_anomalies,
                                       sample_aml_alerts, business_details, tmp_path):
        generator = ReportGenerator(output_dir=str(tmp_path))
        result = generator.generate_report(
            risk_data=sample_risk_data,
            anomalies=sample_anomalies,
            aml_alerts=sample_aml_alerts,
            business_details=business_details,
            task_id="apra_test",
            format="pdf"
        )

        # PDF exists
        pdf_path = Path(result['report_path'])
        assert pdf_path.exists()
        # PDF file size > 0
        assert pdf_path.stat().st_size > 0

    def test_convenience_function(self, sample_risk_data, sample_anomalies,
                                   sample_aml_alerts, business_details, tmp_path):
        output_path = str(tmp_path / "test_report.pdf")
        result_path = generate_pdf_report(
            risk_data=sample_risk_data,
            anomalies=sample_anomalies,
            aml_alerts=sample_aml_alerts,
            business_details=business_details,
            output_path=output_path
        )
        assert Path(result_path).exists()

    def test_report_with_empty_anomalies(self, generator, sample_risk_data,
                                          business_details):
        result = generator.generate_report(
            risk_data=sample_risk_data,
            anomalies=[],
            aml_alerts=[],
            business_details=business_details,
            task_id="empty_test",
            format="pdf"
        )
        assert Path(result['report_path']).exists()

    def test_report_url_format(self, generator, sample_risk_data, sample_anomalies,
                                sample_aml_alerts, business_details):
        result = generator.generate_report(
            risk_data=sample_risk_data,
            anomalies=sample_anomalies,
            aml_alerts=sample_aml_alerts,
            business_details=business_details,
            task_id="url_test",
            format="pdf"
        )
        # URL should be relative API path
        assert result['report_url'].startswith('/reports/')
        assert 'url_test' in result['report_url']

    def test_invalid_format_raises_error(self, generator, sample_risk_data,
                                          sample_anomalies, sample_aml_alerts, business_details):
        with pytest.raises(ValueError, match="Unsupported format"):
            generator.generate_report(
                risk_data=sample_risk_data,
                anomalies=sample_anomalies,
                aml_alerts=sample_aml_alerts,
                business_details=business_details,
                task_id="invalid",
                format="docx"  # not supported
            )
