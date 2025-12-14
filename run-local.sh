#!/bin/bash
set -e

echo "🚀 Starting GlueLinks API locally..."

# Check if .env.local exists
if [ ! -f .env.local ]; then
    echo "❌ .env.local not found. Creating from template..."
    cp .env.local.template .env.local
    echo "✅ Created .env.local - please update with your values"
    exit 1
fi

# Start Valkey
echo "📦 Starting Valkey container..."
docker-compose up -d valkey

# Wait for Valkey to be ready
echo "⏳ Waiting for Valkey to be ready..."
until docker-compose exec -T valkey valkey-cli ping 2>/dev/null | grep -q PONG; do
    sleep 1
done
echo "✅ Valkey is ready"

# Export environment variables
echo "🔧 Loading environment variables..."
export $(cat .env.local | grep -v '^#' | xargs)

# Run the app
echo "🚀 Starting FastAPI server..."
echo "📍 API will be available at: http://localhost:8000"
echo "📍 API docs at: http://localhost:8000/docs"
echo ""
pipenv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
