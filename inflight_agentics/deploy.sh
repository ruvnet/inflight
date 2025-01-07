#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print status messages
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check prerequisites
echo "Checking prerequisites..."

# Check Docker
if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi
print_status "Docker is installed"

# Check Docker Compose
if ! command_exists docker-compose; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi
print_status "Docker Compose is installed"

# Check if .env exists, if not create from example
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        print_warning "Created .env file from .env.example"
        print_warning "Please edit .env and add your OpenAI API key before continuing"
        exit 1
    else
        print_error ".env.example file not found"
        exit 1
    fi
fi

# Check if OpenAI API key is set
if ! grep -q "^OPENAI_API_KEY=sk-" .env; then
    print_error "OpenAI API key not set in .env file"
    print_warning "Please run ./get_openai_key.sh to configure your API key"
    exit 1
fi
print_status "OpenAI API key configured"

# Stop any running containers
echo "Stopping any running containers..."
docker-compose down

# Remove old containers, networks, and volumes
echo "Cleaning up old deployment..."
docker-compose rm -f
docker system prune -f

# Pull latest images
echo "Pulling latest images..."
docker-compose pull

# Build and start services
echo "Building and starting services..."
docker-compose up --build -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
attempt=1
max_attempts=30
interval=10

while [ $attempt -le $max_attempts ]; do
    if docker-compose ps | grep -q "healthy"; then
        unhealthy_count=$(docker-compose ps | grep -c "unhealthy")
        if [ $unhealthy_count -eq 0 ]; then
            print_status "All services are healthy!"
            echo
            echo "Access services at:"
            echo "- Kafka UI: http://localhost:8080"
            echo "- View logs: docker-compose logs -f"
            exit 0
        fi
    fi
    
    print_warning "Waiting for services to be healthy (Attempt $attempt/$max_attempts)..."
    sleep $interval
    attempt=$((attempt + 1))
done

print_error "Timeout waiting for services to be healthy"
print_warning "Check logs with: docker-compose logs"
exit 1
