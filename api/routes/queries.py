#!/usr/bin/env python3
"""Queries Routes for Enterprise RAG Workspace.

Handles grounded Q&A query submission with Server-Sent Events (SSE)
streaming of token responses. Includes contextual query rewriting,
vector retrieval, re-ranking, and source citation grounding.
"""

from flask import Blueprint, request, jsonify, current_app, Response
from api.app import db
from api.models import Workspace, Document, DocumentChunk, AuditLog
from services.embedding import get_embedding
from services.rag import retrieve_and_rerank
import json
import time


queries_bp = Blueprint("queries", __name__, url_prefix="/api/queries")


def log_query_activity(workspace_id, user_id, action, resource_type, resource_id=None, details=None):
    """Helper to write an audit log entry."""
    from api.models import AuditLog
    log = AuditLog(
        workspace_id=workspace_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
    )
    db.session.add(log)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()


@queries_bp.route("/submit", methods=["POST"])
def submit_query():
    """Submit a grounded Q&A query.

    Expected JSON payload:
    {
        "workspace_id": 1,
        "document_ids": [1, 2, 3],  # optional; omit to search all docs in workspace
        "question": "What is the revenue growth Q3 2024?",
        "user_id": 123
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON payload required"}), 400

    workspace_id = data.get("workspace_id")
    document_ids = data.get("document_ids", [])
    question = data.get("question", "").strip()
    user_id = data.get("user_id")

    if not workspace_id:
        return jsonify({"error": "workspace_id required"}), 400
    if not question:
        return jsonify({"error": "Question required"}), 400

    # Validate workspace
    workspace = Workspace.query.get(workspace_id)
    if not workspace:
        return jsonify({"error": "Workspace not found"}), 404

    # Log query submission
    log_query_activity(
        workspace_id=workspace_id,
        user_id=user_id,
        action="query_submit",
        resource_type="query",
        resource_id=None,
        details={"question": question, "doc_count": len(document_ids)},
    )

    # Step 1: Contextual Query Rewriting (resolve ambiguous follow-ups)
    rewritten_question = contextualize_question(question, document_ids, workspace_id)

    # Step 2: Generate query embedding
    try:
        query_embedding = get_embedding(rewritten_question)
    except Exception as e:
        return jsonify({"error": f"Embedding generation failed: {str(e)}"}), 500

    # Step 3: Vector retrieval + re-ranking
    try:
        retrieved_chunks = retrieve_and_rerank(
            query_embedding=query_embedding,
            workspace_id=workspace_id,
            query=rewritten_question,
            document_ids=document_ids,
        )
    except Exception as e:
        return jsonify({"error": f"Retrieval failed: {str(e)}"}), 500

    # Step 4: Stream the grounded response via SSE
    # We pass the retrieved chunks and the original question
    return Response(
        stream_query_response(
            question=question,
            rewritten_question=rewritten_question,
            chunks=retrieved_chunks,
            workspace_id=workspace_id,
            user_id=user_id,
        ),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


def contextualize_question(question, document_ids, workspace_id):
    """Contextual query rewriting: resolve ambiguous follow-up questions.

    In a production system, this would use an LLM to detect if the question
    refers to context from previous turns and rewrite it as a self-contained
    query. For this prototype, we apply simple heuristics.
    """
    q = question.strip()

    # Heuristic: if question starts with "it", "this", "that", "the topic",
    # there's a risk of ambiguity. Prepend context from document titles.
    ambiguous_starters = ["it", "this", "that", "the", "these", "those"]
    lower_q = q.lower()

    if any(lower_q.startswith(s + " ") for s in ambiguous_starters):
        # Simple contextual prefix - in production, use LLM prompt
        if document_ids:
            # Prefix with document reference
            return f"Based on the documents, {q}"
        # If no docs, keep as-is but flag for user

    return q


def retrieve_and_rerank(query_embedding, workspace_id, query, document_ids):
    """Perform vector retrieval with re-ranking pipeline.

    This service integrates with the vector index (ChromaDB/Milvus/Qdrant
    or local FAISS) to find relevant chunks, then re-ranks them using
    a cross-encoder or similar mechanism.
    """
    from services.vector_store import search_similar_chunks

    # Search for top-k similar chunks
    k = current_app.config.get("RETRIEVAL_K", 10)
    chunks = search_similar_chunks(
        query_embedding=query_embedding,
        workspace_id=workspace_id,
        document_ids=document_ids,
        k=k * 2,  # Get extra for re-ranking
    )

    # TODO: Implement re-ranking with cross-encoder
    # For now, return top-k as-is
    return chunks[:k]


def stream_query_response(question, rewritten_question, chunks, workspace_id, user_id):
    """Generator that yields SSE events for the token-streamed response.

    Yields:
        str: SSE-formatted data lines (e.g., "data: {"token": "Hello"}")
    """
    # Build context from retrieved chunks, ordered by relevance
    context_parts = []
    source_references = []
    for i, chunk in enumerate(chunks):
        # Format source reference for citation pills
        source_ref = {
            "chunk_id": chunk.id,
            "page_number": chunk.page_number,
            "text_snippet": chunk.text[:150] + "..." if len(chunk.text) > 150 else chunk.text,
            "score": getattr(chunk, "score", None),
        }
        source_references.append(source_ref)
        context_parts.append(f"[Page {chunk.page_number}] {chunk.text}")

    context = "\n\n".join(context_parts)

    # Construct the prompt for the LLM grounded response
    # In production, this would be sent to an LLM API (OpenAI, Anthropic, etc.)
    prompt = f"""Answer the user's question based solely on the context below. 
