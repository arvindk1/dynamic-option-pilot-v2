/**
 * TradingTabsContainer - Optimized tab navigation with lazy loading
 * Handles tab switching and performance monitoring for trading dashboard
 */
import React, { memo, useCallback, useMemo, Suspense } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { 
  Activity,
  BarChart3,
  Brain,
  Database,
  Newspaper,
  Settings,
  Shield,
  Target,
  TrendingUp,
  Zap
} from 'lucide-react';
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
import { DynamicStrategyTabs } from '@/components/DynamicStrategyTabs';
import { StrategiesTab } from '@/components/StrategiesTab';
import { TradingCardSkeleton } from '@/components/LoadingStates';
import TradingErrorBoundary from '@/components/TradingErrorBoundary';
import { TabPerformanceMonitor } from '@/components/TabPerformanceMonitor';

interface TabDefinition {
  key: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
  description: string;
  component: React.ComponentType<any>;
  preload?: boolean;
}

interface TradingTabsContainerProps {
  activeTab: string;
  onTabChange: (tabName: string) => void;
  preloadedTabs: Set<string>;
  onTabPreload: (tabName: string) => void;
  // Props for various tabs
  accountMetrics?: any;
  riskMetrics?: any;
  config?: any;
  onConfigUpdate?: (config: any) => void;
  onTradeExecuted?: (pnl: number) => void;
}

const TabLoadingFallback = memo(({ tabName }: { tabName: string }) => (
  <div className="space-y-4 p-4">
    <div className="flex items-center space-x-2">
      <div className="h-4 w-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
      <div className="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
    </div>
    <TradingCardSkeleton />
    <TradingCardSkeleton />
  </div>
));

TabLoadingFallback.displayName = 'TabLoadingFallback';

export const TradingTabsContainer = memo<TradingTabsContainerProps>(({
  activeTab,
  onTabChange,
  preloadedTabs,
  onTabPreload,
  accountMetrics,
  riskMetrics,
  config,
  onConfigUpdate,
  onTradeExecuted
}) => {
  // Define tabs configuration - memoized for performance
  const tabsConfig = useMemo((): TabDefinition[] => [
    {
      key: 'overview',
      label: 'Overview',
      icon: Activity,
      description: 'Account overview and quick metrics',
      component: LazyTabContent,
      preload: true
    },
    {
      key: 'trading',
      label: 'Trading',
      icon: TrendingUp,
      badge: 'Live',
      description: 'Active trading opportunities',
      component: DynamicStrategyTabs
    },
    {
      key: 'strategies',
      label: 'Strategies',
      icon: Target,
      description: 'Strategy configuration and sandbox',
      component: StrategiesTab
    },
    {
      key: 'signals',
      label: 'Signals',
      icon: Zap,
      badge: 'AI',
      description: 'Trading signals and alerts',
      component: LazyEnhancedSignalsTab
    },
    {
      key: 'risk',
      label: 'Risk',
      icon: Shield,
      description: 'Risk management and analysis',
      component: LazyEnhancedRiskTab
    },
    {
      key: 'positions',
      label: 'Positions',
      icon: BarChart3,
      description: 'Position management',
      component: LazyTradeManager
    },
    {
      key: 'market',
      label: 'Market',
      icon: Database,
      description: 'Market data and analysis',
      component: LazyMarketCommentary
    },
    {
      key: 'sentiment',
      label: 'Sentiment',
      icon: Brain,
      description: 'Market sentiment analysis',
      component: LazySentimentDashboard
    },
    {
      key: 'events',
      label: 'Events',
      icon: Newspaper,
      description: 'Economic events calendar',
      component: LazyEconomicEventsDashboard
    },
    {
      key: 'ai-coach',
      label: 'AI Coach',
      icon: Brain,
      badge: 'Beta',
      description: 'AI trading assistance',
      component: LazyAITradeCoach
    }
  ], []);

  // Handle tab change with preloading
  const handleTabChange = useCallback((newTab: string) => {
    console.log(`🔄 Switching to tab: ${newTab}`);
    
    // Preload adjacent tabs for better UX
    const currentIndex = tabsConfig.findIndex(tab => tab.key === newTab);
    if (currentIndex >= 0) {
      // Preload next tab
      if (currentIndex < tabsConfig.length - 1) {
        const nextTab = tabsConfig[currentIndex + 1].key;
        if (!preloadedTabs.has(nextTab)) {
          setTimeout(() => onTabPreload(nextTab), 100);
        }
      }
      // Preload previous tab
      if (currentIndex > 0) {
        const prevTab = tabsConfig[currentIndex - 1].key;
        if (!preloadedTabs.has(prevTab)) {
          setTimeout(() => onTabPreload(prevTab), 200);
        }
      }
    }
    
    onTabChange(newTab);
  }, [tabsConfig, preloadedTabs, onTabPreload, onTabChange]);

  // Render tab content with error boundary
  const renderTabContent = useCallback((tab: TabDefinition) => {
    const Component = tab.component;
    
    // Props mapping for different tab types
    const getTabProps = () => {
      switch (tab.key) {
        case 'overview':
          return { 
            tabName: 'overview',
            accountMetrics,
            riskMetrics
          };
        case 'trading':
          return {
            onTradeExecuted,
            accountMetrics
          };
        case 'strategies':
          return {
            config,
            onConfigUpdate
          };
        case 'risk':
          return {
            riskMetrics,
            accountMetrics
          };
        case 'ai-coach':
          return {
            accountMetrics,
            riskMetrics
          };
        default:
          return {};
      }
    };

    return (
      <TradingErrorBoundary key={tab.key} tabName={tab.key}>
        <Suspense fallback={<TabLoadingFallback tabName={tab.key} />}>
          <Component {...getTabProps()} />
        </Suspense>
      </TradingErrorBoundary>
    );
  }, [accountMetrics, riskMetrics, config, onConfigUpdate, onTradeExecuted]);

  return (
    <div className="w-full">
      <TabPerformanceMonitor />
      
      <Tabs 
        value={activeTab} 
        onValueChange={handleTabChange}
        className="w-full"
      >
        {/* Tab Navigation */}
        <TabsList className="grid w-full grid-cols-5 lg:grid-cols-10 gap-1 h-auto p-1">
          {tabsConfig.map((tab) => (
            <TabsTrigger
              key={tab.key}
              value={tab.key}
              className="flex items-center space-x-2 px-3 py-2 text-xs font-medium transition-all data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm"
              title={tab.description}
            >
              <tab.icon className="h-4 w-4 flex-shrink-0" />
              <span className="hidden sm:inline truncate">{tab.label}</span>
              {tab.badge && (
                <Badge 
                  variant="secondary" 
                  className="ml-1 px-1 py-0 text-xs h-4 hidden md:inline-flex"
                >
                  {tab.badge}
                </Badge>
              )}
            </TabsTrigger>
          ))}
        </TabsList>

        {/* Tab Contents */}
        {tabsConfig.map((tab) => (
          <TabsContent 
            key={tab.key}
            value={tab.key}
            className="mt-4 space-y-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            tabIndex={-1}
          >
            {renderTabContent(tab)}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
});

TradingTabsContainer.displayName = 'TradingTabsContainer';

export default TradingTabsContainer;