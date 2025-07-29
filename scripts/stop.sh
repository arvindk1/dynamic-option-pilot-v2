#!/bin/bash

# Dynamic Option Pilot v2.0 Stop Script
# Usage: ./scripts/stop.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Stopping Dynamic Option Pilot v2.0${NC}"

# Function to kill processes gracefully
kill_process() {
    local process_name=$1
    local pids=$(pgrep -f "$process_name" 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}🔄 Stopping $process_name processes...${NC}"
        echo "$pids" | xargs kill -TERM 2>/dev/null || true
        
        # Wait a bit for graceful shutdown
        sleep 3
        
        # Force kill if still running
        local remaining_pids=$(pgrep -f "$process_name" 2>/dev/null || true)
        if [ -n "$remaining_pids" ]; then
            echo -e "${YELLOW}⚡ Force stopping remaining processes...${NC}"
            echo "$remaining_pids" | xargs kill -KILL 2>/dev/null || true
        fi
        
        echo -e "${GREEN}✅ Stopped $process_name${NC}"
    else
        echo -e "${YELLOW}ℹ️ No $process_name processes found${NC}"
    fi
}

# Stop backend processes
kill_process "python.*main.py"
kill_process "uvicorn.*main:app"

# Stop frontend processes (if any)
kill_process "npm.*run.*dev"
kill_process "vite"
kill_process "node.*vite"

# Clean up PID files
if [ -f "/tmp/dop_frontend.pid" ]; then
    echo -e "${YELLOW}🧹 Cleaning up PID files...${NC}"
    rm -f /tmp/dop_frontend.pid
fi

if [ -f "/tmp/dop_backend.pid" ]; then
    rm -f /tmp/dop_backend.pid
fi

# Stop tmux sessions if they exist
if command -v tmux >/dev/null 2>&1; then
    tmux kill-session -t dop-backend 2>/dev/null || true
    tmux kill-session -t dop-frontend 2>/dev/null || true
fi

# Check if ports are still in use
echo -e "\n${BLUE}🔍 Checking ports...${NC}"

if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ Port 8000 still in use${NC}"
    PORT_PID=$(lsof -Pi :8000 -sTCP:LISTEN -t)
    echo -e "${YELLOW}Killing process on port 8000 (PID: $PORT_PID)${NC}"
    kill -9 $PORT_PID 2>/dev/null || true
else
    echo -e "${GREEN}✅ Port 8000 is free${NC}"
fi

if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ Port 5173 still in use${NC}"
    PORT_PID=$(lsof -Pi :5173 -sTCP:LISTEN -t)
    echo -e "${YELLOW}Killing process on port 5173 (PID: $PORT_PID)${NC}"
    kill -9 $PORT_PID 2>/dev/null || true
else
    echo -e "${GREEN}✅ Port 5173 is free${NC}"
fi

echo -e "\n${GREEN}🎉 Dynamic Option Pilot v2.0 stopped successfully${NC}"
echo -e "${BLUE}💡 To start again, run: ./scripts/start.sh${NC}"