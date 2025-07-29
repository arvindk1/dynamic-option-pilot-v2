#!/bin/bash

# Dynamic Option Pilot v2.0 Frontend Startup Script
# Usage: ./scripts/start-frontend.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}🌐 Starting Dynamic Option Pilot v2.0 Frontend${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Node.js
if ! command_exists node; then
    echo -e "${RED}❌ Node.js is required but not installed${NC}"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✅ Node.js ${NODE_VERSION} found${NC}"

# Check npm
if ! command_exists npm; then
    echo -e "${RED}❌ npm is required but not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ npm found${NC}"

# Change to project root
cd "$PROJECT_ROOT"

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ package.json not found. Are you in the right directory?${NC}"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
    npm install
else
    echo -e "${GREEN}✅ Frontend dependencies already installed${NC}"
fi

# Make sure we're not in a Python virtual environment
deactivate 2>/dev/null || true

# Check if ports are available
echo -e "${BLUE}🔍 Checking available ports...${NC}"

if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ Port 5173 is busy, Vite will use an alternative port${NC}"
else
    echo -e "${GREEN}✅ Port 5173 is available${NC}"
fi

# Start the development server
echo -e "${GREEN}🚀 Starting frontend development server...${NC}"
echo -e "${BLUE}Press Ctrl+C to stop${NC}"
echo ""

# Start Vite
npm run dev

# This will only execute if npm run dev exits
echo -e "\n${YELLOW}🛑 Frontend server stopped${NC}"