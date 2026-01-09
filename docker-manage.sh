#!/bin/bash
# RAG Chatbot Docker Management Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_requirements() {
    log_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    log_success "All prerequisites are installed"
}

# Build images
build() {
    log_info "Building Docker images..."
    docker-compose build
    log_success "Images built successfully"
}

# Build specific service
build_service() {
    local service=$1
    if [ -z "$service" ]; then
        log_error "Please specify a service: api or ui"
        return 1
    fi
    log_info "Building $service service..."
    docker-compose build "$service" --no-cache
    log_success "$service service built successfully"
}

# Start services
up() {
    log_info "Starting services..."
    docker-compose up -d
    log_success "Services started"
    sleep 3
    status
}

# Stop services
down() {
    log_info "Stopping services..."
    docker-compose down
    log_success "Services stopped"
}

# View status
status() {
    log_info "Service status:"
    docker-compose ps
}

# View logs
logs() {
    local service=$1
    if [ -z "$service" ]; then
        log_info "Showing all logs (Ctrl+C to exit)..."
        docker-compose logs -f
    else
        log_info "Showing $service logs (Ctrl+C to exit)..."
        docker-compose logs -f "$service"
    fi
}

# Initialize Ollama models
init_ollama() {
    log_warning "Ollama is no longer needed - using Deepseek API for embeddings"
    echo "Services are already initialized with Deepseek API"
}

# Load knowledge base
load_data() {
    log_info "Loading knowledge base..."
    docker-compose exec -T api python load_data.py
    log_success "Knowledge base loaded"
}

# Execute command in container
exec_cmd() {
    local service=$1
    shift
    local cmd="$@"
    
    if [ -z "$service" ] || [ -z "$cmd" ]; then
        log_error "Usage: $0 exec <service> <command>"
        return 1
    fi
    
    docker-compose exec -T "$service" $cmd
}

# Health check
health() {
    log_info "Checking service health..."
    
    echo -n "API: "
    if curl -s http://localhost:8000/health > /dev/null; then
        log_success "Healthy"
    else
        log_error "Unhealthy"
    fi
    
    echo -n "Ollama: "
    if curl -s http://localhost:11434/api/tags > /dev/null; then
        log_success "Healthy"
    else
        log_error "Unhealthy"
    fi
    
    echo -n "UI: "
    if curl -s http://localhost:8501 > /dev/null; then
        log_success "Healthy"
    else
        log_error "Unhealthy"
    fi
}

# Restart service
restart() {
    local service=$1
    if [ -z "$service" ]; then
        log_info "Restarting all services..."
        docker-compose restart
    else
        log_info "Restarting $service..."
        docker-compose restart "$service"
    fi
    log_success "Services restarted"
}

# Clean up
clean() {
    log_warning "This will remove all containers, volumes, and networks"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        log_success "Cleaned up"
    else
        log_info "Cleanup cancelled"
    fi
}

# Backup
backup() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="backup_chroma_${timestamp}.tar.gz"
    
    log_info "Backing up Chroma database to $backup_file..."
    docker cp rag-api:/app/chroma_langchain_db ./chroma_langchain_db_backup_${timestamp}
    log_success "Backup created in ./chroma_langchain_db_backup_${timestamp}"
}

# Show help
show_help() {
    cat << EOF
${BLUE}RAG Chatbot Docker Management Script${NC}

Usage: $0 <command> [options]

Commands:
    ${GREEN}setup${NC}           Initial setup (check requirements)
    ${GREEN}build${NC}           Build Docker images
    ${GREEN}build api|ui${NC}    Build specific service
    ${GREEN}up${NC}              Start all services
    ${GREEN}down${NC}            Stop all services
    ${GREEN}restart${NC}         Restart all services (or specific: restart api)
    ${GREEN}status${NC}          Show service status
    ${GREEN}logs${NC}            View logs (all or specific: logs api)
    ${GREEN}health${NC}          Check service health
    ${GREEN}load-data${NC}       Load knowledge base documents
    ${GREEN}exec <svc> <cmd>${NC} Execute command in container
    ${GREEN}backup${NC}          Backup Chroma database
    ${GREEN}clean${NC}           Remove all containers and volumes
    ${GREEN}help${NC}            Show this help message

Examples:
    $0 setup                 # Initial check
    $0 build                # Build all images
    $0 up                   # Start services
    $0 init-ollama          # Download models (first time only)
    $0 load-data            # Load your documents
    $0 logs api             # View API logs
    $0 exec api bash        # Get shell in API container
    $0 health               # Check all services
    $0 down                 # Stop services

Services:
    - api         FastAPI backend (port 8000)
    - ui          Streamlit UI (port 8501)
    - ollama      LLM and embedding service (port 11434)

URLs (after starting services):
    - UI:    http://localhost:8501
    - API:   http://localhost:8000
    - Docs:  http://localhost:8000/docs

EOF
}

# Main script
main() {
    local cmd=$1
    
    case "$cmd" in
        setup)
            check_requirements
            ;;
        build)
            check_requirements
            build_service "$2"
            if [ -z "$2" ]; then
                build
            fi
            ;;
        up)
            up
            ;;
        down)
            down
            ;;
        restart)
            restart "$2"
            ;;
        status)
            status
            ;;
        logs)
            logs "$2"
            ;;
        health)
            health
            ;;
        load-data)
            load_data
            ;;
        exec)
            exec_cmd "$2" "${@:3}"
            ;;
        backup)
            backup
            ;;
        clean)
            clean
            ;;
        help|--help|-h|"")
            show_help
            ;;
        *)
            log_error "Unknown command: $cmd"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
