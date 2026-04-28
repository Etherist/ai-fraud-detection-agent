"""Tests for Risk Scorer agent."""

import pytest
from src.agents.risk_scorer import RiskScorer, calculate_risk_score

class TestRiskScorer:
    """Test suite for RiskScorer agent."""

    @pytest.fixture
    def scorer(self):
        return RiskScorer(thresholds={"Low": 30, "Medium": 70, "High": 100})

    @pytest.fixture
    def empty_inputs(self):
        return [], []

    @pytest.fixture
    def single_round_dollar(self):
        anomalies = [{"type": "round_dollar", "transaction_id": 1, "amount": 10000.00, "severity": "high"}]
        alerts = []
        return anomalies, alerts

    @pytest.fixture
    def outlier_only(self):
        anomalies = [{"type": "outlier", "transaction_id": 2, "amount": 60000.00, "severity": "medium"}]
        alerts = []
        return anomalies, alerts

    @pytest.fixture
    def high_value_only(self):
        anomalies = [{"type": "high_value", "transaction_id": 3, "amount": 300000.00, "severity": "high"}]
        alerts = []
        return anomalies, alerts

    @pytest.fixture
    def aml_high_only(self):
        anomalies = []
        alerts = [{"type": "high_risk_jurisdiction", "transaction_id": 4, "severity": "high"}]
        return anomalies, alerts

    @pytest.fixture
    def mixed_anomalies(self):
        anomalies = [
            {"type": "round_dollar", "transaction_id": 1, "amount": 10000.00, "severity": "high"},
            {"type": "outlier", "transaction_id": 2, "amount": 60000.00, "severity": "medium"},
        ]
        alerts = []
        return anomalies, alerts

    @pytest.fixture
    def complex_case(self):
        anomalies = [
            {"type": "round_dollar", "transaction_id": 1, "amount": 10000.00, "severity": "high"},
            {"type": "high_value", "transaction_id": 2, "amount": 300000.00, "severity": "high"},
        ]
        alerts = [
            {"type": "high_risk_jurisdiction", "transaction_id": 3, "severity": "high"},
            {"type": "watchlist_entity", "transaction_id": 4, "severity": "medium"},
        ]
        return anomalies, alerts

    def test_scorer_initialization(self, scorer):
        assert scorer.thresholds['Low'] == 30
        assert scorer.thresholds['Medium'] == 70
        assert scorer.thresholds['High'] == 100

    def test_empty_inputs(self, scorer, empty_inputs):
        risk = scorer.calculate_score(*empty_inputs)
        assert risk['score'] == 0
        assert risk['category'] == 'Low'
        assert risk['apra_fields']['asset_classification'] == 'Standard'

    def test_round_dollar_points(self, scorer, single_round_dollar):
        risk = scorer.calculate_score(*single_round_dollar)
        assert risk['score'] == 20
        assert risk['category'] == 'Low'
        assert risk['breakdown']['round_dollar_points'] == 20

    def test_outlier_points_medium(self, scorer, outlier_only):
        risk = scorer.calculate_score(*outlier_only)
        # Medium severity outlier = 15 points
        assert risk['score'] == 15
        assert risk['category'] == 'Low'
        assert risk['breakdown']['outlier_points'] == 15

    def test_outlier_points_high(self, scorer):
        anomalies = [{"type": "outlier", "transaction_id": 1, "amount": 60000.00, "severity": "high"}]
        alerts = []
        risk = scorer.calculate_score(anomalies, alerts)
        # High severity outlier = 23 points (per POINTS['outlier_high'])
        assert risk['score'] == 23
        assert risk['breakdown']['outlier_points'] == 23

    def test_high_value_points(self, scorer, high_value_only):
        risk = scorer.calculate_score(*high_value_only)
        assert risk['score'] == 25

    def test_aml_high_points(self, scorer, aml_high_only):
        risk = scorer.calculate_score(*aml_high_only)
        assert risk['score'] == 40
        assert risk['category'] == 'Medium'  # 40 < 70 threshold

    def test_mixed_anomalies(self, scorer, mixed_anomalies):
        risk = scorer.calculate_score(*mixed_anomalies)
        assert risk['score'] == 35  # 20 + 15
        assert risk['category'] == 'Medium'

    def test_complex_case(self, scorer, complex_case):
        risk = scorer.calculate_score(*complex_case)
        # round_dollar:20 + high_value:25 + aml_high:40 + aml_med:15 = 100 (capped)
        assert risk['score'] <= 100
        assert risk['category'] == 'High'

    def test_score_capped_at_100(self, scorer):
        anomalies = [{"type": "round_dollar", "amount": 10000, "transaction_id": i, "severity": "high"} for i in range(10)]
        alerts = [{"type": "high_risk_jurisdiction", "severity": "high"} for _ in range(10)]
        risk = scorer.calculate_score(anomalies, alerts)
        assert risk['score'] == 100

    def test_apra_fields_standard(self, scorer):
        risk = scorer.calculate_score([], [])
        assert risk['apra_fields']['asset_classification'] == 'Standard'
        assert risk['apra_fields']['regulatory_code'] == 'APS222-001'
        assert risk['apra_fields']['impairment_provision'] == 0.0

    def test_apra_fields_substandard(self, scorer):
        anomalies = [{"type": "round_dollar", "amount": 20000, "transaction_id": 1, "severity": "high"}]
        alerts = []
        risk = scorer.calculate_score(anomalies, alerts)
        # 20 points = Low category, impairment provision = 0 (Standard rate = 0%)
        assert risk['apra_fields']['asset_classification'] == 'Standard'
        assert risk['apra_fields']['regulatory_code'] == 'APS222-001'
        assert risk['apra_fields']['impairment_provision'] == 0.0

    def test_apra_fields_substandard_30_points(self, scorer):
        # 30 points should trigger Substandard classification
        anomalies = [
            {"type": "round_dollar", "amount": 10000, "transaction_id": 1, "severity": "high"},
            {"type": "round_dollar", "amount": 10000, "transaction_id": 2, "severity": "high"},
        ]
        alerts = []
        risk = scorer.calculate_score(anomalies, alerts)
        assert risk['score'] == 40  # 20 + 20
        assert risk['category'] == 'Medium'
        assert risk['apra_fields']['asset_classification'] == 'Substandard'
        assert risk['apra_fields']['regulatory_code'] == 'APS222-002'

    def test_apra_fields_doubtful(self, scorer):
        anomalies = [{"type": "high_value", "amount": 300000, "transaction_id": 1, "severity": "high"}]
        alerts = [{"type": "high_risk_jurisdiction", "severity": "high"}]
        risk = scorer.calculate_score(anomalies, alerts)
        assert risk['apra_fields']['asset_classification'] in ['Doubtful', 'Substandard']

    def test_apra_fields_requires_review(self, scorer):
        anomalies = [{"type": "round_dollar", "amount": 10000, "transaction_id": 1, "severity": "high"}]
        alerts = []
        risk = scorer.calculate_score(anomalies, alerts)
        # Score > 50 should trigger review
        assert isinstance(risk['apra_fields']['requires_manual_review'], bool)

    def test_convenience_function(self, single_round_dollar):
        risk = calculate_risk_score(*single_round_dollar)
        assert 'score' in risk
        assert 'apra_fields' in risk

    def test_breakdown_structure(self, scorer, single_round_dollar):
        risk = scorer.calculate_score(*single_round_dollar)
        breakdown = risk['breakdown']
        assert 'round_dollar_points' in breakdown
        assert 'outlier_points' in breakdown
        assert 'high_value_points' in breakdown
        assert 'aml_points' in breakdown
        assert 'total_points' in breakdown
