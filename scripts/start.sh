#!/bin/bash

# Dynamic Option Pilot v2.0 Startup Script
# Usage: ./scripts/start.sh [environment]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get environment (default to development)
ENVIRONMENT=${1:-development}
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}🚀 Starting Dynamic Option Pilot v2.0${NC}"
echo -e "${BLUE}Environment: ${ENVIRONMENT}${NC}"
echo -e "${BLUE}Project root: ${PROJECT_ROOT}${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
            echo -e "${GREEN}✅ Python $PYTHON_VERSION detected${NC}"
            return 0
        else
            echo -e "${RED}❌ Python 3.11+ required, found $PYTHON_VERSION${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Python 3 not found${NC}"
        return 1
    fi
}

# Function to setup virtual environment
setup_venv() {
    cd "$PROJECT_ROOT/backend"
    
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
        python3 -m venv venv
    fi
    
    echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
    source venv/bin/activate
    
    echo -e "${YELLOW}📥 Installing/upgrading dependencies...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo -e "${GREEN}✅ Virtual environment ready${NC}"
}

# Function to check database
setup_database() {
    echo -e "${YELLOW}🗃️ Setting up database...${NC}"
    
    # For now, we'll use SQLite, but this can be expanded for other databases
    if [ ! -f "$PROJECT_ROOT/backend/dev.db" ]; then
        echo -e "${YELLOW}📊 Creating database...${NC}"
        # In the future, add alembic migration here
        # python -m alembic upgrade head
    fi
    
    echo -e "${GREEN}✅ Database ready${NC}"
}

# Function to check configuration
check_config() {
    CONFIG_FILE="$PROJECT_ROOT/backend/config/environments/${ENVIRONMENT}.yaml"
    
    if [ -f "$CONFIG_FILE" ]; then
        echo -e "${GREEN}✅ Configuration file found: ${CONFIG_FILE}${NC}"
    else
        echo -e "${RED}❌ Configuration file not found: ${CONFIG_FILE}${NC}"
        echo -e "${YELLOW}Creating default configuration...${NC}"
        cp "$PROJECT_ROOT/backend/config/environments/development.yaml" "$CONFIG_FILE"
    fi
}

# Function to start backend
start_backend() {
    echo -e "${BLUE}🖥️ Starting backend server...${NC}"
    cd "$PROJECT_ROOT/backend"
    
    # Set environment variables
    export ENVIRONMENT="$ENVIRONMENT"
    export PYTHONPATH="$PROJECT_ROOT/backend:$PYTHONPATH"
    
    # Check if port is available
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}⚠️ Port 8000 is already in use${NC}"
        echo -e "${YELLOW}Attempting to stop existing process...${NC}"
        pkill -f "python.*main.py" || true
        sleep 2
    fi
    
    # Start the server
    if [ "$ENVIRONMENT" = "production" ]; then
        echo -e "${GREEN}🚀 Starting production server...${NC}"
        python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
    else
        echo -e "${GREEN}🚀 Starting development server with reload...${NC}"
        python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    fi
}

# Function to start frontend (if exists)
start_frontend() {
    if [ -f "$PROJECT_ROOT/package.json" ]; then
        echo -e "${BLUE}🌐 Frontend detected${NC}"
        
        if command_exists npm; then
            echo -e "${YELLOW}📦 Checking frontend dependencies...${NC}"
            cd "$PROJECT_ROOT"
            
            # Only run npm install if node_modules doesn't exist
            if [ ! -d "node_modules" ]; then
                echo -e "${YELLOW}📥 Installing frontend dependencies...${NC}"
                npm install
            else
                echo -e "${GREEN}✅ Frontend dependencies already installed${NC}"
            fi
            
            # Make sure we're not in Python venv when running npm
            deactivate 2>/dev/null || true
            
            echo -e "${GREEN}🚀 Starting frontend development server...${NC}"
            npm run dev &
            FRONTEND_PID=$!
            echo "Frontend PID: $FRONTEND_PID" > /tmp/dop_frontend.pid
            
            # Give frontend a moment to start
            sleep 2
        else
            echo -e "${YELLOW}⚠️ npm not found, skipping frontend${NC}"
        fi
    else
        echo -e "${YELLOW}ℹ️ No frontend package.json found${NC}"
    fi
}

# Function to show status
show_status() {
    echo -e "\n${GREEN}🎉 Dynamic Option Pilot v2.0 Status${NC}"
    echo -e "${GREEN}=====================================${NC}"
    echo -e "Environment: ${ENVIRONMENT}"
    echo -e "Backend: http://localhost:8000"
    echo -e "API Docs: http://localhost:8000/docs"
    echo -e "Health Check: http://localhost:8000/health"
    
    if [ -f "$PROJECT_ROOT/package.json" ]; then
        echo -e "Frontend: http://localhost:5173 or http://localhost:5174 (if 5173 is busy)"
    fi
    
    echo -e "\n${YELLOW}📝 Useful Commands:${NC}"
    echo -e "• Health check: curl http://localhost:8000/health"
    echo -e "• System status: curl http://localhost:8000/system/status"
    echo -e "• Stop backend: pkill -f 'python.*main.py'"
    echo -e "• View logs: tail -f backend/logs/development.log"
    echo -e "\n${GREEN}✅ Startup complete!${NC}"
}

# Main execution flow
main() {
    echo -e "${BLUE}🔍 Pre-flight checks...${NC}"
    
    # Check Python version
    if ! check_python_version; then
        exit 1
    fi
    
    # Check if we're in the right directory
    if [ ! -f "$PROJECT_ROOT/backend/main.py" ]; then
        echo -e "${RED}❌ main.py not found. Are you in the right directory?${NC}"
        exit 1
    fi
    
    # Setup virtual environment
    setup_venv
    
    # Check configuration
    check_config
    
    # Setup database
    setup_database
    
    # Create logs directory
    mkdir -p "$PROJECT_ROOT/backend/logs"
    
    echo -e "\n${GREEN}🚀 All checks passed! Starting services...${NC}\n"
    
    # Start frontend in background if it exists
    start_frontend
    
    # Start backend (this will run in foreground)
    start_backend
}

# Handle script termination
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down services...${NC}"
    
    # Kill frontend if it was started
    if [ -f "/tmp/dop_frontend.pid" ]; then
        FRONTEND_PID=$(cat /tmp/dop_frontend.pid)
        kill $FRONTEND_PID 2>/dev/null || true
        rm -f /tmp/dop_frontend.pid
    fi
    
    echo -e "${GREEN}✅ Cleanup complete${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check for help flag
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Dynamic Option Pilot v2.0 Startup Script"
    echo ""
    echo "Usage: $0 [environment]"
    echo ""
    echo "Environments:"
    echo "  development (default) - Development mode with auto-reload"
    echo "  staging              - Staging environment"
    echo "  production           - Production mode with multiple workers"
    echo ""
    echo "Examples:"
    echo "  $0                   # Start in development mode"
    echo "  $0 production        # Start in production mode"
    echo ""
    exit 0
fi

# Run main function
main