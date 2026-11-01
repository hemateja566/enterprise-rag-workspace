#!/usr/bin/env python3
"""Celery Tasks for Enterprise RAG Workspace.

Background PDF ingestion pipeline that extracts text, images, and tables
from uploaded documents without blocking Flask workers.

Key Pipeline Stages:
1. PDF text and image extraction (using pdf2image + OCR if needed)
2. Chunking text into semantic segments
3. Generating dense vector embeddings
4. Storing chunks/tables in MySQL + vectors in vector store
5. Updating document status from "processing" to "ready"
"""

import os
import uuid
import time
import logging
from typing import Dict, Any, List, Optional

from celery import Celery
from PIL import Image

# Import project modules
from api.models import Document, DocumentChunk, DocumentTable, db
from api.services.embedding import get_embedding, batch_get_embeddings
from api.services.vector_store import get_vector_store, VECTOR_BACKEND

# Configure logging
logger = logging.getLogger(__name__)


# Celery app configuration
# In production, use Redis as broker and result backend
celery_app = Celery(
    "enterprise_rag",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)


# Update Celery configuration from env
celery_app.conf.update(
    task_time_limit=int(os.getenv("CELERY_TASK_TIMEOUT", "300")),  # 5 min max
    task_soft_time_limit=int(os.getenv("CELERY_SOFT_TIMEOUT", "240")),  # 4 min soft
    result_expires=int(os.getenv("CELERY_RESULT_EXPIRES", "86400")),  # 24h
    task_always_eager=False,  # Set True for testing without Redis
    task_ignore_result=False,
)


def make_celery_app():
    """Return Celery app attached to Flask app context.

    In a real Flask-Celery setup, this would use the
    `ctx squeez` pattern to push app context into tasks.
    """
    return celery_app


@celery_app.task(bind=True, soft_time_limit=240, time_limit=300)
def ingest_document(self, document_id: int) -> Dict[str, Any]:
    """Background task: Full document ingestion pipeline.

    Processes an uploaded PDF/document:
    - Extracts text per page
    - Generates semantic chunks
    - Creates vector embeddings
    - Stores chunks in MySQL and vector index
    - Stores tabular extracts (if applicable)
    - Updates Document status to "ready"

    Args:
        document_id: ID of the Document model record to process.

    Returns:
        Dict with processing results (chunks created, embedding count, etc.).
    """
    try:
        # Fetch document record with row lock for safety
        from api.app import db
        document = Document.query.filter_by(id=document_id).with_for_update().first()

        if not document:
            logger.error(f"Document {document_id} not found")
            return {"error": "Document not found"}

        # Update status to processing
        document.status = "processing"
        db.session.commit()
        self.update(state="PROGRESS", meta={"status": "Starting PDF extraction..."})

        logger.info(f"Starting ingestion for document {document.id} ({document.original_filename})")

        # Stage 1: Extract text and tables from PDF
        # In production, this would use pdfplumber, PyMuPDF, or pdf2image + OCR
        extraction_result = _extract_pdf_content(document.stored_path)

        self.update(state="PROGRESS", meta={"status": "Generating embeddings..."})

        # Stage 2: Create chunks from extracted text
        chunks_data = _create_chunks(document, extraction_result)

        if not chunks_data:
            document.status = "error"
            db.session.commit()
            return {"error": "No extractable content found in document"}

        # Stage 3: Generate embeddings for all chunks
        chunk_texts = [cd["text"] for cd in chunks_data]
        chunk_ids = [f"chunk_{document.id}_{i}" for i in range(len(chunks_data))]

        # Get embeddings in batch
        embeddings = batch_get_embeddings(chunk_texts)

        # Stage 4: Store chunks in MySQL
        for i, cd in enumerate(chunks_data):
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=i,
                text=cd["text"],
                page_number=cd.get("page_number", 1),
                char_start=cd.get("char_start"),
                char_end=cd.get("char_end"),
                embedding_id=chunk_ids[i],
                embedding_model=os.getenv("DEFAULT_EMBEDDING_MODEL", "text-embedding-3-large"),
            )
            db.session.add(chunk)

        # Stage 5: Store vectors in vector index (backend-dependent)
        vector_store = get_vector_store(document.workspace_id)

        # Prepare data for vector store
        vectors_data = []
        for i, (cd, emb) in enumerate(zip(chunks_data, embeddings)):
            vectors_data.append({
                "id": chunk_ids[i],
                "embedding": emb,
                "document_id": document.id,
                "text": cd["text"],
                "page_number": cd.get("page_number", 1),
            })

        # Add to vector store (backend-agnostic call)
        try:
            vector_store.add_chunks(
                chunks=[{"text": cd["text"], "document_id": document.id, "page_number": cd.get("page_number", 1)} for cd in chunks_data],
                embeddings=embeddings,
                chunk_ids=chunk_ids,
            )
        except Exception as ve:
            logger.warning(f"Vector store add failed (continuing with MySQL only): {ve}")

        # Stage 6: Extract and store tabular data (if any)
        _store_tables(document, extraction_result)

        # Stage 7: Mark document as ready
        document.status = "ready"
        db.session.commit()

        logger.info(f"Ingestion complete for document {document.id}: "
                     f"{len(chunks_data)} chunks embedded")

        return {
            "document_id": document.id,
            "chunks_created": len(chunks_data),
            "embeddings_generated": len(embeddings),
            "status": "ready",
            "pages_processed": extraction_result.get("total_pages", 0),
        }

    except Exception as exc:
        logger.error(f"Ingestion task failed for document {document_id}: {exc}", exc_info=True)

        # Try to update document status to error
        try:
            from api.models import Document
            document = Document.query.get(document_id)
            if document:
                document.status = "error"
                db.session.commit()
        except Exception:
            db.session.rollback()

        # Re-raise or return error (Celery will mark task as failed)
        raise self.retry(exc=exc, countdown=60, max_retries=3)


