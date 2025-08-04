import React, { useState, useEffect, useCallback } from 'react';
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
import { LiveOpportunitiesTab } from '@/components/LiveOpportunitiesTab';
import { WebSocketStatus } from '@/components/WebSocketStatus';
import { TradingTour, TourTrigger } from '@/components/TradingTour';
import MarketStatusWidget from '@/components/MarketStatusWidget';
import { DemoDataService } from '@/services/demoData';
import SystemStatus from '@/components/SystemStatus';
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
import { TieredNavigation } from '@/components/TieredNavigation';
import { HelpMenu } from '@/components/HelpMenu';
import { StrategySandboxTab } from '@/components/StrategySandboxTab';
import { useAccountMetrics } from '@/hooks/useAccountMetrics';
import { useTradingOpportunities } from '@/hooks/useTradingOpportunities';
import { useTradingConfig } from '@/hooks/useTradingConfig';

const TradingDashboard = React.memo(() => {
  const { theme, toggleTheme } = useTheme();
  const { announceToScreenReader } = useAccessibility();
  
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [demoModeInitialized, setDemoModeInitialized] = useState(false);
  const [showTour, setShowTour] = useState(false);
  const [isFirstVisit, setIsFirstVisit] = useState(DemoDataService.isFirstVisit());
  
  const { accountMetrics, loadAccountMetrics } = useAccountMetrics(isDemoMode, demoModeInitialized);
  const {
    dataSourceInfo,
    loadTradingOpportunities,
  } = useTradingOpportunities(isDemoMode, demoModeInitialized);
  const { config, setConfig } = useTradingConfig();

  const [activeTab, setActiveTab] = useState("overview");
  const [preloadedTabs, setPreloadedTabs] = useState<Set<string>>(new Set());
  
  const handleTabChange = useCallback((tabName: string) => {
    tabPerformanceService.measureTabSwitch(tabName);
    setActiveTab(tabName);
    announceToScreenReader(`Switched to ${tabName} tab`);
  }, [announceToScreenReader]);
  
  useTabPreload({
    currentTab: activeTab,
    onPreload: (tabName: string) => {
      setPreloadedTabs(prev => new Set([...prev, tabName]));
      tabPerformanceService.preloadTabResources(tabName);
    },
    preloadDelay: 500
  });

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
  
  const { 
    marketData, 
    performanceData, 
    isMarketOpen, 
    addPerformancePoint,
  } = useRealTimeData();

  const handleTradeExecuted = useCallback((pnl: number) => {
    addPerformancePoint(pnl);
    setTimeout(() => {
      setActiveTab('positions');
      announceToScreenReader("Trade executed successfully. Switched to Positions tab to view trade.");
    }, 1000);
  }, [addPerformancePoint, announceToScreenReader]);

  const [marketBias, setMarketBias] = useState<'BULLISH' | 'NEUTRAL' | 'BEARISH'>('NEUTRAL');
  const [confidence, setConfidence] = useState(0.72);
  const [volatilityRegime, setVolatilityRegime] = useState<'HIGH_VOL' | 'NORMAL_VOL' | 'LOW_VOL'>('NORMAL_VOL');

  const handleDemoModeToggle = useCallback((enabled: boolean) => {
    setIsDemoMode(enabled);
    if (enabled) {
      DemoDataService.enableDemoMode();
    } else {
      DemoDataService.disableDemoMode();
    }
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
        setIsDemoMode(DemoDataService.isDemoMode());
      }
      setDemoModeInitialized(true);
    };

    initializeDemoMode();
  }, []);

  useEffect(() => {
    if (demoModeInitialized && isFirstVisit && DemoDataService.shouldShowTour()) {
      if (isDemoMode) {
        const timer = setTimeout(() => {
          setShowTour(true);
        }, 1500);
        
        return () => clearTimeout(timer);
      }
    }
  }, [isFirstVisit, isDemoMode, demoModeInitialized]);

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
              
              <div className="dashboard-overview hidden lg:block text-right space-y-2 bg-gradient-to-br from-card/40 to-card/20 p-4 rounded-lg backdrop-blur-sm border border-border/50 shadow-lg min-w-[240px]">
                {/* Account Balance - Primary metric */}
                <div className="border-b border-border/30 pb-2">
                  <div className="text-2xl font-bold text-emerald-400">${accountMetrics.account_balance.toLocaleString()}</div>
                  <div className="text-xs text-muted-foreground">Account Balance</div>
                </div>
                
                {/* Key Trading Metrics */}
                <div className="space-y-1.5">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Cash:</span>
                    <span className="text-blue-400 font-medium">${accountMetrics.cash.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Buying Power:</span>
                    <span className="text-purple-400 font-medium">${accountMetrics.buying_power.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">P&L Today:</span>
                    <span className={`font-medium ${accountMetrics.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {accountMetrics.total_pnl >= 0 ? '+' : ''}${accountMetrics.total_pnl.toLocaleString()}
                    </span>
                  </div>
                </div>
                
                {/* Options Level & Status */}
                <div className="pt-2 border-t border-border/30">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-muted-foreground">Options Level:</span>
                    <Badge variant="secondary" className="text-xs">{accountMetrics.options_level}</Badge>
                  </div>
                  <div className="flex justify-between items-center text-xs mt-1">
                    <span className="text-muted-foreground">Status:</span>
                    <Badge variant={accountMetrics.account_status === 'ACTIVE' ? 'default' : 'secondary'} className="text-xs">
                      {accountMetrics.account_status}
                    </Badge>
                  </div>
                </div>
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

          {/* Trading → Execution Tab - Live trading opportunities from production strategies */}
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
              <LiveOpportunitiesTab
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

          {/* Strategies Tab - Strategy Sandbox for creating and testing custom strategies */}
          <TabsContent value="strategies" className="space-y-6">
            <LazyTabContent 
              isActive={activeTab === "strategies"}
              preload={preloadedTabs.has("strategies")}
            >
              <StrategySandboxTab />
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

          {/* System Status Tab */}
          <TabsContent value="system-status" className="space-y-6">
            <SystemStatus />
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
