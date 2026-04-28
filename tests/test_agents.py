"""Tests for DocumentIngestor agent."""

import os
import pytest
import pandas as pd
from src.agents.document_ingestor import DocumentIngestor, ingest_file
from src.utils.helpers import validate_file
import tempfile
import csv

class TestDocumentIngestor:
    """Test suite for DocumentIngestor."""

    def test_ingestor_initialization(self):
        ingestor = DocumentIngestor()
        assert ingestor.supported_extensions == ['.csv', '.pdf']

    def test_parse_csv_success(self):
        """Test successful CSV parsing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['transaction_id', 'date', 'amount', 'description'])
            writer.writeheader()
            writer.writerow({
                'transaction_id': 1,
                'date': '2025-07-01',
                'amount': '50000.00',
                'description': 'Test payment'
            })
            f.flush()
            csv_path = f.name

        try:
            ingestor = DocumentIngestor()
            result = ingestor.ingest_file(csv_path)

            assert result['format'] == 'csv'
            assert result['row_count'] == 1
            assert len(result['data']) == 1
            assert result['data'][0]['amount'] == 50000.00
        finally:
            os.unlink(csv_path)

    def test_parse_csv_multiple_rows(self):
        """Test CSV with multiple rows."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['transaction_id', 'date', 'amount'])
            writer.writeheader()
            for i in range(5):
                writer.writerow({'transaction_id': i, 'date': f'2025-07-{i+1:02d}', 'amount': i * 1000})
            f.flush()
            csv_path = f.name

        try:
            ingestor = DocumentIngestor()
            result = ingestor.ingest_file(csv_path)

            assert result['row_count'] == 5
            assert len(result['columns']) == 3
        finally:
            os.unlink(csv_path)

    def test_parse_unsupported_format(self):
        """Test that unsupported format raises error."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'test data')
            f.flush()
            txt_path = f.name

        try:
            ingestor = DocumentIngestor()
            with pytest.raises(ValueError, match="Unsupported file format"):
                ingestor.ingest_file(txt_path)
        finally:
            os.unlink(txt_path)

    def test_file_not_found(self):
        """Test missing file raises error."""
        ingestor = DocumentIngestor()
        with pytest.raises(ValueError, match="File not found"):
            ingestor.ingest_file("/nonexistent/file.csv")

    def test_ingest_multiple_files(self):
        """Test ingesting multiple files."""
        # Create two temp CSVs
        files = []
        for i in range(2):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                writer = csv.DictWriter(f, fieldnames=['a', 'b'])
                writer.writeheader()
                writer.writerow({'a': i, 'b': i*10})
                f.flush()
                files.append(f.name)

        try:
            ingestor = DocumentIngestor()
            results = ingestor.ingest_multiple(files)

            assert len(results) == 2
            assert all(r['format'] == 'csv' for r in results)
        finally:
            for f in files:
                os.unlink(f)

    def test_ingest_pdf_placeholder(self):
        """Test PDF ingestion (placeholder for now)."""
        # PDF parsing requires actual PDF; we'll skip full OCR test
        # But we can test error handling for missing deps
        pass

    def test_convenience_function(self):
        """Test standalone ingest_file function."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("a,b\n1,2\n")
            f.flush()
            csv_path = f.name

        try:
            result = ingest_file(csv_path)
            assert result['format'] == 'csv'
            assert result['row_count'] == 1
        finally:
            os.unlink(csv_path)