def _extract_pdf_content(pdf_path: str) -> Dict[str, Any]:
    """Extract text and table information from a PDF file.

    In production, this would use:
    - pdfplumber for text + table extraction with coordinates
    - PyMuPDF (fitz) for fast text extraction
    - pdf2image + pytesseract for OCR on scanned PDFs
    - camelot or tabula for table structure detection

    Returns dict with per-page text and detected tables.
    """
    import pdfplumber  # Example PDF text extraction library

    result = {
        "total_pages": 0,
        "pages": {},  # page_num -> {"text": str, "tables": [table_data]}
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            result["total_pages"] = len(pdf.pages)

            for page_num, page in enumerate(pdf.pages, start=1):
                # Extract text
                text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""

                # Extract tables
                tables = page.extract_tables() or []
                tables_data = []
                for table in tables:
                    # Each table is a list of rows, each row is a list of cell texts
                    tables_data.append({
                        "rows": len(table),
                        "cols": len(table[0]) if table else 0,
                        "data": table,  # 2D array of cell text
                    })

                result["pages"][page_num] = {
                    "text": text,
                    "tables": tables_data,
                }

    except Exception as e:
        logger.warning(f"PDF extraction had issues: {e}")
        # Fallback: try a simpler extraction
        result = _fallback_pdf_extraction(pdf_path)

    return result


def _fallback_pdf_extraction(pdf_path: str) -> Dict[str, Any]:
    """Fallback PDF extraction using PyMuPDF."""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(pdf_path)
        result = {"total_pages": len(doc.pages), "pages": {}}

        for page_num in range(len(doc.pages)):
            page = doc[page_num]
            text = page.get_text("text") or ""
            result["pages"][page_num + 1] = {"text": text, "tables": []}

        doc.close()
        return result
    except Exception as e:
        logger.error(f"Fallback PDF extraction also failed: {e}")
        return {"total_pages": 0, "pages": {}}


def _create_chunks(document: Document, extraction_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Create semantic text chunks from extracted PDF content.

    Chunking strategy:
    - Split by pages (primary unit)
    - Within each page, split by sentence boundaries or fixed-size windows
    - Preserve page_number for source grounding

    Args:
        document: Document model record
        extraction_result: Result from _extract_pdf_content

    Returns:
        List of chunk dicts with keys: text, page_number, char_start, char_end
    """
    chunks = []
    page_chunks_map = extraction_result.get("pages", {})

    for page_num in range(1, document.pages + 1):
        page_data = page_chunks_map.get(page_num, {"text": ""})
        page_text = page_data.get("text", "")

        if not page_text.strip():
            # Still create an empty chunk so page is represented
            chunks.append({
                "text": "",
                "page_number": page_num,
                "char_start": 0,
                "char_end": 0,
            })
            continue

        # Simple chunking: split into sentences and group into windows
        # In production, use a proper chunker (sentence-transformers, etc.)
        sentences = _split_into_sentences(page_text)
        chunk_size = int(os.getenv("CHUNK_SIZE", "500"))  # characters per chunk
        chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "50"))  # char overlap

        i = 0
        while i < len(sentences):
            # Build a chunk from consecutive sentences
            chunk_text_parts = []
            char_start = None
            char_end = None

            # Accumulate sentences until we hit chunk_size
            accumulated = 0
            j = i
            while j < len(sentences) and accumulated < chunk_size:
                sent = sentences[j]
                sent_start = page_text.find(sent, char_end if char_end else 0)
                if sent_start == -1:
                    # Fallback: just append
                    chunk_text_parts.append(sent)
                    accumulated += len(sent)
                else:
                    if accumulated == 0:
                        char_start = sent_start
                    else:
                        # Add overlap/continuation space
                        chunk_text_parts[-1] += " " + sent if chunk_text_parts else sent
                    accumulated += len(sent) + 1  # +1 for space
                j += 1

            # Determine char_end
            if char_start is not None and j > i:
                # Find the actual end position in the original text
                end_pos = char_start + accumulated
                chunk_text = " ".join(chunk_text_parts) if chunk_text_parts else ""
                chunk_end = min(end_pos, len(page_text))
                chunks.append({
                    "text": chunk_text[:chunk_end],
                    "page_number": page_num,
                    "char_start": char_start,
                    "char_end": chunk_end,
                })
            else:
                # Fallback: add remaining text as one chunk
                chunks.append({
                    "text": page_text[char_start:] if char_start else page_text,
                    "page_number": page_num,
                    "char_start": char_start if char_start else 0,
                    "char_end": len(page_text),
                })

            i = j

    return chunks


def _split_into_sentences(text: str) -> List[str]:
    """Simple sentence tokenizer (regex-based)."""
    import re

    # Split on sentence-ending punctuation followed by space/newline
    # This is a heuristic; nltk.sent_tokenize would be better
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    # Filter out empty strings
    return [s.strip() for s in sentences if s.strip()]


def _store_tables(document: Document, extraction_result: Dict[str, Any]) -> None:
    """Extract and store tabular data from PDF into MySQL.

    For financial reports, specs, etc. where table structures
    need to be queryable via SQL in addition to vector search.

    Args:
        document: Document model record
        extraction_result: Result from _extract_pdf_content
    """
    import json

    page_chunks_map = extraction_result.get("pages", {})

    for page_num in range(1, document.pages + 1):
        page_data = page_chunks_map.get(page_num, {})
        tables_data = page_data.get("tables", [])

        for table_info in tables_data:
            table_data = table_info.get("data", [])

            if not table_data:
                continue

            # Generate a table name
            table_name = f"tbl_{document.id}_p{page_num}_{uuid.uuid4().hex[:8]}"

            # Convert 2D array to SQL-friendly format
            # Create a CREATE TABLE statement (simplified)
            num_cols = len(table_data[0]) if table_data else 0
            col_defs = ", ".join([f"col_{i} TEXT" for i in range(min(num_cols, 20))])

            # Serialize the table data as JSON for later retrieval
            table_json = json.dumps(table_data)

            # Create INSERT statement representative sample
            # In production, would use proper SQL generation
            create_stmt = f"CREATE TABLE IF NOT EXISTS {table_name} ({col_defs});"
            # Sample insert (first row)
            first_row = table_data[0] if table_data else []
            placeholders = ", ".join([f"'{str(c).replace(chr(39), chr(96))}'" for c in first_row[:20]])
            insert_stmt = f"INSERT INTO {table_name} VALUES ({placeholders});"

            # Store in MySQL
            from api.app import db

            table_record = DocumentTable(
                document_id=document.id,
                table_name=table_name,
                sql_create_statement=create_stmt,
                source_page=page_num,
                row_count=len(table_data),
                column_info=json.dumps({
                    "num_columns": num_cols,
                    "column_names": [f"col_{i}" for i in range(min(num_cols, 20))]
                }),
            )

            db.session.add(table_record)

    try:
        db.session.commit()
    except Exception as e:
        logger.error(f"Table storage failed: {e}")
        db.session.rollback()