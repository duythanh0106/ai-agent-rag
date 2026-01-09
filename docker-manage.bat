@echo off
REM RAG Chatbot Docker Management Script for Windows

setlocal enabledelayedexpansion

REM Colors (using ANSI codes)
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM Helper functions
:log_info
    echo [INFO] %~1
    exit /b

:log_success
    echo [SUCCESS] %~1
    exit /b

:log_warning
    echo [WARNING] %~1
    exit /b

:log_error
    echo [ERROR] %~1
    exit /b

REM Main commands
if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="setup" goto setup
if "%1"=="build" goto build
if "%1"=="up" goto up
if "%1"=="down" goto down
if "%1"=="restart" goto restart
if "%1"=="status" goto status
if "%1"=="logs" goto logs
if "%1"=="health" goto health
if "%1"=="init-ollama" goto init_ollama
if "%1"=="load-data" goto load_data
if "%1"=="exec" goto exec_cmd
if "%1"=="backup" goto backup
if "%1"=="clean" goto clean

echo Unknown command: %1
goto help

:setup
    echo Checking prerequisites...
    docker --version >nul 2>&1
    if errorlevel 1 (
        echo Docker is not installed. Please install Docker first.
        exit /b 1
    )
    docker-compose --version >nul 2>&1
    if errorlevel 1 (
        echo Docker Compose is not installed. Please install Docker Compose first.
        exit /b 1
    )
    echo All prerequisites are installed
    exit /b

:build
    if "%2"=="" (
        echo Building all Docker images...
        docker-compose build
    ) else (
        echo Building %2 service...
        docker-compose build %2 --no-cache
    )
    exit /b

:up
    echo Starting services...
    docker-compose up -d
    timeout /t 3 /nobreak
    docker-compose ps
    exit /b

:down
    echo Stopping services...
    docker-compose down
    exit /b

:restart
    if "%2"=="" (
        echo Restarting all services...
        docker-compose restart
    ) else (
        echo Restarting %2...
        docker-compose restart %2
    )
    exit /b

:status
    echo Service status:
    docker-compose ps
    exit /b

:logs
    if "%2"=="" (
        docker-compose logs -f
    ) else (
        docker-compose logs -f %2
    )
    exit /b

:health
    echo Checking service health...
    
    echo Checking API...
    curl -s http://localhost:8000/health >nul
    if errorlevel 1 (
        echo API: Unhealthy
    ) else (
        echo API: Healthy
    )
    
    echo Checking Ollama...
    curl -s http://localhost:11434/api/tags >nul
    if errorlevel 1 (
        echo Ollama: Unhealthy
    ) else (
        echo Ollama: Healthy
    )
    
    echo Checking UI...
    curl -s http://localhost:8501 >nul
    if errorlevel 1 (
        echo UI: Unhealthy
    ) else (
        echo UI: Healthy
    )
    exit /b

:init_ollama
    echo Ollama is no longer needed - using Deepseek API for embeddings
    echo Services are already initialized with Deepseek API
    exit /b

:load_data
    echo Loading knowledge base...
    docker-compose exec -T api python load_data.py
    exit /b

:exec_cmd
    if "%2"=="" (
        echo Usage: %0 exec ^<service^> ^<command^>
        exit /b 1
    )
    docker-compose exec -T %2 %3 %4 %5 %6 %7 %8 %9
    exit /b

:backup
    for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
    for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
    set timestamp=!mydate!_!mytime!
    set backup_file=backup_chroma_!timestamp!.tar.gz
    
    echo Backing up Chroma database to !backup_file!...
    docker cp rag-api:/app/chroma_langchain_db ./chroma_langchain_db_backup_!timestamp!
    echo Backup created in ./chroma_langchain_db_backup_!timestamp!
    exit /b

:clean
    echo This will remove all containers, volumes, and networks
    set /p confirm=Are you sure? (y/N): 
    if /i "!confirm!"=="y" (
        docker-compose down -v
        echo Cleaned up
    ) else (
        echo Cleanup cancelled
    )
    exit /b

:help
    echo RAG Chatbot Docker Management Script
    echo.
    echo Usage: %0 ^<command^> [options]
    echo.
    echo Commands:
    echo   setup           Initial setup (check requirements)
    echo   build           Build Docker images
    echo   build api^|ui   Build specific service
    echo   up              Start all services
    echo   down            Stop all services
    echo   restart         Restart all services (or specific: restart api)
    echo   status          Show service status
    echo   logs            View logs (all or specific: logs api)
    echo   health          Check service health
    echo   load-data       Load knowledge base documents
    echo   exec ^<svc^> ^<cmd^>  Execute command in container
    echo   backup          Backup Chroma database
    echo   clean           Remove all containers and volumes
    echo   help            Show this help message
    echo.
    echo Examples:
    echo   %0 setup                 # Initial check
    echo   %0 build                 # Build all images
    echo   %0 up                    # Start services
    echo   %0 init-ollama           # Download models (first time only)
    echo   %0 load-data             # Load your documents
    echo   %0 logs api              # View API logs
    echo   %0 health                # Check all services
    echo   %0 down                  # Stop services
    echo.
    echo URLs (after starting services):
    echo   - UI:    http://localhost:8501
    echo   - API:   http://localhost:8000
    echo   - Docs:  http://localhost:8000/docs
    exit /b

endlocal
