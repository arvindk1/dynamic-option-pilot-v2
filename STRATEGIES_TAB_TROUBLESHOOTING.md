# Strategies Tab Troubleshooting Guide

## 📋 Overview

This document covers troubleshooting for the Strategy Sandbox system in Dynamic Options Pilot v2. The Strategy Tab provides a safe testing environment for developing and validating trading strategies before deployment.

## ✅ Fixed Issues (2025-08-01)

### 1. **API Timeout Issues** - RESOLVED
**Problem**: Sandbox API endpoints hanging for 2+ minutes
**Root Cause**: Backend service connectivity issues
**Solution**: API endpoints now respond within 200ms
**Verification**: `curl -v --max-time 10 http://localhost:8000/api/sandbox/strategies/`

### 2. **Dark Mode Integration** - RESOLVED  
**Problem**: StrategiesTab showing light theme regardless of theme setting
**Root Cause**: Hardcoded light theme classes (`bg-white`, `text-gray-900`)
**Solution**: Implemented theme-aware styling with `useTheme()` hook
```typescript
const { theme } = useTheme();
const themeClasses = {
  container: theme === 'dark' ? 'bg-gray-900 text-white' : 'bg-gray-50 text-gray-900',
  // ...other theme classes
};
```

### 3. **Test Results Display** - RESOLVED
**Problem**: Test runs succeed (6 opportunities, 82.3% win rate) but UI shows no results
**Root Cause**: Missing `opportunities` array in `TestResult` interface
**Solution**: 
- Updated `TestResult` interface to include `opportunities: any[]`
- Enhanced `TestResultsPanel` to display individual opportunities with details
- Added theme-aware opportunity cards showing symbol, win rate, premium, DTE, etc.

### 4. **Parameter Editing State Management** - RESOLVED
**Problem**: Parameter changes not persisting or showing visually
**Root Cause**: `StrategyParametersPanel` called without `onParameterChange` prop
**Solution**:
- Added `handleParameterChange` function in `StrategyEditor`
- Implemented PUT `/api/sandbox/strategies/{id}` for persistence
- Added local state management with `currentStrategy` for immediate UI updates

### 5. **Cross-Tab Contamination Prevention** - RESOLVED
**Problem**: Concern that sandbox tests might affect Trading tab data
**Solution**: Sandbox system uses separate data layer:
- Separate database tables (`sandbox_strategy_configs`, `sandbox_test_runs`)
- Isolated strategy instances with `is_sandbox_test: true` flag
- Strategy ID mapping (`thetacrop_weekly` → `ThetaCropWeekly`) prevents conflicts

## 🚨 Remaining Issues

### 1. **Strategy Duplication** - PENDING
**Problem**: Two identical "ThetaCrop Weekly Test" strategies appear
**Current Status**: DELETE endpoint exists but duplication persists
**Investigation**: Check database persistence and strategy creation logic
```bash
# Verify current strategies
curl -s http://localhost:8000/api/sandbox/strategies/ | python3 -c "import json,sys; [print(f'{s[\"name\"]} - {s[\"id\"]}') for s in json.load(sys.stdin)]"

# Delete duplicate (if ID known)
curl -X DELETE http://localhost:8000/api/sandbox/strategies/{duplicate-id}
```

## 🏗️ Architecture Overview

### Data Flow
```
Frontend StrategyEditor
    ↓
Parameter Change → handleParameterChange()
    ↓
PUT /api/sandbox/strategies/{id} → Backend persistence
    ↓
Local state update → Immediate UI feedback
    ↓
Parent component update → Strategy list refresh
```

### Theme Integration
```
useTheme() hook → theme state ('dark' | 'light')
    ↓
themeClasses object → conditional CSS classes
    ↓
All components → theme-aware styling
```

### Test Execution Flow
```
"Run Test" button → POST /api/sandbox/test/run/{id}
    ↓
Backend: Strategy mapping (thetacrop_weekly → ThetaCropWeekly)
    ↓
Live strategy execution with sandbox flag
    ↓
Response: opportunities + performance_metrics
    ↓
Frontend: TestResultsPanel displays results
```

