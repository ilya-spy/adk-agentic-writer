#!/bin/bash
set -e

echo "🚀 Setting up ADK Agentic Writer..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python $required_version or higher is required. Found Python $python_version"
    exit 1
fi

echo "✅ Python version check passed"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install backend dependencies
echo "📥 Installing backend dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup frontend
if command -v npm &> /dev/null; then
    echo "📥 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
    echo "✅ Frontend setup complete"
else
    echo "⚠️  npm not found. Skipping frontend setup."
    echo "   Install Node.js to set up the frontend."
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "To get started:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Start the backend: make run-backend"
echo "  3. In a new terminal, start the frontend: make run-frontend"
echo ""
echo "Or use Docker Compose: make docker-up"
echo ""
echo "Visit http://localhost:3000 to access the application"
echo "API docs available at http://localhost:8000/docs"
