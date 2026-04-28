"""Tests for Data Extractor agent."""

import pytest
from src.agents.data_extractor import DataExtractor, extract_data

class TestDataExtractor:
    """Test suite for DataExtractor agent."""

    @pytest.fixture
    def extractor(self):
        return DataExtractor()

    @pytest.fixture
    def csv_parsed_data(self):
        return {
            "format": "csv",
            "data": [
                {
                    "transaction_id": 1,
                    "date": "2025-07-01",
                    "amount": "50000.00",
                    "description": "Invoice payment",
                    "business_name": "Acme Pty Ltd",
                    "abn": "12345678901",
                    "counterparty_jurisdiction": "AU"
                }
            ],
            "columns": ["transaction_id", "date", "amount", "description", "business_name", "abn"]
        }

    @pytest.fixture
    def text_parsed_data(self):
        text = """
        Business Name: Acme Pty Ltd
        ABN: 12345678901
        Address: 123 Main St, Sydney NSW 2000

        01/07/2025  $50,000.00  Customer Payment
        02/07/2025  $12,345.67  Supplier Invoice
        """
        return {
            "format": "pdf",
            "text": text,
            "file_path": "test.pdf"
        }

    def test_extractor_initialization(self, extractor):
        assert extractor is not None

    def test_extract_from_csv(self, extractor, csv_parsed_data):
        result = extractor.extract(csv_parsed_data)

        assert len(result['transactions']) == 1
        tx = result['transactions'][0]
        assert tx['amount'] == 50000.00
        assert tx['business_name'] == 'Acme Pty Ltd'
        assert result['abn'] == '12345678901'

    def test_extract_from_text(self, extractor, text_parsed_data):
        result = extractor.extract(text_parsed_data)

        assert result['abn'] == '12345678901'
        assert result['business_name'] == 'Acme Pty Ltd'
        assert len(result['transactions']) >= 2

    def test_extract_amount_cleaning(self, extractor):
        data = {
            "format": "csv",
            "data": [{"transaction_id": 1, "amount": "$50,000.00"}],
            "columns": ["transaction_id", "amount"]
        }
        result = extractor.extract(data)
        assert result['transactions'][0]['amount'] == 50000.00

    def test_extract_empty_csv(self, extractor):
        data = {"format": "csv", "data": [], "columns": []}
        result = extractor.extract(data)
        assert result['transactions'] == []
        assert result['business_name'] == ''

    def test_extract_empty_text(self, extractor):
        data = {"format": "pdf", "text": ""}
        result = extractor.extract(data)
        assert result['transactions'] == []

    def test_extract_unknown_format(self, extractor):
        data = {"format": "unknown", "data": None}
        result = extractor.extract(data)
        assert result['transactions'] == []
        assert result['source'] == 'unknown'

    def test_convenience_function(self, csv_parsed_data):
        result = extract_data(csv_parsed_data)
        assert 'transactions' in result

    def test_date_preservation(self, extractor, csv_parsed_data):
        result = extractor.extract(csv_parsed_data)
        assert result['transactions'][0]['date'] == "2025-07-01"

    def test_multiple_transactions(self, extractor):
        data = {
            "format": "csv",
            "data": [
                {"transaction_id": i, "amount": f"${i*1000}.00"} for i in range(1, 6)
            ],
            "columns": ["transaction_id", "amount"]
        }
        result = extractor.extract(data)
        assert len(result['transactions']) == 5
        assert result['transactions'][4]['amount'] == 5000.00
