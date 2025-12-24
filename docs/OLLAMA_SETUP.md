# Ollama Setup Guide

This guide explains how to set up and configure Ollama for this project.

## Installation

### Windows
1. Download the installer from [ollama.ai](https://ollama.ai)
2. Run the installer and follow the setup wizard
3. Ollama will start automatically as a service

### macOS
```bash
brew install ollama
```

### Linux
```bash
curl https://ollama.ai/install.sh | sh
```

## Pulling Required Models

This project requires two models for optimal functionality:

### 1. Nomic Embed Text (For RAG/Embeddings)
```bash
ollama pull nomic-embed-text
```
- **Purpose**: Generates embeddings for Retrieval-Augmented Generation (RAG)
- **Model Size**: ~274MB
- **Use Case**: Converting documents and queries into vector embeddings for Milvus

### 2. Qwen (For LLM Inference)
```bash
ollama pull qwen
```
- **Purpose**: General-purpose language model for text generation
- **Model Size**: ~4.4GB (7B parameters)
- **Use Case**: Generating responses based on prompts and RAG context

## Running Ollama

### Local Development
Ollama starts as a background service on `http://localhost:11434`

Check if Ollama is running:
```bash
curl http://localhost:11434/api/tags
```

### Using Ollama in Your Application
The application communicates with Ollama via HTTP API at `http://localhost:11434`

Configure the endpoint in `.env`:
```env
OLLAMA_HOST=http://localhost:11434
```

## Verifying Setup

### List available models
```bash
ollama list
```

### Test a model
```bash
ollama run qwen "Hello, how are you?"
```

### Test embeddings
```bash
ollama run nomic-embed-text "sample text"
```

## Troubleshooting

### Models not loading
- Ensure Ollama service is running
- Check internet connection (first pull downloads models)
- Verify disk space (Qwen needs ~5GB)

### Connection refused errors
- Check that Ollama is running: `ollama serve` (if not running as service)
- Verify the host/port in `.env` matches Ollama configuration
- Default: `http://localhost:11434`

### Slow performance
- Qwen 7B may be slow on CPU-only systems
- Consider using smaller models or GPU acceleration
- Check system resources while running

## Model Information

| Model | Purpose | Size | Parameters |
|-------|---------|------|-----------|
| nomic-embed-text | RAG Embeddings | 274MB | - |
| qwen | LLM Inference | 4.4GB | 7B |

## Next Steps
- Configure the application in `.env`
- Check [ARCHITECTURE.md](./ARCHITECTURE.md) for system design
- Review [API.md](./API.md) for endpoint documentation
