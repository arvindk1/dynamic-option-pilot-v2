# Dynamic Options Pilot v2 - Protection System

## 🛡️ Overview

This document outlines the comprehensive protection system implemented to prevent accidental deletion or modification of critical trading system components. The protection system ensures stability while allowing safe development and strategy testing.

## 🔒 Protection Levels

### Level 1: Critical System Files (NEVER MODIFY)
**These files are essential for system operation and should never be modified without explicit approval:**

```
backend/models/                 # Database models and schemas
backend/core/                   # Core orchestration and system logic  
backend/main.py                 # FastAPI application entry point
src/main.tsx                    # React application entry point
package.json                    # Dependencies and build configuration
requirements.txt                # Python dependencies
.env                           # Environment configuration (Contains API keys)
backend/.env                   # Backend environment variables (Alpaca credentials)
docker-compose.yml             # Container orchestration
Dockerfile                     # Container build instructions
.github/                       # CI/CD workflows
```

### Level 2: Strategy Configuration Files (PROTECTED)
**Production strategy configurations - read-only with backup system:**

```
backend/config/strategies/production/    # Production strategy configs (READ-ONLY)
backend/config/strategies/rules/         # Core strategy rules (PROTECTED)
```

### Level 3: Development Areas (SAFE TO MODIFY)
**Areas specifically designed for development and customization:**

```
backend/config/strategies/development/   # Development strategy configs
backend/plugins/trading/                 # Strategy implementations
src/components/StrategiesTab.tsx        # Strategy UI components
backend/services/sandbox_service.py     # Strategy testing service
backend/api/sandbox.py                  # Strategy testing API
```

## 🔧 Implementation Recommendations

### 1. File Permissions Protection
```bash
# Set read-only permissions on production configs
chmod 444 backend/config/strategies/production/*.json
chmod 444 backend/config/strategies/rules/*.json

# Ensure development configs remain editable
chmod 644 backend/config/strategies/development/*.json

# Protect critical system files
chmod 444 backend/models/*.py
chmod 444 backend/core/**/*.py
chmod 444 backend/main.py
chmod 444 src/main.tsx
```

### 2. Git Pre-Commit Hook Protection
Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Dynamic Options Pilot v2 - Protection System Pre-Commit Hook

protected_files=(
  "backend/models/"
  "backend/core/"
  "backend/main.py"
  "src/main.tsx"
  "package.json"
  "requirements.txt"
  ".env"
  "backend/.env"
  "backend/config/strategies/production/"
  "backend/config/strategies/rules/"
)

echo "🛡️ Protection System: Checking for modifications to critical files..."

for pattern in "${protected_files[@]}"; do
  if git diff --cached --name-only | grep -q "$pattern"; then
    echo "❌ ERROR: Attempting to modify protected file/directory: $pattern"
    echo "🔒 This file is protected by the Dynamic Options Pilot Protection System"
    echo "📝 If this change is intentional, please:"
    echo "   1. Document the reason for the change"
    echo "   2. Get approval from system administrator"  
    echo "   3. Create backup before proceeding"
    echo "   4. Use: git commit --no-verify (to bypass this check)"
    exit 1
  fi
done

echo "✅ Protection System: No protected files modified"
exit 0
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

### 3. Automated Backup System
```bash
#!/bin/bash
# backup-strategies.sh - Automated Strategy Configuration Backup

BACKUP_DIR="backend/config/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup all strategy configurations
echo "🔄 Creating strategy configuration backup..."
rsync -av backend/config/strategies/ "$BACKUP_DIR/strategies-$TIMESTAMP/"

# Keep only last 10 backups
echo "🧹 Cleaning old backups (keeping last 10)..."
ls -dt "$BACKUP_DIR"/strategies-* | tail -n +11 | xargs rm -rf

echo "✅ Backup completed: $BACKUP_DIR/strategies-$TIMESTAMP/"
```

### 4. Database Protection
```bash
# Backup production database
sqlite3 backend/prod.db ".backup backend/config/backups/prod-$(date +%Y%m%d-%H%M%S).db"

# Backup development database  
sqlite3 backend/dev.db ".backup backend/config/backups/dev-$(date +%Y%m%d-%H%M%S).db"
```

## 🚨 Recovery Procedures

### Strategy Files Disappeared
```bash
# 1. Check git status for accidental deletions
git status

# 2. Verify files exist on filesystem
ls -la backend/config/strategies/development/

# 3. Check if backend can load strategies
curl http://localhost:8000/api/strategies/

# 4. Restore from backup if needed
cp -r backend/config/backups/strategies-latest/* backend/config/strategies/

# 5. Restart backend to reload strategies
# Kill backend process and restart
```

### Database Corruption
```bash
# 1. Check database integrity
sqlite3 backend/dev.db "PRAGMA integrity_check;"

# 2. Restore from latest backup
cp backend/config/backups/dev-latest.db backend/dev.db

# 3. Restart system
docker-compose restart  # or manual restart
```

### System Won't Start
```bash
# 1. Check for permission issues
ls -la backend/main.py
ls -la src/main.tsx

# 2. Verify dependencies
cat package.json
cat requirements.txt

# 3. Check environment variables
ls -la .env
ls -la backend/.env

# 4. Restore from git if files were modified
git checkout HEAD -- backend/main.py src/main.tsx

# 5. Reset file permissions
chmod 644 backend/main.py
chmod 644 src/main.tsx
```

## 📋 Protection Checklist

### Daily Operations
- [ ] Backup strategy configurations before major changes
- [ ] Test changes in development environment first
- [ ] Use git branches for experimental features
- [ ] Verify system health after changes: `curl http://localhost:8000/health`

### Weekly Maintenance
- [ ] Review backup retention (keep last 10 backups)
- [ ] Check file permissions on critical files
- [ ] Verify git hooks are functioning
- [ ] Test recovery procedures

### Monthly Security Review
- [ ] Audit protected file access
- [ ] Review backup integrity
- [ ] Update protection patterns if new critical files added
- [ ] Document any approved changes to protected files

## 🔍 Monitoring Commands

### Check Protection Status
```bash
# Verify file permissions
find backend/config/strategies/production/ -type f ! -perm 444

# Check for unexpected modifications
git status --porcelain | grep -E "(backend/models/|backend/core/|backend/main.py|src/main.tsx)"

# Verify backup system
ls -la backend/config/backups/

# Test git hooks
git commit --dry-run  # Should trigger protection check
```

### System Health Verification
```bash
# Backend health
curl http://localhost:8000/health

# Strategy loading
curl http://localhost:8000/api/strategies/ | python3 -c "
import json,sys; data=json.load(sys.stdin); 
print(f'Strategies loaded: {len(data[\"strategies\"])}')"

# Sandbox functionality
curl http://localhost:8000/api/sandbox/strategies/

# Database connectivity
sqlite3 backend/dev.db "SELECT COUNT(*) FROM opportunities;"
```

## 🎯 Summary

The protection system provides:
- ✅ **Multi-level file protection** preventing accidental critical file modifications
- ✅ **Automated backup system** with retention management
- ✅ **Git hook protection** blocking dangerous commits
- ✅ **Recovery procedures** for common failure scenarios
- ✅ **Monitoring commands** for ongoing system health verification

This ensures the trading system remains stable and recoverable while allowing safe development in designated areas.