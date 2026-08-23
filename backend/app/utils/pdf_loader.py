"""
Extracts text from uploaded documents.

Supports:

1. Normal text PDFs using pypdf
2. Scanned/handwritten PDFs using Gemini
3. TXT files
4. Markdown files
"""

from pathlib import Path

from pypdf import PdfReader

from app.services.document_ocr import (
    document_ocr_service,
)


def load_pdf_text(
    file_path: str | Path,
) -> str:
    """
    Extract normal machine-readable text
    from a PDF using pypdf.
    """

    reader = PdfReader(str(file_path))

    pages_text = []

    for page in reader.pages:

        text = page.extract_text() or ""

        text = text.strip()

        if text:
            pages_text.append(text)

    return "\n\n".join(
        pages_text
    ).strip()


def load_text_file(
    file_path: str | Path,
) -> str:
    """
    Load TXT or Markdown file.
    """

    return Path(
        file_path
    ).read_text(
        encoding="utf-8",
        errors="ignore",
    ).strip()


def load_document_text(
    file_path: str | Path,
) -> str:
    """
    Main document loader.

    PDF:
        Try pypdf first.
        If no text is found, use Gemini OCR.

    TXT/MD:
        Read directly.
    """

    file_path = Path(file_path)

    suffix = file_path.suffix.lower()

    # --------------------------------------------------
    # PDF
    # --------------------------------------------------

    if suffix == ".pdf":

        # First attempt:
        # Normal machine-readable PDF
        text = load_pdf_text(
            file_path
        )

        if text:

            print(
                "PDF contains extractable text."
            )

            return text

        # --------------------------------------------------
        # No text found
        # Therefore it may be scanned/handwritten
        # --------------------------------------------------

        print(
            "No normal PDF text found."
        )

        print(
            "Starting Gemini handwritten OCR..."
        )

        text = (
            document_ocr_service.extract_pdf_text(
                file_path
            )
        )

        if not text.strip():

            raise ValueError(
                "Could not extract text from PDF."
            )

        return text.strip()

    # --------------------------------------------------
    # TXT / Markdown
    # --------------------------------------------------

    if suffix in (
        ".txt",
        ".md",
    ):

        text = load_text_file(
            file_path
        )

        if not text:

            raise ValueError(
                "The uploaded file is empty."
            )

        return text

    # --------------------------------------------------
    # Unsupported file
    # --------------------------------------------------

    raise ValueError(
        f"Unsupported file type: {suffix}"
    )