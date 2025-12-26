#!/bin/bash

# Setup script for AI Agent with Model Invocation
# This script helps you quickly set up the project

set -e  # Exit on error

echo "🚀 Setting up AI Agent with Model Invocation..."
echo ""

# Check Python version
echo "📋 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Found Python $PYTHON_VERSION"

if [[ $(echo "$PYTHON_VERSION < 3.11" | bc -l) -eq 1 ]]; then
    echo "⚠️  Warning: Python 3.11+ is recommended, you have $PYTHON_VERSION"
fi

echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"

echo ""

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"

echo ""

# Setup .env file
if [ ! -f ".env" ]; then
    echo "⚙️  Setting up .env file..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✅ Created .env file from env.example"
        echo ""
        echo "⚠️  IMPORTANT: Please edit .env and add your API keys!"
        echo "   You need at least one provider configured:"
        echo "   - OpenAI: https://platform.openai.com/api-keys"
        echo "   - DeepSeek: https://platform.deepseek.com/"
        echo "   - Anthropic: https://console.anthropic.com/"
    else
        echo "⚠️  Warning: env.example not found. Please create .env manually."
    fi
else
    echo "✅ .env file already exists"
fi

echo ""

# Create docs directory if it doesn't exist
if [ ! -d "docs" ]; then
    mkdir -p docs
    echo "✅ Created docs directory"
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "📖 Next steps:"
echo "   1. Edit .env file and add your API keys"
echo "   2. Run: source venv/bin/activate (if not already activated)"
echo "   3. Run: chainlit run app.py -w"
echo "   4. Open: http://localhost:8000"
echo ""
echo "📚 For more information:"
echo "   - Quick Start: docs/QUICK_START.md"
echo "   - Configuration: docs/CONFIGURATION.md"
echo "   - Full README: README.md"
echo ""
echo "Happy chatting! 🤖"

