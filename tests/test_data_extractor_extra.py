"""Data Extractor - Additional unit tests."""

import pytest
from src.agents.data_extractor import DataExtractor

class TestDataExtractorAdditional:
    """Additional edge case tests for DataExtractor."""

    def test_extract_mixed_case_columns(self):
        """Test column names with different casing."""
        extractor = DataExtractor()
        data = {
            "format": "csv",
            "data": [
                {
                    "Transaction_ID": 1,
                    "DaTe": "2025-07-01",
                    "AMOUNT": "$1,000.00",
                    "Description": "Test"
                }
            ],
            "columns": ["Transaction_ID", "DaTe", "AMOUNT", "Description"]
        }
        result = extractor.extract(data)
        assert len(result['transactions']) == 1
        tx = result['transactions'][0]
        assert tx['amount'] == 1000.00
        assert tx['date'] == "2025-07-01"

    def test_extract_business_details_priority(self):
        """Test that CSV business details take precedence over empty tax data."""
        extractor = DataExtractor()
        data = {
            "format": "csv",
            "data": [
                {
                    "transaction_id": 1,
                    "amount": 1000,
                    "business_name": "CSV Business",
                    "abn": "111111111"
                }
            ],
            "columns": ["transaction_id", "amount", "business_name", "abn"]
        }
        result = extractor.extract(data)
        assert result['business_name'] == 'CSV Business'
        assert result['abn'] == '111111111'

    def test_extract_text_no_abn(self, tmp_path):
        """Test PDF text extraction with no ABN found."""
        extractor = DataExtractor()
        data = {
            "format": "pdf",
            "text": "This is a random document with no business details.",
            "file_path": str(tmp_path / "test.pdf")
        }
        result = extractor.extract(data)
        assert result['abn'] == ''
        assert result['business_name'] == ''
        # Should still have empty transactions list
        assert result['transactions'] == []
