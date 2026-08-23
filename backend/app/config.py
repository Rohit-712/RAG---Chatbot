"""
Centralized application configuration.
All values can be overridden via environment variables or a .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # --- App ---
    APP_NAME: str = "RAG Chatbot API"
    ENV: str = "development"

    # --- Auth ---
    SECRET_KEY: str = "change-this-secret-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./data/app.db"

    # --- Vector store ---
    # FAISS is the actual vector store used by the project.
    FAISS_STORAGE_DIR: str = "./data/faiss"

    # --- Embeddings ---
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # --- LLM ---
    LLM_MODEL: str = "llama3.2:3b"
    LLM_TEMPERATURE: float = 0.3

    # --- Gemini ---
    # Used for handwritten/scanned PDF extraction.
    GOOGLE_API_KEY: str = ""
    GEMINI_OCR_MODEL: str = "gemini-2.5-flash"

    # --- Chunking ---
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 120
    TOP_K: int = 4

    # --- Uploads ---
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_MB: int = 25

    # --- CORS ---
    CORS_ORIGINS: list[str] = [
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()