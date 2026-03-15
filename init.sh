#!/bin/bash
# init.sh - Idempotent setup script for daily_stock_analysis project
# This script can be safely re-run multiple times

set -e  # Exit on error

echo "======================================="
echo "Daily Stock Analysis - Environment Setup"
echo "======================================="

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Phase 1: Check Python environment
print_info "Phase 1: Checking Python environment..."

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.10+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
print_info "Found Python $PYTHON_VERSION"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv .venv
    print_info "Virtual environment created successfully"
else
    print_info "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source .venv/bin/activate

# Phase 2: Install Python dependencies
print_info "Phase 2: Installing Python dependencies..."

if [ -f "requirements.txt" ]; then
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    print_info "Python dependencies installed successfully"
else
    print_warn "requirements.txt not found, skipping Python dependency installation"
fi

# Phase 3: Check Node.js environment
print_info "Phase 3: Checking Node.js environment..."

if [ -d "apps/dsa-web" ]; then
    if ! command -v node &> /dev/null; then
        print_warn "Node.js is not installed. Skipping frontend setup."
        print_warn "Install Node.js 16+ to set up the frontend."
    else
        NODE_VERSION=$(node --version)
        print_info "Found Node.js $NODE_VERSION"

        # Install npm dependencies
        print_info "Installing frontend dependencies..."
        cd apps/dsa-web

        if [ -f "package.json" ]; then
            npm install --silent
            print_info "Frontend dependencies installed successfully"
        else
            print_warn "package.json not found in apps/dsa-web, skipping frontend setup"
        fi

        cd "$PROJECT_ROOT"
    fi
else
    print_warn "Frontend directory (apps/dsa-web) not found, skipping frontend setup"
fi

# Phase 4: Initialize database if it doesn't exist
print_info "Phase 4: Initializing database..."

python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from src.storage import DatabaseManager
try:
    db = DatabaseManager.get_instance()
    db.init_db()
    print('Database initialized successfully')
except Exception as e:
    print(f'Database initialization failed: {e}')
    sys.exit(1)
"

# Phase 5: Run basic smoke test
print_info "Phase 5: Running basic smoke test..."

# Test Python imports
print_info "Testing Python imports..."
python3 -c "import fastapi; import sqlalchemy; import pandas; print('Python imports OK')" || {
    print_error "Python import test failed"
    exit 1
}

# Test database connection
print_info "Testing database connection..."
python3 -c "
from src.storage import DatabaseManager
db = DatabaseManager.get_instance()
with db.get_session() as session:
    print('Database connection OK')
" || {
    print_error "Database connection test failed"
    exit 1
}

# Test FastAPI app import
print_info "Testing FastAPI app..."
python3 -c "
from api.app import create_app
app = create_app()
print('FastAPI app OK')
" || {
    print_error "FastAPI app test failed"
    exit 1
}

# Phase 6: Check for .env file
print_info "Phase 6: Checking environment configuration..."

if [ ! -f ".env" ]; then
    print_warn ".env file not found"
    if [ -f ".env.example" ]; then
        print_info "Copying .env.example to .env..."
        cp .env.example .env
        print_warn "Please edit .env file with your configuration before running the application"
    else
        print_warn ".env.example not found, skipping .env creation"
    fi
else
    print_info ".env file exists"
fi

echo ""
echo "======================================="
print_info "Environment setup completed successfully!"
echo "======================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Start the development server:"
echo "   - Backend only: python main.py --webui-only"
echo "   - Backend + Scheduler: python main.py --webui"
echo "   - Start all: python main.py --serve"
echo ""
echo "For more information, see README.md"
echo ""
