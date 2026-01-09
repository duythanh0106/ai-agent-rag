@echo off
REM Initial Docker Setup Script for Windows

echo 🚀 RAG Chatbot - Docker Initial Setup
echo ======================================
echo.

REM Check if .env exists
if not exist ".env" (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ✅ .env created. Please edit it with your DEEPSEEK_API_KEY
    echo.
    pause
) else (
    echo ✅ .env file exists
)

echo.
echo 📦 Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not found
    exit /b 1
)
echo ✅ Docker installed

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose not found
    exit /b 1
)
echo ✅ Docker Compose installed

echo.
echo 🏗️  Building Docker images...
docker-compose build

echo.
echo 🚀 Starting services...
docker-compose up -d

echo.
echo 🚀 Starting services...
docker-compose up -d

echo.
echo ✅ Setup complete!
echo.
echo 📝 Next steps:
echo    1. Place your PDF/DOCX files in ./Knowledge-Base/
echo    2. Run: docker-compose exec api python load_data.py
echo    3. Access:
echo       - Streamlit UI: http://localhost:8501
echo       - FastAPI:      http://localhost:8000
echo       - API Docs:     http://localhost:8000/docs
echo.
echo 📖 For more help, see DOCKER_README.md
echo.
echo View logs: docker-compose logs -f
echo Stop services: docker-compose down
echo.
pause
