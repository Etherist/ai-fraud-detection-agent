"""Tests for AML Checker agent."""

import pytest
from src.agents.aml_checker import AMLChecker, check_aml

class TestAMLChecker:
    """Test suite for AMLChecker agent."""

    @pytest.fixture
    def checker(self):
        return AMLChecker()

    @pytest.fixture
    def sample_transactions(self):
        return [
            {
                "transaction_id": 1,
                "amount": 50000.00,
                "description": "Normal payment",
                "counterparty": "Acme Pty Ltd",
                "counterparty_jurisdiction": "AU"
            },
            {
                "transaction_id": 2,
                "amount": 10000.00,
                "description": "Round transfer",
                "counterparty": "Shell Corp",
                "counterparty_jurisdiction": "XY"  # high-risk
            },
            {
                "transaction_id": 3,
                "amount": 9500.00,  # just under $10k reporting threshold
                "description": "Cash deposit",
                "counterparty": "Cash Business",
                "counterparty_jurisdiction": "AU"
            }
        ]

    @pytest.fixture
    def suspicious_business(self):
        return {
            "business_name": "Shell Corp",
            "abn": "999999999",
            "addresses": ["123 PO Box, Sydney NSW 2000"]
        }

    def test_checker_initialization(self, checker):
        assert checker.high_risk_jurisdictions is not None
        assert checker.watchlist_entities is not None
        assert isinstance(checker.high_risk_jurisdictions, set)

    def test_high_risk_jurisdiction_detection(self, checker, sample_transactions):
        alerts = checker.check_transactions(sample_transactions, {})
        jurisdiction_alerts = [a for a in alerts if a['type'] == 'high_risk_jurisdiction']
        assert len(jurisdiction_alerts) >= 1
        alert = jurisdiction_alerts[0]
        assert alert['severity'] == 'high'
        assert alert['transaction_id'] == 2

    def test_watchlist_entity_detection(self, checker, suspicious_business):
        txs = [{"transaction_id": 1, "amount": 100, "counterparty": "Shell Corp"}]
        alerts = checker.check_transactions(txs, suspicious_business)

        entity_alerts = [a for a in alerts if a['type'] == 'watchlist_entity']
        assert len(entity_alerts) >= 1

    def test_watchlist_abn_detection(self, checker):
        business = {"business_name": "Test", "abn": "99999999999"}
        alerts = checker.check_transactions([], business)
        abn_alerts = [a for a in alerts if a['type'] == 'watchlist_abn']
        assert len(abn_alerts) >= 1
        assert abn_alerts[0]['severity'] == 'high'

    def test_shell_company_indicator(self, checker):
        business = {
            "business_name": "Test Co",
            "abn": "123456789",
            "addresses": ["123 PO Box, Sydney NSW 2000"]
        }
        alerts = checker.check_transactions([], business)
        shell_alerts = [a for a in alerts if a['type'] == 'shell_company_indicator']
        assert len(shell_alerts) >= 1

    def test_possible_structuring(self, checker):
        """Test detection of sub-threshold transactions (~$10k)."""
        txs = [{"transaction_id": 1, "amount": 9800.00, "description": "cash"}]
        alerts = checker.check_transactions(txs, {})
        struct_alerts = [a for a in alerts if a['type'] == 'possible_structuring']
        assert len(struct_alerts) >= 1

    def test_no_alerts_for_clean_data(self, checker):
        """Test clean transactions produce no alerts."""
        txs = [
            {"transaction_id": 1, "amount": 1000.00, "counterparty": "Normal Co", "counterparty_jurisdiction": "AU"},
            {"transaction_id": 2, "amount": 2000.00, "counterparty": "Regular Ltd", "counterparty_jurisdiction": "AU"}
        ]
        business = {"business_name": "Clean Business", "abn": "123456789"}
        alerts = checker.check_transactions(txs, business)
        # Should only be empty or very low severity
        high_severity = [a for a in alerts if a['severity'] == 'high']
        assert len(high_severity) == 0

    def test_convenience_function(self, sample_transactions):
        alerts = check_aml(sample_transactions, {})
        assert isinstance(alerts, list)

    def test_deduplication(self, checker):
        """Test that duplicate alerts are removed."""
        txs = [
            {"transaction_id": 1, "amount": 100, "counterparty": "Shell Corp"},
            {"transaction_id": 2, "amount": 200, "counterparty": "Shell Corp"}
        ]
        business = {"business_name": "Shell Corp", "abn": "999999999"}
        alerts = checker.check_transactions(txs, business)
        # Each transaction generates its own watchlist_entity alert (different transaction_id)
        # So we expect 2 alerts, not deduplicated
        entity_alerts = [a for a in alerts if a['type'] == 'watchlist_entity']
        assert len(entity_alerts) == 2
        # But business-level alerts (watchlist_business_name) would be deduplicated
        business_alerts = [a for a in alerts if a['type'] == 'watchlist_business_name']
        assert len(business_alerts) == 1

    def test_case_insensitive_jurisdiction(self, checker):
        txs = [{"transaction_id": 1, "amount": 100, "counterparty_jurisdiction": "xy"}]  # lowercase
        alerts = checker.check_transactions(txs, {})
        assert any(a['type'] == 'high_risk_jurisdiction' for a in alerts)

    def test_empty_inputs(self, checker):
        alerts = checker.check_transactions([], {})
        assert isinstance(alerts, list)
        # Should still check business details
        assert len(alerts) == 0
