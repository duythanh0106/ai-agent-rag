# 🐳 Docker Deployment - RAG Chatbot

## 🚀 Quick Start (3 Steps)

### 1️⃣ Configure Environment
```bash
cp .env.example .env
# Edit .env and add your DEEPSEEK_API_KEY
```

### 2️⃣ Start Services
```bash
# Linux/Mac
chmod +x docker-manage.sh
./docker-manage.sh setup
./docker-manage.sh build
./docker-manage.sh up
./docker-manage.sh init-ollama    # First time only (5-10 mins)

# Windows
docker-manage.bat setup
docker-manage.bat build
docker-manage.bat up
docker-manage.bat init-ollama     # First time only (5-10 mins)

# Or use docker-compose directly
docker-compose up -d
docker-compose exec ollama ollama pull embeddinggemma
docker-compose exec ollama ollama pull llama3.1:8b
```

### 3️⃣ Load Your Documents
```bash
# Put PDF/DOCX files in ./Knowledge-Base/
./docker-manage.sh load-data

# Or directly
docker-compose exec api python load_data.py
```

## 🌐 Access Services

| Service | URL | Purpose |
|---------|-----|---------|
| Streamlit UI | http://localhost:8501 | Chat interface |
| FastAPI | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Interactive documentation |
| Ollama | http://localhost:11434 | Local LLM service |

## 📋 Useful Commands

```bash
# View all services status
./docker-manage.sh status
docker-compose ps

# View logs
./docker-manage.sh logs              # All logs
./docker-manage.sh logs api          # API logs only
docker-compose logs -f

# Health check
./docker-manage.sh health

# Restart service
./docker-manage.sh restart api

# Execute command in container
./docker-manage.sh exec api bash     # Get shell access

# Backup database
./docker-manage.sh backup

# Stop all services
./docker-manage.sh down
docker-compose down

# Clean everything (careful!)
./docker-manage.sh clean
docker-compose down -v
```

## 📁 Project Structure

```
RAG/
├── api.py                      # FastAPI backend
├── chat.py                     # Streamlit UI
├── load_data.py                # Data ingestion script
├── pdf_loader.py               # PDF processing
├── docx_loader.py              # DOCX processing
├── Dockerfile.api              # API container definition
├── Dockerfile.ui               # UI container definition
├── docker-compose.yml          # Multi-container orchestration
├── docker-manage.sh            # Linux/Mac helper script
├── docker-manage.bat           # Windows helper script
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── DEPLOYMENT.md               # Detailed deployment guide
├── Knowledge-Base/             # Your documents (PDFs, DOCX)
├── chroma_langchain_db/        # Vector database (auto-created)
└── data/                       # Input data
```

## 🔧 Environment Variables

Create `.env` file (copy from `.env.example`):

```env
# Required: Your Deepseek API key
DEEPSEEK_API_KEY=your_key_here

# Optional: Ollama configuration
OLLAMA_HOST=http://ollama:11434

# Optional: Database paths
CHROMA_PATH=./chroma_langchain_db
DATA_PATH=/data

# Optional: Model selection
EMBEDDING_MODEL=embeddinggemma
LLM_MODEL=llama3.1:8b
```

## 🐛 Troubleshooting

### Services won't start?
```bash
# Check logs
docker-compose logs

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

### Ollama models not loading?
```bash
# Manual pull
docker-compose exec ollama ollama list
docker-compose exec ollama ollama pull embeddinggemma
docker-compose exec ollama ollama pull llama3.1:8b
```

### Port already in use?
```bash
# Edit docker-compose.yml and change ports:
# Change "8000:8000" to "8000:8001", etc.
```

### Memory/CPU issues?
- Reduce model size: Use `mistral` or `llama3.2` instead
- Check resources: `docker stats`
- Add limits in docker-compose.yml

## 📦 Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- Docker Hub/ECR registry setup
- Kubernetes deployment
- Reverse proxy (Nginx)
- Security best practices
- Performance optimization
- Monitoring & logging

## 📚 API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Query with sources
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Your question here", "k": 10}'

# Simple query (answer only)
curl -X POST http://localhost:8000/query/simple \
  -H "Content-Type: application/json" \
  -d '{"question": "Your question here"}'

# Database stats
curl http://localhost:8000/stats

# API documentation
open http://localhost:8000/docs
```

## ⚙️ Customization

### Change Models
Edit `docker-compose.yml`:
```yaml
environment:
  - EMBEDDING_MODEL=nomic-embed-text
  - LLM_MODEL=mistral
```

Then:
```bash
docker-compose exec ollama ollama pull nomic-embed-text
docker-compose exec ollama ollama pull mistral
docker-compose restart api
```

### Add More Services
Add to `docker-compose.yml`:
```yaml
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=password
```

### Modify Chunk Settings
Edit `load_data.py`:
```python
chunk_size=1500      # Increase for larger chunks
chunk_overlap=300    # Increase for more overlap
```

Then reload:
```bash
./docker-manage.sh load-data --reset
```

## 🔐 Security Notes

1. **Never commit .env file** - Use `.env.example` instead
2. **Rotate API keys** regularly
3. **Use HTTPS** in production (reverse proxy)
4. **Limit API access** - Add authentication
5. **Backup database** regularly: `./docker-manage.sh backup`

## 📞 Support

For issues:
1. Check logs: `docker-compose logs -f`
2. Check health: `./docker-manage.sh health`
3. Review [DEPLOYMENT.md](DEPLOYMENT.md)
4. Check individual service logs:
   - API: `docker-compose logs api`
   - UI: `docker-compose logs ui`
   - Ollama: `docker-compose logs ollama`

## 📄 License

Same as parent project

---

**Ready to deploy?** Start with `./docker-manage.sh up` 🚀
