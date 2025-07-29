import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { 
  Activity, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  Settings,
  Database,
  BarChart3,
  Shield,
  Zap,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  Clock,
  Target,
  Brain,
  Moon,
  Sun,
  Newspaper
} from 'lucide-react';
import { useTheme } from '@/contexts/ThemeContext';
import { useRealTimeData } from '@/hooks/useRealTimeData';
import { RealTimeChart } from '@/components/RealTimeChart';
import { SpreadExecutor } from '@/components/SpreadExecutor';
import { EnhancedTradeExecutor } from '@/components/EnhancedTradeExecutor';
import { DynamicStrategyTabs } from '@/components/DynamicStrategyTabs';
import { WebSocketStatus } from '@/components/WebSocketStatus';
import { TradingTour, TourTrigger } from '@/components/TradingTour';
import MarketStatusWidget from '@/components/MarketStatusWidget';
// MarketCommentary is imported via LazyTabContent for better performance
import { DemoDataService } from '@/services/demoData';
import { dataThrottleService } from '@/services/dataThrottle';
import { 
  LazyTabContent,
  LazySentimentDashboard,
  LazyEconomicEventsDashboard,
  LazyAITradeCoach,
  LazyEnhancedSignalsTab,
  LazyEnhancedRiskTab,
  LazyTradeManager,
  LazyMarketCommentary
} from '@/components/LazyTabContent';
import { useTabPreload } from '@/hooks/useTabPreload';
import { TabPerformanceMonitor } from '@/components/TabPerformanceMonitor';
import { tabPerformanceService } from '@/services/tabPerformance';
import TradingErrorBoundary from '@/components/TradingErrorBoundary';
import { useKeyboardNavigation } from '@/hooks/useKeyboardNavigation';
import { useAccessibility } from '@/components/AccessibilityProvider';
import { TradingCardSkeleton, DashboardLoadingState } from '@/components/LoadingStates';
import { TieredNavigation } from '@/components/TieredNavigation';
import { HelpMenu } from '@/components/HelpMenu';

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

interface ApiOpportunity {
  id: string;
  symbol: string;
  short_strike?: number;
  long_strike?: number;
  strike?: number;
  premium: number;
  max_loss: number;
  delta: number;
  probability_profit: number;
  expected_value: number;
  days_to_expiration: number;
  underlying_price: number;
  liquidity_score: number;
  bias: string;
  rsi: number;
}

interface SpreadCandidate {
  id: string;
  symbol?: string;
  shortStrike: number;
  longStrike: number;
  credit: number;
  maxLoss: number;
  delta: number;
  probabilityProfit: number;
  expectedValue: number;
  daysToExpiration: number;
  type: 'PUT' | 'CALL';
  underlyingPrice?: number;
  liquidityScore?: number;
  bias?: string;
  rsi?: number;
}

interface EnhancedTradeOpportunity {
  id: string;
  symbol: string;
  strategy_type: string;
  option_type?: string;
  strike?: number;
  short_strike?: number;
  long_strike?: number;
  expiration: string;
  days_to_expiration: number;
  premium: number;
  max_loss: number;
  max_profit: number;
  probability_profit: number;
  expected_value: number;
  delta: number;
  gamma?: number;
  theta?: number;
  vega?: number;
  implied_volatility?: number;
  volume?: number;
  open_interest?: number;
  liquidity_score: number;
  underlying_price: number;
  bias: string;
  rsi: number;
  macd_signal?: string;
  support_resistance?: { support: number; resistance: number };
  trade_setup: string;
  risk_level: string;
}

interface EnhancedTradeCategories {
  high_probability: EnhancedTradeOpportunity[];
  quick_scalps: EnhancedTradeOpportunity[];
  swing_trades: EnhancedTradeOpportunity[];
  volatility_plays: EnhancedTradeOpportunity[];
  thetacrop: EnhancedTradeOpportunity[];
}

interface RiskMetrics {
  portfolio_metrics: {
    total_delta: number;
    total_theta: number;
    total_vega: number;
    total_gamma: number;
  };
  var_95: number;
  expected_shortfall: number;
  correlation_spy: number;
}

