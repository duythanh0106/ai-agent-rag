#!/bin/bash
# Initial Docker Setup Script

set -e

echo "🚀 RAG Chatbot - Docker Initial Setup"
echo "======================================"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env created. Please edit it with your DEEPSEEK_API_KEY"
    echo "   Run: nano .env"
    echo ""
    read -p "Press Enter when you've updated .env..."
else
    echo "✅ .env file exists"
fi

# Check DEEPSEEK_API_KEY
if grep -q "your_deepseek_api_key_here" .env; then
    echo "❌ DEEPSEEK_API_KEY not set in .env"
    echo "   Please edit .env and set your API key"
    exit 1
fi

echo ""
echo "📦 Checking Docker installation..."
docker --version && echo "✅ Docker installed" || (echo "❌ Docker not found" && exit 1)
docker-compose --version && echo "✅ Docker Compose installed" || (echo "❌ Docker Compose not found" && exit 1)

echo ""
echo "🏗️  Building Docker images..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "📥 Starting services..."
docker-compose up -d

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Place your PDF/DOCX files in ./Knowledge-Base/"
echo "   2. Run: docker-compose exec api python load_data.py"
echo "   3. Access:"
echo "      - Streamlit UI: http://localhost:8501"
echo "      - FastAPI:      http://localhost:8000"
echo "      - API Docs:     http://localhost:8000/docs"
echo ""
echo "📖 For more help, see DOCKER_README.md"
echo ""
echo "View logs: docker-compose logs -f"
echo "Stop services: docker-compose down"
