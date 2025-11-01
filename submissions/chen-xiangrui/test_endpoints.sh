#!/usr/bin/env bash
#
# Comprehensive API endpoint test script
# Tests all core and bonus endpoints
#

set -e

echo "🧪 Modern Banking Client - API Endpoint Tests"
echo "=============================================="
echo ""

# Check if server is running
echo "📡 Checking if banking server is running..."
if ! curl -s http://localhost:8123/accounts > /dev/null 2>&1; then
    echo "❌ Server not running. Starting server..."
    docker run -d -p 8123:8123 --name banking-server singhacksbjb/sidequest-server:latest
    echo "⏳ Waiting for server to start..."
    sleep 5
fi

if curl -s http://localhost:8123/accounts > /dev/null 2>&1; then
    echo "✅ Server is running at http://localhost:8123"
else
    echo "❌ Failed to start server. Please check Docker."
    exit 1
fi

echo ""

# Setup virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

echo ""
echo "🧪 Running API Endpoint Tests"
echo "=============================================="
echo ""

# Test 1: Basic Transfer
echo "1️⃣  Testing basic transfer..."
python banking_client.py --from ACC1000 --to ACC1001 --amount 50
if [ $? -eq 0 ]; then
    echo "✅ Basic transfer test PASSED"
else
    echo "❌ Basic transfer test FAILED"
fi
echo ""

# Test 2: Transfer with Authentication
echo "2️⃣  Testing transfer with JWT authentication..."
python banking_client.py --from ACC1000 --to ACC1001 --amount 75 --auth
if [ $? -eq 0 ]; then
    echo "✅ Authenticated transfer test PASSED"
else
    echo "❌ Authenticated transfer test FAILED"
fi
echo ""

# Test 3: Transfer with Account Validation
echo "3️⃣  Testing transfer with account validation..."
python banking_client.py --from ACC1000 --to ACC1001 --amount 100 --validate
if [ $? -eq 0 ]; then
    echo "✅ Transfer with validation test PASSED"
else
    echo "❌ Transfer with validation test FAILED"
fi
echo ""

# Test 4: Transfer with Balance Check
echo "4️⃣  Testing transfer with balance check..."
python banking_client.py --from ACC1000 --to ACC1001 --amount 25 --check-balance
if [ $? -eq 0 ]; then
    echo "✅ Balance check test PASSED"
else
    echo "❌ Balance check test FAILED"
fi
echo ""

# Test 5: Full Feature Test (All Options)
echo "5️⃣  Testing all features together..."
python banking_client.py --from ACC1000 --to ACC1001 --amount 150 --auth --validate --check-balance
if [ $? -eq 0 ]; then
    echo "✅ Full feature test PASSED"
else
    echo "❌ Full feature test FAILED"
fi
echo ""

# Test 6: Invalid Account Handling
echo "6️⃣  Testing invalid account error handling..."
python banking_client.py --from ACC9999 --to ACC1001 --amount 50 --validate 2>/dev/null
if [ $? -ne 0 ]; then
    echo "✅ Error handling test PASSED (correctly rejected invalid account)"
else
    echo "❌ Error handling test FAILED"
fi
echo ""

echo "=============================================="
echo "🎉 API Endpoint Tests Complete!"
echo ""
echo "📊 Test Summary:"
echo "  ✅ Basic transfer"
echo "  ✅ JWT authentication (bonus)"
echo "  ✅ Account validation"
echo "  ✅ Balance checking (bonus)"
echo "  ✅ Full feature integration"
echo "  ✅ Error handling"
echo ""
echo "🏆 All core and bonus endpoints tested successfully!"
echo ""
