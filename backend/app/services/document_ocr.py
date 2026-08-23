"""
Gemini-based document extraction service.

Used for scanned and handwritten PDF documents.
"""

from pathlib import Path

from google import genai

from app.config import settings


class DocumentOCRService:

    def __init__(self) -> None:

        if not settings.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=settings.GOOGLE_API_KEY
        )

        self.model = settings.GEMINI_OCR_MODEL

    def extract_pdf_text(
        self,
        file_path: str | Path,
    ) -> str:

        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"PDF not found: {file_path}"
            )

        print(
            f"Uploading PDF to Gemini: "
            f"{file_path.name}"
        )

        # Upload PDF
        uploaded_file = self.client.files.upload(
            file=str(file_path)
        )

        print("PDF uploaded.")
        print("Extracting handwritten text...")

        prompt = """
You are a document transcription system.

Transcribe the entire provided PDF faithfully.

The PDF may contain handwritten notes.

IMPORTANT RULES:

1. Read every page.
2. Transcribe handwritten text as accurately as possible.
3. Preserve headings and subheadings.
4. Preserve bullet points.
5. Preserve numbered lists.
6. Preserve technical terminology.
7. Preserve the original order of the content.
8. Keep page boundaries using:

--- PAGE 1 ---

--- PAGE 2 ---

--- PAGE 3 ---

9. Do NOT summarize the document.
10. Do NOT explain the document.
11. Do NOT invent missing text.
12. If handwriting is genuinely unreadable,
    write [unclear].
13. Preserve important technical terms such as:
    RAG, LLM, embeddings, vector database,
    FAISS, Python, machine learning, etc.
14. Return ONLY the transcription.
"""

        # Gemini Interactions API
        interaction = self.client.interactions.create(
            model=self.model,
            input=[
                {
                    "type": "document",
                    "uri": uploaded_file.uri,
                    "mime_type": uploaded_file.mime_type,
                },
                {
                    "type": "text",
                    "text": prompt,
                },
            ],
        )

        text = interaction.output_text or ""

        if not text.strip():
            raise ValueError(
                "Gemini returned empty document text."
            )

        print(
            f"Gemini extraction completed. "
            f"Characters: {len(text)}"
        )

        return text.strip()


# Singleton
document_ocr_service = DocumentOCRService()