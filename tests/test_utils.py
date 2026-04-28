"""Tests for utility functions."""

import pytest
from src.utils.helpers import (
    validate_file,
    clean_amount,
    validate_abn,
    load_json_file,
    format_currency,
    generate_task_id
)
from pathlib import Path
import tempfile
import json

class TestHelpers:
    """Test suite for helper utilities."""

    def test_validate_file_not_found(self):
        with pytest.raises(ValueError, match="File not found"):
            validate_file("/nonexistent/file.csv")

    def test_validate_file_invalid_extension(self):
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"test")
            f.flush()
            path = f.name

        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                validate_file(path)
        finally:
            os.unlink(path)

    def test_validate_file_too_large(self):
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            f.write(b"x" * (11 * 1024 * 1024))  # 11MB > default 10MB
            f.flush()
            path = f.name

        try:
            with pytest.raises(ValueError, match="File too large"):
                validate_file(path, max_size_mb=10)
        finally:
            os.unlink(path)

    def test_clean_amount_currency_symbol(self):
        assert clean_amount("$1,234.56") == 1234.56
        assert clean_amount("£5,000.00") == 5000.00

    def test_clean_amount_already_float(self):
        assert clean_amount(1234.56) == 1234.56

    def test_clean_amount_invalid(self):
        assert clean_amount("abc") == 0.0

    def test_validate_abn_valid(self):
        # Valid ABN: 5300485611 (checksum passes)
        assert validate_abn("5300485611") == True

    def test_validate_abn_invalid_length(self):
        assert validate_abn("12345") == False

    def test_validate_abn_non_numeric(self):
        assert validate_abn("12345678A") == False

    def test_load_json_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"key": "value"}, f)
            f.flush()
            path = f.name

        try:
            data = load_json_file(path)
            assert data['key'] == 'value'
        finally:
            os.unlink(path)

    def test_load_json_missing_file(self):
        data = load_json_file("/nonexistent.json")
        assert data == {}

    def test_load_json_invalid(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{invalid}")
            f.flush()
            path = f.name

        try:
            data = load_json_file(path)
            assert data == {}
        finally:
            os.unlink(path)

    def test_format_currency(self):
        assert format_currency(1234.56) == "$1,234.56"
        assert format_currency(0) == "$0.00"

    def test_generate_task_id(self):
        task_id = generate_task_id()
        # Should be a valid UUID string (36 chars with hyphens or 32 hex)
        assert isinstance(task_id, str)
        # Accept either format
        assert len(task_id) in (32, 36)  # hex or UUID with hyphens
        # Verify it's a valid UUID
        import uuid
        try:
            uuid.UUID(task_id, version=4)
        except ValueError:
            self.fail("task_id is not a valid UUID4")

    def test_generate_task_id_unique(self):
        ids = [generate_task_id() for _ in range(100)]
        assert len(set(ids)) == 100  # All unique

import os
