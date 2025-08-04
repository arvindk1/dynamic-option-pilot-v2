# Claude Code Instructions for Dynamic Options Pilot v2

## 🎯 PRIMARY FOCUS
You are working on **Strategy Sandbox Development** for a mission-critical options trading platform. Your work should be focused on strategy-related components only.

## 🔒 PROTECTED AREAS - NEVER MODIFY WITHOUT EXPLICIT PERMISSION

### Core System Files (HANDS OFF)
- `backend/models/` - Database schemas and models
- `backend/core/` - Core orchestration system  
- `backend/main.py` - FastAPI application entry point
- `src/main.tsx` - React application entry point
- `package.json` - Dependencies and build config
- `requirements.txt` - Python dependencies

### Infrastructure (PROTECTED)
- Build configurations (vite.config.ts, tsconfig.json, tailwind.config.ts)
- Docker files and CI/CD configurations
- Authentication and security modules
- WebSocket and core context providers

## ✅ STRATEGY WORK ALLOWED AREAS

### Backend Strategy Components
- `backend/plugins/trading/` - Strategy implementations
- `backend/config/strategies/` - Strategy configurations
- `backend/services/sandbox_service.py` - Strategy testing
- `backend/api/sandbox.py` - Strategy API endpoints
- `backend/data/universes/` - Trading universe data

### Frontend Strategy Components  
- `src/components/StrategiesTab.tsx` - Strategy sandbox UI
- Strategy-related component files
- Strategy documentation files

### Documentation
- `CLAUDE.md` - Project instructions
- `README.md` - Project overview
- `TROUBLESHOOTING_GUIDE.md` - Debugging procedures
- `STRATEGY_CONFIGURATION_GUIDE.md` - Strategy setup
- `ADDING_NEW_STRATEGIES.md` - Strategy development

## 🛡️ SAFETY PROTOCOL

### Before Making ANY Change
1. **Check if file is in protected areas** - Ask permission if unsure
2. **Focus only on strategy-related functionality** 
3. **Read project documentation first** (README.md, CLAUDE.md)
4. **Test changes in sandbox environment**
5. **Create git commits for logical changes**

### Required Confirmations
Always ask user permission before:
- Modifying any file in `backend/models/` or `backend/core/`
- Changing `package.json`, `main.py`, or `main.tsx`
- Updating build configurations or dependencies
- Making changes outside strategy-focused areas

### Workflow
1. Read `CLAUDE.md` and `README.md` first
2. Focus on strategy sandbox improvements only
3. Test changes thoroughly
4. Document changes in appropriate files
5. Commit changes with descriptive messages

## 🎯 CURRENT OBJECTIVES
- Strategy sandbox UI improvements
- Trading universe management
- Strategy testing and configuration
- Strategy-related bug fixes and enhancements
- Documentation updates for strategy development

Remember: This is a **mission-critical trading platform**. Safety and reliability are paramount. When in doubt, ask for permission before making changes.