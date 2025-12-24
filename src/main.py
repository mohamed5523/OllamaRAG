"""
RAG API Service - Document ingestion and retrieval
FastAPI-based service for managing R&D knowledge base
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import hashlib
from pathlib import Path
import requests
import json
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
import pymilvus as np
import re

app = FastAPI(title="Company AI RAG API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
MILVUS_HOST = os.getenv("MILVUS_HOST", "milvus-standalone")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
COLLECTION_NAME = "company_documents"
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Pydantic models
class SearchQuery(BaseModel):
    query: str
    top_k: int = 5
    filter_metadata: Optional[Dict] = None

class DocumentMetadata(BaseModel):
    filename: str
    doc_type: str
    uploaded_by: Optional[str] = None
    tags: Optional[List[str]] = None

class ChunkResponse(BaseModel):
    chunk_id: str
    text: str
    metadata: Dict
    score: float

# Initialize Milvus connection
def init_milvus():
    """Initialize Milvus connection and create collection if not exists"""
    try:
        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
        
        if not utility.has_collection(COLLECTION_NAME):
            # Define schema
            fields = [
                FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),  # nomic-embed-text dimension
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=8000),
                FieldSchema(name="filename", dtype=DataType.VARCHAR, max_length=500),
                FieldSchema(name="doc_type", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="chunk_index", dtype=DataType.INT64),
            ]
            
            schema = CollectionSchema(fields=fields, description="Company documents collection")
            collection = Collection(name=COLLECTION_NAME, schema=schema)
            
            # Create index for vector search
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            collection.create_index(field_name="embedding", index_params=index_params)
            print(f"Created collection: {COLLECTION_NAME}")
        
        return Collection(COLLECTION_NAME)
    except Exception as e:
        print(f"Milvus initialization error: {e}")
        return None

# Initialize on startup
@app.on_event("startup")
async def startup_event():
    global collection
    collection = init_milvus()
    if collection:
        collection.load()
        print(f"Milvus collection '{COLLECTION_NAME}' loaded successfully")

# Embedding functions
def get_embedding(text: str) -> List[float]:
    """Generate embedding using Ollama"""
    url = f"{OLLAMA_HOST}/api/embeddings"
    payload = {
        "model": EMBEDDING_MODEL,
        "prompt": text
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        embedding = response.json()["embedding"]
        return embedding
    except Exception as e:
        print(f"Embedding error: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {e}")

# Text processing functions
def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundaries
        if end < text_length:
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)
            
            if break_point > chunk_size * 0.5:  # Only break if we're past halfway
                chunk = text[start:start + break_point + 1]
                end = start + break_point + 1
        
        chunks.append(chunk.strip())
        start = end - overlap
    
    return chunks

def extract_text_from_file(filepath: Path) -> str:
    """Extract text from various file formats"""
    suffix = filepath.suffix.lower()
    
    if suffix in ['.txt', '.md', '.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.go', '.rs']:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    elif suffix == '.pdf':
        try:
            import PyPDF2
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            raise HTTPException(status_code=500, detail="PyPDF2 not installed. Install with: pip install PyPDF2")
    
    elif suffix in ['.docx']:
        try:
            import docx
            doc = docx.Document(filepath)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except ImportError:
            raise HTTPException(status_code=500, detail="python-docx not installed. Install with: pip install python-docx")
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

# API Endpoints
@app.get("/")
async def root():
    return {
        "service": "Company AI RAG API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload - Upload documents",
            "search": "/search - Search for relevant context",
            "documents": "/documents - List all documents",
            "delete": "/delete/{doc_id} - Delete a document"
        }
    }

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = "general",
    uploaded_by: Optional[str] = None,
    background_tasks: BackgroundTasks = None
):
    """Upload and process a document"""
    
    # Save uploaded file
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, 'wb') as f:
        content = await file.read()
        f.write(content)
    
    # Process in background
    background_tasks.add_task(process_document, file_path, doc_type, uploaded_by)
    
    return {
        "status": "uploaded",
        "filename": file.filename,
        "message": "Document is being processed in background"
    }

async def process_document(file_path: Path, doc_type: str, uploaded_by: Optional[str]):
    """Process document: extract text, chunk, embed, and store"""
    try:
        # Extract text
        text = extract_text_from_file(file_path)
        
        # Chunk text
        chunks = chunk_text(text)
        
        # Generate embeddings and prepare data
        chunk_ids = []
        embeddings = []
        texts = []
        filenames = []
        doc_types = []
        chunk_indices = []
        
        filename_hash = hashlib.md5(file_path.name.encode()).hexdigest()[:8]
        
        for idx, chunk in enumerate(chunks):
            if len(chunk.strip()) < 50:  # Skip very short chunks
                continue
            
            chunk_id = f"{filename_hash}_{idx}"
            embedding = get_embedding(chunk)
            
            chunk_ids.append(chunk_id)
            embeddings.append(embedding)
            texts.append(chunk[:8000])  # Truncate if needed
            filenames.append(file_path.name)
            doc_types.append(doc_type)
            chunk_indices.append(idx)
        
        # Insert into Milvus
        if chunk_ids:
            data = [
                chunk_ids,
                embeddings,
                texts,
                filenames,
                doc_types,
                chunk_indices
            ]
            collection.insert(data)
            collection.flush()
            print(f"Inserted {len(chunk_ids)} chunks from {file_path.name}")
        
    except Exception as e:
        print(f"Error processing {file_path.name}: {e}")

@app.post("/search", response_model=List[ChunkResponse])
async def search_documents(query: SearchQuery):
    """Search for relevant document chunks"""
    try:
        # Generate query embedding
        query_embedding = get_embedding(query.query)
        
        # Search parameters
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        
        # Perform search
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=query.top_k,
            output_fields=["text", "filename", "doc_type", "chunk_index"]
        )
        
        # Format results
        response = []
        for hits in results:
            for hit in hits:
                response.append(ChunkResponse(
                    chunk_id=hit.id,
                    text=hit.entity.get("text"),
                    metadata={
                        "filename": hit.entity.get("filename"),
                        "doc_type": hit.entity.get("doc_type"),
                        "chunk_index": hit.entity.get("chunk_index")
                    },
                    score=float(hit.score)
                ))
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

@app.get("/documents")
async def list_documents():
    """List all uploaded documents"""
    try:
        # Query to get unique filenames
        results = collection.query(
            expr="chunk_index >= 0",
            output_fields=["filename", "doc_type"],
            limit=1000
        )
        
        # Get unique documents
        docs = {}
        for result in results:
            filename = result.get("filename")
            if filename not in docs:
                docs[filename] = {
                    "filename": filename,
                    "doc_type": result.get("doc_type")
                }
        
        return {"documents": list(docs.values()), "count": len(docs)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {e}")

@app.delete("/delete/{filename}")
async def delete_document(filename: str):
    """Delete all chunks of a document"""
    try:
        expr = f'filename == "{filename}"'
        collection.delete(expr)
        collection.flush()
        
        return {"status": "deleted", "filename": filename}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Milvus connection
        milvus_status = "connected" if collection else "disconnected"
        
        # Check Ollama
        ollama_status = "disconnected"
        try:
            response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
            if response.status_code == 200:
                ollama_status = "connected"
        except:
            pass
        
        return {
            "status": "healthy",
            "milvus": milvus_status,
            "ollama": ollama_status,
            "collection": COLLECTION_NAME
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)