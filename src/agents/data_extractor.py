"""Data Extractor Agent - Extracts key fields from raw document data."""

import logging
import re
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime

from src.utils.helpers import validate_abn, clean_amount

logger = logging.getLogger(__name__)


class DataExtractor:
    """Agent responsible for extracting structured fields from parsed document data."""

    def __init__(self):
        """Initialize DataExtractor."""
        logger.info("DataExtractor initialized")

    def extract(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured fields from parsed document.

        Args:
            parsed_data: Output from DocumentIngestor (contains 'format', 'data', or 'text')

        Returns:
            Dictionary with extracted fields:
                - transactions: List[Dict] with transaction details
                - business_details: Dict with business info
                - abn: str (extracted ABN)
                - business_name: str
                - addresses: List[str]
        """
        logger.info("Extracting data from parsed document")

        file_format = parsed_data.get('format', 'unknown')

        if file_format == 'csv':
            return self._extract_from_csv(parsed_data)
        elif file_format == 'pdf':
            return self._extract_from_text(parsed_data)
        else:
            logger.warning(f"Unknown format: {file_format}")
            return self._empty_extraction()

    def _extract_from_csv(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract fields from CSV data (tabular transactions)."""
        records = parsed_data.get('data', [])
        columns = parsed_data.get('columns', [])

        # Normalize column names (case-insensitive matching)
        columns_lower = [c.lower() for c in columns]

        # Map common column names
        col_map = {}
        for norm_col in ['transaction_id', 'date', 'amount', 'description', 'business_name', 'abn', 'counterparty_jurisdiction']:
            for i, col in enumerate(columns_lower):
                if norm_col.replace('_', ' ') in col or col in norm_col:
                    col_map[norm_col] = columns[i]
                    break

        transactions = []
        for record in records:
            tx = {}
            for field, col_name in col_map.items():
                if col_name in record:
                    tx[field] = record[col_name]

            # Clean amount
            if 'amount' in tx:
                tx['amount'] = clean_amount(tx['amount'])

            # Parse date
            if 'date' in tx:
                tx['date'] = str(tx['date'])  # Could parse to datetime later

            if tx:
                transactions.append(tx)

        # Extract business details (first record's business info)
        business_details = {}
        if records:
            first_record = records[0]
            for key in ['business_name', 'abn', 'address']:
                for col in columns:
                    if key.lower() in col.lower() and col in first_record:
                        business_details[key] = str(first_record[col])
                        break

        result = {
            "transactions": transactions,
            "business_details": business_details,
            "abn": business_details.get('abn', ''),
            "business_name": business_details.get('business_name', ''),
            "addresses": [business_details.get('address', '')] if business_details.get('address') else [],
            "source": "csv"
        }

        logger.info(f"Extracted {len(transactions)} transactions from CSV")
        return result

    def _extract_from_text(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract fields from OCR'd PDF text using regex patterns."""
        text = parsed_data.get('text', '')

        # Initialize extraction results
        result = {
            "transactions": [],
            "business_details": {},
            "abn": "",
            "business_name": "",
            "addresses": [],
            "source": "pdf"
        }

        # Extract ABN using regex
        abn_pattern = r'ABN\s*:?\s*(\d{11})'
        abn_match = re.search(abn_pattern, text, re.IGNORECASE)
        if abn_match:
            result['abn'] = abn_match.group(1)
            logger.info(f"Extracted ABN: {result['abn']}")

        # Extract business name
        # Common patterns: "Business Name:", "Trading As:", etc.
        name_patterns = [
            r'Business\s+Name\s*:?\s*(.+)',
            r'Trading\s+As\s*:?\s*(.+)',
            r'Company\s+Name\s*:?\s*(.+)'
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['business_name'] = match.group(1).strip()
                logger.info(f"Extracted business name: {result['business_name']}")
                break

        # Extract address
        address_pattern = r'Address\s*:?\s*(.+(?:\n.+)?)'
        address_match = re.search(address_pattern, text, re.IGNORECASE)
        if address_match:
            result['addresses'] = [address_match.group(1).strip()]

        # Extract transactions from bank statement text (heuristic)
        # Look for date-amount-description patterns
        result['transactions'] = self._extract_transactions_from_text(text)

        logger.info(f"Extracted {len(result['transactions'])} transactions from text")
        return result

    def _extract_transactions_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract transaction-like entries from unstructured text.

        Uses regex patterns common in bank statements.
        """
        transactions = []

        # Pattern 1: DD/MM/YYYY amount description
        pattern1 = r'(\d{2}/\d{2}/\d{4})\s+[\$£€]?\s*([\d,]+\.?\d*)\s+(.+)'
        matches = re.findall(pattern1, text)

        for match in matches:
            date_str, amount_str, description = match
            try:
                amount = clean_amount(amount_str)
                transactions.append({
                    "date": date_str,
                    "amount": amount,
                    "description": description.strip(),
                    "transaction_id": len(transactions) + 1
                })
            except Exception as e:
                logger.debug(f"Failed to parse transaction: {e}")

        # Pattern 2: Alternative format (YYYY-MM-DD)
        if not transactions:
            pattern2 = r'(\d{4}-\d{2}-\d{2})\s+[\$£€]?\s*([\d,]+\.?\d*)\s+(.+)'
            matches = re.findall(pattern2, text)
            for i, match in enumerate(matches):
                date_str, amount_str, description = match
                try:
                    amount = clean_amount(amount_str)
                    transactions.append({
                        "date": date_str,
                        "amount": amount,
                        "description": description.strip(),
                        "transaction_id": i + 1
                    })
                except Exception as e:
                    logger.debug(f"Failed to parse transaction: {e}")

        return transactions

    def _empty_extraction(self) -> Dict[str, Any]:
        """Return empty extraction result."""
        return {
            "transactions": [],
            "business_details": {},
            "abn": "",
            "business_name": "",
            "addresses": [],
            "source": "unknown"
        }


def extract_data(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to extract structured data.

    Args:
        parsed_data: Output from DocumentIngestor

    Returns:
        Extracted structured data
    """
    extractor = DataExtractor()
    return extractor.extract(parsed_data)
