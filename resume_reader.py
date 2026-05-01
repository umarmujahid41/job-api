"""
AI Job Agent - Resume Reader
Extracts clean text from a PDF resume.
"""

import logging
from pathlib import Path

import pdfplumber

from config import RESUME_PDF_PATH

logger = logging.getLogger(__name__)


def read_resume_pdf(pdf_path: str = RESUME_PDF_PATH) -> str:
    """
    Extract all text from a PDF resume.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Plain text content of the resume.
    """
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Resume not found at '{pdf_path}'.\n"
            f"Please set RESUME_PDF_PATH in your .env file."
        )

    logger.info(f"Reading resume from: {path.resolve()}")

    text_parts = []

    with pdfplumber.open(path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
            else:
                logger.debug(f"Page {page_num} had no extractable text.")

    full_text = "\n\n".join(text_parts).strip()

    if not full_text:
        raise ValueError(
            "Could not extract any text from the PDF. "
            "Make sure it's not a scanned image-only PDF."
        )

    logger.info(f"Resume extracted: {len(full_text)} characters, {len(pdf.pages)} pages.")
    return full_text


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    text = read_resume_pdf()
    print(f"\n{'='*60}")
    print("RESUME TEXT PREVIEW (first 500 chars):")
    print(text[:500])
    print(f"{'='*60}")
    print(f"Total characters: {len(text)}")
