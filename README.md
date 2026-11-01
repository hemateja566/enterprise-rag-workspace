# Enterprise Multi-Document RAG & Semantic Analytics Workspace

## Overview
A SaaS-style research workspace where users upload domain documents (financial reports, technical specs, policy docs), run grounded Q&A with live source citations, and query tabular extracts stored directly in MySQL.

## Architecture Stack
- **React**: PDF side-by-side viewer with highlight coordinates, citation pills, and streaming SSE chat interface
- **Flask**: REST API endpoints, streaming generators (Response(stream_with_context(...))), and JWT authentication
- **MySQL**: Stores relational workspace schemas, user accounts, document metadata, audit logs, and external vector index integration
- **Gen AI**: Dense vector embeddings, re-ranking pipelines, and token-streaming grounded responses
- **Celery + Redis**: Background embedding extraction so Flask workers never block on PDF parsing

## Key Features
- Multi-tenant document intelligence system
- Server-Sent Events (SSE) for low-latency token responses
- Dynamic source attribution cutting answer verification time in half
- Page-accurate source grounding (clicking citation scrolls to exact page/paragraph)
- Contextual query rewriting for ambiguous follow-up questions
- Asynchronous Celery ingestion pipeline

## Quick Start
See each section's README for detailed setup instructions.