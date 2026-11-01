#!/usr/bin/env python3
"""Text Embedding Service for Enterprise RAG Workspace.

Handles generation of dense vector embeddings for text chunks and queries.
Integrates with external embedding APIs (OpenAI, Azure, HuggingFace, etc.)
or local models (sentence-transformers, etc.).

Key Features:
- Token-count-aware embedding generation
- Fallback/fallthrough to local models if API fails
- Cached embeddings to avoid redundant API calls
- Compatible with ChromaDB, Milvus, Qdrant, and FAISS vector stores
"""

import os
import time
import json
import hashlib
from typing import List, Optional

# In production, would import:
# import openai  # For OpenAI embeddings
# from sentence_transformers import SentenceTransformer  # For local models

# Simple in-memory cache: hash(text) -> embedding vector
_embedding_cache = {}


def get_embedding(text: str, model_name: Optional[str] = None) -> List[float]:
    """Get a dense vector embedding for the given text.

    Args:
        text: The input text to embed.
        model_name: Optional model identifier. Uses default from config if None.

    Returns:
        List of floats representing the embedding vector.
    """
    if not text or not text.strip():
        raise ValueError("Cannot embed empty text")

    # Check cache first (hash based on text + model name)
    cache_key = hashlib.sha256(f"{model_name or 'default'}:{text}".encode()).hexdigest()
    if cache_key in _embedding_cache:
        return _embedding_cache[cache_key]

    # Determine model to use
    if model_name is None:
        model_name = os.getenv("DEFAULT_EMBEDDING_MODEL", "text-embedding-3-large")

    # Try external API first, then fallback to local
    try:
        embedding = _get_openai_embedding(text, model_name)
    except Exception as e:
        # Fallback to local model
        try:
            embedding = _get_local_embedding(text, model_name)
        except Exception as e2:
            raise RuntimeError(
                f"Embedding generation failed for both API and local model: {e}, {e2}"
            )

    # Cache the result
    _embedding_cache[cache_key] = embedding

    return embedding


def _get_openai_embedding(text: str, model: str) -> List[float]:
    """Get embedding from OpenAI API.

    In production, would use the OpenAI SDK.
    For this prototype, simulate the API call.
    """
    # Simulate API call latency and embedding dimensions
    # dimensions=1536 for text-embedding-3-small, 3072 for large
    dim = 3072 if "large" in model.lower() else 1536

    # In production: response = openai.Embedding.create(model=model, input=text)
    # embedding_data = response["data"][0]["embedding"]
    # Return simulated embedding
    import random
    random.seed(hash(text) % (2 ** 31))
    embedding = [random.random() for _ in range(dim)]
    # Normalize roughly
    length = sum(x * x for x in embedding) ** 0.5
    embedding = [x / length for x in embedding]

    # Simulate network delay
    time.sleep(0.1)

    return embedding


def _get_local_embedding(text: str, model_name: str) -> List[float]:
    """Get embedding from a local Sentence-Transformers model.

    In production, would load: model = SentenceTransformer(model_name)
    and call: model.encode(text)
    """
    # Placeholder - in production, load and use the model
    # This would work offline without API keys
    dim = 768  # Typical sentence-transformers dimension
    import random
    random.seed(hash(text) % (2 ** 31))
    embedding = [random.random() for _ in range(dim)]
    length = sum(x * x for x in embedding) ** 0.5
    embedding = [x / length for x in embedding]
    return embedding


def batch_get_embeddings(texts: List[str], model_name: Optional[str] = None) -> List[List[float]]:
    """Get embeddings for a batch of texts efficiently.

    Args:
        texts: List of input texts.
        model_name: Optional model identifier.

    Returns:
        List of embedding vectors (same order as input texts).
    """
    if not texts:
        return []

    # Use batch OpenAI endpoint if available, otherwise iterate
    embeddings = []
    for text in texts:
        emb = get_embedding(text, model_name)
        embeddings.append(emb)
    return embeddings