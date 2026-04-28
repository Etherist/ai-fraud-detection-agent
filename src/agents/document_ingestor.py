"""Document Ingestor Agent - Parses uploaded files (PDF/CSV) into structured data."""

import logging
from pathlib import Path
from typing import Dict, List, Union, Any
import pandas as pd

from src.utils.helpers import validate_file, extract_text_from_pdf

logger = logging.getLogger(__name__)


class DocumentIngestor:
    """Agent responsible for ingesting and parsing SME loan application documents."""

    def __init__(self, supported_extensions: List[str] = None):
        """
        Initialize DocumentIngestor.

        Args:
            supported_extensions: List of supported file extensions (e.g., ['.csv', '.pdf'])
        """
        self.supported_extensions = supported_extensions or ['.csv', '.pdf']
        logger.info(f"DocumentIngestor initialized with extensions: {self.supported_extensions}")

    def ingest_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a single file into structured data.

        Args:
            file_path: Path to the file to parse

        Returns:
            Dictionary containing parsed data with keys appropriate to file type
                - For CSV: {"data": List[Dict], "columns": List[str], "row_count": int}
                - For PDF: {"text": str, "page_count": int}
        """
        logger.info(f"Ingesting file: {file_path}")

        try:
            validate_file(file_path, allowed_extensions=self.supported_extensions)
            file_ext = Path(file_path).suffix.lower()

            # Additional MIME type validation using magic bytes
            self._validate_magic_bytes(file_path, file_ext)

            if file_ext == '.csv':
                return self._parse_csv(file_path)
            elif file_ext == '.pdf':
                return self._parse_pdf(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")

        except Exception as e:
            logger.error(f"Failed to ingest {file_path}: {e}")
            raise

    def _validate_magic_bytes(self, file_path: str, extension: str) -> None:
        """Validate file content matches expected magic bytes for its extension."""
        if extension == '.pdf':
            # PDF files start with %PDF-
            with open(file_path, 'rb') as f:
                header = f.read(5)
            if not header.startswith(b'%PDF-'):
                raise ValueError("File does not appear to be a valid PDF (missing %PDF header)")

        elif extension == '.csv':
            # CSV should be readable as text (UTF-8). We don't strictly enforce delimiters.
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.read(1024)  # read a sample
            except UnicodeDecodeError:
                raise ValueError("CSV file does not appear to be text (UTF-8 decode failed)")

    def _parse_csv(self, file_path: str) -> Dict[str, Any]:
        """Parse CSV file into structured data."""
        try:
            df = pd.read_csv(file_path)
            records = df.to_dict('records')

            result = {
                "format": "csv",
                "file_path": file_path,
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns),
                "data": records,
                "sample": records[:5] if records else []
            }

            logger.info(f"Parsed CSV: {len(df)} rows, {len(df.columns)} columns")
            return result

        except Exception as e:
            logger.error(f"CSV parsing failed for {file_path}: {e}")
            raise

    def _parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """Parse PDF file using OCR to extract text."""
        try:
            text = extract_text_from_pdf(file_path)

            result = {
                "format": "pdf",
                "file_path": file_path,
                "text": text,
                "char_count": len(text),
                "page_count": text.count('\f') + 1  # Rough estimate
            }

            logger.info(f"Parsed PDF: extracted {len(text)} characters")
            return result

        except Exception as e:
            logger.error(f"PDF parsing failed for {file_path}: {e}")
            raise

    def ingest_multiple(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Parse multiple files.

        Args:
            file_paths: List of file paths to parse

        Returns:
            List of parsed data dictionaries
        """
        results = []
        for file_path in file_paths:
            try:
                result = self.ingest_file(file_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Skipping {file_path} due to error: {e}")
                results.append({"error": str(e), "file_path": file_path})

        return results


def ingest_file(file_path: str) -> Dict[str, Any]:
    """
    Convenience function to parse a single file.

    Args:
        file_path: Path to file

    Returns:
        Parsed data dictionary
    """
    ingestor = DocumentIngestor()
    return ingestor.ingest_file(file_path)
