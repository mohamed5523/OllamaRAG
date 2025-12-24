# Development Guide

## Environment Setup

### Prerequisites
- Python 3.11+
- Ollama installed with models
- Virtual environment tool

### Initial Setup
```bash
# Clone repository
git clone <repo-url>
cd project

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

### Configure .env
Edit `.env` with your settings:
```env
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
OLLAMA_HOST=http://localhost:11434
MILVUS_HOST=localhost
MILVUS_PORT=19530
SECRET_KEY=your-development-secret-key
```

## Running the Application

### Start Ollama First
```bash
# Ollama should start automatically as a service
# Verify it's running:
curl http://localhost:11434/api/tags
```

### Start the API Server
```bash
cd src
uvicorn main:app --reload --port 8000
```

Access the API at `http://localhost:8000` and docs at `/docs`

### Run Tests
```bash
pytest tests/ -v
pytest tests/ -v --cov=src  # With coverage
```

## Project Structure

```
project/
├── src/
│   ├── main.py              # FastAPI entry point
│   ├── auth.py              # Authentication logic
│   ├── ai.py                # AI/RAG engine
│   ├── vscode_ai_helper.py  # VS Code integration
│  
│
├── docs/
│   ├── OLLAMA_SETUP.md      # Ollama configuration
│   ├── ARCHITECTURE.md      # System design
│   ├── API.md               # API documentation
│   └── DEVELOPMENT.md       # This file
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
└── docker-compose.yml
```

## Coding Standards

### Python Style
- Follow PEP 8 guidelines
- Use type hints for function parameters and returns
- Maximum line length: 88 characters (Black formatter)
- Use descriptive variable and function names

### Import Organization
```python
# 1. Standard library
import os
import sys

# 2. Third-party libraries
import fastapi
import numpy as np

# 3. Local imports
from auth import authenticate
from ai import process_document
```

### Documentation
All functions should have docstrings:
```python
def process_document(file_path: str, chunk_size: int = 512) -> dict:
    """
    Process a document and generate embeddings.
    
    Args:
        file_path: Path to the document file
        chunk_size: Size of text chunks for embeddings
        
    Returns:
        Dictionary with embedding results
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is not supported
    """
    pass
```

## Working with Ollama

### Available Models
- **qwen**: Main LLM for inference
- **nomic-embed-text**: Embedding generation

### Common Tasks

#### Generate Embeddings
```python
from ai import generate_embeddings

text = "Sample text to embed"
embeddings = generate_embeddings(text, model="nomic-embed-text")
```

#### Query LLM
```python
from ai import query_llm

response = query_llm(
    prompt="Your question",
    model="qwen",
    temperature=0.7
)
```

#### RAG Pipeline
```python
from ai import rag_query

result = rag_query(
    query="Your question",
    top_k=3,
    use_milvus=True
)
```

## Working with Milvus

### Initialize Milvus Connection
```python
from pymilvus import connections

connections.connect(
    alias="default",
    host="localhost",
    port=19530
)
```

### Create Collection
```python
from pymilvus import Collection

collection = Collection("documents")
```

### Insert Embeddings
```python
embeddings = [[0.1, 0.2, 0.3, ...]]
collection.insert(embeddings)
```



## Troubleshooting

### Ollama Connection Error
1. Check if Ollama is running: `curl http://localhost:11434/api/tags`
2. Verify `OLLAMA_HOST` in `.env`
3. Restart Ollama service

### Milvus Connection Error
1. Verify Milvus is running on port 19530
2. Check network connectivity
3. Review Milvus logs

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [Milvus Documentation](https://milvus.io/)

