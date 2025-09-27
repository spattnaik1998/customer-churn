#!/bin/bash

# Customer Churn Prediction - Docker Startup Script

echo "🚀 Starting Customer Churn Prediction Application..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if model exists
if [ ! -f "models/churn_model.pkl" ]; then
    echo "📊 Training model first..."
    cd src
    python train_model.py
    cd ..
fi

# Build and start services
echo "🏗️  Building Docker images..."
docker-compose build

echo "🎯 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "🔍 Checking service status..."
docker-compose ps

echo ""
echo "✅ Application is running!"
echo ""
echo "🌐 Access the application:"
echo "   Frontend (Streamlit): http://localhost"
echo "   API Documentation:    http://localhost/api/docs"
echo "   Health Check:         http://localhost/health"
echo ""
echo "📊 To stop the application:"
echo "   docker-compose down"
echo ""
echo "📝 To view logs:"
echo "   docker-compose logs -f"