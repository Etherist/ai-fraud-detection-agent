"""Tests for Anomaly Detector."""

import pytest
import numpy as np
from src.agents.anomaly_detector import AnomalyDetector, detect_anomalies

class TestAnomalyDetector:
    """Test suite for AnomalyDetector agent."""

    @pytest.fixture
    def detector(self):
        return AnomalyDetector(contamination=0.1, random_state=42)

    @pytest.fixture
    def sample_transactions(self):
        return [
            {"transaction_id": 1, "amount": 50000.00, "date": "2025-07-01", "description": "normal"},
            {"transaction_id": 2, "amount": 5000.00, "date": "2025-07-02", "description": "normal"},
            {"transaction_id": 3, "amount": 10000.00, "date": "2025-07-03", "description": "round-dollar"},  # flagged
            {"transaction_id": 4, "amount": 250000.00, "date": "2025-07-04", "description": "outlier"},  # flagged
            {"transaction_id": 5, "amount": 750.50, "date": "2025-07-05", "description": "normal"},
        ]

    def test_detector_initialization(self, detector):
        assert detector.contamination == 0.1
        assert detector.random_state == 42

    def test_detect_anomalies_empty(self, detector):
        """Test with empty transaction list."""
        anomalies = detector.detect_anomalies([])
        assert anomalies == []

    def test_detect_round_dollar(self, detector):
        """Test detection of round-dollar transactions."""
        txs = [{"transaction_id": 1, "amount": 10000.00, "date": "2025-07-01"}]
        anomalies = detector.detect_anomalies(txs)

        assert any(a['type'] == 'round_dollar' for a in anomalies)
        round_dollar = next(a for a in anomalies if a['type'] == 'round_dollar')
        assert round_dollar['severity'] == 'high'
        assert round_dollar['amount'] == 10000.00

    def test_detect_round_dollar_small(self, detector):
        """Test round-dollar below threshold is not flagged."""
        txs = [{"transaction_id": 1, "amount": 500.00, "date": "2025-07-01"}]  # < $1000
        anomalies = detector.detect_anomalies(txs)
        assert not any(a['type'] == 'round_dollar' for a in anomalies)

    def test_detect_high_value(self, detector):
        """Test detection of very high-value transactions."""
        txs = [{"transaction_id": 1, "amount": 300000.00, "date": "2025-07-01"}]
        anomalies = detector.detect_anomalies(txs)
        assert any(a['type'] == 'high_value' for a in anomalies)

    def test_detect_outliers(self, detector, sample_transactions):
        """Test Isolation Forest outlier detection."""
        anomalies = detector.detect_anomalies(sample_transactions)
        outlier_anomalies = [a for a in anomalies if a['type'] == 'outlier']
        assert len(outlier_anomalies) >= 1  # At least the $250k transaction

    def test_severity_levels(self, detector):
        """Test severity assignment based on amount."""
        # Medium outlier ($50k)
        txs_med = [{"transaction_id": 1, "amount": 50000.00, "date": "2025-07-01"}]
        anomalies_med = detector.detect_anomalies(txs_med)
        outlier_med = next((a for a in anomalies_med if a['type'] == 'outlier'), None)
        if outlier_med:
            assert outlier_med['severity'] == 'medium'

        # High outlier ($300k)
        txs_high = [{"transaction_id": 2, "amount": 300000.00, "date": "2025-07-02"}]
        anomalies_high = detector.detect_anomalies(txs_high)
        outlier_high = next((a for a in anomalies_high if a['type'] == 'outlier'), None)
        if outlier_high:
            assert outlier_high['severity'] == 'high'

    def test_convenience_function(self, sample_transactions):
        """Test detect_anomalies standalone function."""
        anomalies = detect_anomalies(sample_transactions)
        assert isinstance(anomalies, list)
        assert all('type' in a and 'transaction_id' in a for a in anomalies)

    def test_anomaly_types(self, detector):
        """Test all supported anomaly types."""
        txs = [
            {"transaction_id": 1, "amount": 15000.00, "date": "2025-07-01"},  # round-dollar
            {"transaction_id": 2, "amount": 500000.00, "date": "2025-07-02"}, # high-value + outlier
        ]
        anomalies = detector.detect_anomalies(txs)
        types = [a['type'] for a in anomalies]

        assert 'round_dollar' in types
        assert 'high_value' in types or 'outlier' in types

    def test_missing_amount_field(self, detector):
        """Test handling of transaction without amount."""
        txs = [{"transaction_id": 1, "date": "2025-07-01"}]
        # Should not crash, amount defaults to 0
        anomalies = detector.detect_anomalies(txs)
        assert isinstance(anomalies, list)
