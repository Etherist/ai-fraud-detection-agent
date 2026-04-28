"""Shared utility functions for the AI Fraud Detection Agent."""

import logging
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

# Optional dependencies - imported lazily where needed
# pandas, pytesseract, PIL, pdf2image

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_file(file_path: str, max_size_mb: int = 10, allowed_extensions: List[str] = None) -> bool:
    """
    Validate file format and size.

    Args:
        file_path: Path to the file
        max_size_mb: Maximum allowed file size in MB
        allowed_extensions: List of allowed file extensions (e.g., ['.csv', '.pdf'])

    Returns:
        True if valid, raises ValueError otherwise
    """
    if allowed_extensions is None:
        allowed_extensions = ['.csv', '.pdf']

    path = Path(file_path)

    if not path.exists():
        raise ValueError(f"File not found: {file_path}")

    # Check extension
    if path.suffix.lower() not in allowed_extensions:
        raise ValueError(f"Unsupported file format: {path.suffix}. Allowed: {allowed_extensions}")

    # Check file size
    file_size_mb = path.stat().st_size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        raise ValueError(f"File too large: {file_size_mb:.1f}MB. Maximum: {max_size_mb}MB")

    logger.info(f"File validated: {file_path} ({file_size_mb:.1f}MB)")
    return True


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF using Tesseract OCR via pdf2image.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text as string; empty string on failure
    """
    try:
        # Lazy-import optional dependencies to allow graceful degradation
        try:
            from pdf2image import convert_from_path
        except ImportError:
            logger.error("pdf2image not installed. Install: pip install pdf2image")
            return ""

        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            logger.error("pytesseract or PIL not installed. Install: pip install pytesseract pillow")
            return ""

        logger.info(f"Extracting text from PDF: {pdf_path}")

        # Convert PDF to images (requires poppler installed system-wide)
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                images = convert_from_path(pdf_path, output_folder=tmpdir)
            except Exception as e:
                logger.error(f"pdf2image conversion failed (poppler may be missing): {e}")
                return ""

            if not images:
                logger.warning(f"No pages found in PDF: {pdf_path}")
                return ""

            text_parts = []
            for page_num, img in enumerate(images, start=1):
                try:
                    text = pytesseract.image_to_string(img)
                    text_parts.append(text)
                except pytesseract.TesseractError as e:
                    logger.error(f"Tesseract OCR failed on page {page_num}: {e}")
                    text_parts.append("")  # Keep page count

        full_text = "\n".join(text_parts)
        logger.info(f"Extracted {len(full_text)} characters from PDF ({len(images)} pages)")
        return full_text

    except Exception as e:
        logger.error(f"Unexpected error during PDF extraction: {e}", exc_info=True)
        return ""


def clean_amount(amount_str: str) -> float:
    """
    Clean and convert amount string to float.

    Args:
        amount_str: Amount string (e.g., "$1,234.56", "1234.56")

    Returns:
        Float amount
    """
    if isinstance(amount_str, (int, float)):
        return float(amount_str)

    # Remove currency symbols, commas, and whitespace
    cleaned = re.sub(r'[^\d.-]', '', str(amount_str))
    try:
        return float(cleaned)
    except ValueError:
        logger.warning(f"Could not parse amount: {amount_str}")
        return 0.0


def validate_abn(abn: str) -> bool:
    """
    Validate Australian Business Number (ABN) using official ATO checksum algorithm.

    ABN validation steps:
    1. Subtract 1 from the first digit
    2. Multiply each digit by its weighting factor [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    3. Sum all products
    4. ABN is valid if total modulo 11 equals 0

    Args:
        abn: ABN string to validate (accepts 9-11 digits; pads left with zeros)

    Returns:
        True if valid ABN format, False otherwise
    """
    if not abn:
        return False

    # Clean input: keep digits only
    abn_clean = re.sub(r'\D', '', str(abn))

    if len(abn_clean) < 9 or len(abn_clean) > 11:
        logger.debug(f"ABN length invalid: {len(abn_clean)} digits (expected 9-11)")
        return False

    # Pad to 11 digits ( left-pad with zeros)
    abn_padded = abn_clean.zfill(11)

    # ABN checksum: (first digit - 1) * 10 + sum(digit * weight) for positions 2-11
    weights = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    total = 0

    for i, (digit_char, weight) in enumerate(zip(abn_padded, weights)):
        digit = int(digit_char)
        if i == 0:
            # First digit: subtract 1 before weighting
            digit = digit - 1
        total += digit * weight

    is_valid = (total % 11) == 0
    if not is_valid:
        logger.debug(f"ABN {abn_padded} failed checksum: total={total}, mod11={total % 11}")
    return is_valid


def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load JSON file with error handling.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON as dictionary
    """
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"JSON file not found: {file_path}")
        return {}

    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return {}


def format_currency(amount: float) -> str:
    """Format amount as Australian currency."""
    return f"${amount:,.2f}"


def generate_task_id() -> str:
    """Generate unique task identifier (full UUID)."""
    import uuid
    return str(uuid.uuid4())
