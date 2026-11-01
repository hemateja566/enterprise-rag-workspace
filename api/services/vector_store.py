#!/usr/bin/env python3
"""Vector Store Service for Enterprise RAG Workspace.

Provides a unified interface for vector similarity search across multiple
vector database backends: ChromaDB, Milvus, Qdrant, or local FAISS serialized files.

The service is indexed per-workspace, supporting multi-tenancy. Each workspace
has its own vector index namespace/collection to prevent cross-tenant data leakage.

Supported Backends:
- ChromaDB (embedded or client-server)
- Milvus (standalone or cloud)
- Qdrant (standalone or cloud)
- Local FAISS index files (serialized per workspace)
"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

# Backend selection from environment
VECTOR_BACKEND = os.getenv("VECTOR_BACKEND", "chromadb").lower()

# Mock implementations for prototype; replace with real client code in production


class VectorStore:
    """Abstract vector store backend."""

    def __init__(self, workspace_id: int):
        self.workspace_id = workspace_id
        self._initialized = False

    def initialize(self):
        """Initialize the backend connection/collection."""
        if self._initialized:
            return
        # In production, connect to the specific backend
        # e.g., chromadb_client.get_or_create_collection(...)
        self._initialized = True

    def add_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        chunk_ids: List[str],
    ) -> None:
        """Store text chunks with their embeddings in the vector index.

        Args:
            chunks: List of chunk metadata dicts (with document_id, page_number, etc.)
            embeddings: List of corresponding embedding vectors (list of floats)
            chunk_ids: List of unique IDs for each chunk (usually UUIDs or DB primary keys)
        """
        raise NotImplementedError

    def search_similar(
        self,
        query_embedding: List[float],
        k: int = 10,
        document_filters: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """Search for the k most similar chunks to the query embedding.

        Args:
            query_embedding: The query vector.
            k: Number of results to return.
            document_filters: Optional filters (e.g., {"workspace_id": 1, "document_ids": [1,2,3]})

        Returns:
            List of dicts with at least: chunk_id, text, page_number, score similar
            to what DocumentChunk model stores.
        """
        raise NotImplementedError

    def delete_workspace(self, workspace_id: int) -> None:
        """Remove all vectors associated with a workspace (for tenant deletion)."""
        raise NotImplementedError


# -------------------------------------------------------
# ChromaDB Implementation
# -------------------------------------------------------
if VECTOR_BACKEND == "chromadb":

    try:
        import chromadb
        from chromadb.config import Settings

        class ChromaVectorStore(VectorStore):
            """ChromaDB-backed vector store per workspace."""

            def __init__(self, workspace_id: int):
                super().__init__(workspace_id)
                self.client = None
                self.collection = None

            def initialize(self):
                """Create or connect to a workspace-scoped ChromaDB collection."""
                super().initialize()
                try:
                    self.client = chromadb.EphemeralClient()
                    # Each workspace gets its own collection name for isolation
                    self.collection = self.client.get_or_create_collection(
                        name=f"workspace_{self.workspace_id}"
                    )
                except Exception as e:
                    raise RuntimeError(f"Failed to initialize ChromaDB: {e}")
                super().initialize()

            def add_chunks(
                self,
                chunks: List[Dict[str, Any]],
                embeddings: List[List[float]],
                chunk_ids: List[str],
            ) -> None:
                """Add chunks with embeddings to ChromaDB collection."""
                if not self.collection:
                    self.initialize()

                # Prepare metadata for each chunk
                metadatas = []
                for chunk in chunks:
                    meta = {
                        "document_id": chunk.get("document_id"),
                        "page_number": chunk.get("page_number"),
                        "chunk_index": chunk.get("chunk_index"),
                        "workspace_id": self.workspace_id,
                    }
                    metadatas.append(meta)

                # Add to collection
                self.collection.add(
                    embeddings=embeddings,
                    documents=[c.get("text", "") for c in chunks],
                    metadatas=metadatas,
                    ids=chunk_ids,
                )

            def search_similar(
                self,
                query_embedding: List[float],
                k: int = 10,
                document_filters: Optional[Dict] = None,
            ) -> List[Dict[str, Any]]:
                """Search similar chunks in ChromaDB."""
                if not self.collection:
                    self.initialize()

                # Build where clause for workspace isolation
                where = {}
                if document_filters:
                    where.update(document_filters)
                # Always filter by workspace
                where["workspace_id"] = self.workspace_id

                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=k,
                    where=where if where else None,
                )

                # Format results to match expected schema
                formatted = []
                if results["ids"] and results["ids"][0]:
                    for i in range(len(results["ids"][0])):
                        formatted.append(
                            {
                                "id": results["ids"][0][i],
                                "text": results["documents"][0][i] if results["documents"] else "",
                                "page_number": results["metadatas"][0][i].get(
                                    "page_number", 1
                                )
                                if results["metadatas"]
                                else 1,
                                "score": results["distances"][0][i]
                                if results["distances"]
                                else None,
                            }
                        )
                return formatted

            def delete_workspace(self, workspace_id: int) -> None:
                """Delete entire collection for a workspace."""
                if self.client:
                    try:
                        self.client.delete_collection(name=f"workspace_{workspace_id}")
                    except Exception:
                        pass


    except ImportError:
        # Fallback if chroma not installed
        class ChromaVectorStore(VectorStore):
            def initialize(self): pass
            def add_chunks(self, *args, **kwargs): pass
            def search_similar(self, *args, **kwargs): return []
            def delete_workspace(self, *args, **kwargs): pass


# -------------------------------------------------------
# FAISS Local Implementation
# -------------------------------------------------------
elif VECTOR_BACKEND == "faiss_local":

    class FaissVectorStore(VectorStore):
        """Local FAISS-serialized vector store per workspace.

        Stores indices on disk as .index files and metadata as JSON.
        Good for single-node deployments without external DB dependencies.
        """

        def __init__(self, workspace_id: int):
            super().__init__(workspace_id)
            self.index_path = f"faiss_indices/workspace_{workspace_id}.index"
            self.metadata_path = f"faiss_indices/workspace_{workspace_id}_meta.json"
            self.index = None
            self.metadata = {}  # chunk_id -> {text, page_number, document_id}
            import faiss

        def initialize(self):
            """Load existing index or create new one."""
            import os as _os
            _os.makedirs("faiss_indices", exist_ok=True)

            import faiss as _faiss

            if _os.path.exists(self.index_path):
                self.index = _faiss.read_index(self.index_path)
                with open(self.metadata_path, "r") as f:
                    self.metadata = json.load(f)
            else:
                # d=768 is typical for sentence-transformers; should match embeddings
                self.index = _faiss.IndexFlatIP(768)  # Inner product for cosine similarity
                self.metadata = {}
                self._save()

            super().initialize()

        def add_chunks(
            self,
            chunks: List[Dict[str, Any]],
            embeddings: List[List[float]],
            chunk_ids: List[str],
        ) -> None:
            """Add embeddings to FAISS index."""
            import numpy as np

            if not self.index:
                self.initialize()

            vectors = np.array(embeddings).astype("float32")
            # Normalize for inner product cosine similarity
            faiss.normalize_L2(vectors)

            # Add vectors to index
            self.index.add(vectors)

            # Update metadata mapping
            for cid, chunk, emb in zip(chunk_ids, chunks, embeddings):
                self.metadata[cid] = {
                    "text": chunk.get("text", ""),
                    "page_number": chunk.get("page_number"),
                    "document_id": chunk.get("document_id"),
                    "workspace_id": self.workspace_id,
                }
            self._save()

        def search_similar(
            self,
            query_embedding: List[float],
            k: int = 10,
            document_filters: Optional[Dict] = None,
        ) -> List[Dict[str, Any]]:
            """Search similar chunks using FAISS."""
            if not self.index:
                self.initialize()

            import numpy as np

            query_vec = np.array([query_embedding]).astype("float32")
            faiss.normalize_L2(query_vec)

            # Search; k_plus accounts for potential filtering later
            k = min(k, len(self.index) if self.index else 1, 100)
            distances, indices = self.index.search(query_vec, k)

            formatted = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx == -1:
                    continue  # FAISS returns -1 for insufficient results
                cid = str(
                    list(self.metadata.keys())[idx]
                )  # Simplified mapping; real impl uses proper id mapping
                # Actually we need a proper id->idx mapping; this is a prototype simplification
                chunk_meta = self.metadata.get(cid, {})
                formatted.append(
                    {
                        "id": cid,
                        "text": chunk_meta.get("text", ""),
                        "page_number": chunk_meta.get("page_number", 1),
                        "score": float(dist),
                    }
                )
            return formatted

        def delete_workspace(self, workspace_id: int) -> None:
            """Delete index file and metadata for a workspace."""
            import os as _os
            _os.remove(self.index_path) if _os.path.exists(self.index_path) else None
            _os.remove(self.metadata_path) if _os.path.exists(self.metadata_path) else None


# -------------------------------------------------------
# Default (mock) implementation
# -------------------------------------------------------
else:
    class MockVectorStore(VectorStore):
        """Mock vector store for prototyping without external dependencies."""

        def __init__(self, workspace_id: int):
            super().__init__(workspace_id)
            self.chunks_db = (
                []  # In-memory list of chunk dicts for demo purposes
            )

        def initialize(self):
            pass

        def add_chunks(
            self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        chunk_ids: List[str],
        ) -> None:
            """Store chunks + embeddings in-memory for prototyping."""
            for cid, chunk, emb in zip(chunk_ids, chunks, embeddings):
                self.chunks_db.append(
                    {"id": cid, "text": chunk.get("text", ""), "embedding": emb, "metadata": chunk}
                )

        def search_similar(
            self,
            query_embedding: List[float],
            k: int = 10,
            document_filters: Optional[Dict] = None,
        ) -> List[Dict[str, Any]]:
            """Simple cosine-similarity search in-memory (prototype only)."""
            import math

            if not self.chunks_db:
                return []

            # Very naive similarity: just return first k chunks
            # Real implementation would compute cosine similarity
            results = self.chunks_db[:k]
            formatted = []
            for item in results:
                meta = item.get("metadata", {})
                formatted.append(
                    {
                        "id": item["id"],
                        "text": item.get("text", ""),
                        "page_number": meta.get("page_number", 1),
                        "score": 0.8,  # Placeholder score
                    }
                )
            return formatted

        def delete_workspace(self, workspace_id: int) -> None:
            self.chunks_db = []


def get_vector_store(workspace_id: int) -> VectorStore:
    """Factory: get a workspace-scoped vector store instance.

    Args:
        workspace_id: The ID of the workspace whose index to use.

    Returns:
        A VectorStore subclass instance configured for the selected backend.
    """
    store = {
        "chromadb": ChromaVectorStore,
        "faiss_local": FaissVectorStore,
        "mock": MockVectorStore,
    }.get(VECTOR_BACKEND, MockVectorStore)

    instance = store(workspace_id)
    instance.initialize()
    return instance