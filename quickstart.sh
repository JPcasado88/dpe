#!/bin/bash

# Dynamic Pricing Engine - Quick Start Script
# This script sets up and runs the entire application

echo "🚀 Dynamic Pricing Engine - Quick Start"
echo "======================================"

# Check prerequisites
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 is not installed. Please install $1 first."
        exit 1
    fi
    echo "✅ $1 is installed"
}

echo ""
echo "Checking prerequisites..."
check_command docker
check_command docker-compose
check_command git

# Create environment file if it doesn't exist
if [ ! -f backend/.env ]; then
    echo ""
    echo "Creating environment configuration..."
    cat > backend/.env << EOL
DATABASE_URL=postgresql://dpe_user:dpe_password@postgres:5432/dynamic_pricing_engine
REDIS_URL=redis://redis:6379
SECRET_KEY=your-secret-key-here-change-in-production
ENVIRONMENT=development
EOL
    echo "✅ Environment file created"
fi

# Build and start services
echo ""
echo "Starting services with Docker Compose..."
docker-compose down 2>/dev/null
docker-compose up -d --build

# Wait for services to be ready
echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check if PostgreSQL is ready
until docker-compose exec -T postgres pg_isready -U dpe_user -d dynamic_pricing_engine > /dev/null 2>&1; do
    echo "⏳ Waiting for PostgreSQL..."
    sleep 2
done
echo "✅ PostgreSQL is ready"

# Check if Redis is ready
until docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; do
    echo "⏳ Waiting for Redis..."
    sleep 2
done
echo "✅ Redis is ready"

# Initialize database with sample data
echo ""
echo "Initializing database with sample data..."
docker-compose exec -T backend python scripts/seed_sample_data.py

# Check services
echo ""
echo "Checking service health..."
API_HEALTH=$(curl -s http://localhost:8000/health || echo "failed")
if [[ $API_HEALTH == *"healthy"* ]]; then
    echo "✅ API is healthy"
else
    echo "⚠️  API health check failed"
fi

# Display access information
echo ""
echo "=========================================="
echo "🎉 Dynamic Pricing Engine is ready!"
echo "=========================================="
echo ""
echo "Access the application:"
echo "  📊 Dashboard: http://localhost:3000"
echo "  📚 API Docs:  http://localhost:8000/docs"
echo "  🔧 Database:  localhost:5432"
echo "  🚀 Redis:     localhost:6379"
echo ""
echo "Default credentials:"
echo "  Database: dpe_user / dpe_password"
echo ""
echo "Quick commands:"
echo "  View logs:    docker-compose logs -f"
echo "  Stop:         docker-compose down"
echo "  Reset data:   docker-compose exec backend python scripts/generate_data.py"
echo ""
echo "Happy pricing! 💰"