# AI Assistant (Medical)

AI-powered medical document assistant using RAG (Retrieval-Augmented Generation) for healthcare document query.

## Overview

A medical AI assistant that allows users to upload medical documents and ask questions. Uses vector embeddings and semantic search to provide grounded answers from the uploaded documents.

## Features

- PDF document upload and processing
- Medical document chunking and embedding
- Vector similarity search (FAISS)
- Grounded answer generation with citations
- Source document references
- Medical terminology support

## Tech Stack

- **Language**: Python
- **Framework**: Streamlit (UI)
- **LLM**: Hugging Face models
- **Vector DB**: FAISS
- **Document Processing**: PyPDFLoader, LangChain
- **Embeddings**: Sentence Transformers

## Project Structure

```
ai-assisstannt/
├── medical_docs/           # Medical document storage
├── app.py                  # Streamlit application
├── requirements.txt        # Python dependencies
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.9+
- pip
- Hugging Face account (for model access)

### Installation

```bash
git clone https://github.com/hemateja566/ai-assisstannt.git
cd ai-assisstannt

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Configuration

Create `.env` file:
```env
HF_TOKEN=your_huggingface_token
```

### Running

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`

## Usage

1. Launch the app
2. Upload medical PDF documents
3. Documents are processed and indexed
4. Ask medical questions in the chat interface
5. View answers with source citations

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
```

## Medical Document Processing

### Supported Formats
- PDF (primary)
- Text files
- Future: DICOM, HL7

### Chunking Strategy
- Medical-aware chunking (preserves sections)
- Overlap for context continuity
- Metadata preservation (page numbers, sections)

### Embeddings
- Model: `sentence-transformers/all-MiniLM-L6-v2` or medical-specific
- Dimension: 384
- Stored in FAISS index

## RAG Pipeline

```
User Question
     ↓
Embedding Generation
     ↓
FAISS Similarity Search (top-k)
     ↓
Context Assembly
     ↓
LLM Generation (grounded)
     ↓
Answer + Citations
```

## Privacy & Compliance

⚠️ **Important**: This is a prototype. For production medical use:
- HIPAA compliance required
- Data encryption at rest/transit
- Audit logging
- Access controls
- PHI de-identification
- Business Associate Agreements

## Limitations

- Not a substitute for professional medical advice
- Accuracy depends on document quality
- Hallucination possible despite RAG
- Limited to uploaded document knowledge

## Future Enhancements

- [ ] Multi-document comparison
- [ ] Medical ontology integration (SNOMED, ICD-10)
- [ ] Voice interface
- [ ] Multi-language support
- [ ] Fine-tuned medical LLM
- [ ] Clinical trial matching

## License

MIT License - Not for clinical use without proper validation and compliance