# Enterprise Multi-Document RAG & Semantic Analytics Workspace

## 📋 Project Overview

A SaaS-style research workspace where users upload domain documents (financial reports, technical specs, policy docs), run grounded Q&A with live source citations, and query tabular extracts stored directly in MySQL.

## 🏗️ Architecture Stack

| Technology | Purpose |
|------------|---------|
| **React** | PDF side-by-side viewer (react-pdf) with highlight coordinates, citation pills, and streaming SSE chat interface |
| **Flask** | REST API endpoints, streaming generators (`Response(stream_with_context(...))`), and JWT authentication |
| **MySQL** | Stores relational workspace schemas, user accounts, document metadata, audit logs, and tabular extracts; integrates external vector index (ChromaDB/Milvus/Qdrant/FAISS) |
| **Gen AI** | Dense vector embeddings, re-ranking pipelines, and token-streaming grounded responses |
| **Celery + Redis** | Background embedding extraction so Flask workers never block on PDF parsing |

## ✨ Key Features

- **Multi-tenant document intelligence** - Each workspace is isolated via `workspace_id`
- **Server-Sent Events (SSE)** - Low-latency token responses with dynamic source attribution (cuts verification time in half)
- **Page-accurate source grounding** - Clicking a citation scrolls the document viewer to the exact page and paragraph
- **Contextual query rewriting** - Resolves ambiguous follow-up questions before document retrieval
- **Asynchronous Celery ingestion pipeline** - PDF parsing runs in background; Flask workers never block
- **Tabular extracts in MySQL** - SQL-queryable table structures from PDFs in addition to vector search
- **JWT authentication** - Stateless token-based auth for all API routes

## 📁 Project Structure

```
enterprise-rag-workspace/
├── api/                    # Flask REST API backend
│   ├── app.py              # App factory, route registration
│   ├── models.py           # SQLAlchemy MySQL models (6 tables)
│   ├── routes/             # Blueprint routes (auth, documents, queries)
│   ├── services/           # Embedding & vector store services
│   └── package.json
├── celery/                 # Background task queue
│   ├── tasks.py            # PDF ingestion pipeline
│   ├── config.py           # Celery app with Flask integration
│   └── __init__.py
├── frontend/               # React client application
│   ├── src/
│   │   ├── components/     # PDFViewer, ChatSSE, DocumentUpload, QueryInput
│   │   ├── pages/          # Dashboard (main workspace UI)
│   │   ├── services/       # api.js - Flask API client
│   │   └── App.js (entry point)
│   └── package.json
├── docker/                 # Docker deployment (Option A)
│   ├── docker-compose.yml
│   ├── Dockerfile.api
│   ├── Dockerfile.frontend
│   ├── nginx.conf
│   └── init_db/01-schema.sql
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
├── start-docker.bat        # Windows one-click Docker starter
├── SUMMARY.md              # Section-wise architecture overview
└── README.md               # This file
```

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
cd enterprise-rag-workspace
cp .env.example .env    # Edit with your values (secrets, DB creds, etc.)
docker compose up --build -d
```

Wait 60-90 seconds for all services to initialize, then visit:
- **Frontend:** http://localhost:3000
- **API:** http://localhost:5000/api (SSE at `/queries/submit`)
- **Health:** http://localhost:5000/api/health

### Option 2: Non-Docker (Traditional)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
mysql -u root -e "CREATE DATABASE enterprise_rag;"
redis-server --daemonize yes
flask db upgrade                                    # Runs Alembic migrations
celery -A celery.tasks ingest_document worker --loglevel=info   # Background terminal
python api/app.py                                   # Starts Flask on http://0.0.0.0:5000
cd frontend && npm install && npm start             # React dev server on http://localhost:3000
```

Register an account, upload a PDF, wait for Celery processing, then query with grounded Q&A.

## 🛠️ Deployment Options

### Option A: Docker Compose (Easiest)

See `docker/` directory for full stack orchestration:
- Flask API + MySQL + Redis + React Frontend + Celery Worker
- One-command setup: `docker compose up --build -d`
- Production checklist in `SUMMARY.md`

### Option B: Traditional Deployment

Manual setup without Docker:
1. Install system deps: `apt-get install gcc gmysql redis-server`
2. Python venv + `pip install -r requirements.txt`
3. Create MySQL database, run migrations (`flask db upgrade`)
4. Start Celery worker
5. Run Flask app
6. Build & serve React frontend
7. Configure vector store (ChromaDB/FAISS)

### Option C: Cloud / Managed Platforms

| Platform | Steps |
|----------|-------|
| **AWS ECS/Fargate** | Containerize each service; use RDS + ElastiCache |
| **Google Cloud Run** | Two container services; Cloud SQL + Memorystore |
| **Azure Container Apps** | Two container apps; Azure PostgreSQL + Azure Cache |
| **Render.com** | Backend Web Service + Static Site for frontend |
| **Railway** | Single service with docker-compose.yml |

## 📦 Requirements

```text
Flask>=3.0.0
Flask-JWT-Extended>=5.7.0
Flask-SQLAlchemy>=3.1.0
Flask-CORS>=5.0.0
python-dotenv>=10.0.0
mysql-connector-python>=8.3.0
sqlalchemy>=2.0.0
pdfplumber>=0.9.0
PyPDF2>=3.0.0
reportlab>=4.1.0
openai>=1.3.0              # for embeddings/API
sentence-transformers>=3.0.0  # local embeddings
celery>=5.4.0
redis>=5.0.0
Pillow>=10.0.0
react>=18.3.0
react-dom>=18.3.0
react-pdf>=2.5.0
react-scripts>=5.0.1
```

## 📚 Sections Documentation

For detailed section-wise breakdown, see `SUMMARY.md` which covers:

1. **Backend API** - Flask app factory, JWT, MySQL models, SSE streaming
2. **Database & MySQL Schema** - 6 tables, relationships, indexes
3. **Vector Embeddings Service** - OpenAI/local embeddings, caching, batch support
4. **Vector Store Service** - ChromaDB/FAISS/Mock per-workspace isolation
5. **Background Ingestion** - Celery + Redis pipeline: PDF → chunks → embeddings → storage
6. **React Frontend** - 15+ components, SSE streaming, UI flow
7. **Contextual Query Rewriting** - Heuristic-based ambiguous question resolution
8. **Security & Compliance** - JWT auth, audit logging, MIME validation, multi-tenancy
9. **Deployment Notes** - Production checklist, env vars, quickstart
10. **Future Enhancements** - Roadmap items

## 🔐 Environment Variables (`.env.example`)

```env
# Flask / API
SECRET_KEY=change-this-to-a-really-random-string
JWT_SECRET_KEY=change-this-also
MYSQL_URI=mysql+pymysql://rag_user:rag_password@mysql:3306/enterprise_rag
FLASK_DEBUG=False

# Embeddings
DEFAULT_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_API_KEY=sk-...

# Vector Store
VECTOR_BACKEND=chromadb
CHROMADA_PERSIST_PATH=/data/chromadb

# Celery / Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# App
API_PORT=5000
MAX_DOCUMENT_SIZE=52428800   # 50MB in bytes
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/foo`)
3. Commit your changes (`git commit -m 'Add foo'`)
4. Push to the branch (`git push origin feature/foo`)
5. Open a Pull Request

## 📄 License

MIT License - see the `LICENSE` file for details (or add one if needed).

---

*Built with ❤️ using React, Flask, MySQL, Celery, and Gen AI.*