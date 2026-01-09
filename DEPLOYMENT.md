# Docker Deployment Guide - RAG Chatbot

## 📋 Prerequisites

- **Docker**: v20.10+
- **Docker Compose**: v1.29+
- **Deepseek API Key**: Get from https://platform.deepseek.com

## 🚀 Quick Start

### 1. Clone/Prepare Environment

```bash
cd /path/to/RAG
```

### 2. Configure Environment Variables

```bash
# Copy example to .env
cp .env.example .env

# Edit .env with your values
# Add your DEEPSEEK_API_KEY
nano .env
```

### 3. Build Images

```bash
# Build all services
docker-compose build

# Or build specific services
docker-compose build api ui
```

### 4. Start Services

```bash
# Start all services in background
docker-compose up -d

# Or with logs visible
docker-compose up

# Wait for Ollama to be ready (~30 seconds)
docker-compose logs ollama
```

### 5. Initialize Ollama Models

```bash
# Pull required models (first time only, ~5-10 minutes)
docker-compose exec ollama ollama pull embeddinggemma
docker-compose exec ollama ollama pull llama3.1:8b
```

### 6. Load Knowledge Base

```bash
# Option A: Using Docker
docker-compose exec api python load_data.py

# Option B: Direct (if running locally)
python load_data.py
```

### 7. Access Services

- **Streamlit UI**: http://localhost:8501
- **FastAPI Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Ollama API**: http://localhost:11434

## 📊 Service Details

### Ollama (LLM & Embeddings)
- **Container**: rag-ollama
- **Port**: 11434
- **Volume**: ollama_data (persisted)
- **Models**:
  - `embeddinggemma` - Embedding model
  - `llama3.1:8b` - LLM model

### FastAPI Backend
- **Container**: rag-api
- **Port**: 8000
- **Endpoints**:
  - `GET /` - Health check
  - `GET /health` - Detailed health check
  - `POST /query` - Query with sources
  - `POST /query/simple` - Simple query
  - `GET /stats` - Database statistics
- **Docs**: http://localhost:8000/docs

### Streamlit UI
- **Container**: rag-ui
- **Port**: 8501
- **Features**: Chat interface, knowledge base management

## 🔧 Common Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f ui
docker-compose logs -f ollama
```

### Stop Services

```bash
# Stop without removing
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove all data (careful!)
docker-compose down -v
```

### Rebuild After Code Changes

```bash
# Rebuild specific service
docker-compose build api --no-cache
docker-compose up -d api

# Or rebuild all
docker-compose build --no-cache
docker-compose up -d
```

### Access Container Shell

```bash
# API container
docker-compose exec api bash

# UI container
docker-compose exec ui bash

# Ollama container
docker-compose exec ollama bash
```

### Check Health

```bash
# All services
docker-compose ps

# Specific endpoint
curl http://localhost:8000/health
curl http://localhost:11434/api/tags
```

## 📦 Production Deployment

### 1. Update docker-compose.yml for Production

```yaml
# Change from build to image pull
services:
  api:
    image: your-registry/rag-api:latest
    # Remove 'build' section
```

### 2. Build and Push Images

```bash
# Login to registry (Docker Hub, AWS ECR, etc.)
docker login

# Build with version tag
docker build -f Dockerfile.api -t your-registry/rag-api:1.0.0 .
docker build -f Dockerfile.ui -t your-registry/rag-ui:1.0.0 .

# Push to registry
docker push your-registry/rag-api:1.0.0
docker push your-registry/rag-ui:1.0.0
```

### 3. Environment Configuration

```bash
# Use .env file or environment variables
export DEEPSEEK_API_KEY="your_key_here"
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Use Docker Secrets (Kubernetes/Swarm)

```bash
# Create secrets
echo "your_api_key" | docker secret create deepseek_api_key -

# Reference in compose file
secrets:
  deepseek_api_key:
    external: true
```

### 5. Networking & Reverse Proxy

```nginx
# Example Nginx config
upstream api {
    server api:8000;
}

upstream ui {
    server ui:8501;
}

server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://api/;
        proxy_set_header Host $host;
    }

    location / {
        proxy_pass http://ui/;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs api

# Common issues:
# - DEEPSEEK_API_KEY not set
# - Port already in use
# - Insufficient resources
```

### Ollama Connection Error

```bash
# Check if Ollama is running
docker-compose ps ollama

# Check health
docker-compose exec ollama curl http://ollama:11434/api/tags

# Restart Ollama
docker-compose restart ollama
```

### High Memory Usage

- Reduce batch size in API
- Use smaller models (llama3.2, mistral)
- Enable GPU if available: `runtime: nvidia` in compose

### Data Persistence Issues

```bash
# Check volume
docker volume ls | grep rag

# Inspect volume
docker volume inspect rag_chroma_data

# Backup data
docker run -v rag_chroma_data:/data -v $(pwd)/backup:/backup \
  alpine tar czf /backup/chroma.tar.gz -C /data .
```

## 🔒 Security Best Practices

1. **API Keys**: Use Docker secrets or environment variable files
2. **Network**: Use `networks` for inter-service communication only
3. **Volumes**: Set proper permissions on mounted volumes
4. **HTTPS**: Use reverse proxy with SSL certificates
5. **Rate Limiting**: Add rate limiting middleware
6. **Authentication**: Implement API authentication if needed

```python
# Example: Add authentication to FastAPI
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/query")
async def query_chatbot(request: QueryRequest, credentials = Depends(security)):
    # Verify credentials
    pass
```

## 📈 Performance Optimization

### 1. Database Optimization

```bash
# Monitor Chroma
docker-compose exec api python -c "
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
db = Chroma(persist_directory='./chroma_langchain_db', 
            embedding_function=OllamaEmbeddings(model='embeddinggemma'))
print(f'Total documents: {db._collection.count()}')
"
```

### 2. Resource Limits

```yaml
# In docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### 3. Caching

```python
# Add caching to frequently accessed queries
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_results(query: str):
    return db.similarity_search(query, k=10)
```

## 📝 Maintenance

### Update Models

```bash
# Update embedding model
docker-compose exec ollama ollama pull embeddinggemma:latest

# Update LLM
docker-compose exec ollama ollama pull llama3.2:latest
```

### Backup Database

```bash
# Backup Chroma database
docker-compose exec api tar czf /tmp/chroma_backup.tar.gz ./chroma_langchain_db
docker cp rag-api:/tmp/chroma_backup.tar.gz ./backup/

# Restore from backup
docker cp ./backup/chroma_backup.tar.gz rag-api:/tmp/
docker-compose exec api tar xzf /tmp/chroma_backup.tar.gz
```

### Monitor Logs

```bash
# Real-time logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Logs since timestamp
docker-compose logs --since 2024-01-01
```

## 📚 Additional Resources

- [Docker Official Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Ollama GitHub](https://github.com/ollama/ollama)
- [LangChain Documentation](https://python.langchain.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
