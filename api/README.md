# API Backend (Flask)

## Purpose
REST API endpoints, streaming generators for SSE chat, and JWT authentication for the Enterprise RAG Workspace.

## Key Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/auth/login` | JWT authentication login |
| POST   | `/auth/register` | User registration |
| POST   | `/documents/upload` | Upload PDF/document files |
| GET    | `/documents/{id}` | Get document metadata |
| DELETE | `/documents/{id}` | Delete document |
| POST   | `/queries` | Submit a grounded Q&A query |
| GET    | `/queries/{id}/status` | Query status (for async processing) |
| GET    | `/sse/queries/{id}` | Server-Sent Events stream for query response |

## Core Concepts
- **JWT Authentication**: Stateless token-based auth for API routes
- **Streaming Generators**: `Response(stream_with_context(...))` for token-by-token SSE streaming
- **Document States**: `uploaded` → `processing` → `ready` → `error`
- **Query Workflow**: User query → contextual rewriting → vector retrieval → re-ranking → streaming response with citations

## File Structure
- `app.py` - Main Flask application with auth, middleware, and route registration
- `routes/documents.py` - Document upload/download metadata routes
- `routes/queries.py` - Query submission and SSE streaming routes
- `services/embedding.py` - Text embedding service (integrates with OpenAI/Azure/HuggingFace)
- `services/rag.py` - Core RAG pipeline (retrieval, re-ranking, grounding)
- `services/pdf_parser.py` - PDF text/image extraction (called by Celery)
- `models.py` - SQLAlchemy models for MySQL schemas