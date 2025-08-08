/**
 * OptimizedTradingDashboard - Refactored trading dashboard with improved performance
 * Split into focused components with proper memoization and lazy loading
 */
import React, { useState, useEffect, useCallback, useMemo, memo } from 'react';
import { usePerformanceMonitoring, useRenderOptimization } from '@/utils/performance';
import { useTheme } from '@/contexts/ThemeContext';
import { useAccessibility } from '@/components/AccessibilityProvider';
import { useRealTimeData } from '@/hooks/useRealTimeData';
import { useTabPreload } from '@/hooks/useTabPreload';
import { useKeyboardNavigation } from '@/hooks/useKeyboardNavigation';
import { DemoDataService } from '@/services/demoData';
import { dataThrottleService } from '@/services/dataThrottle';
import { tabPerformanceService } from '@/services/tabPerformance';
import { TradingTour } from '@/components/TradingTour';
import TradingErrorBoundary from '@/components/TradingErrorBoundary';

// Import optimized sub-components
import TradingDashboardHeader from '@/components/TradingDashboard/TradingDashboardHeader';
import TradingMetricsPanel from '@/components/TradingDashboard/TradingMetricsPanel';
import TradingTabsContainer from '@/components/TradingDashboard/TradingTabsContainer';

// Type definitions
interface TradingConfig {
  brokerPlugin: string;
  paperTrading: boolean;
  symbol: string;
  dteMin: number;
  dteMax: number;
  deltaTarget: number;
  creditThreshold: number;
  maxSpreadWidth: number;
  maxPositions: number;
  positionSizePct: number;
  maxMarginUsage: number;
  maxDrawdown: number;
  kellyFraction: number;
}

interface AccountMetrics {
  account_balance: number;
  cash: number;
  buying_power: number;
  account_status: string;
  margin_used: number;
  total_pnl: number;
  win_rate: number;
  total_trades: number;
  positions_open: number;
  max_drawdown: number;
  sharpe_ratio: number;
  vix: number;
  iv_rank: number;
  options_level: string;
  data_state?: string;
  warning?: string;
}

interface RiskMetrics {
  portfolio_beta: number;
  portfolio_delta: number;
  portfolio_gamma: number;
  portfolio_theta: number;
  portfolio_vega: number;
  max_loss_per_trade: number;
  concentration_risk: number;
  margin_utilization: number;
  kelly_position_size: number;
  expected_move: number;
  probability_profit: number;
  risk_reward_ratio: number;
  sharpe_ratio: number;
  var_95: number;
  correlation_spy: number;
}

// Performance tracking array for analytics
const performancePoints: Array<{ timestamp: number; pnl: number }> = [];

