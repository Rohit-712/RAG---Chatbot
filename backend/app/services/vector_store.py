"""
FAISS vector store.

Responsibilities:
1. Store document chunk embeddings
2. Search relevant chunks
3. Isolate documents by user
4. Filter by selected documents
5. Delete a document and rebuild the FAISS index
6. Persist FAISS index and metadata to disk
7. Preserve page numbers for document sources
"""

import os
import pickle

import faiss
import numpy as np

from app.services.embeddings import embedding_service


class FAISSVectorStore:

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(self):

        # ------------------------------------------------------
        # Storage paths FIRST
        # ------------------------------------------------------

        self.storage_dir = "./data/faiss"

        self.index_path = os.path.join(
            self.storage_dir,
            "index.faiss",
        )

        self.metadata_path = os.path.join(
            self.storage_dir,
            "metadata.pkl",
        )

        os.makedirs(
            self.storage_dir,
            exist_ok=True,
        )

        # ------------------------------------------------------
        # In-memory data
        # ------------------------------------------------------

        self.index = None

        self.texts = []

        self.metadata = []

        # ------------------------------------------------------
        # Load existing FAISS data
        # ------------------------------------------------------

        self.load()

    # ==========================================================
    # ADD CHUNKS
    # ==========================================================

    def add_chunks(
        self,
        chunks,
        document_name,
        owner_id,
        page_numbers=None,
    ):
        """
        Add document chunks to FAISS.

        Each chunk stores:

        - document name
        - owner ID
        - page number
        """

        if not chunks:
            return 0

        # ------------------------------------------------------
        # Validate page numbers
        # ------------------------------------------------------

        if page_numbers is None:

            page_numbers = [
                None
                for _ in chunks
            ]

        if len(page_numbers) != len(chunks):

            raise ValueError(
                "page_numbers count must match chunks count."
            )

        # ------------------------------------------------------
        # Generate embeddings
        # ------------------------------------------------------

        vectors = embedding_service.embed_texts(
            chunks
        )

        if not vectors:

            raise ValueError(
                "Could not generate embeddings."
            )

        # ------------------------------------------------------
        # Convert to numpy
        # ------------------------------------------------------

        vectors = np.asarray(
            vectors,
            dtype="float32",
        )

        # ------------------------------------------------------
        # Create FAISS index
        # ------------------------------------------------------

        if self.index is None:

            dimension = vectors.shape[1]

            self.index = faiss.IndexFlatL2(
                dimension
            )

        # ------------------------------------------------------
        # Validate vector dimension
        # ------------------------------------------------------

        if vectors.shape[1] != self.index.d:

            raise ValueError(
                f"Embedding dimension mismatch. "
                f"FAISS expects {self.index.d}, "
                f"but received {vectors.shape[1]}."
            )

        # ------------------------------------------------------
        # Add vectors
        # ------------------------------------------------------

        self.index.add(
            vectors
        )

        # ------------------------------------------------------
        # Store text + metadata
        # ------------------------------------------------------

        for chunk, page_number in zip(
            chunks,
            page_numbers,
        ):

            self.texts.append(
                chunk
            )

            self.metadata.append(
                {
                    "document": document_name,
                    "owner_id": owner_id,
                    "page_number": page_number,
                }
            )

        # ------------------------------------------------------
        # Save
        # ------------------------------------------------------

        self.save()

        print(
            f"Added {len(chunks)} chunks "
            f"from '{document_name}'"
        )

        return len(chunks)

    # ==========================================================
    # QUERY
    # ==========================================================

    def query(
        self,
        query_text,
        owner_id,
        top_k=5,
        selected_documents=None,
    ):
        """
        Search relevant chunks.

        Filters:
        1. owner_id
        2. selected_documents

        Returns:
        - document_name
        - page_number
        - chunk_index
        - text
        - score
        """

        # ------------------------------------------------------
        # Empty index
        # ------------------------------------------------------

        if (
            self.index is None
            or self.index.ntotal == 0
        ):

            return []

        # ------------------------------------------------------
        # Validate question
        # ------------------------------------------------------

        if (
            not query_text
            or not query_text.strip()
        ):

            return []

        # ------------------------------------------------------
        # Embed question
        # ------------------------------------------------------

        query_embeddings = (
            embedding_service.embed_texts(
                [query_text]
            )
        )

        if not query_embeddings:

            return []

        query_vector = np.asarray(
            query_embeddings,
            dtype="float32",
        )

        # ------------------------------------------------------
        # Search more than top_k
        #
        # Some results may belong to:
        # - another user
        # - another selected document
        # ------------------------------------------------------

        search_k = min(
            max(top_k * 10, 20),
            self.index.ntotal,
        )

        distances, indices = (
            self.index.search(
                query_vector,
                search_k,
            )
        )

        results = []

        # ------------------------------------------------------
        # Process results
        # ------------------------------------------------------

        for position, index_id in enumerate(
            indices[0]
        ):

            if index_id < 0:
                continue

            if index_id >= len(
                self.texts
            ):
                continue

            if index_id >= len(
                self.metadata
            ):
                continue

            meta = self.metadata[
                index_id
            ]

            # --------------------------------------------------
            # Owner isolation
            # --------------------------------------------------

            if meta.get(
                "owner_id"
            ) != owner_id:

                continue

            # --------------------------------------------------
            # Selected document filtering
            # --------------------------------------------------

            if (
                selected_documents
                and meta.get("document")
                not in selected_documents
            ):

                continue

            # --------------------------------------------------
            # Build result
            # --------------------------------------------------

            result = {
                "document_name": meta.get(
                    "document"
                ),

                "page_number": meta.get(
                    "page_number"
                ),

                "chunk_index": int(
                    index_id
                ),

                "text": self.texts[
                    index_id
                ],

                "score": float(
                    distances[0][position]
                ),
            }

            results.append(
                result
            )

            # --------------------------------------------------
            # Enough results
            # --------------------------------------------------

            if len(results) >= top_k:
                break

        return results

    # ==========================================================
    # DELETE DOCUMENT
    # ==========================================================

    def delete_document(
        self,
        document_name: str,
        owner_id: int,
    ) -> int:
        """
        Delete all chunks for a document
        belonging to a specific user.

        Returns number of deleted chunks.
        """

        if (
            self.index is None
            or self.index.ntotal == 0
        ):

            return 0

        keep_texts = []

        keep_metadata = []

        deleted_count = 0

        # ------------------------------------------------------
        # Find records to keep
        # ------------------------------------------------------

        for text, meta in zip(
            self.texts,
            self.metadata,
        ):

            same_document = (
                meta.get("document")
                == document_name
            )

            same_owner = (
                meta.get("owner_id")
                == owner_id
            )

            if (
                same_document
                and same_owner
            ):

                deleted_count += 1

                continue

            keep_texts.append(
                text
            )

            keep_metadata.append(
                meta
            )

        # ------------------------------------------------------
        # Nothing deleted
        # ------------------------------------------------------

        if deleted_count == 0:

            return 0

        # ------------------------------------------------------
        # Replace data
        # ------------------------------------------------------

        self.texts = keep_texts

        self.metadata = keep_metadata

        # ------------------------------------------------------
        # Rebuild FAISS
        # ------------------------------------------------------

        if self.texts:

            embeddings = (
                embedding_service.embed_texts(
                    self.texts
                )
            )

            if embeddings:

                vectors = np.asarray(
                    embeddings,
                    dtype="float32",
                )

                self.index = (
                    faiss.IndexFlatL2(
                        vectors.shape[1]
                    )
                )

                self.index.add(
                    vectors
                )

            else:

                self.index = None

        else:

            self.index = None

        # ------------------------------------------------------
        # Save
        # ------------------------------------------------------

        self.save()

        print(
            f"Deleted {deleted_count} chunks "
            f"from '{document_name}'"
        )

        return deleted_count

    # ==========================================================
    # SAVE
    # ==========================================================

    def save(self):
        """
        Save FAISS index and metadata.
        """

        # ------------------------------------------------------
        # No index
        # ------------------------------------------------------

        if self.index is None:

            if os.path.exists(
                self.index_path
            ):

                os.remove(
                    self.index_path
                )

            if os.path.exists(
                self.metadata_path
            ):

                os.remove(
                    self.metadata_path
                )

            return

        # ------------------------------------------------------
        # Save FAISS index
        # ------------------------------------------------------

        faiss.write_index(
            self.index,
            self.index_path,
        )

        # ------------------------------------------------------
        # Save metadata
        # ------------------------------------------------------

        with open(
            self.metadata_path,
            "wb",
        ) as f:

            pickle.dump(
                {
                    "texts": self.texts,
                    "metadata": self.metadata,
                },
                f,
            )

    # ==========================================================
    # LOAD
    # ==========================================================

    def load(self):
        """
        Load FAISS index and metadata.

        If no files exist,
        start with an empty store.
        """

        # ------------------------------------------------------
        # Check FAISS index
        # ------------------------------------------------------

        if not os.path.exists(
            self.index_path
        ):

            print(
                "No FAISS index found. "
                "Starting with empty store."
            )

            return

        # ------------------------------------------------------
        # Check metadata
        # ------------------------------------------------------

        if not os.path.exists(
            self.metadata_path
        ):

            print(
                "No FAISS metadata found. "
                "Starting with empty store."
            )

            return

        try:

            # --------------------------------------------------
            # Load FAISS
            # --------------------------------------------------

            self.index = (
                faiss.read_index(
                    self.index_path
                )
            )

            # --------------------------------------------------
            # Load metadata
            # --------------------------------------------------

            with open(
                self.metadata_path,
                "rb",
            ) as f:

                data = pickle.load(
                    f
                )

            self.texts = data.get(
                "texts",
                [],
            )

            self.metadata = data.get(
                "metadata",
                [],
            )

            # --------------------------------------------------
            # Validate metadata
            # --------------------------------------------------

            if len(
                self.texts
            ) != len(
                self.metadata
            ):

                raise ValueError(
                    "FAISS metadata mismatch: "
                    f"{len(self.texts)} texts vs "
                    f"{len(self.metadata)} metadata."
                )

            # --------------------------------------------------
            # Validate FAISS
            # --------------------------------------------------

            if (
                self.index.ntotal
                != len(self.texts)
            ):

                raise ValueError(
                    "FAISS index mismatch: "
                    f"{self.index.ntotal} vectors vs "
                    f"{len(self.texts)} texts."
                )

            print(
                "FAISS loaded successfully."
            )

            print(
                f"Vectors: {self.index.ntotal}"
            )

            print(
                f"Texts: {len(self.texts)}"
            )

            print(
                f"Metadata: {len(self.metadata)}"
            )

        except Exception as exc:

            print(
                "Could not load FAISS store:"
            )

            print(
                exc
            )

            self.index = None

            self.texts = []

            self.metadata = []

    # ==========================================================
    # CLEAR
    # ==========================================================

    def clear(self):
        """
        Delete all vectors and metadata.
        """

        self.index = None

        self.texts = []

        self.metadata = []

        self.save()

        print(
            "FAISS vector store cleared."
        )


# ==========================================================
# SINGLETON INSTANCE
# ==========================================================

vector_store_service = FAISSVectorStore()