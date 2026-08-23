from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ChatMessage(Base):
    """A single message (user or assistant) inside a chat session."""

    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    session_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    user = relationship("User", back_populates="messages")


class Document(Base):
    """Metadata for uploaded source documents.
    Actual vectors live in the FAISS vector store.
    """

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
