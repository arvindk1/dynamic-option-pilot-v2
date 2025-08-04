import React, { useState, useEffect, useMemo } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Activity, TrendingUp, Target, Zap, Brain, AlertTriangle, Timer, RefreshCw, DollarSign, Shield } from 'lucide-react';
import { useStrategies, StrategyMetadata } from '@/contexts/StrategyContext';
import { TradeCard } from '@/components/TradeCard';
import { paperTradingService } from '@/services/paperTrading';
import { useToast } from '@/hooks/use-toast';

interface DynamicStrategyTabsProps {
  onTradeExecuted?: (pnl: number) => void;
  symbol?: string;
}

interface TradeOpportunity {
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
  p50_profit?: number;
  p75_profit?: number;
  p90_profit?: number;
  breakeven_probability?: number;
  confidence_intervals?: {
    pop_95?: [number, number];
  };
  value_at_risk?: number;
  sharpe_ratio?: number;
  volatility_regime?: string;
  score?: number;
}

interface TradeTypeCategories {
  high_probability: TradeOpportunity[];
  quick_scalps: TradeOpportunity[];
  swing_trades: TradeOpportunity[];
  volatility_plays: TradeOpportunity[];
}

const getCategoryIcon = (category: string) => {
  switch (category) {
    // Professional strategy categories
    case 'income_generation':
      return <DollarSign className="h-4 w-4 text-green-500" />;
    case 'volatility_trading':
      return <Activity className="h-4 w-4 text-blue-500" />;
    case 'directional_strategies':
      return <TrendingUp className="h-4 w-4 text-purple-500" />;
    case 'risk_management':
      return <Shield className="h-4 w-4 text-orange-500" />;
    case 'advanced_strategies':
      return <Brain className="h-4 w-4 text-red-500" />;
    
    // Legacy categories  
    case 'technical_analysis':
      return <TrendingUp className="h-4 w-4" />;
    case 'volatility_harvesting':
      return <Target className="h-4 w-4" />;
    case 'momentum':
      return <Zap className="h-4 w-4" />;
    case 'mean_reversion':
      return <Brain className="h-4 w-4" />;
    case 'high_probability':
      return <Target className="h-4 w-4" />;
    case 'quick_scalps':
      return <Timer className="h-4 w-4" />;
    case 'swing_trades':
      return <TrendingUp className="h-4 w-4" />;
    case 'volatility_plays':
      return <Activity className="h-4 w-4" />;
    default:
      return <Activity className="h-4 w-4" />;
  }
};

