"""
Chat endpoints: send a message (RAG-augmented) and fetch history for a session.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.schema import ChatRequest, ChatResponse, SourceChunk, ChatHistoryItem
from app.models.user import User
from app.models.chat_history import ChatMessage
from app.utils.security import get_current_user
from app.services.rag_pipeline import rag_pipeline

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def send_message(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = rag_pipeline.answer_query(
    question=payload.message,
    owner_id=current_user.id,
    db=db,
    session_id=payload.session_id,
    top_k=payload.top_k,
    selected_documents=payload.selected_documents,
)

    sources = [
        SourceChunk(
            document_name=h["document_name"],
            chunk_index=h["chunk_index"],
            text=h["text"][:400],  # trim for payload size
            score=h["score"],
        )
        for h in result["sources"]
    ]

    return ChatResponse(
        answer=result["answer"], session_id=result["session_id"], sources=sources
    )


@router.get("/history/{session_id}", response_model=list[ChatHistoryItem])
def get_history(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id, ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return rows
