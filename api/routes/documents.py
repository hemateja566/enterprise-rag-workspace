#!/usr/bin/env python3
"""Documents Routes for Enterprise RAG Workspace.

Handles PDF/document upload, metadata management, and deletion.
Supports multi-tenant isolation via workspace_id.
"""

from flask import Blueprint, request, jsonify, current_app, send_file
from api.app import db
from api.models import Workspace, Document
import os
import uuid
import magic  # for MIME type verification


documents_bp = Blueprint("documents", __name__, url_prefix="/api/documents")


# Allowed MIME types for document upload
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def validate_file(file_storage):
    """Validate uploaded file MIME type and size.

    Returns (is_valid, error_message) tuple.
    """
    if not file_storage:
        return False, "No file uploaded"

    # Check MIME type
    mime = magic.from_file(file_storage.filename, mime=True) if hasattr(file_storage, 'filename') else magic.from_buffer(file_storage.read(2048), mime=True)
    file_storage.seek(0)  # Reset stream position after read

    if mime not in ALLOWED_MIME_TYPES:
        return False, f"File type '{mime}' not allowed. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"

    # Check file size (limit to 50MB by default)
    file_storage.seek(0)
    size = len(file_storage.read())
    file_storage.seek(0)

    max_size = current_app.config.get("MAX_DOCUMENT_SIZE", 50 * 1024 * 1024)  # 50MB
    if size > max_size:
        return False, f"File size ({size / 1024 / 1024:.1f}MB) exceeds limit ({max_size / 1024 / 1024:.1f}MB)"

    return True, None


@documents_bp.route("/upload", methods=["POST"])
def upload():
    """Upload a PDF or document file to a workspace.

    Expected multipart/form-data:
    - workspace_id: ID of the target workspace
    - file: The PDF/document file
    """
    workspace_id = request.form.get("workspace_id")
    file = request.files.get("file")

    if not workspace_id:
        return jsonify({"error": "workspace_id required"}), 400

    if not file or file.filename == "":
        return jsonify({"error": "No file provided"}), 400

    # Validate workspace exists
    workspace = Workspace.query.get(workspace_id)
    if not workspace:
        return jsonify({"error": "Workspace not found"}), 404

    # Validate file
    is_valid, error_msg = validate_file(file)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    # Generate a unique storage filename
    file_ext = os.path.splitext(file.filename)[1].lower()
    if not file_ext:
        file_ext = ".pdf"  # Default extension
    stored_filename = f"{uuid.uuid4()}{file_ext}"
    stored_path = os.path.join(
        current_app.config.get("UPLOAD_FOLDER", "uploads"),
        str(workspace_id),
        stored_filename,
    )

    # Ensure upload directory exists
    os.makedirs(os.path.dirname(stored_path), exist_ok=True)

    # Save the file
    file.save(stored_path)

    # Determine page count (placeholder - would use PDF parser in production)
    # In a real implementation, this would be done via Celery background task
    pages = 1  # placeholder

    # Create document metadata record
    document = Document(
        workspace_id=workspace_id,
        original_filename=file.filename,
        stored_path=stored_path,
        file_size=os.path.getsize(stored_path),
        mime_type=file.mimetype,
        pages=pages,
        status="uploaded",  # Will change to "processing" after Celery task
    )

    db.session.add(document)
    db.session.commit()

    # TODO: Trigger Celery task for background embedding extraction
    # from tasks import ingest_document.delay(document.id)

    return jsonify(
        {
            "message": "Document uploaded successfully",
            "document": document.to_dict(),
        }
    ), 201


@documents_bp.route("/<int:document_id>", methods=["GET"])
def get_document(document_id):
    """Get document metadata by ID."""
    document = Document.query.get(document_id)
    if not document:
        return jsonify({"error": "Document not found"}), 404
    return jsonify({"document": document.to_dict()}), 200


@documents_bp.route("/<int:document_id>", methods=["DELETE"])
def delete_document(document_id):
    """Delete a document and its associated metadata.

    Note: In a production system, you would also remove the embedding
    index entries and cleanup storage files.
    """
    document = Document.query.get(document_id)
    if not document:
        return jsonify({"error": "Document not found"}), 404

    # Delete physical file if it exists
    if document.stored_path and os.path.exists(document.stored_path):
        os.remove(document.stored_path)

    # Delete from database (cascade should handle chunks/tables)
    db.session.delete(document)
    db.session.commit()

    return jsonify({"message": "Document deleted successfully"}), 200


@documents_bp.route("/", methods=["GET"])
def list_documents():
    """List documents for a workspace (requires workspace_id query param)."""
    workspace_id = request.args.get("workspace_id", type=int)
    if not workspace_id:
        return jsonify({"error": "workspace_id query parameter required"}), 400

    documents = Document.query.filter_by(workspace_id=workspace_id).all()
    return jsonify(
        {"documents": [doc.to_dict() for doc in documents]}
    ), 200