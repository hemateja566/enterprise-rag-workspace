# Enterprise Multi-Document RAG & Semantic Analytics Workspace
## Section-Wise Architecture Summary

---
## 1. PROJECT STRUCTURE
```
enterprise-rag-workspace/
├── api/                    # Flask REST API backend
│   ├── app.py              # App factory, routes registration
│   ├── models.py           # SQLAlchemy MySQL models
│   ├── routes/             # Route blueprints
│   │   ├── auth.py         # JWT login/registration
│   │   ├── documents.py    # PDF upload/metadata/delete
│   │   └── queries.py      # SSE streaming queries
│   ├── services/           # Business logic services
│   │   ├── embedding.py    # Text embedding generation
│   │   └── vector_store.py # Vector search (ChromaDB/FISS/Milvus)
│   └── ... (other files)
├── celery/                 # Background task queue
│   ├── tasks.py            # PDF ingestion pipeline
│   ├── config.py           # Celery config with Flask integration
│   └── __init__.py         # Celery app factory
├── frontend/               # React client application
│   ├── src/
│   │   ├── components/     # PDFViewer, ChatSSE, DocumentUpload, QueryInput
│   │   ├── pages/          # Dashboard (main workspace UI)
│   │   ├── services/       # api.js - Flask API client
│   │   └── App.js (entry point)
│   └── package.json
├── requirements.txt        # Python dependencies
└── SUMMARY.md              # This file: section-wise overview
```
---
## 2. SECTION 1: BACKEND API (Flask)

### Purpose
REST API endpoints, streaming generators for SSE chat, and JWT authentication.

### Key Files
- `api/app.py` - Application factory pattern; registers blueprints for auth, documents, queries
- `api/models.py` - SQLAlchemy models for MySQL: User, Workspace, Document, DocumentChunk, DocumentTable, AuditLog
- `api/routes/auth.py` - Login, register, me, refresh endpoints
- `api/routes/documents.py` - Upload (multipart/form-data), get, delete, list documents per workspace
- `api/routes/queries.py` - Query submission with SSE streaming Response(stream_with_context(...))

### Key Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | JWT authentication, returns access/refresh tokens |
| POST | `/api/auth/register` | User registration |
| GET | `/api/auth/me` | Current user info (requires JWT) |
| POST | `/api/documents/upload` | Upload PDF to workspace (multipart/form-data) |
| GET | `/api/documents/{id}` | Get document metadata |
| DELETE | `/api/documents/{id}` | Delete document + storage file |
| GET | `/api/documents` | List documents for workspace (`?workspace_id=X`) |
| POST | `/api/queries/submit` | Submit Q&A query; returns SSE stream |
| GET | `/api/queries/sse/queries/{id}` | SSE endpoint for token streaming |

### Architecture Highlights
- **Application Factory** (`create_app()`) for testability and configuration
- **JWT Authentication** stateless token-based access control
- **Streaming Generators**: `Response(stream_with_context(...))` for token-by-token SSE
- **Multi-tenancy**: Every resource scoped to `workspace_id`; isolated DB rows + vector indices
- **Audit Logging**: All document access/query actions logged to `audit_logs` table
---
## 3. SECTION 2: DATABASE & MYSQL SCHEMA

### Core Tables
| Table | Purpose |
|-------|---------|
| `users` | User accounts, email/password hash, admin flags |
| `workspaces` | Multi-tenant isolation; each workspace = separate user/organization |
| `documents` | Document metadata: filename, storage path, status (uploaded/processing/ready/error), page count |
| `document_chunks` | Semantic text chunks from PDFs; links to embedding vectors |
| `document_tables` | Tabular extracts from PDFs; SQL CREATE/INSERT statements stored in MySQL |
| `audit_logs` | Compliance tracking: who accessed what document/query and when |

### Key Relationships
- **User → Workspaces** (one-to-many): owner relationship
- **Workspace → Documents** (one-to-many): cascade delete
- **Document → Chunks** (one-to-many): chunks embedded for retrieval
- **Document → Tables** (one-to-many): SQL-queryable tabular data

### Indexes
- `idx_doc_chunk_doc_page` on `(document_id, page_number)` for fast per-document retrieval
- `email` unique index on `users` table
---
## 4. SECTION 3: VECTOR EMBEDDINGS SERVICE

### Purpose
Generate dense vector embeddings for text chunks and queries; integrate with vector stores for similarity search.

### Key File: `api/services/embedding.py`
- `get_embedding(text)` - Get embedding for single text (with caching)
- `batch_get_embeddings(texts)` - Batch embedding generation
- Supports OpenAI `text-embedding-3-large` or local `sentence-transformers`
- In-memory cache to avoid redundant API calls
- Fallback from API to local model if API fails

