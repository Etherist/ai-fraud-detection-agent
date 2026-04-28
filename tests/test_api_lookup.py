"""Tests for API Lookup Agent."""

import pytest
from src.agents.api_lookup_agent import APILookupAgent, lookup_business, lookup_tax_return

class TestAPILookupAgent:
    """Test suite for APILookupAgent."""

    @pytest.fixture
    def agent(self):
        return APILookupAgent()

    def test_agent_initialization(self, agent):
        assert agent.abr_url is not None
        assert agent.ato_url is not None
        assert agent.timeout == 5

    def test_lookup_business_valid(self, agent):
        result = agent.lookup_business("12345678901", "Acme Pty Ltd")

        assert result['valid'] == True
        assert result['abn'] == "12345678901"
        assert result['name'] == "Acme Pty Ltd"
        assert result['status'] in ["Active", "Valid"]
        assert 'message' in result

    def test_lookup_business_invalid_abn(self, agent):
        result = agent.lookup_business("99999999999", "Shell Corp")
        assert result['valid'] == False

    def test_lookup_business_missing_params(self, agent):
        result = agent.lookup_business("", "")
        assert result['valid'] == False
        assert 'required' in result['message'].lower()

    def test_lookup_tax_return_filed(self, agent):
        result = agent.lookup_tax_return("12345678901")
        assert result['found'] == True
        assert result['reported_revenue'] > 0

    def test_lookup_tax_return_not_filed(self, agent):
        result = agent.lookup_tax_return("99999999999")
        assert result['found'] == False

    def test_convenience_functions(self):
        result1 = lookup_business("123456789", "Test Co")
        result2 = lookup_tax_return("123456789")
        assert 'valid' in result1 or 'message' in result1
        assert 'found' in result2

    def test_api_timeout_handling(self, agent):
        # With very short timeout, should still handle gracefully
        fast_agent = APILookupAgent(timeout=0.001)
        result = fast_agent.lookup_business("123456789", "Test")
        assert 'valid' in result or 'message' in result

    def test_batch_lookup(self, agent):
        businesses = [
            {"abn": "123456789", "business_name": "Acme Pty Ltd"},
            {"abn": "999999999", "business_name": "Shell Corp"}
        ]
        result = agent.batch_lookup(businesses)

        assert 'batch_size' in result
        assert result['batch_size'] == 2
        assert 'results' in result
        assert len(result['results']) == 2
