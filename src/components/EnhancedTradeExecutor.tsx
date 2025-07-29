import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { paperTradingService } from '@/services/paperTrading';
import { useToast } from '@/hooks/use-toast';
import { RSICouponCard } from './RSICouponCard';
import { TradeCard, RiskValidationDialog } from './TradeCard';
import { 
  Zap, 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Target, 
  Star, 
  DollarSign, 
  Timer, 
  Gauge,
  TrendingDown as Volatility,
  Calendar,
  BarChart3,
  Shield,
  AlertTriangle,
  CheckCircle,
  Brain
} from 'lucide-react';

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
  // Enhanced Phase 3 metrics
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

interface TradeCategories {
  high_probability: TradeOpportunity[];
  quick_scalps: TradeOpportunity[];
  swing_trades: TradeOpportunity[];
  volatility_plays: TradeOpportunity[];
  thetacrop: TradeOpportunity[];
}

interface RiskValidationResult {
  valid: boolean;
  warnings: string[];
  margin_required: number;
  buying_power_effect: number;
  max_loss: number;
  max_profit: number;
  break_even: number;
  margin_usage_pct: number;
  position_count_after: number;
  new_delta_exposure: number;
}

interface DataSourceInfo {
  underlying_data: string;
  options_pricing: string;
  expiration_dates: string;
  disclaimer: string;
}

interface ScanMethodology {
  universe: string[];
  symbols_scanned: number;
  total_symbols: number;
  strategies: string[];
  filters: Record<string, string>;
  expiration_range: string;
  refresh_rate: string;
}

interface EnhancedTradeExecutorProps {
  opportunities: TradeOpportunity[];
  categories: TradeCategories;
  onTradeExecuted?: (pnl: number) => void;
  loadingOpportunities?: boolean;
  dataSourceInfo?: DataSourceInfo;
  scanMethodology?: ScanMethodology;
}

