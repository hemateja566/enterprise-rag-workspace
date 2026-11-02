# AI Placement Assistant

A Retrieval-Augmented Generation (RAG) application for placement preparation. Upload PDF documents (company profiles, interview experiences, study materials) and ask questions to get grounded answers with source citations.

## Features

- **PDF Upload**: Drag-and-drop multiple PDF files
- **Document Processing**: Automatic text extraction and chunking
- **Vector Embeddings**: Sentence Transformers for semantic search
- **Vector Store**: FAISS for efficient similarity search
- **RAG Pipeline**: Retrieval + Generation with citations
- **Source Attribution**: Shows exact PDF pages for each answer
- **Streamlit UI**: Clean, interactive web interface

## Architecture

```
User Uploads PDFs
       ↓
PyPDFLoader reads pages
       ↓
Text split into chunks (RecursiveCharacterTextSplitter)
       ↓
Embedding model converts chunks → vectors
       ↓
FAISS creates vector database
       ↓
User asks question
       ↓
Retriever finds top-k relevant chunks
       ↓
Context + Question → LLM (Qwen/HF model)
       ↓
Answer + Source pages displayed
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| UI | Streamlit |
| Document Loading | LangChain (PyPDFLoader) |
| Text Splitting | LangChain (RecursiveCharacterTextSplitter) |
| Embeddings | Sentence Transformers (all-MiniLM-L6-v2) |
| Vector DB | FAISS |
| LLM | Hugging Face (Qwen/Qwen2.5-7B-Instruct or similar) |
| Orchestration | LangChain RAG chain |

## Project Structure

```
AI_placement_assisstant/
├── app.py                  # Streamlit application
├── requirements.txt        # Python dependencies
├── README.md
└── .env                    # Environment variables (local)
```

## Getting Started

### Prerequisites

- Python 3.10+
- pip
- Hugging Face account (for model access)
- ~4GB RAM minimum (for model inference)

### Installation

```bash
git clone https://github.com/hemateja566/AI_placement_assisstant.git
cd AI_placement_assisstant

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Configuration

Create `.env` file:
```env
HF_TOKEN=your_huggingface_token
# Optional: specify models
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
```

### Running

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`

## Usage

1. **Upload Documents**: Click "Browse files" and select PDF files (company brochures, interview experiences, prep materials)
2. **Process**: Click "Process Documents" - extracts text, creates chunks, generates embeddings, builds FAISS index
3. **Ask Questions**: Type placement-related questions:
   - "What are common interview questions for Google?"
   - "What's the CTC range for Amazon SDE-1?"
   - "How to prepare for system design interviews?"
4. **View Answers**: Get grounded responses with source page citations

## Dependencies (requirements.txt)

```
streamlit
langchain
langchain-community
faiss-cpu
sentence-transformers
pypdf
python-dotenv
huggingface-hub
torch
accelerate
```

## Configuration Options

### Chunking (in app.py)
```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,      # Characters per chunk
    chunk_overlap=200,    # Overlap for context
    length_function=len,
)
```

### Retrieval
```python
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4}  # Top 4 chunks
)
```

### LLM Parameters
```python
llm = HuggingFacePipeline(
    pipeline=pipe,
    model_kwargs={
        "temperature": 0.1,
        "max_new_tokens": 512,
        "top_p": 0.95,
    }
)
```

## Example Use Cases

### For Students
- Upload company presentation PDFs
- Ask: "What technologies does Company X use?"
- Get specific answers with page references

### For Placement Cells
- Upload past interview experiences
- Query: "What questions were asked in Microsoft 2023 interviews?"
- Build knowledge base for future batches

### For Self-Prep
- Upload study materials (OS, DBMS, CN notes)
- Ask: "Explain deadlock prevention methods"
- Get concise explanations from your own materials

## Limitations

- **Not a substitute** for comprehensive preparation
- Accuracy depends on uploaded document quality
- LLM may hallucinate if context insufficient
- Processing time increases with document count
- Memory usage scales with vector index size

## Privacy

- Documents processed locally (no upload to external servers unless using cloud LLM)
- FAISS index stored in memory/session
- Clear data on session end
- For sensitive docs: use local LLM (Ollama, llama.cpp)

## Deployment

### Streamlit Cloud
1. Push to GitHub
2. Connect to Streamlit Cloud
3. Add `HF_TOKEN` in secrets
4. Deploy

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Hugging Face Spaces
- Create Space with Streamlit SDK
- Add requirements.txt
- Set HF_TOKEN secret

## Future Enhancements

- [ ] Multi-user support with authentication
- [ ] Persistent vector store (disk-based FAISS)
- [ ] Document management (delete, update)
- [ ] Chat history export
- [ ] Question templates for common placement topics
- [ ] Integration with job portals API
- [ ] Resume parsing and matching
- [ ] Mock interview simulation

## License

MIT License - Educational and personal use