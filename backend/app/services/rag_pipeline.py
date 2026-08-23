"""
RAG pipeline.

Flow:
1. Extract document text
2. Split text page-by-page
3. Split each page into chunks
4. Generate embeddings
5. Store chunks + page metadata in FAISS
6. Save document record in database
7. Retrieve relevant chunks
8. Generate answer using Ollama
9. Save chat history
"""

import re
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models.chat_history import ChatMessage, Document
from app.services.llm import llm_service
from app.services.vector_store import vector_store_service
from app.utils.chunking import chunk_text
from app.utils.pdf_loader import load_document_text


class RAGPipeline:

    # ==========================================================
    # PAGE PARSER
    # ==========================================================

    def split_into_pages(
        self,
        text: str,
    ) -> list[tuple[int, str]]:
        """
        Split OCR text into individual pages.

        Expected OCR format:

        --- PAGE 1 ---

        text...

        --- PAGE 2 ---

        text...

        Returns:

        [
            (1, "page 1 text"),
            (2, "page 2 text"),
        ]
        """

        pattern = re.compile(
            r"---\s*PAGE\s+(\d+)\s*---",
            flags=re.IGNORECASE,
        )

        matches = list(
            pattern.finditer(text)
        )

        pages = []

        # ------------------------------------------------------
        # If OCR contains page markers
        # ------------------------------------------------------

        if matches:

            for index, match in enumerate(matches):

                page_number = int(
                    match.group(1)
                )

                start = match.end()

                if index + 1 < len(matches):

                    end = matches[
                        index + 1
                    ].start()

                else:

                    end = len(text)

                page_text = text[
                    start:end
                ].strip()

                if page_text:

                    pages.append(
                        (
                            page_number,
                            page_text,
                        )
                    )

            return pages

        # ------------------------------------------------------
        # Fallback
        # ------------------------------------------------------

        if text.strip():

            return [
                (
                    1,
                    text.strip(),
                )
            ]

        return []

    # ==========================================================
    # DOCUMENT INGESTION
    # ==========================================================

    def ingest_document(
        self,
        file_path: str | Path,
        owner_id: int,
        db: Session,
    ) -> tuple[str, int, int]:

        document_name = Path(
            file_path
        ).name

        print(
            f"Starting ingestion: {document_name}"
        )

        # ------------------------------------------------------
        # 1. Extract text
        # ------------------------------------------------------

        raw_text = load_document_text(
            file_path
        )

        if not raw_text.strip():

            raise ValueError(
                "No text could be extracted "
                "from the document."
            )

        print(
            f"Extracted characters: "
            f"{len(raw_text)}"
        )

        # ------------------------------------------------------
        # 2. Split into pages
        # ------------------------------------------------------

        pages = self.split_into_pages(
            raw_text
        )

        if not pages:

            raise ValueError(
                "Document contains no pages."
            )

        print(
            f"Detected pages: {len(pages)}"
        )

        # ------------------------------------------------------
        # 3. Chunk each page separately
        # ------------------------------------------------------

        all_chunks = []

        for page_number, page_text in pages:

            page_chunks = chunk_text(
                page_text,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
            )

            for chunk in page_chunks:

                all_chunks.append(
                    {
                        "text": chunk,
                        "page_number": page_number,
                    }
                )

        if not all_chunks:

            raise ValueError(
                "Document produced no chunks."
            )

        print(
            f"Created chunks: "
            f"{len(all_chunks)}"
        )

        # ------------------------------------------------------
        # 4. Prepare text + page numbers
        # ------------------------------------------------------

        chunk_texts = [
            item["text"]
            for item in all_chunks
        ]

        page_numbers = [
            item["page_number"]
            for item in all_chunks
        ]

        # ------------------------------------------------------
        # 5. Store chunks + embeddings in FAISS
        # ------------------------------------------------------

        chunk_count = (
            vector_store_service.add_chunks(
                chunks=chunk_texts,
                document_name=document_name,
                owner_id=owner_id,
                page_numbers=page_numbers,
            )
        )

        print(
            f"Indexed chunks: {chunk_count}"
        )

        # ------------------------------------------------------
        # 6. Save document metadata
        # ------------------------------------------------------

        doc_record = Document(
            owner_id=owner_id,
            filename=document_name,
            chunk_count=chunk_count,
        )

        db.add(
            doc_record
        )

        db.commit()

        db.refresh(
            doc_record
        )

        print(
            f"Document saved with ID: "
            f"{doc_record.id}"
        )

        # ------------------------------------------------------
        # 7. Return
        # ------------------------------------------------------

        return (
            document_name,
            chunk_count,
            doc_record.id,
        )

    # ==========================================================
    # QUESTION ANSWERING
    # ==========================================================

    def answer_query(
        self,
        question: str,
        owner_id: int,
        db: Session,
        session_id: str | None = None,
        top_k: int | None = None,
        selected_documents: list[str] | None = None,
    ) -> dict:

        session_id = (
            session_id
            or str(uuid.uuid4())
        )

        # ------------------------------------------------------
        # 1. Retrieve relevant chunks
        # ------------------------------------------------------

        hits = vector_store_service.query(
            query_text=question,
            owner_id=owner_id,
            top_k=(
                top_k
                or settings.TOP_K
            ),
            selected_documents=(
                selected_documents
            ),
        )

        # ------------------------------------------------------
        # 2. Context
        # ------------------------------------------------------

        context_chunks = [
            hit["text"]
            for hit in hits
        ]

        # ------------------------------------------------------
        # 3. Conversation history
        # ------------------------------------------------------

        history_rows = (
            db.query(
                ChatMessage
            )
            .filter(
                ChatMessage.session_id
                == session_id,

                ChatMessage.user_id
                == owner_id,
            )
            .order_by(
                ChatMessage.created_at.asc()
            )
            .all()
        )

        history = [
            {
                "role": row.role,
                "content": row.content,
            }
            for row in history_rows
        ]

        # ------------------------------------------------------
        # 4. Generate answer
        # ------------------------------------------------------

        answer = (
            llm_service.generate_answer(
                question=question,
                context_chunks=context_chunks,
                chat_history=history,
            )
        )

        # ------------------------------------------------------
        # 5. Save user message
        # ------------------------------------------------------

        db.add(
            ChatMessage(
                user_id=owner_id,
                session_id=session_id,
                role="user",
                content=question,
            )
        )

        # ------------------------------------------------------
        # 6. Save assistant message
        # ------------------------------------------------------

        db.add(
            ChatMessage(
                user_id=owner_id,
                session_id=session_id,
                role="assistant",
                content=answer,
            )
        )

        db.commit()

        # ------------------------------------------------------
        # 7. Return
        # ------------------------------------------------------

        return {
            "answer": answer,
            "session_id": session_id,
            "sources": hits,
        }


# ==========================================================
# SINGLETON
# ==========================================================

rag_pipeline = RAGPipeline()