## 🔧 Common Debugging Commands

### Backend Health Checks
```bash
# Check sandbox API endpoints
curl -s http://localhost:8000/api/sandbox/strategies/
curl -s http://localhost:8000/api/sandbox/data/universes

# Test strategy execution
STRATEGY_ID="3a158feb-29d8-44ce-9433-d14c81ab860b"
curl -X POST -H "Content-Type: application/json" \
  -d '{"max_opportunities": 5, "use_cached_data": true}' \
  http://localhost:8000/api/sandbox/test/run/$STRATEGY_ID

# Check universe loading
curl -s http://localhost:8000/api/sandbox/data/universe/mag7
```

### Database Inspection
```bash
# Check sandbox database tables
sqlite3 backend/dev.db "SELECT COUNT(*) FROM sandbox_strategy_configs;"
sqlite3 backend/dev.db "SELECT name, strategy_id FROM sandbox_strategy_configs;"
sqlite3 backend/dev.db "SELECT COUNT(*) FROM sandbox_test_runs;"
```

### Frontend Debugging
```javascript
// Browser Console - Check theme state
localStorage.getItem('theme')

// Check React components
// In StrategiesTab component, add:
console.log('Current theme:', theme);
console.log('Strategy data:', strategy);
console.log('Test result:', lastTestResult);
```

## 🎯 Performance Benchmarks

### Expected Response Times
- **Strategy List**: < 200ms
- **Test Execution**: 1.5-3 seconds (depending on symbols)
- **Parameter Updates**: < 100ms (local state) + < 500ms (persistence)
- **Universe Loading**: < 100ms

### Expected Test Results
```json
{
  "success": true,
  "opportunities_count": 6,
  "execution_time_ms": 2221,
  "performance_metrics": {
    "avg_probability_profit": 0.823,
    "avg_premium": 2.0,
    "total_opportunities": 6
  }
}
```

## 🐛 Error Patterns & Solutions

### Pattern: "Component not updating after parameter change"
**Cause**: Missing `onParameterChange` prop or broken state management
**Solution**: Verify prop passing and state updates in React DevTools

### Pattern: "Test results showing but no individual opportunities"
**Cause**: Missing `opportunities` array in response or interface mismatch
**Solution**: Check API response structure and TypeScript interfaces

### Pattern: "Dark mode not working"
**Cause**: Hardcoded theme classes instead of theme-aware classes
**Solution**: Replace with conditional classes using `useTheme()` hook

### Pattern: "API timeouts or hangs"
**Cause**: Backend service issues or database locks
**Solution**: Check backend logs and database connections

## 📚 Best Practices

### State Management
- Use `useEffect` to sync props with local state
- Implement optimistic updates for better UX
- Add error boundaries for graceful failure handling

### Theme Integration
- Always use `useTheme()` hook for theme-aware components
- Create reusable `themeClasses` objects for consistency
- Test both light and dark modes thoroughly

### API Integration
- Add proper error handling and loading states
- Use TypeScript interfaces for type safety
- Implement retry logic for network failures

### Testing Strategy
- Test parameter changes persist across component re-renders
- Verify test results display correctly with real data
- Ensure theme switching works seamlessly

## 🔄 Future Improvements

1. **Enhanced Parameter Validation**: Real-time validation with clear error messages
2. **Advanced Test Results**: Backtesting with historical data, Monte Carlo simulation
3. **Strategy Comparison**: Side-by-side comparison of different parameter sets
4. **Export Functionality**: Export test results and strategy configurations
5. **Collaborative Features**: Share strategies with team members

## 📞 Support

For additional help:
1. Check backend logs: `tail -f backend/logs/backend.log`
2. Review browser console for frontend errors
3. Use React DevTools to inspect component state
4. Test API endpoints directly with curl/Postman

Last Updated: 2025-08-01  
Version: v2.0  
Status: 5/6 Major Issues Resolved ✅