### Embedding Flow
1. Text chunk extracted from PDF → `get_embedding()` → vector of 1536 or 3072 dimensions
2. Vector stored alongside chunk metadata in MySQL + vector store
3. Query embedding generated similarly → similarity search against stored vectors
---
## 5. SECTION 4: VECTOR STORE SERVICE

### Purpose
Unified interface for vector similarity search across multiple backends.

### Key File: `api/services/vector_store.py`
Supports three backends (select via `VECTOR_BACKEND` env var):

| Backend | Env Var | Use Case |
|---------|---------|----------|
| ChromaDB | `chromadb` | Server-side vector DB; per-workspace collections for multi-tenancy |
| FAISS Local | `faiss_local` | Disk-based indices; good for single-node deployment without external DB |
| Mock | `mock` | Prototyping without external dependencies |

### Core Methods
- `add_chunks(chunks, embeddings, chunk_ids)` - Store vectors with metadata
- `search_similar(query_embedding, k, document_filters)` - Top-k cosine similarity search
- `delete_workspace(workspace_id)` - Remove all vectors for tenant cleanup

### Query Flow
1. User query → `get_embedding()` → query vector
2. `search_similar(k=10)` → retrieve top 10 chunks from vector store
3. Re-ranking (cross-encoder or re-score) → final ranked context
4. Context + question → LLM prompt → grounded response with source citations
---
## 6. SECTION 5: BACKGROUND INGESTION (Celery + Redis)

### Purpose
PDF text/table extraction and embedding generation runs in background via Celery so Flask workers never block on slow PDF parsing.

### Key File: `celery/tasks.py`
Pipeline stages (task: `ingest_document(document_id)`):

1. **PDF Text/Table Extraction** (`_extract_pdf_content`)
   - Uses `pdfplumber` for text + table extraction with coordinates
   - Fallback to `PyMuPDF` (fitz) if primary fails
   - Supports scanned PDFs via OCR (not implemented in prototype)

2. **Semantic Chunking** (`_create_chunks`)
   - Page-aware chunking: split by pages, then by sentence boundaries
   - Configurable `CHUNK_SIZE` (default: 500 chars) and `CHUNK_OVERLAP` (default: 50 chars)
   - Preserves `page_number`, `char_start`, `char_end` for source grounding

3. **Embedding Generation** (`batch_get_embeddings`)
   - Batch call to embedding service for all chunks
   - Vector dimensions match embedding model chosen

4. **MySQL Storage**
   - `DocumentChunk` records: text, page_number, embedding_id, embedding_model
   - `DocumentTable` records: SQL CREATE/INSERT, source page, column info

5. **Vector Index Storage**
   - `VectorStore.add_chunks()` → ChromaDB collection or FAISS index
   - Per-workspace isolation (different collection/filename per workspace)

6. **Document Status Update**
   - `Document.status` changes from `processing` → `ready`
   - Triggers SSE notification or poll-based status check

### Configuration
- Broker: Redis (`redis://localhost:6379/0`)
- Result backend: Redis
- Task timeout: 5 minutes hard / 4 minutes soft
- Retry policy: 3 retries with exponential backoff
---
## 7. SECTION 6: REACT FRONTEND

### Purpose
User interface for document upload, PDF viewing with citations, and SSE-streamed Q&A chat.

### Key Files
- `frontend/src/components/PDFViewer.jsx` - ReactPDF side-by-side viewer; highlights from search results; onHighlightClick callback scrolls to exact page/paragraph
- `frontend/src/components/ChatSSE.jsx` - EventSource-based SSE client; displays streaming tokens; citation pills; auto-scroll; click→scroll
- `frontend/src/components/DocumentUpload.jsx` - Drag-and-drop or browse file upload; progress tracking; status display (idle/uploading/success/error)
- `frontend/src/components/QueryInput.jsx` - Question form → SSE submission → processes stream via `queriesAPI.parseSSE()`
- `frontend/src/pages/Dashboard.jsx` - Main workspace layout: left panel (doc list), right panel (PDF viewer + chat)

### UI Flow
1. **Upload**: User drops PDF → `DocumentUpload` → Flask API → Celery `ingest_document` → status → ready
2. **View**: User clicks document → `PDFViewer` renders page; citations as clickable pills
3. **Query**: User types question → `QueryInput` → `queriesAPI.submit()` → SSE stream
4. **Stream**: `ChatSSE` receives tokens live; accumulates answer text; updates citation pills
5. **Grounding**: Each token carries `source_refs` (page numbers); client can scroll PDF to exact location
6. **Complete**: Final event `done` with full answer text + all source references

