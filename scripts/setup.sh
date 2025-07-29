#!/bin/bash

# Dynamic Option Pilot v2.0 Setup Script
# This script sets up the development environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}🛠️ Dynamic Option Pilot v2.0 Setup${NC}"
echo -e "${BLUE}Project root: ${PROJECT_ROOT}${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "\n${BLUE}🔍 Checking prerequisites...${NC}"

# Check Python
if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is required but not installed${NC}"
    echo -e "${YELLOW}Please install Python 3.11 or higher${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
echo -e "${GREEN}✅ Python ${PYTHON_VERSION} found${NC}"

# Check pip
if ! command_exists pip3; then
    echo -e "${RED}❌ pip3 is required but not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ pip3 found${NC}"

# Check Node.js (optional)
if command_exists node; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js ${NODE_VERSION} found${NC}"
else
    echo -e "${YELLOW}⚠️ Node.js not found (optional for frontend)${NC}"
fi

# Setup backend
echo -e "\n${BLUE}🐍 Setting up backend...${NC}"
cd "$PROJECT_ROOT/backend"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}⬆️ Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}📥 Installing Python dependencies...${NC}"
pip install -r requirements.txt

echo -e "${GREEN}✅ Backend setup complete${NC}"

# Setup frontend (if package.json exists)
if [ -f "$PROJECT_ROOT/package.json" ]; then
    echo -e "\n${BLUE}🌐 Setting up frontend...${NC}"
    cd "$PROJECT_ROOT"
    
    if command_exists npm; then
        echo -e "${YELLOW}📦 Installing Node.js dependencies...${NC}"
        npm install
        echo -e "${GREEN}✅ Frontend setup complete${NC}"
    else
        echo -e "${YELLOW}⚠️ npm not found, skipping frontend setup${NC}"
    fi
else
    echo -e "${YELLOW}ℹ️ No package.json found, skipping frontend setup${NC}"
fi

# Create necessary directories
echo -e "\n${BLUE}📁 Creating directories...${NC}"
mkdir -p "$PROJECT_ROOT/backend/logs"
mkdir -p "$PROJECT_ROOT/backend/data"
mkdir -p "$PROJECT_ROOT/backend/temp"

# Set up environment files
echo -e "\n${BLUE}⚙️ Setting up environment configuration...${NC}"

ENV_FILE="$PROJECT_ROOT/.env.example"
cat > "$ENV_FILE" << EOF
# Dynamic Option Pilot v2.0 Environment Variables
# Copy this file to .env and update with your values

# Application Environment
ENVIRONMENT=development

# Database Configuration
DATABASE_URL=sqlite:///./dev.db

# Trading Configuration
PAPER_TRADING=true
MAX_POSITION_SIZE=1000.0

# Alpaca API (Optional - for real market data)
# Get these from https://app.alpaca.markets/
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here

# Logging
LOG_LEVEL=INFO

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Analysis Configuration
RSI_PERIOD=14
EMA_FAST=12
EMA_SLOW=26
EOF

echo -e "${GREEN}✅ Created .env.example file${NC}"

# Create basic .gitignore if it doesn't exist
if [ ! -f "$PROJECT_ROOT/.gitignore" ]; then
    echo -e "${BLUE}📝 Creating .gitignore...${NC}"
    cat > "$PROJECT_ROOT/.gitignore" << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Database
*.db
*.sqlite
*.sqlite3

# Logs
logs/
*.log

# Environment variables
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Node.js (if frontend exists)
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
dist/
build/

# Temporary files
temp/
tmp/
*.tmp

# Coverage reports
htmlcov/
.coverage
.pytest_cache/

# MyPy
.mypy_cache/
.dmypy.json
dmypy.json
EOF
    echo -e "${GREEN}✅ Created .gitignore${NC}"
fi

# Success message
echo -e "\n${GREEN}🎉 Setup complete!${NC}"
echo -e "${GREEN}=====================${NC}"
echo -e "\n${YELLOW}📝 Next steps:${NC}"
echo -e "1. Copy .env.example to .env and update with your API keys:"
echo -e "   ${BLUE}cp .env.example .env${NC}"
echo -e ""
echo -e "2. Start the application:"
echo -e "   ${BLUE}./scripts/start.sh${NC}"
echo -e ""
echo -e "3. Open your browser to:"
echo -e "   ${BLUE}http://localhost:8000${NC} (API)"
echo -e "   ${BLUE}http://localhost:8000/docs${NC} (API Documentation)"
echo -e ""
echo -e "${YELLOW}💡 Optional:${NC}"
echo -e "• For real market data, get Alpaca API keys from https://app.alpaca.markets/"
echo -e "• Update the .env file with your API credentials"
echo -e ""
echo -e "${GREEN}✅ Ready to trade! 🚀${NC}"
EOF