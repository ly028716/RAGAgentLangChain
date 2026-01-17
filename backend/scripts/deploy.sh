#!/bin/bash
# Deployment helper script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "AI Assistant Backend Deployment Script"
echo "=========================================="

# Function to display usage
usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  init        - Initialize database and seed data"
    echo "  start       - Start all services"
    echo "  stop        - Stop all services"
    echo "  restart     - Restart all services"
    echo "  logs        - View logs"
    echo "  build       - Build Docker images"
    echo "  clean       - Clean up containers and volumes"
    echo "  backup      - Backup database"
    echo "  help        - Display this help message"
    exit 1
}

# Check if .env file exists
check_env() {
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        echo "Error: .env file not found!"
        echo "Please copy .env.docker to .env and configure it:"
        echo "  cp .env.docker .env"
        echo "  nano .env"
        exit 1
    fi
}

# Initialize database
init_db() {
    echo "Initializing database..."
    cd "$PROJECT_DIR"
    docker-compose up -d mysql redis
    sleep 10
    docker-compose run --rm backend python scripts/init_db.py
    docker-compose run --rm backend python scripts/seed_data.py
    echo "Database initialization completed!"
}

# Start services
start_services() {
    echo "Starting services..."
    cd "$PROJECT_DIR"
    docker-compose up -d
    echo "Services started!"
    echo "Backend API: http://localhost:8000"
    echo "API Docs: http://localhost:8000/docs"
    echo "Metrics: http://localhost:9090/metrics"
}

# Stop services
stop_services() {
    echo "Stopping services..."
    cd "$PROJECT_DIR"
    docker-compose down
    echo "Services stopped!"
}

# Restart services
restart_services() {
    echo "Restarting services..."
    stop_services
    start_services
}

# View logs
view_logs() {
    cd "$PROJECT_DIR"
    docker-compose logs -f
}

# Build images
build_images() {
    echo "Building Docker images..."
    cd "$PROJECT_DIR"
    docker-compose build
    echo "Build completed!"
}

# Clean up
clean_up() {
    echo "Warning: This will remove all containers, volumes, and data!"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        cd "$PROJECT_DIR"
        docker-compose down -v
        echo "Cleanup completed!"
    else
        echo "Cleanup cancelled."
    fi
}

# Backup database
backup_db() {
    echo "Backing up database..."
    cd "$PROJECT_DIR"
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    docker-compose exec -T mysql mysqldump -u root -p${MYSQL_ROOT_PASSWORD:-rootpassword} ai_assistant > "$BACKUP_FILE"
    echo "Database backed up to: $BACKUP_FILE"
}

# Main script logic
case "${1:-}" in
    init)
        check_env
        init_db
        ;;
    start)
        check_env
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        check_env
        restart_services
        ;;
    logs)
        view_logs
        ;;
    build)
        build_images
        ;;
    clean)
        clean_up
        ;;
    backup)
        backup_db
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        echo "Error: Unknown command '${1:-}'"
        echo ""
        usage
        ;;
esac