Provide a concise answer and include source citations using the format [Page X].

Context:
{context}

User Question: {question}

Answer:"""

    # Simulate token streaming with grounding
    # In production, this would be a real LLM streaming response
    full_response = generate_grounded_response(prompt, source_references)

    # Yield tokens one by one with simulated delays
    # Grounded response includes source attribution at the end
    words = full_response.split()
    current_text = ""

    for i, word in enumerate(words):
        current_text += word + " "
        # Yield SSE event with partial text and current source references
        event_data = {
            "type": "token",
            "text": word + " ",
            "context": current_text.strip(),
            "source_refs": source_references,  # Full citations for client
            "finished": False,
        }
        yield f"data: {json.dumps(event_data)}\n\n"
        # Simulate token latency - in production, this would be driven by LLM streaming
        # time.sleep(0.05)  # Uncomment for realistic timing

    # Final event marking completion with consolidated sources
    final_event = {
        "type": "done",
        "text": full_response,
        "source_refs": source_references,
        "finished": True,
    }
    yield f"data: {json.dumps(final_event)}\n\n"

    # Log the query completion
    try:
        log_query_activity(
            workspace_id=workspace_id,
            user_id=user_id,
            action="query_complete",
            resource_type="query",
            resource_id=None,
            details={
                "question": question,
                "response_length": len(full_response),
                "chunks_retrieved": len(chunks),
                "sources": [{"page": r.get("page_number")} for r in source_references],
            },
        )
    except Exception:
        db.session.rollback()


def generate_grounded_response(prompt, source_references):
    """Generate a grounded response using the context and source references.

    In production, this would call an LLM API with the prompt and receive
    a streaming response. For this prototype, we synthesize an answer
    from the provided context.

    The key feature: source attribution is embedded in the response so
    users can verify answers by clicking citations.
    """
    # Simple extraction-based prototype: pull key sentences from context
    # that seem relevant to typical financial/technical questions
    import re

    # Check if context has financial indicators
    context_text = " ".join([c.get("text", "") for c in source_references])

    # Look for revenue, growth, profit, etc.
    patterns = {
        "revenue": r"[Rr]evenue[^.]*",
        "growth": r"[Gg]rowth[^.]*",
        "profit": r"[Pp]rofit[^.]*",
    }

    # For demonstration, return a structured response
    # that embeds source page numbers directly
    pages_used = sorted(set([r.get("page_number") for r in source_references if r.get("page_number")]))

    if pages_used:
        source_str = ", ".join([f"Page {p}" for p in pages_used])
        response = f"The relevant information is found in {source_str}."
    else:
        response = "Answer based on available document context."

    # Append the full LLM-style prompt response
    response += f" \n\nPrompt: {prompt[:100]}..."

    return response