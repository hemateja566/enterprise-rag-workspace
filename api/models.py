#!/usr/bin/env python3
"""Database Models for Enterprise RAG Workspace.

SQLAlchemy models representing MySQL tables for:
- User accounts and authentication
- Workspace/tenant schemas
- Document metadata and storage paths
- Audit logs for compliance
- Query/embedding metadata
"""

from api.app import db


class User(db.Model):
    """User account model with JWT authentication support."""

    __tablename__ = "users"

    id = db.Column(db.BigInteger, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime, server_default=db.func.now(), onupdate=db.func.now()
    )

    # Relationships
    workspaces = db.relationship(
        "Workspace", back_populates="owner", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Workspace(db.Model):
    """Workspace/tenant model for multi-tenancy isolation.

    Each workspace represents a separate user or organization's
    document collection, settings, and audit trail.
    """

    __tablename__ = "workspaces"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    owner_id = db.Column(
        db.BigInteger, db.ForeignKey("users.id"), nullable=False
    )
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    # Relationships
    owner = db.relationship("User", back_populates="workspaces")
    documents = db.relationship(
        "Document", back_populates="workspace", cascade="all, delete-orphan"
    )
    audit_logs = db.relationship(
        "AuditLog", back_populates="workspace", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_public": self.is_public,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Document(db.Model):
    """Document metadata model stored per-workspace.

    Tracks PDF upload status, parsing state, and MySQL-stored
    tabular extracts. Links to the Celery ingestion pipeline state.
    """

    __tablename__ = "documents"

    id = db.Column(db.BigInteger, primary_key=True)
    workspace_id = db.Column(
        db.BigInteger, db.ForeignKey("workspaces.id"), nullable=False
    )
    original_filename = db.Column(db.String(500), nullable=False)
    stored_path = db.Column(db.String(500), nullable=False)  # Path to PDF in storage
    file_size = db.Column(db.BigInteger)  # Size in bytes
    mime_type = db.Column(db.String(100))
    status = db.Column(
        db.String(50),
        default="uploaded",
        nullable=False,  # uploaded | processing | ready | error
    )
    pages = db.Column(db.Integer, default=1)  # Number of PDF pages
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    # Relationships
    workspace = db.relationship("Workspace", back_populates="documents")
    chunks = db.relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )
    tables = db.relationship(
        "DocumentTable", back_populates="document", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "original_filename": self.original_filename,
            "stored_path": self.stored_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "status": self.status,
            "pages": self.pages,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DocumentChunk(db.Model):
    """Chunks of document text for vector embedding retrieval.

    Each chunk represents a semantic segment of a PDF page,
    stored with its embedding vector index (ChromaDB/Milvus/Qdrant/FAISS).
    """

    __tablename__ = "document_chunks"

    id = db.Column(db.BigInteger, primary_key=True)
    document_id = db.Column(
        db.BigInteger, db.ForeignKey("documents.id"), nullable=False
    )
    chunk_index = db.Column(db.Integer, nullable=False)  # Order within document
    text = db.Column(db.Text, nullable=False)  # Extracted text content
    page_number = db.Column(db.Integer, nullable=False)  # Source PDF page
    char_start = db.Column(db.Integer)  # Character offset in page
    char_end = db.Column(db.Integer)  # Character offset in page

    # Embedding metadata (links to external vector store)
    embedding_id = db.Column(db.String(255))  # ChromaDB/Milvus ID or FAISS key
    embedding_model = db.Column(db.String(100))  # e.g., "text-embedding-3-large"
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    # Composite index for fast per-document retrieval
    __table_args__ = (
        db.Index("idx_doc_chunk_doc_page", "document_id", "page_number"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "page_number": self.page_number,
            "text": self.text[:200] + "..." if len(self.text) > 200 else self.text,
            "embedding_model": self.embedding_model,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DocumentTable(db.Model):
    """Tabular extracts from documents stored directly in MySQL.

    For financial reports, specs, etc. where table structures
    need to be queryable via SQL in addition to vector search.
    """

    __tablename__ = "document_tables"

    id = db.Column(db.BigInteger, primary_key=True)
    document_id = db.Column(
        db.BigInteger, db.ForeignKey("documents.id"), nullable=False
    )
    table_name = db.Column(db.String(200), nullable=False)  # User-defined or auto-generated
    sql_create_statement = db.Column(db.Text, nullable=False)  # CREATE TABLE or INSERT statements
    source_page = db.Column(db.Integer, nullable=False)  # Which PDF page the table came from
    row_count = db.Column(db.Integer)
    column_info = db.Column(db.JSON)  # Metadata about columns/types
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    # Relationship
    document = db.relationship("Document", back_populates="tables")

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "table_name": self.table_name,
            "source_page": self.source_page,
            "row_count": self.row_count,
            "column_info": self.column_info,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditLog(db.Model):
    """Audit log for compliance and usage tracking.

    Records document access, query activity, and administrative
    actions for security and analytics purposes.
    """

    __tablename__ = "audit_logs"

    id = db.Column(db.BigInteger, primary_key=True)
    workspace_id = db.Column(
        db.BigInteger, db.ForeignKey("workspaces.id"), nullable=False
    )
    user_id = db.Column(
        db.BigInteger, db.ForeignKey("users.id"), nullable=False
    )
    action = db.Column(db.String(100), nullable=False)  # e.g., "document_upload", "query_submit"
    resource_type = db.Column(db.String(50))  # "document", "query", "workspace"
    resource_id = db.Column(db.BigInteger)  # ID of the affected resource
    details = db.Column(db.JSON)  # Free-form key-value audit details
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    # Relationships
    workspace = db.relationship("Workspace", back_populates="audit_logs")
    user = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }