"""
Document management endpoints.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.models.chat_history import Document
from app.models.user import User
from app.services.vector_store import vector_store_service
from app.utils.security import get_current_user


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


# ============================================================
# GET ALL DOCUMENTS
# ============================================================

@router.get("")
def get_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return all documents belonging to the logged-in user.
    """

    documents = (
        db.query(Document)
        .filter(
            Document.owner_id == current_user.id
        )
        .order_by(
            Document.id.asc()
        )
        .all()
    )

    return [
        {
            "id": document.id,
            "filename": document.filename,
            "chunk_count": document.chunk_count,
            "owner_id": document.owner_id,
        }
        for document in documents
    ]


# ============================================================
# DELETE DOCUMENT
# ============================================================

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a document from:
    
    1. FAISS
    2. Database
    3. Uploaded file
    """

    # --------------------------------------------------------
    # 1. Find document belonging to current user
    # --------------------------------------------------------

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.owner_id == current_user.id,
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    document_name = document.filename

    # --------------------------------------------------------
    # 2. Delete from FAISS
    # --------------------------------------------------------

    deleted_chunks = (
        vector_store_service.delete_document(
            document_name=document_name,
            owner_id=current_user.id,
        )
    )

    # --------------------------------------------------------
    # 3. Delete database record
    # --------------------------------------------------------

    db.delete(document)

    db.commit()

    # --------------------------------------------------------
    # 4. Delete physical uploaded file
    # --------------------------------------------------------

    file_path = (
        Path(settings.UPLOAD_DIR)
        / document_name
    )

    file_deleted = False

    if file_path.exists():

        try:

            file_path.unlink()

            file_deleted = True

        except Exception as error:

            print(
                f"Could not delete physical file: {error}"
            )

    # --------------------------------------------------------
    # 5. Response
    # --------------------------------------------------------

    return {
        "message": "Document deleted successfully.",
        "document_id": document_id,
        "document_name": document_name,
        "chunks_deleted": deleted_chunks,
        "file_deleted": file_deleted,
    }