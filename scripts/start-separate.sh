#!/bin/bash

# Dynamic Option Pilot v2.0 - Start in Separate Terminal Windows
# Usage: ./scripts/start-separate.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}🚀 Starting Dynamic Option Pilot v2.0 (Separate Windows)${NC}"

# Function to detect terminal type
detect_terminal() {
    if command -v gnome-terminal >/dev/null 2>&1; then
        echo "gnome-terminal"
    elif command -v xterm >/dev/null 2>&1; then
        echo "xterm"
    elif command -v konsole >/dev/null 2>&1; then
        echo "konsole"
    elif command -v alacritty >/dev/null 2>&1; then
        echo "alacritty"
    else
        echo "unknown"
    fi
}

# Start backend in new terminal
start_backend_terminal() {
    local terminal_type=$(detect_terminal)
    local backend_cmd="cd '$PROJECT_ROOT/backend' && source venv/bin/activate && python main.py"
    
    case $terminal_type in
        "gnome-terminal")
            gnome-terminal --tab --title="Backend - Dynamic Option Pilot" -- bash -c "$backend_cmd; exec bash"
            ;;
        "xterm")
            xterm -T "Backend - Dynamic Option Pilot" -e bash -c "$backend_cmd; exec bash" &
            ;;
        "konsole")
            konsole --new-tab -p tabtitle="Backend - Dynamic Option Pilot" -e bash -c "$backend_cmd; exec bash" &
            ;;
        "alacritty")
            alacritty -t "Backend - Dynamic Option Pilot" -e bash -c "$backend_cmd; exec bash" &
            ;;
        *)
            echo -e "${YELLOW}⚠️ Could not detect supported terminal, falling back to tmux/screen${NC}"
            if command -v tmux >/dev/null 2>&1; then
                tmux new-session -d -s dop-backend -c "$PROJECT_ROOT/backend" "source venv/bin/activate && python main.py"
                echo -e "${GREEN}✅ Backend started in tmux session 'dop-backend'${NC}"
                echo -e "${BLUE}   Attach with: tmux attach -t dop-backend${NC}"
            else
                echo -e "${RED}❌ No supported terminal found. Please start manually:${NC}"
                echo -e "${BLUE}cd $PROJECT_ROOT/backend && source venv/bin/activate && python main.py${NC}"
                return 1
            fi
            ;;
    esac
    
    if [ "$terminal_type" != "unknown" ]; then
        echo -e "${GREEN}✅ Backend started in new $terminal_type window${NC}"
    fi
}

# Start frontend in new terminal
start_frontend_terminal() {
    local terminal_type=$(detect_terminal)
    local frontend_cmd="cd '$PROJECT_ROOT' && deactivate 2>/dev/null || true && npm run dev"
    
    case $terminal_type in
        "gnome-terminal")
            gnome-terminal --tab --title="Frontend - Dynamic Option Pilot" -- bash -c "$frontend_cmd; exec bash"
            ;;
        "xterm")
            xterm -T "Frontend - Dynamic Option Pilot" -e bash -c "$frontend_cmd; exec bash" &
            ;;
        "konsole")
            konsole --new-tab -p tabtitle="Frontend - Dynamic Option Pilot" -e bash -c "$frontend_cmd; exec bash" &
            ;;
        "alacritty")
            alacritty -t "Frontend - Dynamic Option Pilot" -e bash -c "$frontend_cmd; exec bash" &
            ;;
        *)
            if command -v tmux >/dev/null 2>&1; then
                tmux new-session -d -s dop-frontend -c "$PROJECT_ROOT" "npm run dev"
                echo -e "${GREEN}✅ Frontend started in tmux session 'dop-frontend'${NC}"
                echo -e "${BLUE}   Attach with: tmux attach -t dop-frontend${NC}"
            else
                echo -e "${RED}❌ No supported terminal found. Please start manually:${NC}"
                echo -e "${BLUE}cd $PROJECT_ROOT && npm run dev${NC}"
                return 1
            fi
            ;;
    esac
    
    if [ "$terminal_type" != "unknown" ]; then
        echo -e "${GREEN}✅ Frontend started in new $terminal_type window${NC}"
    fi
}

# Main execution
main() {
    echo -e "${BLUE}🔍 Detecting terminal type...${NC}"
    local terminal_type=$(detect_terminal)
    echo -e "${GREEN}✅ Detected: $terminal_type${NC}"
    
    echo -e "\n${BLUE}🖥️ Starting backend in separate terminal...${NC}"
    start_backend_terminal
    
    # Wait a moment between starts
    sleep 2
    
    echo -e "\n${BLUE}🌐 Starting frontend in separate terminal...${NC}"
    start_frontend_terminal
    
    echo -e "\n${GREEN}🎉 Services started in separate terminals!${NC}"
    echo -e "${GREEN}=====================================${NC}"
    echo -e "Frontend: http://localhost:5173"
    echo -e "Backend:  http://localhost:8000"
    echo -e "API Docs: http://localhost:8000/docs"
    
    echo -e "\n${YELLOW}📝 To stop services:${NC}"
    echo -e "• Use Ctrl+C in each terminal window"
    echo -e "• Or run: ./scripts/stop.sh"
    
    if command -v tmux >/dev/null 2>&1 && [ "$terminal_type" = "unknown" ]; then
        echo -e "\n${BLUE}📺 tmux Sessions:${NC}"
        echo -e "• Backend:  tmux attach -t dop-backend"
        echo -e "• Frontend: tmux attach -t dop-frontend"
        echo -e "• Kill sessions: tmux kill-session -t dop-backend && tmux kill-session -t dop-frontend"
    fi
}

# Check for help flag
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Dynamic Option Pilot v2.0 - Start in Separate Terminals"
    echo ""
    echo "This script will start the backend and frontend in separate terminal windows/tabs."
    echo ""
    echo "Supported terminals:"
    echo "  - gnome-terminal (tabs)"
    echo "  - xterm (new windows)"
    echo "  - konsole (tabs)"
    echo "  - alacritty (new windows)"
    echo "  - tmux (sessions, as fallback)"
    echo ""
    echo "Usage: $0"
    echo ""
    exit 0
fi

# Run main function
main