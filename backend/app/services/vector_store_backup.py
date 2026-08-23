import faiss
import numpy as np

from app.services.embeddings import embedding_service


class FAISSVectorStore:

    def __init__(self):
        self.index = None
        self.texts = []
        self.metadata = []

    def add_chunks(self, chunks, document_name, owner_id):
        embeddings = embedding_service.embed_texts(chunks)
        vectors = np.array(embeddings).astype("float32")

        if self.index is None:
            dim = vectors.shape[1]
            self.index = faiss.IndexFlatL2(dim)

        self.index.add(vectors)

        for chunk in chunks:
            self.texts.append(chunk)
            self.metadata.append({
                "document": document_name,
                "owner_id": owner_id
            })

        return len(chunks)

    def query(self, query_text, owner_id, top_k=5):
        query_embedding = embedding_service.embed_texts([query_text])
        query_vector = np.array(query_embedding).astype("float32")

        distances, indices = self.index.search(
            query_vector,
            top_k
        )

        results = []

        for idx, i in enumerate(indices[0]):

            if i < 0 or i >= len(self.texts):
                continue

            meta = self.metadata[i]

            if meta["owner_id"] == owner_id:
                results.append({
                    "document_name": meta["document"],
                    "chunk_index": i,
                    "text": self.texts[i],
                    "score": float(distances[0][idx]),
                })

        return results


vector_store_service = FAISSVectorStore()