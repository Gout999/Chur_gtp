#!/bin/bash

# ChurGPT Deployment Script
# Usage: ./deploy.sh [dev|prod]

set -e

ENV=${1:-dev}
echo "🚀 Deploying ChurGPT in $ENV mode..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check environment file
if [ "$ENV" = "prod" ]; then
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from .env.example..."
        cp .env.example .env
        print_warning "Please edit .env file with your production settings before continuing."
        exit 1
    fi
fi

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose -f docker-compose.yml down --remove-orphans 2>/dev/null || true

if [ "$ENV" = "prod" ]; then
    docker-compose -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true
fi

# Build and start containers
if [ "$ENV" = "prod" ]; then
    print_status "Building and starting production containers..."
    docker-compose -f docker-compose.prod.yml up -d --build
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    sleep 5
    
    # Run migrations
    print_status "Running database migrations..."
    docker-compose -f docker-compose.prod.yml exec -T backend alembic upgrade head
else
    print_status "Building and starting development containers..."
    docker-compose up -d --build
    
    # Wait for database
    print_status "Waiting for database to be ready..."
    sleep 3
    
    # Run migrations
    print_status "Running database migrations..."
    docker-compose exec -T backend alembic upgrade head
fi

# Health check
print_status "Performing health checks..."
sleep 2

if curl -s http://localhost:8000/health > /dev/null; then
    print_status "Backend API is healthy!"
else
    print_error "Backend API health check failed"
    exit 1
fi

if [ "$ENV" = "prod" ]; then
    if curl -s http://localhost > /dev/null; then
        print_status "Frontend is accessible!"
    else
        print_error "Frontend health check failed"
        exit 1
    fi
fi

# Print success message
echo ""
echo "========================================"
print_status "ChurGPT deployed successfully!"
echo "========================================"
echo ""

if [ "$ENV" = "prod" ]; then
    echo "Frontend: http://localhost"
    echo "Backend API: http://localhost:8000"
    echo "API Docs: http://localhost:8000/docs"
else
    echo "Backend API: http://localhost:8000"
    echo "API Docs: http://localhost:8000/docs"
    echo "Frontend (dev): Run 'cd frontend && npm run dev' separately"
fi

echo ""
print_status "Logs: docker-compose logs -f"
print_status "Stop: docker-compose down"
echo ""
