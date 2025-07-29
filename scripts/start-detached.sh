#!/bin/bash

# Dynamic Option Pilot v2.0 - Start Both Services in Background
# Usage: ./scripts/start-detached.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}🚀 Starting Dynamic Option Pilot v2.0 (Detached Mode)${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Start Frontend in Background
start_frontend_detached() {
    if [ -f "$PROJECT_ROOT/package.json" ]; then
        echo -e "${BLUE}🌐 Starting frontend in background...${NC}"
        cd "$PROJECT_ROOT"
        
        # Make sure we're not in Python venv
        deactivate 2>/dev/null || true
        
        # Start frontend with output redirected to log file
        mkdir -p logs
        nohup npm run dev > logs/frontend.log 2>&1 &
        FRONTEND_PID=$!
        echo "Frontend PID: $FRONTEND_PID" > /tmp/dop_frontend.pid
        echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
        echo -e "${BLUE}   Frontend logs: tail -f logs/frontend.log${NC}"
    fi
}

# Start Backend in Background
start_backend_detached() {
    echo -e "${BLUE}🖥️ Starting backend in background...${NC}"
    cd "$PROJECT_ROOT/backend"
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Set environment variables
    export ENVIRONMENT="development"
    export PYTHONPATH="$PROJECT_ROOT/backend:$PYTHONPATH"
    
    # Create logs directory
    mkdir -p logs
    
    # Start backend with output redirected to log file
    nohup python main.py > logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo "Backend PID: $BACKEND_PID" > /tmp/dop_backend.pid
    echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
    echo -e "${BLUE}   Backend logs: tail -f backend/logs/backend.log${NC}"
}

# Check if services are already running
check_running_services() {
    if pgrep -f "python.*main.py" > /dev/null; then
        echo -e "${YELLOW}⚠️ Backend appears to be already running${NC}"
        echo -e "${YELLOW}   Run ./scripts/stop.sh first if you want to restart${NC}"
        exit 1
    fi
    
    if pgrep -f "vite" > /dev/null; then
        echo -e "${YELLOW}⚠️ Frontend appears to be already running${NC}"
        echo -e "${YELLOW}   Run ./scripts/stop.sh first if you want to restart${NC}"
        exit 1
    fi
}

# Main execution
main() {
    check_running_services
    
    echo -e "${BLUE}🔍 Starting services in detached mode...${NC}"
    
    # Start both services
    start_frontend_detached
    start_backend_detached
    
    # Wait a moment for services to start
    echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
    sleep 5
    
    # Check if services are running
    echo -e "\n${GREEN}🎉 Services Status:${NC}"
    
    if pgrep -f "python.*main.py" > /dev/null; then
        echo -e "${GREEN}✅ Backend: Running${NC}"
    else
        echo -e "${RED}❌ Backend: Not running (check logs/backend.log)${NC}"
    fi
    
    if pgrep -f "vite" > /dev/null; then
        echo -e "${GREEN}✅ Frontend: Running${NC}"
    else
        echo -e "${RED}❌ Frontend: Not running (check logs/frontend.log)${NC}"
    fi
    
    echo -e "\n${BLUE}🌐 Access URLs:${NC}"
    echo -e "Frontend: http://localhost:5173"
    echo -e "Backend:  http://localhost:8000"
    echo -e "API Docs: http://localhost:8000/docs"
    
    echo -e "\n${YELLOW}📝 Useful Commands:${NC}"
    echo -e "• Stop services: ./scripts/stop.sh"
    echo -e "• View frontend logs: tail -f logs/frontend.log"
    echo -e "• View backend logs: tail -f backend/logs/backend.log"
    echo -e "• Check status: curl http://localhost:8000/health"
    
    echo -e "\n${GREEN}✅ Both services running in background!${NC}"
    echo -e "${BLUE}💡 Your terminal is now free to use${NC}"
}

# Run main function
main