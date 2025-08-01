import React, { useMemo } from 'react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
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
  Brain
} from 'lucide-react';

interface TradeOpportunity {
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

interface TradeCardMetricsProps {
  trade: TradeOpportunity;
}

export const TradeCardMetrics: React.FC<TradeCardMetricsProps> = React.memo(({ trade }) => {
  const biasIcon = useMemo(() => {
    switch (trade.bias) {
      case 'BULLISH': return <TrendingUp className="h-4 w-4 text-green-400" />;
      case 'BEARISH': return <TrendingDown className="h-4 w-4 text-red-400" />;
      case 'NEUTRAL': return <Activity className="h-4 w-4 text-yellow-400" />;
      default: return <Activity className="h-4 w-4 text-gray-400" />;
    }
  }, [trade.bias]);

  const biasColor = useMemo(() => {
    switch (trade.bias) {
      case 'BULLISH': return 'text-green-400';
      case 'BEARISH': return 'text-red-400';
      case 'NEUTRAL': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  }, [trade.bias]);

  const riskColor = useMemo(() => {
    switch ((trade.risk_level || 'MEDIUM').toUpperCase()) {
      case 'LOW': return 'bg-green-100 text-green-800';
      case 'MEDIUM': return 'bg-yellow-100 text-yellow-800';
      case 'HIGH': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  }, [trade.risk_level]);

  const starRating = useMemo(() => {
    if (!trade.score) return null;
    return Array.from({ length: 5 }, (_, i) => (
      <Star 
        key={i} 
        className={`h-3 w-3 ${i < Math.round(trade.score! / 2) ? 'text-yellow-400 fill-current' : 'text-gray-300'}`} 
      />
    ));
  }, [trade.score]);

  return (
    <>
      {/* Core Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
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
            <Badge className={riskColor}>
              {trade.risk_level || 'MEDIUM'}
            </Badge>
          </div>
          <div className="text-xs text-muted-foreground">
            Max profit: ${trade.max_profit === 999.99 ? 'Unlimited' : (trade.max_profit || trade.premium || 0).toFixed(2)}
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
                  {starRating}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Technical Analysis Section */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <div className="flex items-center p-2 bg-background rounded border">
          {biasIcon}
          <div className="ml-2">
            <div className="text-xs text-muted-foreground">Bias</div>
            <div className={`text-sm font-semibold ${biasColor}`}>
              {trade.bias}
            </div>
          </div>
        </div>
        
        <div className="flex items-center p-2 bg-background rounded border">
          <Gauge className="h-4 w-4 text-orange-400" />
          <div className="ml-2">
            <div className="text-xs text-muted-foreground">RSI</div>
            <div className="text-sm font-semibold">
              {trade.rsi?.toFixed(1) || 'N/A'}
            </div>
          </div>
        </div>
        
        <div className="flex items-center p-2 bg-background rounded border">
          <Timer className="h-4 w-4 text-purple-400" />
          <div className="ml-2">
            <div className="text-xs text-muted-foreground">DTE</div>
            <div className="text-sm font-semibold">
              {trade.days_to_expiration}
            </div>
          </div>
        </div>
        
        <div className="flex items-center p-2 bg-background rounded border">
          <BarChart3 className="h-4 w-4 text-cyan-400" />
          <div className="ml-2">
            <div className="text-xs text-muted-foreground">Delta</div>
            <div className="text-sm font-semibold">
              {(trade.delta || 0).toFixed(3)}
            </div>
          </div>
        </div>
      </div>
    </>
  );
});

TradeCardMetrics.displayName = 'TradeCardMetrics';