export const EnhancedTradeExecutor: React.FC<EnhancedTradeExecutorProps> = ({ 
  opportunities, 
  categories,
  onTradeExecuted,
  loadingOpportunities = false,
  dataSourceInfo,
  scanMethodology
}) => {
  const { toast } = useToast();
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [pendingTrade, setPendingTrade] = useState<TradeOpportunity | null>(null);
  const [riskValidation, setRiskValidation] = useState<RiskValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [showRiskDialog, setShowRiskDialog] = useState(false);

  const validateTradeRisk = async (trade: TradeOpportunity): Promise<RiskValidationResult> => {
    const response = await fetch('/api/trading/validate-risk', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        id: trade.id,
        symbol: trade.symbol,
        strategy_type: trade.strategy_type,
        option_type: trade.option_type,
        strike: trade.strike,
        short_strike: trade.short_strike,
        long_strike: trade.long_strike,
        expiration: trade.expiration,
        days_to_expiration: trade.days_to_expiration,
        premium: trade.premium || trade.credit,
        quantity: 1
      }),
    });

    if (!response.ok) {
      throw new Error('Risk validation failed');
    }

    return response.json();
  };

  const handleExecuteTrade = async (trade: TradeOpportunity) => {
    try {
      setIsValidating(true);
      setPendingTrade(trade);
      
      // Validate risk first
      const validation = await validateTradeRisk(trade);
      setRiskValidation(validation);

      if (!validation.valid) {
        // Show risk warning dialog
        setShowRiskDialog(true);
        setIsValidating(false);
        return;
      }

      // If validation passes, execute directly
      await executeTrade(trade);
    } catch (error) {
      console.error('Risk validation error:', error);
      toast({
        title: "Risk Validation Failed",
        description: `Unable to validate trade risk: ${error instanceof Error ? error.message : 'Unknown error'}`,
        variant: "destructive",
      });
      setIsValidating(false);
      setPendingTrade(null);
      setRiskValidation(null);
    }
  };

  const executeTrade = async (trade: TradeOpportunity) => {
    try {
      setIsValidating(true);
      const tradeOrder = {
        ...trade,
        expiration: trade.expiration
      };
      
      const executedTrade = await paperTradingService.executeTrade(tradeOrder, 1);
      
      toast({
        title: "Trade Executed!",
        description: `${trade.strategy_type} ${trade.symbol} executed for order ${executedTrade.order_id}`,
      });

      if (onTradeExecuted && executedTrade.execution_price) {
        onTradeExecuted(executedTrade.execution_price * 100);
      }
    } catch (error) {
      console.error('Trade execution error:', error);
      toast({
        title: "Execution Failed",
        description: `Failed to execute trade: ${error instanceof Error ? error.message : 'Unknown error'}`,
        variant: "destructive",
      });
    } finally {
      setIsValidating(false);
      setPendingTrade(null);
      setRiskValidation(null);
      setShowRiskDialog(false);
    }
  };

  const handleRiskDialogConfirm = () => {
    if (pendingTrade) {
      executeTrade(pendingTrade);
    }
  };

  const handleRiskDialogCancel = () => {
    setShowRiskDialog(false);
    setPendingTrade(null);
    setRiskValidation(null);
    setIsValidating(false);
  };

  const getBiasIcon = (bias: string) => {
    switch (bias) {
      case 'BULLISH': return <TrendingUp className="h-4 w-4 text-green-400" />;
      case 'BEARISH': return <TrendingDown className="h-4 w-4 text-red-400" />;
      case 'NEUTRAL': return <Activity className="h-4 w-4 text-yellow-400" />;
      default: return <Activity className="h-4 w-4 text-gray-400" />;
    }
  };

  const getBiasColor = (bias: string) => {
    switch (bias) {
      case 'BULLISH': return 'text-green-400';
      case 'BEARISH': return 'text-red-400';
      case 'NEUTRAL': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  const getSetupIcon = (setup: string) => {
    switch (setup) {
      case 'MOMENTUM': return <Zap className="h-4 w-4 text-blue-400" />;
      case 'MEAN_REVERSION': return <Target className="h-4 w-4 text-purple-400" />;
      case 'VOLATILITY': return <Volatility className="h-4 w-4 text-orange-400" />;
      case 'EARNINGS': return <Brain className="h-4 w-4 text-cyan-400" />;
      default: return <Activity className="h-4 w-4 text-gray-400" />;
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'LOW': return 'bg-green-100 text-green-800';
      case 'MEDIUM': return 'bg-yellow-100 text-yellow-800';
      case 'HIGH': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStrategyBadgeColor = (strategy: string) => {
    switch (strategy) {
      case 'SINGLE_OPTION': return 'bg-blue-100 text-blue-800';
      case 'CREDIT_SPREAD': return 'bg-purple-100 text-purple-800';
      case 'IRON_CONDOR': return 'bg-orange-100 text-orange-800';
      case 'RSI_COUPON': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getLiquidityStars = (score: number) => {
    const stars = Math.min(5, Math.max(1, Math.round(score / 2)));
    return Array.from({ length: 5 }, (_, i) => (
      <Star 
        key={i} 
        className={`h-3 w-3 ${i < stars ? 'text-yellow-400 fill-current' : 'text-gray-600'}`} 
      />
    ));
  };

  const renderTradeCard = (trade: TradeOpportunity) => {
    // Special handling for RSI Coupon strategy
    if (trade.strategy_type === 'RSI_COUPON') {
      return <RSICouponCard key={trade.id} opportunity={trade} onExecute={handleExecuteTrade} />;
    }
    
    return (
    <div key={trade.id} className="bg-muted p-6 rounded-lg border border-border hover:bg-muted/80 transition-colors">
      {/* Header Row */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-4">
          <Badge variant="outline" className="text-lg font-bold">
            {trade.symbol}
          </Badge>
          <Badge className={getStrategyBadgeColor(trade.strategy_type)}>
            {trade.strategy_type.replace('_', ' ')}
          </Badge>
          <div className="flex items-center space-x-1">
            {getBiasIcon(trade.bias)}
            <span className={`text-sm font-medium ${getBiasColor(trade.bias)}`}>
              {trade.bias}
            </span>
          </div>
          <div className="flex items-center space-x-1">
            {getSetupIcon(trade.trade_setup)}
            <span className="text-sm font-medium">{trade.trade_setup}</span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-sm text-muted-foreground">Underlying</div>
          <div className="font-bold">${(trade.underlying_price || 0).toFixed(2)}</div>
        </div>
      </div>

      {/* Strategy-specific details */}
      {trade.strategy_type === 'SINGLE_OPTION' && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div className="text-center">
            <div className="text-xs text-muted-foreground mb-1">Type</div>
            <Badge variant={trade.option_type === 'PUT' ? 'secondary' : 'outline'}>
              {trade.option_type}
            </Badge>
          </div>
          <div className="text-center">
            <div className="text-xs text-muted-foreground mb-1">Strike</div>
            <div className="font-mono font-bold">${trade.strike?.toFixed(2)}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-muted-foreground mb-1">Premium</div>
            <div className="text-green-600 font-bold">${(trade.premium || 0).toFixed(2)}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-muted-foreground mb-1">Max Loss</div>
            <div className="text-red-600 font-bold">${(trade.max_loss || 0).toFixed(2)}</div>
          </div>
        </div>
      )}

      {trade.strategy_type === 'CREDIT_SPREAD' && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div className="text-center">
            <div className="text-xs text-muted-foreground mb-1">Type</div>
            <Badge variant={trade.option_type === 'PUT' ? 'secondary' : 'outline'}>
              {trade.option_type} Spread
            </Badge>
          </div>
          <div className="text-center">
            <div className="text-xs text-muted-foreground mb-1">Strikes</div>
            <div className="font-mono font-bold">
              {trade.short_strike?.toFixed(0)}/{trade.long_strike?.toFixed(0)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-muted-foreground mb-1">Credit</div>
            <div className="text-green-600 font-bold">${(trade.premium || 0).toFixed(2)}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-muted-foreground mb-1">Max Loss</div>
            <div className="text-red-600 font-bold">${(trade.max_loss || 0).toFixed(2)}</div>
          </div>
        </div>
      )}

      {/* Enhanced Greeks and Technical Data */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-4">
        <div className="text-center">
          <div className="text-xs text-muted-foreground mb-1">Delta</div>
          <div className="font-mono font-medium">{(trade.delta || 0).toFixed(3)}</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-muted-foreground mb-1">Gamma</div>
          <div className="font-mono font-medium">{trade.gamma?.toFixed(4) || '--'}</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-muted-foreground mb-1">Theta</div>
          <div className="font-mono font-medium">{trade.theta?.toFixed(3) || '--'}</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-muted-foreground mb-1">Vega</div>
          <div className="font-mono font-medium">{trade.vega?.toFixed(4) || '--'}</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-muted-foreground mb-1">IV</div>
          <div className="font-medium">{trade.implied_volatility ? (trade.implied_volatility * 100).toFixed(1) + '%' : '--'}</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-muted-foreground mb-1">DTE</div>
          <div className="font-medium">{trade.days_to_expiration}d</div>
        </div>
      </div>

      {/* Enhanced Profitability and Risk Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
        <div className="bg-background p-3 rounded border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">POP</span>
            <span className="text-lg font-bold text-blue-600">
              {(trade.probability_profit || 0).toFixed(1)}%
            </span>
          </div>
          <div className="text-xs text-muted-foreground">
            {trade.confidence_intervals?.pop_95 && (
              <span>95% CI: {(trade.confidence_intervals?.pop_95?.[0] || 0).toFixed(1)}%-{(trade.confidence_intervals?.pop_95?.[1] || 0).toFixed(1)}%</span>
            )}
          </div>
          <Progress value={trade.probability_profit * 100} className="h-2" />
        </div>
        
        <div className="bg-background p-3 rounded border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">P50 Profit</span>
            <span className={`text-lg font-bold ${(trade.p50_profit || trade.expected_value) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${(trade.p50_profit || trade.expected_value || 0).toFixed(2)}
            </span>
          </div>
          <div className="text-xs text-muted-foreground">
            {trade.p75_profit && (
              <span>P75: ${(trade.p75_profit || 0).toFixed(2)} | P90: ${(trade.p90_profit || 0).toFixed(2)}</span>
            )}
          </div>
        </div>
        
        <div className="bg-background p-3 rounded border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Risk Level</span>
            <Badge className={getRiskColor(trade.risk_level)}>
              {trade.risk_level}
            </Badge>
          </div>
          <div className="text-xs text-muted-foreground">
            Max profit: ${trade.max_profit === 999.99 ? 'Unlimited' : (trade.max_profit || 0).toFixed(2)}
          </div>
        </div>
        
        <div className="bg-background p-3 rounded border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Vol Analysis</span>
            <Badge variant={trade.volatility_regime === 'HIGH_VOLATILITY' ? 'destructive' : 
                           trade.volatility_regime === 'LOW_VOLATILITY' ? 'secondary' : 'default'}>
              {trade.volatility_regime?.replace('_', ' ') || 'Normal'}
            </Badge>
          </div>
          <div className="text-xs text-muted-foreground">
            {trade.sharpe_ratio && trade.sharpe_ratio < 1e10 && (
              <span>Sharpe: {(trade.sharpe_ratio || 0).toFixed(2)}</span>
            )}
            {trade.value_at_risk && (
              <span> | VaR: ${(trade.value_at_risk || 0).toFixed(2)}</span>
            )}
          </div>
        </div>
      </div>

      {/* Enhanced Probability Analysis Section */}
      {(trade.breakeven_probability || trade.p50_profit) && (
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg border mb-4">
          <h4 className="text-sm font-semibold mb-3 flex items-center">
            <Brain className="h-4 w-4 mr-2 text-blue-600" />
            Advanced Probability Analysis
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {trade.breakeven_probability && (
              <div className="text-center">
                <div className="text-xs text-muted-foreground mb-1">Breakeven Prob</div>
                <div className="text-lg font-bold text-blue-600">
                  {(trade.breakeven_probability || 0).toFixed(1)}%
                </div>
                <Progress value={trade.breakeven_probability} className="h-2 mt-1" />
              </div>
            )}
            {trade.p50_profit && (
              <div className="text-center">
                <div className="text-xs text-muted-foreground mb-1">Median Outcome</div>
                <div className={`text-lg font-bold ${trade.p50_profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ${(trade.p50_profit || 0).toFixed(2)}
                </div>
                <div className="text-xs text-muted-foreground">50th percentile</div>
              </div>
            )}
            {trade.score && (
              <div className="text-center">
                <div className="text-xs text-muted-foreground mb-1">Dynamic Score</div>
                <div className="text-lg font-bold text-purple-600">
                  {(trade.score || 0).toFixed(1)}/10
                </div>
                <div className="flex justify-center mt-1">
                  {Array.from({ length: 5 }, (_, i) => (
                    <Star 
                      key={i} 
                      className={`h-3 w-3 ${i < Math.round(trade.score! / 2) ? 'text-yellow-400 fill-current' : 'text-gray-300'}`} 
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Action Button */}
      <div className="flex justify-center">
        <Button 
          onClick={() => handleExecuteTrade(trade)}
          className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold px-8 py-2 transition-all duration-200"
          disabled={loadingOpportunities || isValidating}
        >
          {isValidating && pendingTrade?.id === trade.id ? (
            <>
              <Gauge className="h-4 w-4 mr-2 animate-spin" />
              Validating Risk...
            </>
          ) : (
            <>
              <DollarSign className="h-4 w-4 mr-2" />
              Execute Trade (Paper)
            </>
          )}
        </Button>
      </div>
    </div>
    );
  };

  const getCurrentOpportunities = () => {
    if (selectedCategory === 'all') return opportunities;
    return categories[selectedCategory as keyof TradeCategories] || [];
  };

  return (
    <div className="space-y-6">
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Target className="h-5 w-5 text-blue-500" />
              <span>Enhanced Trade Opportunities</span>
              <Badge variant="secondary" className="bg-blue-600 text-white">
                Multi-Strategy Analysis
              </Badge>
            </div>
            {loadingOpportunities && (
              <Badge variant="outline" className="bg-yellow-600 text-white">
                <Activity className="h-4 w-4 mr-1" />
                Analyzing Markets...
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mb-6">
            <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
              <TabsList className="grid w-full grid-cols-7">
                <TabsTrigger value="all">All Trades</TabsTrigger>
                <TabsTrigger value="high_probability">High Probability</TabsTrigger>
                <TabsTrigger value="quick_scalps">Quick Scalps</TabsTrigger>
                <TabsTrigger value="swing_trades">Swing Trades</TabsTrigger>
                <TabsTrigger value="volatility_plays">Volatility</TabsTrigger>
                <TabsTrigger value="rsi_coupon">RSI Coupon</TabsTrigger>
                <TabsTrigger value="thetacrop">ThetaCrop</TabsTrigger>
              </TabsList>
              
              <TabsContent value="all" className="mt-4">
                <div className="mb-4 text-sm text-muted-foreground">
                  Complete analysis of high-probability options opportunities across multiple strategies and timeframes.
                </div>
              </TabsContent>
              
              <TabsContent value="high_probability" className="mt-4">
                <div className="mb-4 text-sm text-muted-foreground">
                  <CheckCircle className="inline h-4 w-4 mr-1 text-green-500" />
                  Trades with &gt;75% win rate based on technical confluence and historical data.
                </div>
              </TabsContent>
              
              <TabsContent value="quick_scalps" className="mt-4">
                <div className="mb-4 text-sm text-muted-foreground">
                  <Timer className="inline h-4 w-4 mr-1 text-blue-500" />
                  Short-term opportunities (0-7 DTE) for quick momentum plays.
                </div>
              </TabsContent>
              
              <TabsContent value="swing_trades" className="mt-4">
                <div className="mb-4 text-sm text-muted-foreground">
                  <Calendar className="inline h-4 w-4 mr-1 text-purple-500" />
                  Medium-term setups (14-45 DTE) with strong technical support.
                </div>
              </TabsContent>
              
              <TabsContent value="volatility_plays" className="mt-4">
                <div className="mb-4 text-sm text-muted-foreground">
                  <Volatility className="inline h-4 w-4 mr-1 text-orange-500" />
                  Volatility-based strategies including straddles and premium collection.
                </div>
              </TabsContent>
              
              <TabsContent value="rsi_coupon" className="mt-4">
                <div className="bg-green-50 p-4 rounded-lg mb-4">
                  <h3 className="font-semibold text-green-800 mb-2">🎫 RSI Mean-Reversion "Coupon" Strategy</h3>
                  <p className="text-sm text-green-700">
                    Two-stage funnel: Screen 20 tickers for RSI &lt; 30 + bullish trend, then find cheap options (40-60 DTE, Delta 0.30-0.40).
                    Targets: 50% profit OR 30% loss OR signal invalidation.
                  </p>
                  <div className="mt-2 text-xs text-green-600">
                    Universe: SPY, QQQ, IWM, AAPL, MSFT, NVDA, TSLA + 13 others • Position Size: 0.5% account risk
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="thetacrop" className="mt-4">
                <div className="bg-blue-50 p-4 rounded-lg mb-4">
                  <h3 className="font-semibold text-blue-800 mb-2">🎯 ThetaCrop Weekly Iron Condor Strategy</h3>
                  <p className="text-sm text-blue-700">
                    Weekly short-volatility strategy: Enter Thursday 11:30 ET with ±20 delta wings, 7-8 DTE, targeting 50% profit or manage at 30% loss.
                    Systematic theta decay harvesting with defined risk parameters.
                  </p>
                  <div className="mt-2 text-xs text-blue-600">
                    Universe: SPY, QQQ, IWM • Wing Width: $2-$4 • Min Credit: ≥25% of width • Assignment Protection
                  </div>
                </div>
              </TabsContent>
            </Tabs>
            
            {/* Scan Methodology Info */}
            {scanMethodology && (
              <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                <h4 className="text-sm font-medium text-blue-900 mb-2">Scan Methodology</h4>
                <div className="text-xs text-blue-800 space-y-1">
                  <div><strong>Universe:</strong> {scanMethodology.symbols_scanned}/{scanMethodology.total_symbols} symbols from {scanMethodology.universe.length} categories</div>
                  <div><strong>Strategies:</strong> {scanMethodology.strategies.join(', ')}</div>
                  <div><strong>Filters:</strong> P(Profit) {scanMethodology.filters.probability_profit}, EV {scanMethodology.filters.expected_value}, Liquidity {scanMethodology.filters.liquidity_score}</div>
                  <div><strong>DTE Range:</strong> {scanMethodology.expiration_range} • <strong>Refresh:</strong> {scanMethodology.refresh_rate}</div>
                </div>
              </div>
            )}
          </div>
          
          {getCurrentOpportunities().length === 0 && !loadingOpportunities ? (
            <div className="text-center py-8">
              <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">No trading opportunities found for this category.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {getCurrentOpportunities().map(renderTradeCard)}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Risk Validation Dialog */}
      <AlertDialog open={showRiskDialog} onOpenChange={setShowRiskDialog}>
        <AlertDialogContent className="max-w-2xl">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              Risk Warning
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-4">
              <div className="text-sm text-gray-600">
                Our risk analysis has identified potential concerns with this trade:
              </div>
              
              {riskValidation && (
                <div className="space-y-3">
                  {/* Risk Warnings */}
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                    <h4 className="font-medium text-yellow-800 mb-2">Risk Warnings:</h4>
                    <ul className="space-y-1">
                      {riskValidation.warnings.map((warning, index) => (
                        <li key={index} className="text-sm text-yellow-700 flex items-start gap-2">
                          <Shield className="h-4 w-4 mt-0.5 flex-shrink-0" />
                          {warning}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Risk Metrics */}
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span>Margin Required:</span>
                        <span className="font-medium">${riskValidation.margin_required.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Max Loss:</span>
                        <span className="font-medium text-red-600">${riskValidation.max_loss.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Max Profit:</span>
                        <span className="font-medium text-green-600">${riskValidation.max_profit.toLocaleString()}</span>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span>Margin Usage:</span>
                        <span className={`font-medium ${riskValidation.margin_usage_pct > 0.8 ? 'text-red-600' : 'text-gray-900'}`}>
                          {((riskValidation.margin_usage_pct || 0) * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Position Count:</span>
                        <span className={`font-medium ${riskValidation.position_count_after > 5 ? 'text-red-600' : 'text-gray-900'}`}>
                          {riskValidation.position_count_after}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Portfolio Delta:</span>
                        <span className={`font-medium ${Math.abs(riskValidation.new_delta_exposure) > 0.5 ? 'text-red-600' : 'text-gray-900'}`}>
                          {(riskValidation.new_delta_exposure || 0).toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="text-xs text-gray-500 mt-3">
                    Break-even: ${(riskValidation.break_even || 0).toFixed(2)}
                  </div>
                </div>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleRiskDialogCancel}>
              Cancel Trade
            </AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleRiskDialogConfirm}
              className="bg-red-600 hover:bg-red-700"
            >
              <AlertTriangle className="h-4 w-4 mr-2" />
              Execute Anyway
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};