const TradingDashboard = React.memo(() => {
  const { theme, toggleTheme } = useTheme();
  const { announceToScreenReader } = useAccessibility();
  
  // Demo mode and tour state
  const [isDemoMode, setIsDemoMode] = useState(false); // Default to false, will be determined async
  const [demoModeInitialized, setDemoModeInitialized] = useState(false);
  const [showTour, setShowTour] = useState(false);
  const [isFirstVisit, setIsFirstVisit] = useState(DemoDataService.isFirstVisit());
  
  // Tab management state
  const [activeTab, setActiveTab] = useState("overview");
  const [preloadedTabs, setPreloadedTabs] = useState<Set<string>>(new Set());
  
  // Enhanced tab navigation with accessibility and performance tracking
  const handleTabChange = useCallback((tabName: string) => {
    // Measure tab switch performance
    tabPerformanceService.measureTabSwitch(tabName);
    
    setActiveTab(tabName);
    announceToScreenReader(`Switched to ${tabName} tab`);
  }, [announceToScreenReader]);
  
  // Setup tab preloading
  const { markTabAsPreloaded, isTabPreloaded } = useTabPreload({
    currentTab: activeTab,
    onPreload: (tabName: string) => {
      setPreloadedTabs(prev => new Set([...prev, tabName]));
      // Preload resources for the tab
      tabPerformanceService.preloadTabResources(tabName);
    },
    preloadDelay: 500 // Reduced from 800ms to 500ms for faster preloading
  });
  
  // Keyboard navigation
  const { showHelp } = useKeyboardNavigation({
    onNavigateToTab: handleTabChange,
    onToggleTheme: toggleTheme,
    onToggleDemoMode: () => setIsDemoMode(!isDemoMode),
    onRefreshData: () => {
      loadAccountMetrics();
      loadTradingOpportunities();
      announceToScreenReader("Market data refreshed");
    },
    onOpenHelp: () => showHelp(),
  });
  
  // Move all hooks to top level (React rules compliance)
  const { 
    marketData, 
    performanceData, 
    accountValue, 
    isMarketOpen, 
    addPerformancePoint,
    signals,
    connectionStatus,
    usingWebSocket,
    wsConnected
  } = useRealTimeData();

  // Enhanced trade execution callback that links to position tracking
  const handleTradeExecuted = useCallback((pnl: number) => {
    // Add performance data point
    addPerformancePoint(pnl);
    
    // Auto-switch to positions tab to show the new trade
    setTimeout(() => {
      setActiveTab('positions');
      // Announce to screen reader
      announceToScreenReader("Trade executed successfully. Switched to Positions tab to view trade.");
    }, 1000); // Small delay to allow execution to complete
  }, [addPerformancePoint, announceToScreenReader]);
  
  const [accountMetrics, setAccountMetrics] = useState<AccountMetrics>({
    account_balance: 0,
    cash: 0,
    buying_power: 0,
    account_status: 'LOADING',
    margin_used: 0,
    total_pnl: 0,
    win_rate: 0,
    total_trades: 0,
    positions_open: 0,
    max_drawdown: 0,
    sharpe_ratio: 0,
    vix: 0,
    iv_rank: 0,
    options_level: 'Unknown'
  });

  const [riskMetrics, setRiskMetrics] = useState<RiskMetrics | null>(null);
  
  const [config, setConfig] = useState<TradingConfig>({
    brokerPlugin: 'alpaca',
    paperTrading: true,
    symbol: 'SPX', // Using SPX for S&P 500 index tracking
    dteMin: 30,
    dteMax: 45,
    deltaTarget: 0.10,
    creditThreshold: 0.50,
    maxSpreadWidth: 50,
    maxPositions: 5,
    positionSizePct: 0.02,
    maxMarginUsage: 0.50,
    maxDrawdown: 0.15,
    kellyFraction: 0.25
  });

  const [marketBias, setMarketBias] = useState<'BULLISH' | 'NEUTRAL' | 'BEARISH'>('NEUTRAL');
  const [confidence, setConfidence] = useState(0.72);
  const [volatilityRegime, setVolatilityRegime] = useState<'HIGH_VOL' | 'NORMAL_VOL' | 'LOW_VOL'>('NORMAL_VOL');

  // Load real account metrics
  const loadAccountMetrics = useCallback(async () => {
    try {
      // Use demo data when in demo mode
      const endpoint = isDemoMode ? '/api/demo/account/metrics' : '/api/dashboard/metrics';
      
      // Use throttled data service to prevent excessive calls
      const metrics = await dataThrottleService.getData(
        `account-metrics-${isDemoMode}`,
        async () => {
          const response = await fetch(endpoint);
          if (response.ok) {
            return await response.json();
          }
          throw new Error('Failed to fetch account metrics');
        },
        180000 // Cache for 3 minutes
      );
      
      if (metrics) {
        setAccountMetrics({
          account_balance: metrics.account_balance || 0,
          cash: metrics.cash || 0,
          buying_power: metrics.buying_power || 0,
          account_status: metrics.account_status || 'UNKNOWN',
          margin_used: metrics.margin_used || 0,
          total_pnl: metrics.total_pnl || 0,
          win_rate: metrics.win_rate || 0,
          total_trades: metrics.total_trades || 0,
          positions_open: metrics.positions_open || 0,
          max_drawdown: metrics.max_drawdown || 0,
          sharpe_ratio: metrics.sharpe_ratio || 0,
          options_level: metrics.options_level || 'Level 1',
          vix: metrics.vix || 18.5, // Default VIX value
          iv_rank: metrics.iv_rank || 45 // Default IV rank
        });
      }
    } catch (error) {
      console.error('Failed to load account metrics:', error);
    }
  }, [isDemoMode]);

  // Load advanced risk metrics
  const loadRiskMetrics = useCallback(async () => {
    try {
      // For v2.0, use mock risk metrics until analytics endpoint is implemented
      const response = { ok: false }; // await fetch('http://localhost:8000/api/analytics/risk-metrics');
      if (response.ok) {
        const metrics = await response.json();
        setRiskMetrics(metrics);
      }
    } catch (error) {
      console.error('Failed to load risk metrics:', error);
    }
  }, []);

  // Real spread candidates from backend API
  const [spreadCandidates, setSpreadCandidates] = useState<SpreadCandidate[]>([]);
  const [enhancedOpportunities, setEnhancedOpportunities] = useState<EnhancedTradeOpportunity[]>([]);
  const [tradeCategories, setTradeCategories] = useState<EnhancedTradeCategories>({
    high_probability: [],
    quick_scalps: [],
    swing_trades: [],
    volatility_plays: [],
    thetacrop: []
  });
  const [loadingOpportunities, setLoadingOpportunities] = useState(false);
  const [dataSourceInfo, setDataSourceInfo] = useState<{
    underlying_data: string;
    options_pricing: string;
    expiration_dates: string;
    disclaimer: string;
  } | null>(null);
  const [scanMethodology, setScanMethodology] = useState<{
    universe: string[];
    symbols_scanned: number;
    total_symbols: number;
    strategies: string[];
    filters: Record<string, string>;
    expiration_range: string;
    refresh_rate: string;
  } | null>(null);

  // Load real trading opportunities from backend
  const loadTradingOpportunities = useCallback(async () => {
    setLoadingOpportunities(true);
    try {
      // Use demo data when in demo mode
      const endpoint = isDemoMode ? '/api/demo/opportunities' : '/api/trading/opportunities';
      
      // Use throttled data service to prevent excessive calls
      const data = await dataThrottleService.getData(
        `trading-opportunities-${isDemoMode}`,
        async () => {
          const response = await fetch(endpoint);
          if (response.ok) {
            return await response.json();
          }
          throw new Error('Failed to fetch trading opportunities');
        },
        240000 // Cache for 4 minutes
      );
      
      if (data) {
        
        // Set enhanced opportunities
        setEnhancedOpportunities(data.opportunities || []);
        
        // Set categorized opportunities
        if (data.categories) {
          setTradeCategories(data.categories);
        }

        // Capture data source and scan methodology info
        if (data.data_source_info) {
          setDataSourceInfo(data.data_source_info);
        }
        if (data.scan_methodology) {
          setScanMethodology(data.scan_methodology);
        }
        
        // Legacy format for backward compatibility (memoized for performance)
        const rawOpportunities = data.opportunities || [];
        const candidates = rawOpportunities.map((opp: ApiOpportunity) => ({
          id: opp.id,
          symbol: opp.symbol,
          shortStrike: opp.short_strike || opp.strike,
          longStrike: opp.long_strike || (opp.strike - 5),
          credit: opp.premium,
          maxLoss: opp.max_loss * 100,
          delta: opp.delta,
          probabilityProfit: opp.probability_profit,
          expectedValue: opp.expected_value * 100,
          daysToExpiration: opp.days_to_expiration,
          underlyingPrice: opp.underlying_price,
          liquidityScore: opp.liquidity_score,
          bias: opp.bias,
          rsi: opp.rsi
        }));
        setSpreadCandidates(candidates);
      }
    } catch (error) {
      console.error('Failed to load trading opportunities:', error);
      // Fallback to empty array
      setSpreadCandidates([]);
    } finally {
      setLoadingOpportunities(false);
    }
  }, [isDemoMode]);

  // Demo mode and tour handlers
  const handleDemoModeToggle = useCallback((enabled: boolean) => {
    setIsDemoMode(enabled);
    if (enabled) {
      DemoDataService.enableDemoMode();
    } else {
      DemoDataService.disableDemoMode();
    }
    // Reload data when switching modes
    loadAccountMetrics();
    loadTradingOpportunities();
  }, [loadAccountMetrics, loadTradingOpportunities]);

  const handleStartTour = useCallback(() => {
    setShowTour(true);
  }, []);

  const handleTourComplete = useCallback(() => {
    setShowTour(false);
    DemoDataService.completeTour();
    setIsFirstVisit(false);
  }, []);

  const handleTourClose = useCallback(() => {
    setShowTour(false);
  }, []);

  // Initialize demo mode based on account balance and user status
  useEffect(() => {
    const initializeDemoMode = async () => {
      try {
        const shouldEnableDemo = await DemoDataService.shouldEnableDemoMode();
        setIsDemoMode(shouldEnableDemo);
        if (shouldEnableDemo) {
          DemoDataService.enableDemoMode();
        }
      } catch (error) {
        console.error('Failed to initialize demo mode:', error);
        // Fallback to current localStorage value or false
        setIsDemoMode(DemoDataService.isDemoMode());
      }
      setDemoModeInitialized(true);
    };

    initializeDemoMode();
  }, []);

  // Auto-start tour for first-time visitors (only after demo mode is initialized)
  useEffect(() => {
    if (demoModeInitialized && isFirstVisit && DemoDataService.shouldShowTour()) {
      // If demo mode is enabled for first-time users, start tour after a short delay
      if (isDemoMode) {
        const timer = setTimeout(() => {
          setShowTour(true);
        }, 1500);
        
        return () => clearTimeout(timer);
      }
    }
  }, [isFirstVisit, isDemoMode, demoModeInitialized]);
  
  useEffect(() => {
    // Only start loading data after demo mode has been initialized
    if (demoModeInitialized) {
      loadAccountMetrics();
      loadRiskMetrics();
      loadTradingOpportunities();
      const interval = setInterval(() => {
        loadAccountMetrics();
        loadRiskMetrics();
      }, 300000); // Update every 5 minutes (reduced from 60 seconds)
      const opportunitiesInterval = setInterval(loadTradingOpportunities, 300000); // Update every 5 minutes (reduced from 2 minutes)
      return () => {
        clearInterval(interval);
        clearInterval(opportunitiesInterval);
      };
    }
  }, [demoModeInitialized, loadAccountMetrics, loadRiskMetrics, loadTradingOpportunities]);

  const pluginStatus = [
    { name: 'Data Ingestion', status: 'active', lastUpdate: '2 min ago', plugin: 'alpaca' },
    { name: 'Signal Engine', status: 'active', lastUpdate: '1 min ago', plugin: 'composite_signals' },
    { name: 'Trade Selector', status: 'active', lastUpdate: '30 sec ago', plugin: 'dynamic_spread_selector' },
    { name: 'Risk Manager', status: 'active', lastUpdate: '45 sec ago', plugin: 'portfolio_manager' },
    { name: 'Execution Engine', status: 'standby', lastUpdate: '5 min ago', plugin: 'alpaca_paper' }
  ];

  const getBiasColor = (bias: string) => {
    switch (bias) {
      case 'BULLISH': return 'text-green-400';
      case 'BEARISH': return 'text-red-400';
      default: return 'text-yellow-400';
    }
  };

  const getBiasIcon = (bias: string) => {
    switch (bias) {
      case 'BULLISH': return <TrendingUp className="h-4 w-4" />;
      case 'BEARISH': return <TrendingDown className="h-4 w-4" />;
      default: return <Minus className="h-4 w-4" />;
    }
  };

  return (
    <TradingErrorBoundary context="trading">
      {/* Skip to content link for accessibility */}
      <a href="#main-content" className="skip-link">Skip to main content</a>
      
      
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 text-foreground">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <header className="sticky top-0 z-50 bg-background/95 backdrop-blur-md border-b border-border/40 px-6 py-4 shadow-sm">
            <div className="flex items-center justify-between w-full">
              <div>
                <h1 className="text-3xl lg:text-4xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-emerald-400 bg-clip-text text-transparent">
                  Dynamic Options Pilot
                </h1>
                <p className="text-muted-foreground mt-1 text-sm lg:text-base">Algorithmic Options Trading Platform</p>
              </div>
              <div className="flex items-center gap-3 lg:gap-4">
              {/* Demo Mode Toggle */}
              <div className="demo-mode-toggle flex items-center gap-2 px-3 py-2 bg-card/50 border rounded-lg backdrop-blur-sm">
                <Label htmlFor="demo-mode" className="text-xs lg:text-sm font-medium">Demo</Label>
                <Switch
                  id="demo-mode"
                  checked={isDemoMode}
                  onCheckedChange={handleDemoModeToggle}
                />
              </div>
            
            {/* Help Menu */}
            <HelpMenu onStartTour={handleStartTour} />
            
            {/* Tour Trigger - Show only for first-time visitors */}
            {!isFirstVisit && (
              <TourTrigger onStartTour={handleStartTour} variant="link" />
            )}
            
              <Button variant="outline" size="icon" onClick={toggleTheme} className="hover:bg-accent/50">
                {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              </Button>
              
              <Badge variant={config.paperTrading ? "secondary" : "destructive"} className="px-2 py-1 text-xs">
                {config.paperTrading ? 'Paper' : 'Live'}
              </Badge>
              
              <WebSocketStatus />
              
              <div className="dashboard-overview hidden lg:block text-right space-y-1 bg-card/30 p-3 rounded-lg backdrop-blur-sm border">
                <div className="text-xl font-bold text-emerald-400">${accountMetrics.account_balance.toLocaleString()}</div>
                <div className="text-xs text-muted-foreground">Account Balance</div>
                <div className="flex justify-between text-xs gap-4">
                  <span className="text-blue-400">Cash: ${accountMetrics.cash.toLocaleString()}</span>
                  <span className="text-purple-400">Power: ${accountMetrics.buying_power.toLocaleString()}</span>
                </div>
                <div className="text-xs text-yellow-400">Options Lvl: {accountMetrics.options_level}</div>
              </div>
              </div>
            </div>
          </header>

          <main id="main-content" role="main" className="p-8 space-y-8">
            <TieredNavigation 
              activeTab={activeTab} 
              onTabChange={handleTabChange}
            >

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Plugin Status */}
            <Card className="bg-gradient-to-br from-card to-card/50 border border-border/50 shadow-lg">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-3 text-xl font-bold">
                  <div className="p-2 bg-blue-500/20 rounded-lg">
                    <Activity className="h-5 w-5 text-blue-400" />
                  </div>
                  <span>System Status</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4">
                  {pluginStatus.map((plugin, index) => (
                     <div key={index} className="bg-gradient-to-br from-background to-muted/30 p-4 rounded-xl border border-border/40 hover:border-border/80 transition-all duration-200 hover:shadow-md">
                       <div className="flex items-center justify-between mb-3">
                         <span className="font-semibold text-sm text-foreground">{plugin.name}</span>
                         <div className={`h-3 w-3 rounded-full ${plugin.status === 'active' ? 'bg-emerald-400 shadow-lg shadow-emerald-400/50 animate-pulse' : 'bg-yellow-400 shadow-lg shadow-yellow-400/50'}`} />
                       </div>
                       <div className="text-xs text-muted-foreground mb-2 font-medium">{plugin.plugin}</div>
                       <div className="text-xs text-muted-foreground/80">{plugin.lastUpdate}</div>
                     </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Real-time Market Data and Charts */}
            <Card className="bg-gradient-to-br from-card to-card/50 border border-border/50 shadow-lg">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-3 text-xl font-bold">
                  <div className="p-2 bg-green-500/20 rounded-lg">
                    <BarChart3 className="h-5 w-5 text-green-400" />
                  </div>
                  <span>Trading Performance</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="chart-container">
                <RealTimeChart data={performanceData} marketData={marketData} isMarketOpen={isMarketOpen} />
              </CardContent>
            </Card>

            {/* Market Commentary Section */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <LazyTabContent 
                  isActive={activeTab === "overview"}
                  preload={preloadedTabs.has("overview")}
                  loadOnMount={true}
                >
                  <LazyMarketCommentary 
                    compact={false} 
                    allowCollapse={true}
                    onNavigateToCommentary={() => setActiveTab("commentary")}
                  />
                </LazyTabContent>
              </div>
              <div>
                <MarketStatusWidget compact={false} />
              </div>
            </div>

            {/* Market Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card className="bg-card border-border">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Target className="h-5 w-5 text-purple-400" />
                    <span>Market Bias</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-full bg-slate-900 ${getBiasColor(marketBias)}`}>
                      {getBiasIcon(marketBias)}
                    </div>
                    <div>
                      <div className={`text-xl font-bold ${getBiasColor(marketBias)}`}>
                        {marketBias}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Confidence: {(confidence * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                  <Progress value={confidence * 100} className="mt-4" />
                </CardContent>
              </Card>

              <Card className="bg-card border-border">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <BarChart3 className="h-5 w-5 text-orange-400" />
                    <span>Volatility Regime</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-500 mb-2">
                      {volatilityRegime.replace('_', ' ')}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      IV Rank: {(accountMetrics.iv_rank * 100).toFixed(0)}th percentile
                    </div>
                    <div className="text-sm text-muted-foreground">
                      VIX: {accountMetrics.vix.toFixed(1)}
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-card border-border">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <DollarSign className="h-5 w-5 text-green-400" />
                    <span>Portfolio Stats</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Total P&L</span>
                      <span className={`font-bold ${
                        accountMetrics.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {accountMetrics.total_pnl >= 0 ? '+' : ''}${accountMetrics.total_pnl.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Win Rate</span>
                      <span className="text-blue-400 font-medium">
                        {Math.round(accountMetrics.win_rate)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Sharpe Ratio</span>
                      <span className="text-purple-400 font-medium">
                        {accountMetrics.sharpe_ratio.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Max Drawdown</span>
                      <span className="text-yellow-400 font-medium">
                        {Math.abs(accountMetrics.max_drawdown * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Sentiment Tab */}
          <TabsContent value="sentiment" className="space-y-6">
            <LazyTabContent 
              isActive={activeTab === "sentiment"}
              preload={preloadedTabs.has("sentiment")}
            >
              <LazySentimentDashboard />
            </LazyTabContent>
          </TabsContent>

          {/* Economic Events Tab */}
          <TabsContent value="economic" className="space-y-6">
            <LazyTabContent 
              isActive={activeTab === "economic"}
              preload={preloadedTabs.has("economic")}
            >
              <LazyEconomicEventsDashboard />
            </LazyTabContent>
          </TabsContent>

          {/* AI Trade Coach Tab */}
          <TabsContent value="ai-coach" className="space-y-6">
            <LazyTabContent 
              isActive={activeTab === "ai-coach"}
              preload={preloadedTabs.has("ai-coach")}
            >
              <LazyAITradeCoach />
            </LazyTabContent>
          </TabsContent>

          {/* Enhanced Signals Tab */}
          <TabsContent value="signals" className="space-y-6">
            <LazyTabContent 
              isActive={activeTab === "signals"}
              preload={preloadedTabs.has("signals")}
            >
              <LazyEnhancedSignalsTab />
            </LazyTabContent>
          </TabsContent>

          {/* Trades Tab */}
          <TabsContent value="trades" className="space-y-6">
            {/* Data Source Warning */}
            {dataSourceInfo && (
              <div className="bg-amber-50 border-l-4 border-amber-400 p-4 rounded-md">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-amber-800">Paper Trading Data Notice</h3>
                    <div className="mt-2 text-sm text-amber-700">
                      <p>{dataSourceInfo.disclaimer}</p>
                      <div className="mt-2">
                        <p><strong>Underlying Data:</strong> {dataSourceInfo.underlying_data}</p>
                        <p><strong>Options Pricing:</strong> {dataSourceInfo.options_pricing}</p>
                        <p><strong>Expiration Dates:</strong> {dataSourceInfo.expiration_dates}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <LazyTabContent 
              isActive={activeTab === "trades"}
              preload={preloadedTabs.has("trades")}
              loadOnMount={true}
            >
              <DynamicStrategyTabs 
                onTradeExecuted={handleTradeExecuted}
                symbol={config.symbol}
              />
            </LazyTabContent>
          </TabsContent>

          {/* Positions Tab */}
          <TabsContent value="positions" className="space-y-6">
            <LazyTabContent 
              isActive={activeTab === "positions"}
              preload={preloadedTabs.has("positions")}
            >
              <LazyTradeManager />
            </LazyTabContent>
          </TabsContent>

          {/* Commentary Tab */}
          <TabsContent value="commentary" className="space-y-6">
            <LazyTabContent 
              isActive={activeTab === "commentary"}
              preload={preloadedTabs.has("commentary")}
            >
              <LazyMarketCommentary compact={false} />
            </LazyTabContent>
          </TabsContent>

          {/* Enhanced Risk Tab */}
          <TabsContent value="risk" className="space-y-6">
            <LazyTabContent 
              isActive={activeTab === "risk"}
              preload={preloadedTabs.has("risk")}
            >
              <LazyEnhancedRiskTab />
            </LazyTabContent>
          </TabsContent>

          {/* Config Tab */}
          <TabsContent value="config" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="bg-card border-border">
                <CardHeader>
                  <CardTitle>Trading Configuration</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="symbol" className="text-foreground">Symbol</Label>
                      <Input 
                        id="symbol"
                        value={config.symbol}
                        onChange={(e) => setConfig({...config, symbol: e.target.value})}
                        className="bg-input border-border"
                      />
                    </div>
                    <div>
                      <Label htmlFor="broker" className="text-foreground">Broker Plugin</Label>
                      <Input 
                        id="broker"
                        value={config.brokerPlugin}
                        onChange={(e) => setConfig({...config, brokerPlugin: e.target.value})}
                        className="bg-input border-border"
                      />
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="paper-trading"
                      checked={config.paperTrading}
                      onCheckedChange={(checked) => setConfig({...config, paperTrading: checked})}
                    />
                    <Label htmlFor="paper-trading" className="text-foreground">Paper Trading Mode</Label>
                  </div>

                  <Separator className="bg-border" />

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="dte-min" className="text-foreground">DTE Min</Label>
                      <Input 
                        id="dte-min"
                        type="number"
                        value={config.dteMin}
                        onChange={(e) => setConfig({...config, dteMin: parseInt(e.target.value)})}
                        className="bg-input border-border"
                      />
                    </div>
                    <div>
                      <Label htmlFor="dte-max" className="text-foreground">DTE Max</Label>
                      <Input 
                        id="dte-max"
                        type="number"
                        value={config.dteMax}
                        onChange={(e) => setConfig({...config, dteMax: parseInt(e.target.value)})}
                        className="bg-input border-border"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="delta-target" className="text-foreground">Delta Target</Label>
                      <Input 
                        id="delta-target"
                        type="number"
                        step="0.01"
                        value={config.deltaTarget}
                        onChange={(e) => setConfig({...config, deltaTarget: parseFloat(e.target.value)})}
                        className="bg-input border-border"
                      />
                    </div>
                    <div>
                      <Label htmlFor="credit-threshold" className="text-foreground">Credit Threshold</Label>
                      <Input 
                        id="credit-threshold"
                        type="number"
                        step="0.01"
                        value={config.creditThreshold}
                        onChange={(e) => setConfig({...config, creditThreshold: parseFloat(e.target.value)})}
                        className="bg-input border-border"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-card border-border">
                <CardHeader>
                  <CardTitle>Risk Management</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="max-positions" className="text-foreground">Max Positions</Label>
                      <Input 
                        id="max-positions"
                        type="number"
                        value={config.maxPositions}
                        onChange={(e) => setConfig({...config, maxPositions: parseInt(e.target.value)})}
                        className="bg-input border-border"
                      />
                    </div>
                    <div>
                      <Label htmlFor="position-size" className="text-foreground">Position Size %</Label>
                      <Input 
                        id="position-size"
                        type="number"
                        step="0.01"
                        value={config.positionSizePct}
                        onChange={(e) => setConfig({...config, positionSizePct: parseFloat(e.target.value)})}
                        className="bg-input border-border"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="max-margin" className="text-foreground">Max Margin Usage</Label>
                      <Input 
                        id="max-margin"
                        type="number"
                        step="0.01"
                        value={config.maxMarginUsage}
                        onChange={(e) => setConfig({...config, maxMarginUsage: parseFloat(e.target.value)})}
                        className="bg-input border-border"
                      />
                    </div>
                    <div>
                      <Label htmlFor="max-drawdown" className="text-foreground">Max Drawdown</Label>
                      <Input 
                        id="max-drawdown"
                        type="number"
                        step="0.01"
                        value={config.maxDrawdown}
                        onChange={(e) => setConfig({...config, maxDrawdown: parseFloat(e.target.value)})}
                        className="bg-input border-border"
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="kelly-fraction" className="text-foreground">Kelly Fraction</Label>
                    <Input 
                      id="kelly-fraction"
                      type="number"
                      step="0.01"
                      value={config.kellyFraction}
                      onChange={(e) => setConfig({...config, kellyFraction: parseFloat(e.target.value)})}
                      className="bg-input border-border"
                    />
                  </div>

                  <Button className="w-full bg-primary text-primary-foreground hover:bg-primary/90 mt-4">
                    Save Configuration
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          </TieredNavigation>
        
        {/* Trading Tour Component */}
        <TradingTour
          isOpen={showTour}
          onClose={handleTourClose}
          onComplete={handleTourComplete}
        />
        
        {/* Performance Monitor (dev only) */}
        <TabPerformanceMonitor 
          activeTab={activeTab}
          onPerformanceData={(data) => {
            // Log performance in development
            if (process.env.NODE_ENV === 'development') {
              console.log(`Tab ${data.tabName} loaded in ${data.loadTime}ms`);
            }
          }}
        />
          </main>
        </div>
      </div>
    </TradingErrorBoundary>
  );
});

export default TradingDashboard;
