#!/bin/bash
# init.sh - Idempotent setup script for daily_stock_analysis project
# Safe to re-run multiple times. Sets up Python venv, installs deps,
# initializes DB, installs frontend, and runs smoke tests.

set -e

echo "======================================="
echo "Daily Stock Analysis - Environment Setup"
echo "======================================="

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ── Phase 1: Python environment ──────────────────────────────────────────
print_info "Phase 1: Checking Python environment..."

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.10+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
print_info "Found Python $PYTHON_VERSION"

if [ ! -d ".venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv .venv
    print_info "Virtual environment created"
else
    print_info "Virtual environment already exists"
fi

# shellcheck disable=SC1091
source .venv/bin/activate

# ── Phase 2: Python dependencies ─────────────────────────────────────────
print_info "Phase 2: Installing Python dependencies..."

if [ -f "requirements.txt" ]; then
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    print_info "Python dependencies installed"
else
    print_warn "requirements.txt not found, skipping"
fi

# ── Phase 3: Node.js / Frontend ──────────────────────────────────────────
print_info "Phase 3: Checking Node.js environment..."

if [ -d "apps/dsa-web" ]; then
    if ! command -v node &> /dev/null; then
        print_warn "Node.js is not installed. Skipping frontend setup."
        print_warn "Install Node.js 18+ to set up the frontend."
    else
        NODE_VERSION=$(node --version)
        print_info "Found Node.js $NODE_VERSION"

        if [ -f "apps/dsa-web/package.json" ]; then
            print_info "Installing frontend dependencies..."
            cd apps/dsa-web
            npm install --silent
            print_info "Frontend dependencies installed"
            cd "$PROJECT_ROOT"
        else
            print_warn "package.json not found in apps/dsa-web, skipping"
        fi
    fi
else
    print_warn "Frontend directory (apps/dsa-web) not found, skipping"
fi

# ── Phase 4: Database initialization ─────────────────────────────────────
print_info "Phase 4: Initializing database..."

python3 -c "
import sys, os
sys.path.insert(0, '$PROJECT_ROOT')
os.chdir('$PROJECT_ROOT')
from src.config import setup_env
setup_env()
from src.storage import DatabaseManager
try:
    db = DatabaseManager.get_instance()
    db.init_db()
    print('Database initialized successfully')
except Exception as e:
    print(f'Database initialization failed: {e}')
    sys.exit(1)
"

# ── Phase 5: Environment config ──────────────────────────────────────────
print_info "Phase 5: Checking environment configuration..."

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        print_info "Copying .env.example to .env..."
        cp .env.example .env
        print_warn "Please edit .env with your API keys before running the application"
    else
        print_warn "No .env or .env.example found"
    fi
else
    print_info ".env file exists"
fi

# ── Phase 6: Smoke tests ─────────────────────────────────────────────────
print_info "Phase 6: Running smoke tests..."

print_info "  Python syntax check (core modules)..."
python3 -m py_compile main.py
python3 -m py_compile server.py
python3 -m py_compile src/config.py
python3 -m py_compile src/storage.py
python3 -m py_compile src/analyzer.py
python3 -m py_compile api/app.py
print_info "  Syntax check passed"

print_info "  Testing critical imports..."
python3 -c "
import fastapi, sqlalchemy, pandas, litellm
from src.config import get_config
from src.storage import DatabaseManager
from api.app import create_app
from data_provider import DataFetcherManager
print('All critical imports OK')
" || {
    print_error "Import test failed"
    exit 1
}

print_info "  Testing database connection..."
python3 -c "
from src.config import setup_env
setup_env()
from src.storage import DatabaseManager
db = DatabaseManager.get_instance()
with db.get_session() as session:
    print('Database connection OK')
" || {
    print_error "Database connection test failed"
    exit 1
}

echo ""
echo "======================================="
print_info "Environment setup completed successfully!"
echo "======================================="
echo ""
echo "Next steps:"
echo "  1. Edit .env with your API keys (see .env.example)"
echo "  2. Start the development server:"
echo "     make dev-backend           # Backend on :8000"
echo "     make dev-frontend          # Frontend on :5173"
echo "     python main.py --serve-only  # Full stack (auto-builds frontend)"
echo "  3. Run tests:"
echo "     make test-backend          # Backend tests"
echo "     make test-quick            # Quick check (both)"
echo "     make check                 # Full lint + type + test"
echo ""
echo "For more information, see README.md"
echo ""
