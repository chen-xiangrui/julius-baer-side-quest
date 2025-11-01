#!/usr/bin/env bash
#
# Quick start script for Modern Banking Client
#

set -e

echo "🏦 Modern Banking Client - Quick Start"
echo "======================================"
echo ""

# Check if server is running
echo "📡 Checking if banking server is running..."
if curl -s http://localhost:8123/accounts > /dev/null 2>&1; then
    echo "✅ Server is running at http://localhost:8123"
else
    echo "⚠️  Server not detected. Starting server..."
    docker run -d -p 8123:8123 singhacksbjb/sidequest-server:latest
    echo "⏳ Waiting for server to start..."
    sleep 3
    echo "✅ Server started successfully"
fi

echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment exists"
fi

echo ""

# Activate virtual environment and install dependencies
echo "📥 Installing dependencies..."
source venv/bin/activate
pip install -q -r requirements.txt
echo "✅ Dependencies installed"

echo ""
echo "🚀 Running banking client..."
echo "======================================"
echo ""

# Run the client with provided arguments or defaults
if [ $# -eq 0 ]; then
    python banking_client.py --from ACC1000 --to ACC1001 --amount 100.00
else
    python banking_client.py "$@"
fi

echo ""
echo "======================================"
echo "✅ Script completed successfully!"
echo ""
echo "💡 Usage examples:"
echo "  ./run.sh --from ACC1000 --to ACC1001 --amount 50"
echo "  ./run.sh --from ACC1000 --to ACC1001 --amount 100 --auth"
echo "  ./run.sh --from ACC1000 --to ACC1001 --amount 75 --validate"
echo ""