export const OptimizedTradingDashboard = memo(() => {
  const { announceToScreenReader } = useAccessibility();
  
  // Performance monitoring
  const { measureRender, measureApiCall } = usePerformanceMonitoring('OptimizedTradingDashboard');
  const { trackPropsChange } = useRenderOptimization('OptimizedTradingDashboard');
  
  // Start render measurement
  const endRender = measureRender('main-render');
  
  // State management - split into logical groups
  const [appState, setAppState] = useState({
    isDemoMode: false,
    demoModeInitialized: false,
    showTour: false,
    isFirstVisit: DemoDataService.isFirstVisit(),
    activeTab: "overview"
  });
  
  const [preloadedTabs, setPreloadedTabs] = useState<Set<string>>(new Set());
  
  // Memoized initial metrics to prevent unnecessary re-renders
  const initialAccountMetrics = useMemo((): AccountMetrics => ({
    account_balance: 50000,
    cash: 25000,
    buying_power: 100000,
    account_status: 'ACTIVE',
    margin_used: 0,
    total_pnl: 0,
    win_rate: 0,
    total_trades: 0,
    positions_open: 0,
    max_drawdown: 0,
    sharpe_ratio: 0,
    vix: 20.5,
    iv_rank: 0.45,
    options_level: 'Level 3'
  }), []);
  
  const initialConfig = useMemo((): TradingConfig => ({
    brokerPlugin: 'demo_broker',
    paperTrading: true,
    symbol: 'SPY',
    dteMin: 15,
    dteMax: 45,
    deltaTarget: 0.15,
    creditThreshold: 0.10,
    maxSpreadWidth: 10,
    maxPositions: 5,
    positionSizePct: 0.02,
    maxMarginUsage: 0.25,
    maxDrawdown: 0.10,
    kellyFraction: 0.25
  }), []);
  
  const [accountMetrics, setAccountMetrics] = useState<AccountMetrics>(initialAccountMetrics);
  const [riskMetrics, setRiskMetrics] = useState<RiskMetrics | null>(null);
  const [config, setConfig] = useState<TradingConfig>(initialConfig);
  const [marketBias, setMarketBias] = useState<'BULLISH' | 'NEUTRAL' | 'BEARISH'>('NEUTRAL');
  const [confidence, setConfidence] = useState(0.72);

  // Tab management with preloading
  const handleTabChange = useCallback((tabName: string) => {
    console.log(`🔄 Tab change: ${tabName}`);
    tabPerformanceService.logTabSwitch(appState.activeTab, tabName);
    
    setAppState(prev => ({ ...prev, activeTab: tabName }));
    
    // Announce to screen readers
    announceToScreenReader(`Switched to ${tabName} tab`);
  }, [appState.activeTab, announceToScreenReader]);

  const { markTabAsPreloaded, isTabPreloaded } = useTabPreload({
    activeTab: appState.activeTab,
    preloadedTabs,
    setPreloadedTabs,
    preloadDelay: 500
  });

  // Keyboard navigation
  const { showHelp } = useKeyboardNavigation({
    onEscape: () => setAppState(prev => ({ ...prev, showTour: false })),
    onArrowLeft: () => {
      // Previous tab logic could be added here
    },
    onArrowRight: () => {
      // Next tab logic could be added here
    },
    onEnter: () => {
      // Tab activation logic
    }
  });

  // Trade execution handler with performance tracking
  const handleTradeExecuted = useCallback((pnl: number) => {
    console.log(`💰 Trade executed with P&L: $${pnl}`);
    
    // Add to performance tracking
    const newPoint = { timestamp: Date.now(), pnl };
    performancePoints.push(newPoint);
    
    // Keep only last 100 points for performance
    if (performancePoints.length > 100) {
      performancePoints.splice(0, 1);
    }

    // Update account metrics
    setAccountMetrics(prev => {
      const newTotalPnL = prev.total_pnl + pnl;
      const newTotalTrades = prev.total_trades + 1;
      const newWinRate = pnl > 0 ? 
        (prev.win_rate * prev.total_trades + 1) / newTotalTrades :
        (prev.win_rate * prev.total_trades) / newTotalTrades;

      return {
        ...prev,
        total_pnl: newTotalPnL,
        total_trades: newTotalTrades,
        win_rate: newWinRate,
        account_balance: prev.account_balance + pnl
      };
    });

    // Announce to screen readers
    announceToScreenReader(
      `Trade executed with ${pnl > 0 ? 'profit' : 'loss'} of $${Math.abs(pnl).toFixed(2)}`
    );
  }, [announceToScreenReader]);

  // Data loading with throttling
  useEffect(() => {
    let mounted = true;

    const loadDashboardData = async () => {
      try {
        console.log('🔄 Loading dashboard data...');
        
        // Simulate API calls with proper error handling
        const [accountData, riskData] = await Promise.all([
          measureApiCall('account-data', () => 
            dataThrottleService.throttledFetch('/api/account', { timeout: 5000 })
          ).catch(() => initialAccountMetrics), // Fallback on error
          
          measureApiCall('risk-data', () =>
            dataThrottleService.throttledFetch('/api/risk-metrics', { timeout: 3000 })
          ).catch(() => null) // Fallback on error
        ]);

        if (mounted) {
          if (accountData) {
            setAccountMetrics(prevMetrics => ({
              ...prevMetrics,
              ...accountData
            }));
          }
          
          if (riskData) {
            setRiskMetrics(riskData);
          }
          
          setAppState(prev => ({ 
            ...prev, 
            isDemoMode: accountData?.account_status === 'DEMO' || false,
            demoModeInitialized: true
          }));
        }
      } catch (error) {
        console.error('❌ Error loading dashboard data:', error);
        if (mounted) {
          setAppState(prev => ({ ...prev, demoModeInitialized: true }));
        }
      }
    };

    loadDashboardData();
    
    // Set up data refresh interval
    const refreshInterval = setInterval(loadDashboardData, 30000); // 30 seconds

    return () => {
      mounted = false;
      clearInterval(refreshInterval);
    };
  }, [initialAccountMetrics, measureApiCall]);

  // End render measurement
  useEffect(() => {
    endRender();
  }, [endRender]);

  // Memoized handlers to prevent unnecessary re-renders
  const handleConfigUpdate = useCallback((newConfig: Partial<TradingConfig>) => {
    setConfig(prev => ({ ...prev, ...newConfig }));
  }, []);

  const handleShowTour = useCallback(() => {
    setAppState(prev => ({ ...prev, showTour: true }));
  }, []);

  const handleTabPreload = useCallback((tabName: string) => {
    markTabAsPreloaded(tabName);
  }, [markTabAsPreloaded]);

  // Render optimization - track prop changes in development
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      trackPropsChange({ 
        activeTab: appState.activeTab,
        accountMetrics,
        riskMetrics,
        isDemoMode: appState.isDemoMode
      });
    }
  }, [appState.activeTab, accountMetrics, riskMetrics, appState.isDemoMode, trackPropsChange]);

  return (
    <TradingErrorBoundary tabName="main-dashboard">
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4 space-y-6">
        {/* Header Section */}
        <TradingDashboardHeader
          accountMetrics={accountMetrics}
          isDemoMode={appState.isDemoMode}
          isFirstVisit={appState.isFirstVisit}
          onShowTour={handleShowTour}
        />

        {/* Metrics Panel */}
        <TradingMetricsPanel
          accountMetrics={accountMetrics}
          riskMetrics={riskMetrics}
          marketBias={marketBias}
          confidence={confidence}
        />

        {/* Main Tabs Container */}
        <TradingTabsContainer
          activeTab={appState.activeTab}
          onTabChange={handleTabChange}
          preloadedTabs={preloadedTabs}
          onTabPreload={handleTabPreload}
          accountMetrics={accountMetrics}
          riskMetrics={riskMetrics}
          config={config}
          onConfigUpdate={handleConfigUpdate}
          onTradeExecuted={handleTradeExecuted}
        />

        {/* Trading Tour */}
        {appState.showTour && (
          <TradingTour 
            onComplete={() => setAppState(prev => ({ ...prev, showTour: false }))}
          />
        )}
      </div>
    </TradingErrorBoundary>
  );
});

OptimizedTradingDashboard.displayName = 'OptimizedTradingDashboard';

export default OptimizedTradingDashboard;