"""
Pydantic schemas used for request validation and response serialization.
Kept separate from SQLAlchemy models (app/models) on purpose.
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Chat ----------
class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = None
    top_k: int | None = None
    selected_documents: list[str] | None = None

class SourceChunk(BaseModel):
    document_name: str
    chunk_index: int
    text: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: list[SourceChunk] = []


class ChatHistoryItem(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Upload ----------
class UploadResponse(BaseModel):
    document_id: int
    document_name: str
    chunks_indexed: int
    message: str

# ---------- Documents ----------

class DocumentOut(BaseModel):
    id: int
    filename: str
    chunk_count: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DeleteDocumentResponse(BaseModel):
    message: str
    document_name: str
    chunks_deleted: int