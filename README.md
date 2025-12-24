# OllamaRAG
# Local AI Document Processing & Q&A System


A FastAPI-based application with AI integration, authentication, and document processing capabilities.

## Features
- FastAPI REST API
- AI-powered capabilities with Ollama
- RAG (Retrieval-Augmented Generation) using Nomic embeddings
- LLM inference with Qwen model
- Milvus vector database for embeddings
- Authentication system
- PDF and DOCX document processing
- Docker containerization

## Tech Stack
- **Backend**: FastAPI with Uvicorn
- **Python**: 3.11
- **LLM Engine**: Ollama (Qwen + Nomic)
- **Vector DB**: Milvus
- **Containerization**: Docker & Docker Compose

## Prerequisites
- Python 3.11+
- [Ollama](https://ollama.ai) with the following models:
  - `nomic-embed-text` - For RAG embeddings
  - `qwen` - For LLM inference
- Docker & Docker Compose (optional)

## Setup & Installation

### Prerequisites Setup

#### Install Ollama and Models
1. Download and install [Ollama](https://ollama.ai)
2. Pull the required models:
   ```bash
   ollama pull nomic-embed-text  # For RAG embeddings
   ollama pull qwen              # For LLM inference
   ```
3. Start Ollama (runs on `http://localhost:11434` by default)

### Local Development
1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   ```
6. Ensure Ollama is running with models loaded
7. Run: `cd src && uvicorn main:app --reload`

API available at `http://localhost:8000`  
API Docs: `http://localhost:8000/docs`

### Docker Setup
Run with: `docker-compose up --build`

Access at `http://localhost:8000` and docs at `/docs`

### Ollama Integration
The application connects to Ollama running locally on port 11434. Make sure:
- Ollama service is running
- Models `nomic-embed-text` and `qwen` are pulled
- Environment variable `OLLAMA_HOST` is properly configured in `.env`

## Project Structure
```
src/                   - Application code (main.py, ai.py, auth.py)
docs/                  - Documentation
docker-compose.yml     - build the iamge for the docker network and run the containers
Dockerfile             - image setup
```
