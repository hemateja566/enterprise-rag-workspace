# React Frontend - Enterprise RAG Workspace

## Overview
Client-side application for the Enterprise Multi-Document RAG & Semantic Analytics Workspace.

## Tech Stack
- React 18+ with hooks
- react-pdf for PDF side-by-side viewer
- SSE (EventSource) for streaming chat responses
- JWT authentication via http-only cookies or Authorization header
- CSS Modules or Tailwind for styling

## Key Components

### PDFViewer Component
- Side-by-side or single-page PDF rendering
- Highlight coordinates from search results
- Click-to-scroll source citations

### ChatSSE Component
- Server-Sent Events connection for streaming token responses
- Auto-scroll as tokens arrive
- Citation pill rendering (clickable page references)

### DocumentUpload Component
- Drag-and-drop PDF upload
- Progress tracking
- Status display (uploaded → processing → ready)

### QueryInput Component
- Natural language question input
- Contextual query rewriting support
- Submit → SSE stream → display pipeline

## File Structure
- `src/components/PDFViewer.jsx` - PDF rendering with highlights
- `src/components/ChatSSE.jsx` - SSE streaming chat interface
- `src/components/DocumentUpload.jsx` - File upload UI
- `src/components/QueryInput.jsx` - Question input + submit
- `src/pages/Dashboard.jsx` - Main workspace dashboard
- `src/pages/DocumentViewer.jsx` - Document viewer with citations
- `src/services/api.js` - Flask API client functions
- `src/context/AuthContext.jsx` - JWT auth state