// Component to display all opportunities grouped by strategy
interface AllOpportunitiesViewProps {
  strategies: StrategyMetadata[];
  opportunitiesByStrategy: Record<string, { opportunities: TradeOpportunity[] }>;
  loadingOpportunities: Record<string, boolean>;
  onTradeExecuted?: (pnl: number) => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

const AllOpportunitiesView: React.FC<AllOpportunitiesViewProps> = ({
  strategies,
  opportunitiesByStrategy,
  loadingOpportunities,
  onTradeExecuted,
  onRefresh,
  isRefreshing = false
}) => {
  const [executingTrades, setExecutingTrades] = useState<Set<string>>(new Set());
  const { toast } = useToast();

  const handleTradeExecution = async (opportunity: TradeOpportunity) => {
    const tradeId = opportunity.id;
    if (executingTrades.has(tradeId)) return;

    try {
      setExecutingTrades(prev => new Set(prev).add(tradeId));
      
      const result = await paperTradingService.executeTrade(opportunity, 1);
      
      toast({
        title: "Trade Executed Successfully",
        description: `${opportunity.symbol} ${opportunity.strategy_type} executed for $${opportunity.premium.toFixed(2)}`,
        duration: 5000,
      });

      onTradeExecuted?.(opportunity.expected_value || 0);
      
    } catch (error) {
      console.error('Trade execution failed:', error);
      toast({
        title: "Trade Execution Failed",
        description: error instanceof Error ? error.message : "Unknown error occurred",
        variant: "destructive",
        duration: 5000,
      });
    } finally {
      setExecutingTrades(prev => {
        const newSet = new Set(prev);
        newSet.delete(tradeId);
        return newSet;
      });
    }
  };

  return (
    <div className="space-y-8">
      {strategies.map(strategy => {
        const strategyData = opportunitiesByStrategy[strategy.id];
        const isLoading = loadingOpportunities[strategy.id];
        const opportunities = strategyData?.opportunities || [];
        
        // Deduplicate opportunities by ID to prevent React key warnings
        const seen = new Set<string>();
        const uniqueOpportunities = opportunities.filter(opportunity => {
          if (seen.has(opportunity.id)) {
            return false;
          }
          seen.add(opportunity.id);
          return true;
        });

        if (isLoading) {
          return (
            <div key={strategy.id} className="space-y-4">
              <div className="flex items-center space-x-2 text-lg font-semibold text-muted-foreground">
                <Loader2 className="h-5 w-5 animate-spin" />
                <span>Loading {strategy.name}...</span>
              </div>
            </div>
          );
        }

        if (uniqueOpportunities.length === 0) {
          return (
            <div key={strategy.id} className="space-y-4">
              <div className="flex items-center justify-between border-b pb-3">
                <div className="flex items-center space-x-3">
                  {getCategoryIcon(strategy.category)}
                  <div>
                    <h3 className="text-lg font-semibold text-muted-foreground">{strategy.name}</h3>
                    <p className="text-xs text-muted-foreground">{strategy.description}</p>
                  </div>
                  <Badge variant="outline" className="text-muted-foreground">0 opportunities</Badge>
                  <Badge className={getStatusColor(strategy.status)}>{strategy.status}</Badge>
                </div>
              </div>
              
              <div className="bg-gradient-to-r from-muted/30 to-muted/10 p-4 rounded-lg border border-dashed border-muted-foreground/30">
                <div className="flex items-start space-x-3">
                  <Activity className="h-5 w-5 text-muted-foreground mt-0.5" />
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-muted-foreground mb-2">No Current Opportunities</h4>
                    <p className="text-xs text-muted-foreground/80 mb-3">
                      This strategy hasn't found any trades matching its criteria in current market conditions. 
                      Market volatility, time decay, and liquidity requirements may be outside optimal ranges.
                    </p>
                    <div className="flex items-center justify-between">
                      <div className="text-xs text-muted-foreground">
                        Last scan: {strategy.last_updated ? new Date(strategy.last_updated).toLocaleTimeString() : 'Never'}
                      </div>
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={onRefresh}
                        disabled={isRefreshing}
                        className="text-xs h-7 px-3"
                      >
                        <RefreshCw className={`h-3 w-3 mr-1 ${isRefreshing ? 'animate-spin' : ''}`} />
                        Rescan
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        }

        return (
          <div key={strategy.id} className="space-y-4">
            <div className="flex items-center justify-between border-b pb-2">
              <div className="flex items-center space-x-3">
                {getCategoryIcon(strategy.category)}
                <h3 className="text-lg font-semibold">{strategy.name}</h3>
                <Badge variant="secondary">{uniqueOpportunities.length} opportunities</Badge>
                <Badge className={getStatusColor(strategy.status)}>{strategy.status}</Badge>
              </div>
            </div>
            
            <div className="space-y-4">
              {uniqueOpportunities.map((opportunity) => (
                <TradeCard
                  key={opportunity.id}
                  trade={opportunity}
                  onExecute={handleTradeExecution}
                  isExecuting={executingTrades.has(opportunity.id)}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// Component to display opportunities for a single strategy
interface StrategyOpportunitiesViewProps {
  opportunities: TradeOpportunity[];
  loading: boolean;
  onTradeExecuted?: (pnl: number) => void;
}

const StrategyOpportunitiesView: React.FC<StrategyOpportunitiesViewProps> = ({
  opportunities,
  loading,
  onTradeExecuted
}) => {
  const [executingTrades, setExecutingTrades] = useState<Set<string>>(new Set());
  const { toast } = useToast();
  
  // Deduplicate opportunities by ID to prevent React key warnings
  const uniqueOpportunities = useMemo(() => {
    const seen = new Set<string>();
    return opportunities.filter(opportunity => {
      if (seen.has(opportunity.id)) {
        return false;
      }
      seen.add(opportunity.id);
      return true;
    });
  }, [opportunities]);

  const handleTradeExecution = async (opportunity: TradeOpportunity) => {
    const tradeId = opportunity.id;
    if (executingTrades.has(tradeId)) return;

    try {
      setExecutingTrades(prev => new Set(prev).add(tradeId));
      
      const result = await paperTradingService.executeTrade(opportunity, 1);
      
      toast({
        title: "Trade Executed Successfully",
        description: `${opportunity.symbol} ${opportunity.strategy_type} executed for $${opportunity.premium.toFixed(2)}`,
        duration: 5000,
      });

      onTradeExecuted?.(opportunity.expected_value || 0);
      
    } catch (error) {
      console.error('Trade execution failed:', error);
      toast({
        title: "Trade Execution Failed",
        description: error instanceof Error ? error.message : "Unknown error occurred",
        variant: "destructive",
        duration: 5000,
      });
    } finally {
      setExecutingTrades(prev => {
        const newSet = new Set(prev);
        newSet.delete(tradeId);
        return newSet;
      });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Loading opportunities...</span>
        </div>
      </div>
    );
  }

  if (opportunities.length === 0) {
    return (
      <Alert>
        <Activity className="h-4 w-4" />
        <AlertDescription className="flex items-center justify-between">
          <span>No opportunities found for current market conditions.</span>
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      {uniqueOpportunities.map((opportunity) => (
        <TradeCard
          key={opportunity.id}
          trade={opportunity}
          onExecute={handleTradeExecution}
          isExecuting={executingTrades.has(opportunity.id)}
        />
      ))}
    </div>
  );
};

const getCategoryColor = (category: string) => {
  switch (category) {
    // Professional strategy categories with distinct color schemes
    case 'income_generation':
      return 'text-green-700 bg-green-50 border-green-200';
    case 'volatility_trading':
      return 'text-blue-700 bg-blue-50 border-blue-200';
    case 'directional_strategies':
      return 'text-purple-700 bg-purple-50 border-purple-200';
    case 'risk_management':
      return 'text-orange-700 bg-orange-50 border-orange-200';
    case 'advanced_strategies':
      return 'text-red-700 bg-red-50 border-red-200';
    
    // Legacy categories
    case 'technical_analysis':
      return 'text-blue-600 bg-blue-50';
    case 'volatility_harvesting':
      return 'text-green-600 bg-green-50';
    case 'momentum':
      return 'text-orange-600 bg-orange-50';
    case 'mean_reversion':
      return 'text-purple-600 bg-purple-50';
    case 'high_probability':
      return 'text-emerald-600 bg-emerald-50';
    case 'quick_scalps':
      return 'text-red-600 bg-red-50';
    case 'swing_trades':
      return 'text-indigo-600 bg-indigo-50';
    case 'volatility_plays':
      return 'text-orange-600 bg-orange-50';
    default:
      return 'text-gray-600 bg-gray-50';
  }
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'active':
      return 'bg-green-100 text-green-800';
    case 'inactive':
      return 'bg-yellow-100 text-yellow-800';
    case 'error':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};


export const DynamicStrategyTabs: React.FC<DynamicStrategyTabsProps> = ({ 
  onTradeExecuted,
  symbol = 'SPY'
}) => {
  const { 
    strategies, 
    categories, 
    loading: strategiesLoading, 
    error,
    opportunitiesByStrategy,
    loadingOpportunities,
    getStrategiesByCategory,
    getAllOpportunities,
    getOpportunitiesByCategory,
    getStrategyOpportunities,
    refreshAllOpportunities
  } = useStrategies();

  const [activeTab, setActiveTab] = useState('all');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const { toast } = useToast();

  const handleRefresh = async () => {
    try {
      setIsRefreshing(true);
      await refreshAllOpportunities();
      toast({
        title: "Opportunities Refreshed",
        description: "All strategies have been scanned for new opportunities.",
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: "Refresh Failed",
        description: "Failed to refresh opportunities. Please try again.",
        variant: "destructive",
        duration: 5000,
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  // Trade type categories
  const tradeTypeCategories = ['high_probability', 'quick_scalps', 'swing_trades', 'volatility_plays'];
  
  // Check which row type is active
  const isStrategyTab = activeTab === 'all' || categories.includes(activeTab);
  const isTradeTypeTab = tradeTypeCategories.includes(activeTab);
  
  const getOpportunitiesByTradeType = (tradeType: string, allOpportunities: TradeOpportunity[]): TradeOpportunity[] => {
    switch (tradeType) {
      case 'high_probability':
        return allOpportunities.filter(opp => (opp.probability_profit || 0) > 0.75);
      case 'quick_scalps':
        return allOpportunities.filter(opp => (opp.days_to_expiration || 0) <= 7);
      case 'swing_trades':
        return allOpportunities.filter(opp => (opp.days_to_expiration || 0) > 30);
      case 'volatility_plays':
        return allOpportunities.filter(opp => 
          opp.strategy_type === 'IRON_CONDOR' || 
          opp.strategy_type === 'STRADDLE' || 
          opp.strategy_type === 'STRANGLE' ||
          (opp.volatility_rank && opp.volatility_rank > 50)
        );
      default:
        return [];
    }
  };

  // Refresh opportunities when symbol changes
  useEffect(() => {
    strategies.forEach(strategy => {
      if (strategy.status === 'active') {
        getStrategyOpportunities(strategy.id, symbol);
      }
    });
  }, [symbol]);

  if (strategiesLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Loading trading strategies...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Failed to load trading strategies: {error}
        </AlertDescription>
      </Alert>
    );
  }

  const allOpportunities = getAllOpportunities();

  return (
    <div className="space-y-6">
      {/* Enhanced Header with Strategy Overview */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-4">
          <Activity className="h-7 w-7 text-primary" />
          <div>
            <h2 className="text-2xl font-bold bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
              Trading Opportunities
            </h2>
            <div className="flex items-center space-x-4 mt-1">
              <p className="text-sm text-muted-foreground">
                <span className="font-semibold text-foreground">{allOpportunities.length}</span> opportunities across{' '}
                <span className="font-semibold text-foreground">{strategies.length}</span> strategies
              </p>
              <div className="flex items-center space-x-2">
                <Badge variant="secondary" className="text-xs">
                  {strategies.filter(s => s.status === 'active').length} Active
                </Badge>
                <Badge variant="outline" className="text-xs">
                  {categories.length} Categories
                </Badge>
              </div>
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Strategy Status Indicators */}
          <div className="hidden md:flex items-center space-x-2 text-xs text-muted-foreground bg-muted/30 px-3 py-2 rounded-lg">
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>{strategies.filter(s => s.status === 'active').length} Active</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
              <span>{strategies.filter(s => s.status === 'inactive').length} Inactive</span>
            </div>
          </div>
          
          <Button 
            onClick={handleRefresh} 
            disabled={isRefreshing}
            variant="outline"
            size="sm"
            className="flex items-center space-x-2 shadow-sm"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>{isRefreshing ? 'Scanning...' : 'Refresh All'}</span>
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        {/* Two-row tab layout with proper TabsList structure */}
        <TabsList className="h-auto p-2 bg-muted/30">
          <div className="space-y-2 w-full">
            {/* First row - Strategy-based tabs */}
            <div className={`flex items-center space-x-1 p-1 rounded-lg transition-colors ${
              isStrategyTab ? 'bg-primary/5 border border-primary/20' : 'bg-background border border-border/50'
            }`}>
              <div className={`text-xs font-medium px-2 py-1 min-w-fit ${
                isStrategyTab ? 'text-primary' : 'text-muted-foreground'
              }`}>
                By Strategy:
              </div>
              <div className="flex flex-wrap gap-1 flex-1">
                <TabsTrigger value="all" className="flex items-center space-x-2 whitespace-nowrap px-3 py-2 h-8 text-xs data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
                  <Activity className="h-3 w-3" />
                  <span>All</span>
                  <Badge variant="secondary" className="ml-1 text-xs">
                    {allOpportunities.length}
                  </Badge>
                </TabsTrigger>
                
                {categories.map(category => {
                  const categoryOpportunities = getOpportunitiesByCategory(category);
                  
                  return (
                    <TabsTrigger 
                      key={category} 
                      value={category}
                      className="flex items-center space-x-2 whitespace-nowrap px-3 py-2 h-8 text-xs data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
                    >
                      {getCategoryIcon(category)}
                      <span className="capitalize">
                        {category.replace('_', ' ')}
                      </span>
                      <Badge variant="secondary" className="ml-1 text-xs">
                        {categoryOpportunities.length}
                      </Badge>
                    </TabsTrigger>
                  );
                })}
              </div>
            </div>
            
            {/* Second row - Trade-type tabs */}
            <div className={`flex items-center space-x-1 p-1 rounded-lg transition-colors ${
              isTradeTypeTab ? 'bg-primary/5 border border-primary/20' : 'bg-background border border-border/50'
            }`}>
              <div className={`text-xs font-medium px-2 py-1 min-w-fit ${
                isTradeTypeTab ? 'text-primary' : 'text-muted-foreground'
              }`}>
                By Trade Type:
              </div>
              <div className="flex flex-wrap gap-1 flex-1">
                {tradeTypeCategories.map(tradeType => {
                  const tradeTypeOpportunities = getOpportunitiesByTradeType(tradeType, allOpportunities);
                  
                  return (
                    <TabsTrigger 
                      key={tradeType} 
                      value={tradeType}
                      className="flex items-center space-x-2 whitespace-nowrap px-3 py-2 h-8 text-xs data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
                    >
                      {getCategoryIcon(tradeType)}
                      <span className="capitalize">
                        {tradeType.replace('_', ' ')}
                      </span>
                      <Badge variant="secondary" className="ml-1 text-xs">
                        {tradeTypeOpportunities.length}
                      </Badge>
                    </TabsTrigger>
                  );
                })}
              </div>
            </div>
          </div>
        </TabsList>

        <TabsContent value="all" className="mt-6">
          <div className="mb-6 p-4 bg-blue-50 rounded-lg border">
            <div className="flex items-center space-x-2 text-blue-800">
              <Activity className="h-5 w-5" />
              <h3 className="font-semibold">All Trading Strategies</h3>
            </div>
            <p className="text-sm text-blue-600 mt-1">
              Complete analysis across all {strategies.length} trading strategies with {allOpportunities.length} total opportunities.
            </p>
          </div>
          
          <AllOpportunitiesView 
            strategies={strategies}
            opportunitiesByStrategy={opportunitiesByStrategy}
            loadingOpportunities={loadingOpportunities}
            onTradeExecuted={onTradeExecuted}
            onRefresh={handleRefresh}
            isRefreshing={isRefreshing}
          />
        </TabsContent>

        {categories.map(category => {
          const categoryStrategies = getStrategiesByCategory(category);
          const categoryOpportunities = getOpportunitiesByCategory(category);
          
          const getCategoryDescription = (cat: string) => {
            switch (cat) {
              case 'income_generation':
                return 'Conservative strategies focused on consistent premium collection with high probability of profit. Ideal for generating steady income through theta decay.';
              case 'volatility_trading':
                return 'Market-neutral strategies that profit from volatility expansion or contraction. Best used when IV rank is at extremes.';
              case 'directional_strategies':
                return 'Strategies that benefit from price movement in a specific direction. Higher profit potential with directional market moves.';
              case 'risk_management':
                return 'Protective strategies designed to limit downside risk while maintaining upside potential. Essential for portfolio protection.';
              case 'advanced_strategies':
                return 'Sophisticated strategies requiring deeper market analysis and timing. Higher complexity with potentially higher returns.';
              default:
                return `${categoryStrategies.length} strategies in this category with ${categoryOpportunities.length} current opportunities.`;
            }
          };
          
          const getCategoryRiskLevel = (cat: string) => {
            switch (cat) {
              case 'income_generation': return 'Low-Medium Risk';
              case 'volatility_trading': return 'Medium-High Risk';
              case 'directional_strategies': return 'Medium Risk';
              case 'risk_management': return 'Low Risk';
              case 'advanced_strategies': return 'Medium-High Risk';
              default: return 'Variable Risk';
            }
          };
          
          return (
            <TabsContent key={category} value={category} className="mt-6">
              <div className={`mb-6 p-5 rounded-lg border-2 ${getCategoryColor(category)}`}>
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    {getCategoryIcon(category)}
                    <div>
                      <h3 className="text-lg font-bold capitalize">
                        {category.replace('_', ' ')} Strategies
                      </h3>
                      <div className="flex items-center space-x-3 mt-1">
                        <Badge variant="outline" className="text-xs">
                          {getCategoryRiskLevel(category)}
                        </Badge>
                        <span className="text-sm opacity-80">
                          {categoryStrategies.length} strategies • {categoryOpportunities.length} opportunities
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                <p className="text-sm opacity-90 leading-relaxed">
                  {getCategoryDescription(category)}
                </p>
              </div>
              
              <StrategyOpportunitiesView
                opportunities={categoryOpportunities}
                loading={categoryStrategies.some(s => loadingOpportunities[s.id])}
                onTradeExecuted={onTradeExecuted}
              />
            </TabsContent>
          );
        })}

        {tradeTypeCategories.map(tradeType => {
          const tradeTypeOpportunities = getOpportunitiesByTradeType(tradeType, allOpportunities);
          
          const getTradeTypeDescription = (type: string) => {
            switch (type) {
              case 'high_probability':
                return 'High win-rate trades with >75% probability of profit - conservative income strategies.';
              case 'quick_scalps':
                return 'Short-term opportunities (0-7 DTE) for quick momentum plays and rapid profit capture.';
              case 'swing_trades':
                return 'Longer-term positions (30+ DTE) for sustained moves and reduced time decay impact.';
              case 'volatility_plays':
                return 'Strategies targeting volatility expansion/contraction - straddles, strangles, and iron condors.';
              default:
                return '';
            }
          };
          
          return (
            <TabsContent key={tradeType} value={tradeType} className="mt-6">
              <div className={`mb-6 p-4 rounded-lg border ${getCategoryColor(tradeType)}`}>
                <div className="flex items-center space-x-2 mb-2">
                  {getCategoryIcon(tradeType)}
                  <h3 className="font-semibold capitalize">
                    {tradeType.replace('_', ' ')}
                  </h3>
                </div>
                <p className="text-sm opacity-80">
                  {getTradeTypeDescription(tradeType)}
                </p>
                <p className="text-sm opacity-80 mt-1">
                  {tradeTypeOpportunities.length} opportunities available
                </p>
              </div>
              
              <StrategyOpportunitiesView
                opportunities={tradeTypeOpportunities}
                loading={false}
                onTradeExecuted={onTradeExecuted}
              />
            </TabsContent>
          );
        })}
      </Tabs>
    </div>
  );
};