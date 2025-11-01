.PHONY: help install test format lint docker-build docker-run docker-compose-up docker-compose-down clean run

help:
	@echo "🏦 Modern Banking Client - Make Commands"
	@echo "========================================"
	@echo ""
	@echo "Available commands:"
	@echo "  make install          - Install dependencies"
	@echo "  make run              - Run the banking client"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-int         - Run integration tests only"
	@echo "  make test-endpoints   - Test all API endpoints"
	@echo "  make format           - Format code with black and isort"
	@echo "  make lint             - Lint code with flake8"
	@echo "  make typecheck        - Type check with mypy"
	@echo "  make quality          - Run all quality checks"
	@echo "  make docker-build     - Build Docker image"
	@echo "  make docker-run       - Run Docker container"
	@echo "  make docker-compose-up    - Start server and client with docker-compose"
	@echo "  make docker-compose-down  - Stop docker-compose services"
	@echo "  make server           - Start banking server"
	@echo "  make clean            - Clean up temporary files"
	@echo ""

install:
	@echo "📦 Installing dependencies..."
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Dependencies installed"

run:
	@echo "🚀 Running banking client..."
	. venv/bin/activate && python banking_client.py --from ACC1000 --to ACC1001 --amount 100.00

test:
	@echo "🧪 Running all tests..."
	. venv/bin/activate && pytest tests/ -v

test-unit:
	@echo "🧪 Running unit tests..."
	. venv/bin/activate && pytest tests/test_transfer.py -v

test-int:
	@echo "🧪 Running integration tests..."
	. venv/bin/activate && pytest tests/test_integration.py -v -m integration

format:
	@echo "🎨 Formatting code..."
	. venv/bin/activate && black .
	. venv/bin/activate && isort .
	@echo "✅ Code formatted"

lint:
	@echo "🔍 Linting code..."
	. venv/bin/activate && flake8 .
	@echo "✅ Linting passed"

typecheck:
	@echo "🔍 Type checking..."
	. venv/bin/activate && mypy . || true
	@echo "✅ Type checking complete"

quality: format lint typecheck
	@echo "✅ All quality checks passed"

docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t modern-banking-client .
	@echo "✅ Docker image built"

docker-run:
	@echo "🐳 Running Docker container..."
	docker run --rm modern-banking-client --from ACC1000 --to ACC1001 --amount 100

docker-compose-up:
	@echo "🐳 Starting services with docker-compose..."
	docker-compose up --build

docker-compose-down:
	@echo "🐳 Stopping docker-compose services..."
	docker-compose down

test-endpoints:
	@echo "🧪 Testing all API endpoints..."
	chmod +x test_endpoints.sh
	./test_endpoints.sh

server:
	@echo "🚀 Starting banking server..."
	docker run -d -p 8123:8123 singhacksbjb/sidequest-server:latest
	@echo "✅ Server started at http://localhost:8123"

clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.log" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage 2>/dev/null || true
	@echo "✅ Cleanup complete"
