# Architecture Overview

## System Design

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
│                    (main.py - Port 8000)                    │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Auth       │   │   AI/RAG     │   │  Documents   │
│   (auth.py)  │   │  (ai.py)     │   │ Processing   │
└──────────────┘   └──────────────┘   └──────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Ollama     │   │   Milvus     │   │ VS Code      │
│  (Qwen LLM)  │   │   Vector DB   │   │  Helper      │
│  (Nomic Emb) │   │   (Port 19530)│   │              │
└──────────────┘   └──────────────┘   └──────────────┘
    Port 11434                    Port 19530
```

## Components

### 1. **FastAPI Application** (main.py)
- RESTful API server
- Request routing and handling
- Response formatting

### 2. **Authentication Module** (auth.py)
- User authentication
- Token generation and validation
- Security headers

### 3. **AI/RAG Engine** (ai.py)
- Integration with Ollama for LLM inference
- RAG pipeline using embeddings and Milvus
- Document processing and chunking

### 4. **VS Code Helper** (vscode_ai_helper.py)
- Integration with VS Code extension
- IDE-specific endpoints and functionality

## Data Flow: RAG Pipeline

```
Document Input
    │
    ▼
Chunk Document
    │
    ▼
Generate Embeddings (nomic-embed-text via Ollama)
    │
    ▼
Store in Milvus Vector Database
    │
    └─────────────────────────────────┐
                                      │
Query Input                           │
    │                                 │
    ▼                                 │
Generate Query Embedding              │
    │                                 │
    ▼                                 │
Search Similar Vectors (Milvus) ◄────┘
    │
    ▼
Retrieve Context
    │
    ▼
Construct Prompt with Context
    │
    ▼
LLM Inference (Qwen via Ollama)
    │
    ▼
Generate Response
```

## External Services

### Ollama (Port 11434)
- **Models**: 
  - `qwen` - General-purpose LLM
  - `nomic-embed-text` - Embedding model
- **API**: HTTP REST endpoints
- **Status**: Localhost service

### Milvus Vector Database (Port 19530)
- **Purpose**: Stores and searches document embeddings
- **Type**: Vector similarity search
- **Integration**: Python client (pymilvus)

## Data Storage

- **Vector Embeddings**: Milvus DB
- **Document Files**: `/app/uploads` (in Docker)
- **Embeddings Cache**: `/app/embeddings` (in Docker)

## Security Considerations

1. **Authentication**: Token-based auth in auth.py
2. **Environment Variables**: Sensitive data in .env
3. **.gitignore**: Excludes .env files from version control
4. **Input Validation**: Pydantic models validate all inputs

## Deployment

### Local Development
- FastAPI on `localhost:8000`
- Ollama on `localhost:11434`
- Milvus on `localhost:19530`

### Docker Deployment
- Containerized FastAPI service
- Ollama accessible to containers
- Milvus service in separate container

## Dependencies

See [requirements.txt](../requirements.txt) for all dependencies:
- FastAPI & Uvicorn
- Ollama client
- Milvus Python client
- Document processing (PyPDF2, python-docx)
- Request handling (requests)
- Data validation (pydantic, marshmallow)
