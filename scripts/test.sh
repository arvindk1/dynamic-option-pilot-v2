#!/bin/bash

# Dynamic Option Pilot v2.0 Test Script
# Usage: ./scripts/test.sh [test_type]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_TYPE=${1:-all}

echo -e "${BLUE}🧪 Dynamic Option Pilot v2.0 Test Suite${NC}"
echo -e "${BLUE}Test type: ${TEST_TYPE}${NC}"

# Function to run tests with proper environment
run_tests() {
    cd "$PROJECT_ROOT/backend"
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}❌ Virtual environment not found. Run ./scripts/setup.sh first${NC}"
        exit 1
    fi
    
    # Set test environment
    export ENVIRONMENT=testing
    export DATABASE_URL=sqlite:///./test.db
    export PYTHONPATH="$PROJECT_ROOT/backend:$PYTHONPATH"
}

# Function to create test database
setup_test_db() {
    echo -e "${YELLOW}🗃️ Setting up test database...${NC}"
    # Remove existing test database
    rm -f "$PROJECT_ROOT/backend/test.db"
    # In future: run migrations
    # python -m alembic upgrade head
}

# Function to run unit tests
run_unit_tests() {
    echo -e "\n${BLUE}🔬 Running unit tests...${NC}"
    python -m pytest tests/unit/ -v --tb=short
}

# Function to run integration tests
run_integration_tests() {
    echo -e "\n${BLUE}🔗 Running integration tests...${NC}"
    python -m pytest tests/integration/ -v --tb=short
}

# Function to run performance tests
run_performance_tests() {
    echo -e "\n${BLUE}⚡ Running performance tests...${NC}"
    python -m pytest tests/performance/ -v --tb=short
}

# Function to run tests with coverage
run_coverage_tests() {
    echo -e "\n${BLUE}📊 Running tests with coverage...${NC}"
    python -m pytest --cov=. --cov-report=html --cov-report=term-missing
    echo -e "${GREEN}✅ Coverage report generated in htmlcov/index.html${NC}"
}

# Function to run linting
run_linting() {
    echo -e "\n${BLUE}🔍 Running code linting...${NC}"
    
    echo -e "${YELLOW}📏 Running flake8...${NC}"
    python -m flake8 . --exclude=venv,htmlcov --max-line-length=88 --extend-ignore=E203,W503
    
    echo -e "${YELLOW}🎨 Running black (check only)...${NC}"
    python -m black . --check --exclude=venv
    
    echo -e "${YELLOW}🔎 Running mypy...${NC}"
    python -m mypy . --exclude=venv --ignore-missing-imports
    
    echo -e "${GREEN}✅ Linting complete${NC}"
}

# Function to run quick smoke tests
run_smoke_tests() {
    echo -e "\n${BLUE}💨 Running smoke tests...${NC}"
    
    # Test basic imports
    python -c "
import sys
sys.path.insert(0, '.')
from core.orchestrator.plugin_registry import PluginRegistry
from plugins.data.yfinance_provider import YFinanceProvider
from plugins.analysis.technical_analyzer import TechnicalAnalyzer
print('✅ All imports successful')
"
    
    # Test basic plugin creation
    python -c "
import sys, asyncio
sys.path.insert(0, '.')
from core.orchestrator.plugin_registry import PluginRegistry
from plugins.data.yfinance_provider import YFinanceProvider

async def test():
    registry = PluginRegistry()
    registry.register_plugin_class(YFinanceProvider)
    plugin = await registry.create_plugin('yfinance_provider')
    print(f'✅ Plugin created: {plugin.metadata.name}')

asyncio.run(test())
"
    
    echo -e "${GREEN}✅ Smoke tests passed${NC}"
}

