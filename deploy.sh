#!/bin/bash

# QuantAgent Deployment Script
# This script helps deploy QuantAgent using Docker

set -e

echo "🚀 QuantAgent Deployment Script"
echo "================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "✏️  Please edit .env and add your API keys:"
    echo "   - OPENAI_API_KEY (for GPT-4o)"
    echo "   - ANTHROPIC_API_KEY (for Claude)"
    echo "   - DASHSCOPE_API_KEY (for Qwen)"
    echo ""
    read -p "Press Enter after updating .env file..."
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data

echo "🏗️  Building Docker image..."
docker-compose build

echo ""
echo "🚀 Starting QuantAgent..."
docker-compose up -d

echo ""
echo "⏳ Waiting for application to start..."
sleep 10

# Check if container is running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "✅ QuantAgent is now running!"
    echo ""
    echo "🌐 Access the web interface at:"
    echo "   http://localhost:5000"
    echo ""
    echo "📊 Useful commands:"
    echo "   ./logs.sh          - View application logs"
    echo "   ./stop.sh          - Stop the application"
    echo "   docker-compose ps  - Check container status"
    echo ""
else
    echo ""
    echo "❌ Failed to start QuantAgent"
    echo "📋 Check logs with: docker-compose logs"
    exit 1
fi
