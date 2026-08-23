"""
Document upload + ingestion endpoint.
"""

from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
)
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.db.schema import UploadResponse
from app.models.user import User
from app.models.chat_history import Document
from app.utils.security import get_current_user
from app.services.rag_pipeline import rag_pipeline


router = APIRouter(
    prefix="/upload",
    tags=["upload"],
)


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".md",
}


@router.post(
    "",
    response_model=UploadResponse,
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # ==================================================
    # 1. Validate filename
    # ==================================================

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    filename = Path(file.filename).name
    suffix = Path(filename).suffix.lower()

    # ==================================================
    # 2. Validate extension
    # ==================================================

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{suffix}'. "
                f"Allowed: {sorted(ALLOWED_EXTENSIONS)}"
            ),
        )

    # ==================================================
    # 3. Check duplicate document
    # ==================================================

    existing_document = (
        db.query(Document)
        .filter(
            Document.owner_id == current_user.id,
            Document.filename == filename,
        )
        .first()
    )

    if existing_document:

        raise HTTPException(
            status_code=409,
            detail=(
                f"Document '{filename}' "
                f"already exists."
            ),
        )

    # ==================================================
    # 4. Create upload directory
    # ==================================================

    upload_dir = Path(
        settings.UPLOAD_DIR
    )

    upload_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    dest_path = upload_dir / filename

    # ==================================================
    # 5. Read uploaded file
    # ==================================================

    contents = await file.read()

    # ==================================================
    # 6. Validate file size
    # ==================================================

    max_size = (
        settings.MAX_UPLOAD_MB
        * 1024
        * 1024
    )

    if len(contents) > max_size:

        raise HTTPException(
            status_code=400,
            detail=(
                f"File exceeds "
                f"{settings.MAX_UPLOAD_MB}MB limit."
            ),
        )

    if not contents:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    # ==================================================
    # 7. Save uploaded file
    # ==================================================

    try:

        with open(
            dest_path,
            "wb",
        ) as f:
            f.write(contents)

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to save uploaded file: "
                f"{exc}"
            ),
        )

    # ==================================================
    # 8. Ingest document
    #
    # PDF:
    #     pypdf
    #       ↓
    #     Gemini OCR if needed
    #       ↓
    #     Chunking
    #       ↓
    #     MiniLM embeddings
    #       ↓
    #     FAISS
    #       ↓
    #     SQLite Document record
    # ==================================================

    try:

        (
            document_name,
            chunk_count,
            document_id,
        ) = rag_pipeline.ingest_document(
            file_path=dest_path,
            owner_id=current_user.id,
            db=db,
        )

    except Exception as exc:

        # Remove physical file if ingestion fails
        if dest_path.exists():

            try:
                dest_path.unlink()
            except Exception:
                pass

        # Rollback possible database changes
        try:
            db.rollback()
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to process document: "
                f"{exc}"
            ),
        )

    # ==================================================
    # 9. Return successful response
    # ==================================================

    return UploadResponse(
        document_id=document_id,
        document_name=document_name,
        chunks_indexed=chunk_count,
        message=(
            "Document ingested and indexed "
            "successfully."
        ),
    )