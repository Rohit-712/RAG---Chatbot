"""
Embedding generation service.

Uses a local sentence-transformers model by default so the project runs
fully offline without an API key. The model is loaded once (singleton)
because loading is the expensive part.
"""
from functools import lru_cache
from sentence_transformers import SentenceTransformer

from app.config import settings


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    return SentenceTransformer(settings.EMBEDDING_MODEL)


class EmbeddingService:
    def __init__(self) -> None:
        self.model = _get_model()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts, returning one vector per text."""
        if not texts:
            return []
        embeddings = self.model.encode(
            texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


embedding_service = EmbeddingService()
