# API Documentation

## Overview

This API provides endpoints for AI-powered document analysis, RAG (Retrieval-Augmented Generation), and interactive LLM inference.

## Base URL

- **Local Development**: `http://localhost:8000`
- **Docker**: `http://localhost:8000`
- **Interactive Docs**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8000/redoc` (ReDoc)

## Authentication

All endpoints require authentication via Bearer token:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/endpoint
```

## Endpoints

### Health Check
```
GET /health
```
Check if API is running.

**Response:**
```json
{
  "status": "ok"
}
```

### Authentication

#### Login
```
POST /auth/login
```
Generate authentication token.

**Request Body:**
```json
{
  "username": "user",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### AI/RAG Endpoints

#### Upload Document
```
POST /api/documents/upload
```
Upload a document for RAG processing.

**Parameters:**
- `file` (multipart/form-data): PDF or DOCX file

**Response:**
```json
{
  "id": "doc_123",
  "filename": "example.pdf",
  "status": "processing",
  "created_at": "2024-12-24T10:00:00Z"
}
```

#### Query with RAG
```
POST /api/rag/query
```
Query documents with RAG pipeline.

**Request Body:**
```json
{
  "query": "What is the main topic?",
  "top_k": 3
}
```

**Response:**
```json
{
  "query": "What is the main topic?",
  "context": [
    {
      "text": "...",
      "score": 0.95,
      "source": "doc_123"
    }
  ],
  "response": "Based on the documents...",
  "model": "qwen"
}
```

#### Direct LLM Query
```
POST /api/llm/query
```
Direct query to LLM without RAG.

**Request Body:**
```json
{
  "prompt": "Explain quantum computing",
  "temperature": 0.7,
  "max_tokens": 500
}
```

**Response:**
```json
{
  "prompt": "Explain quantum computing",
  "response": "Quantum computing is...",
  "model": "qwen",
  "tokens_used": 150
}
```

#### List Documents
```
GET /api/documents
```
List all uploaded documents.

**Response:**
```json
{
  "documents": [
    {
      "id": "doc_123",
      "filename": "example.pdf",
      "uploaded_at": "2024-12-24T10:00:00Z",
      "status": "ready"
    }
  ]
}
```

#### Delete Document
```
DELETE /api/documents/{document_id}
```
Delete a document and its embeddings.

**Response:**
```json
{
  "success": true,
  "message": "Document deleted"
}
```

## Models

### Ollama Models

#### Embedding Model: `nomic-embed-text`
- **Dimensions**: 768
- **Purpose**: Generate embeddings for RAG
- **Speed**: Fast, ~50ms per document chunk

#### LLM Model: `qwen`
- **Parameters**: 7B
- **Purpose**: Text generation and inference
- **Temperature**: 0.0-1.0 (default: 0.7)
- **Context Window**: 32K tokens

## Error Handling

All errors follow this format:

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-12-24T10:00:00Z"
}
```

### Common Status Codes
- `200`: Success
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `500`: Server Error

## Rate Limiting

No built-in rate limiting currently. Consider implementing based on usage.

## Pagination

List endpoints support pagination:
```
GET /api/documents?skip=0&limit=10
```

## Examples

### Python Example
```python
import requests

BASE_URL = "http://localhost:8000"

# Login
auth_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": "user", "password": "password"}
)
token = auth_response.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# Query RAG
response = requests.post(
    f"{BASE_URL}/api/rag/query",
    json={"query": "What is this document about?"},
    headers=headers
)

print(response.json())
```

### cURL Example
```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"password"}'

# Query
curl -X POST http://localhost:8000/api/rag/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"Your question here"}'
```

## WebSocket Endpoints (Optional)

For streaming responses:
```
WS /api/stream/query
```

Send queries and receive streamed responses in real-time.

## Best Practices

1. **Caching**: Cache embeddings for frequently used documents
2. **Batch Processing**: Upload documents in batches when possible
3. **Token Management**: Refresh tokens before expiration
4. **Error Handling**: Implement retry logic for network failures
5. **Performance**: Use appropriate `top_k` values (3-5 usually optimal)

## Development Notes

- API is auto-documented via OpenAPI/Swagger
- All responses use standard JSON format
- Authentication uses JWT tokens
- Timestamps use ISO 8601 format