# Function to create test files if they don't exist
create_test_structure() {
    echo -e "${YELLOW}📁 Ensuring test structure exists...${NC}"
    
    mkdir -p "$PROJECT_ROOT/backend/tests/unit"
    mkdir -p "$PROJECT_ROOT/backend/tests/integration"
    mkdir -p "$PROJECT_ROOT/backend/tests/performance"
    
    # Create conftest.py if it doesn't exist
    if [ ! -f "$PROJECT_ROOT/backend/tests/conftest.py" ]; then
        cat > "$PROJECT_ROOT/backend/tests/conftest.py" << 'EOF'
"""Test configuration and fixtures."""

import pytest
import asyncio
from typing import Generator

@pytest.fixture
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def plugin_registry():
    """Create a plugin registry for testing."""
    from core.orchestrator.plugin_registry import PluginRegistry
    from core.orchestrator.event_bus import EventBus
    
    event_bus = EventBus()
    registry = PluginRegistry(event_bus)
    
    yield registry
    
    # Cleanup
    await registry.cleanup_all()
EOF
    fi
    
    # Create sample test files if they don't exist
    if [ ! -f "$PROJECT_ROOT/backend/tests/unit/test_plugin_registry.py" ]; then
        cat > "$PROJECT_ROOT/backend/tests/unit/test_plugin_registry.py" << 'EOF'
"""Tests for plugin registry."""

import pytest
from core.orchestrator.plugin_registry import PluginRegistry
from core.orchestrator.event_bus import EventBus
from plugins.data.yfinance_provider import YFinanceProvider

@pytest.mark.asyncio
async def test_plugin_registration():
    """Test plugin registration and creation."""
    event_bus = EventBus()
    registry = PluginRegistry(event_bus)
    
    # Register plugin class
    registry.register_plugin_class(YFinanceProvider)
    
    # Create plugin instance
    plugin = await registry.create_plugin("yfinance_provider")
    
    assert plugin is not None
    assert plugin.metadata.name == "yfinance_provider"
    
    # Cleanup
    await registry.cleanup_all()

@pytest.mark.asyncio
async def test_plugin_lifecycle():
    """Test plugin initialization and cleanup."""
    event_bus = EventBus()
    registry = PluginRegistry(event_bus)
    
    registry.register_plugin_class(YFinanceProvider)
    await registry.create_plugin("yfinance_provider")
    
    # Initialize plugins
    success = await registry.initialize_all()
    assert success is True
    
    # Check plugin status
    status = registry.get_system_status()
    assert status["total_plugins"] == 1
    assert status["active_plugins"] == 1
    
    # Cleanup
    cleanup_success = await registry.cleanup_all()
    assert cleanup_success is True
EOF
    fi
    
    echo -e "${GREEN}✅ Test structure ready${NC}"
}

# Main execution
main() {
    run_tests
    create_test_structure
    setup_test_db
    
    case $TEST_TYPE in
        "unit")
            run_unit_tests
            ;;
        "integration")
            run_integration_tests
            ;;
        "performance")
            run_performance_tests
            ;;
        "coverage")
            run_coverage_tests
            ;;
        "lint")
            run_linting
            ;;
        "smoke")
            run_smoke_tests
            ;;
        "all")
            run_smoke_tests
            run_unit_tests
            run_integration_tests
            run_linting
            echo -e "\n${GREEN}🎉 All tests completed!${NC}"
            ;;
        *)
            echo -e "${RED}❌ Unknown test type: $TEST_TYPE${NC}"
            echo -e "${YELLOW}Available types: unit, integration, performance, coverage, lint, smoke, all${NC}"
            exit 1
            ;;
    esac
}

# Show help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Dynamic Option Pilot v2.0 Test Script"
    echo ""
    echo "Usage: $0 [test_type]"
    echo ""
    echo "Test types:"
    echo "  unit        - Run unit tests only"
    echo "  integration - Run integration tests only"
    echo "  performance - Run performance tests only"
    echo "  coverage    - Run tests with coverage report"
    echo "  lint        - Run code linting (flake8, black, mypy)"
    echo "  smoke       - Run quick smoke tests"
    echo "  all         - Run all tests (default)"
    echo ""
    echo "Examples:"
    echo "  $0          # Run all tests"
    echo "  $0 unit     # Run only unit tests"
    echo "  $0 coverage # Run tests with coverage"
    echo ""
    exit 0
fi

# Run main function
main