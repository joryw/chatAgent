#!/bin/bash

# Quick run script for AI Agent
# This script activates the virtual environment and starts the Chainlit app

set -e

echo "🤖 Starting AI Agent..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it from env.example and add your API keys."
    echo "   cp env.example .env"
    echo "   # Then edit .env with your API keys"
    exit 1
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Check if Chainlit is installed
if ! python -c "import chainlit" 2>/dev/null; then
    echo "❌ Chainlit not installed. Please run ./setup.sh first."
    exit 1
fi

# Start Chainlit app
echo "🚀 Starting Chainlit application..."
echo "📱 Open http://localhost:8000 in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

chainlit run app.py -w