### SSE Architecture
- Flask `Response(stream_with_context(...))` yields SSE events: `data: {"type": "token", "text": "...", "source_refs": [...]}``
- Client uses `EventSource` or custom parser (`queriesAPI.parseSSE()`)
- Auto-scrolling as tokens arrive; manual citation clicking scrolls PDF viewer
---
## 8. SECTION 7: CONTEXTUAL QUERY REWRITING

### Purpose
Resolve ambiguous follow-up questions before document retrieval (e.g., "what about the revenue?" → "What was the revenue growth in Q3 2024?").

### Implementation
- **Heuristic-based** in `api/routes/queries.py::contextualize_question()`
- Detects ambiguous starters: "it", "this", "that", "the", "these", "those"
- Prepends document reference prefix: `"Based on the documents, <question>"`
- Production would use an LLM prompt to rewrite using conversation history

### Integration Point
Called in `queriesAPI.submit()` before embedding generation and retrieval.
---
## 9. SECTION 8: SECURITY & COMPLIANCE

### Authentication
- **JWT** (JSON Web Tokens) via `Flask-JWT-Extended`
- Access tokens: 24-hour expiration (configurable)
- Refresh tokens: rotate on login/logout
- Stateless: no server-side sessions required

### Authorization
- **Multi-tenancy**: Every resource scoped to `workspace_id`
- Users only access workspaces they own or are granted access to
- `is_admin` flag on user model for admin routes

### Audit Logging
- All document uploads, downloads, deletions tracked
- All query submissions logged with question, result length, sources retrieved
- `audit_logs` table supports compliance reporting and usage analytics

### Data Privacy
- No document content stored in URLs or logs (only metadata)
- File uploads validated by MIME type (not just extension)
- Maximum file size configurable (default: 50MB)
---
## 10. DEPLOYMENT NOTES

### Production Checklist
- [ ] Set `SECRET_KEY` and `JWT_SECRET_KEY` from environment (not hardcoded)
- [ ] Configure production MySQL database (not SQLite)
- [ ] Deploy Redis for Celery broker + result backend
- [ ] Set `VECTOR_BACKEND=chromadb` or `faiss_local`
- [ ] Set `DEFAULT_EMBEDDING_MODEL` and `RETRIEVAL_K` environment variables
- [ ] Enable HTTPS; set `USE_SESSION_COOKIE=False` for JWT-only auth
- [ ] Configure CORS origins for production frontend domain
- [ ] Set `MAX_DOCUMENT_SIZE` limit appropriate for your use case
- [ ] Enable log rotation and audit log retention policy
- [ ] Consider read-replica MySQL for query scaling

### Environment Variables (.env)
```
# Flask / API
SECRET_KEY=change-this-to-a-really-random-string
JWT_SECRET_KEY=change-this-also
MYSQL_URI=mysql+pymysql://user:pass@host:3306/db_name
FLASK_DEBUG=False

# Embeddings
DEFAULT_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_API_KEY=sk-...

# Vector Store
VECTOR_BACKEND=chromadb
CHROMADA_PERSIST_PATH=/data/chromadb

# Celery / Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# App
API_PORT=5000
MAX_DOCUMENT_SIZE=52428800  # 50MB in bytes
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

### Development Quickstart
1. `python -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. `cp .env.example .env` and fill in values
4. `mysql -u root -e "CREATE DATABASE enterprise_rag;"`
5. `redis-server --daemonize yes`
6. `flask db init` (Alembic migration for SQLAlchemy models)
7. `flask upgrade` (create tables)
8. `celery -A celery.tasks ingest_document worker --loglevel=info`
9. `python api/app.py` (starts Flask on http://0.0.0.0:5000)
10. `cd frontend && npm install && npm start` (React dev server on http://localhost:3000)
---
## 11 FUTURE ENHANCEMENTS (Roadmap)

- [ ] LLM-powered contextual query rewriting (GPT-4/Claude prompt using conversation history)
- [ ] Hybrid retrieval: vector search + BM25 keyword search
- [ ] Caching layer for frequent queries (Redis or Memcached)
- [ ] Conversation history persistence per user/workspace
- [ ] Multi-modal: table query via natural language -> SQL generation
- [ ] Permission-based access control (RBAC per workspace)
- [ ] Real-time collaboration: multiple users querying same workspace
- [ ] Dashboard analytics: most-asked questions, document popularity, verification metrics
- [ ] Containerized deployment with Docker Compose (Flask + Redis + ChromaDB)
- [ ] API rate limiting and request throttling