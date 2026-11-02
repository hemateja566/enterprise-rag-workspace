-- MySQL schema initialization for Enterprise RAG Workspace
-- Run automatically on first startup via docker-entrypoint-initdb.d

CREATE DATABASE IF NOT EXISTS enterprise_rag DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE enterprise_rag;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Workspaces table (multi-tenant isolation)
CREATE TABLE IF NOT EXISTS workspaces (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE NOT NULL,
    owner_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    workspace_id BIGINT NOT NULL,
    original_filename VARCHAR(500) NOT NULL,
    stored_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'uploaded' NOT NULL,
    pages INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Document chunks (semantic text segments for vector retrieval)
CREATE TABLE IF NOT EXISTS document_chunks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    document_id BIGINT NOT NULL,
    chunk_index INT NOT NULL,
    text TEXT NOT NULL,
    page_number INT NOT NULL,
    char_start INT,
    char_end INT,
    embedding_id VARCHAR(255),
    embedding_model VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Document tables (SQL-queryable extracts from PDFs)
CREATE TABLE IF NOT EXISTS document_tables (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    document_id BIGINT NOT NULL,
    table_name VARCHAR(200) NOT NULL,
    sql_create_statement TEXT NOT NULL,
    source_page INT NOT NULL,
    row_count INT,
    column_info JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Audit log (compliance tracking)
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    workspace_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id BIGINT,
    details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_doc_chunk_doc_page ON document_chunks(document_id, page_number);
CREATE INDEX IF NOT EXISTS idx_doc_chunk_embedding ON document_chunks(embedding_model);
CREATE INDEX IF NOT EXISTS idx_doc_table_doc ON document_tables(document_id);
CREATE INDEX IF NOT EXISTS idx_audit_workspace ON audit_logs(workspace_id);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_workspace_owner ON workspaces(owner_id);

-- Create default admin user (password: ChangeMe123! - change in production!)
INSERT IGNORE INTO users (email, password_hash, full_name, is_active, is_admin)
VALUES ('admin@enterprise-rag.local', '$2b$12$LQv3eIl5YlK.7Y8D.OuD/.gZMEGc/.f5q.GApx8xMQjqCU1e.xyKPS', 'Enterprise RAG Admin', TRUE, TRUE);

GRANT ALL PRIVILEGES ON enterprise_rag.* TO 'rag_user'@'%';
FLUSH PRIVILEGES;