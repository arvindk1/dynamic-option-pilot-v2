import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Target, 
  DollarSign, 
  Timer, 
  Calendar,
  Zap,
  Database,
  AlertTriangle,
  CheckCircle,
  Info,
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Gauge,
  Brain,
  Shield,
  Percent,
  Waves,
  Clock
} from 'lucide-react';
// Removed TradeCardMetrics import - functionality now integrated directly

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
  data_source_type?: string;
  data_source_provider?: string;
  pricing_confidence?: number;
  data_quality_score?: number;
}

interface TradeCardProps {
  trade: TradeOpportunity;
  onExecute: (trade: TradeOpportunity) => void;
  isExecuting?: boolean;
}

// Helper functions for strategy-specific displays
const getStrategyStrikesDisplay = (trade: TradeOpportunity): string => {
  switch (trade.strategy_type) {
    case 'IRON_CONDOR':
      // Format: "Strikes: 447/449/451/453"
      const putStrike = trade.short_strike;
      const callStrike = trade.long_strike;
      const wingWidth = 2; // Could be calculated from trade data
      return `Strikes: ${putStrike-wingWidth}/${putStrike}/${callStrike}/${callStrike+wingWidth}`;
    
    case 'PROTECTIVE_PUT':
      return `Put: $${trade.long_strike} Strike`;
    
    case 'CREDIT_SPREAD':
    case 'PUT_SPREAD':
      return `Strikes: ${trade.long_strike}/${trade.short_strike}`;
    
    case 'STRADDLE':
      return `Strike: ${trade.short_strike} (ATM)`;
    
    case 'STRANGLE':
      return `Strikes: ${trade.short_strike}/${trade.long_strike}`;
    
    case 'BUTTERFLY':
      const center = trade.short_strike;
      const wing = 5; // Could be calculated
      return `Strikes: ${center-wing}/${center}/${center+wing}`;
    
    default:
      if (trade.short_strike && trade.long_strike) {
        return `Strikes: ${trade.long_strike}/${trade.short_strike}`;
      } else if (trade.short_strike) {
        return `Strike: ${trade.short_strike}`;
      }
      return 'Strike: N/A';
  }
};

const getExpirationDisplay = (trade: TradeOpportunity): string => {
  if (trade.expiration) {
    const expDate = new Date(trade.expiration);
    const dte = trade.days_to_expiration || 0;
    return `${expDate.toISOString().split('T')[0]} (${dte}d)`;
  }
  return `${trade.days_to_expiration}d`;
};

const getBreakevenDisplay = (trade: TradeOpportunity): string | null => {
  const price = trade.underlying_price || 0;
  const premium = trade.premium || 0;
  
  switch (trade.strategy_type) {
    case 'PROTECTIVE_PUT':
      return `Breakeven: $${(price + premium).toFixed(2)}`;
    
    case 'IRON_CONDOR':
      const lowerBE = (trade.short_strike || 0) + premium;
      const upperBE = (trade.long_strike || 0) - premium;
      return `Breakeven: $${lowerBE.toFixed(2)} / $${upperBE.toFixed(2)}`;
    
    case 'CREDIT_SPREAD':
    case 'PUT_SPREAD':
      const be = (trade.short_strike || 0) - premium;
      return `Breakeven: $${be.toFixed(2)}`;
    
    case 'STRADDLE':
    case 'STRANGLE':
      const upperBreakeven = price + premium;
      const lowerBreakeven = price - premium;
      return `Breakeven: $${lowerBreakeven.toFixed(2)} / $${upperBreakeven.toFixed(2)}`;
    
    default:
      return null;
  }
};

const getBiasColor = (bias?: string): string => {
  switch (bias?.toUpperCase()) {
    case 'BULLISH': return 'text-green-600';
    case 'BEARISH': return 'text-red-600';
    case 'NEUTRAL': return 'text-blue-600';
    default: return 'text-gray-600';
  }
};

const getVolatilityLevel = (trade: TradeOpportunity): string => {
  // Estimate volatility based on available metrics
  const rsi = trade.rsi || 50;
  const vega = Math.abs(trade.vega || 0);
  
  if (rsi > 70 || rsi < 30 || vega > 0.3) return 'High';
  if (rsi > 60 || rsi < 40 || vega > 0.15) return 'Normal';
  return 'Low';
};

const DataQualityBadge: React.FC<{ trade: TradeOpportunity }> = ({ trade }) => {
  const getDataQualityInfo = () => {
    const confidence = trade.pricing_confidence || 0;
    const qualityScore = trade.data_quality_score || 0;
    const sourceType = trade.data_source_type || 'UNKNOWN';
    const provider = trade.data_source_provider || 'unknown';
    
    // Determine overall quality level
    let qualityLevel: 'high' | 'medium' | 'low' = 'low';
    let icon = <AlertTriangle className="h-3 w-3" />;
    let bgColor = 'bg-red-100 text-red-700';
    let label = 'Low Quality';
    
    if (confidence >= 0.8 && qualityScore >= 0.7) {
      qualityLevel = 'high';
      icon = <CheckCircle className="h-3 w-3" />;
      bgColor = 'bg-green-100 text-green-700';
      label = 'High Quality';
    } else if (confidence >= 0.6 && qualityScore >= 0.5) {
      qualityLevel = 'medium';
      icon = <Info className="h-3 w-3" />;
      bgColor = 'bg-yellow-100 text-yellow-700';
      label = 'Medium Quality';
    }
    
    // Add source type indicator
    if (sourceType === 'SYNTHETIC_CALCULATED') {
      label = `${label} (Synthetic)`;
    } else if (sourceType === 'REAL_TIME') {
      label = `${label} (Live)`;
    }
    
    return {
      icon,
      bgColor,
      label,
      confidence: (confidence * 100).toFixed(0),
      qualityScore: (qualityScore * 100).toFixed(0),
      sourceType,
      provider
    };
  };
  
  const qualityInfo = getDataQualityInfo();
  
  return (
    <div className="flex items-center space-x-2">
      <Badge className={`${qualityInfo.bgColor} text-xs flex items-center space-x-1`}>
        {qualityInfo.icon}
        <span>{qualityInfo.label}</span>
      </Badge>
      <div className="text-xs text-muted-foreground">
        Conf: {qualityInfo.confidence}%
      </div>
    </div>
  );
};

// Get metric icons
const getMetricIcon = (metricType: string) => {
  switch (metricType) {
    case 'pop': return <Percent className="h-4 w-4" />;
    case 'premium': return <DollarSign className="h-4 w-4" />;
    case 'max_loss': return <Shield className="h-4 w-4" />;
    case 'p50': return <Target className="h-4 w-4" />;
    case 'bias': return <TrendingUp className="h-4 w-4" />;
    case 'volatility': return <Waves className="h-4 w-4" />;
    case 'rsi': return <Gauge className="h-4 w-4" />;
    case 'delta': return <BarChart3 className="h-4 w-4" />;
    case 'theta': return <Timer className="h-4 w-4" />;
    case 'vega': return <Activity className="h-4 w-4" />;
    case 'gamma': return <Zap className="h-4 w-4" />;
    case 'liquidity': return <Database className="h-4 w-4" />;
    default: return <Info className="h-4 w-4" />;
  }
};

// Individual metric card component
const MetricCard: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color?: string;
  progress?: number;
  showProgress?: boolean;
  className?: string;
}> = ({ icon, label, value, color = 'text-foreground', progress, showProgress = false, className = '' }) => (
  <div className={`bg-card/50 backdrop-blur-sm border border-border/50 rounded-lg p-3 hover:shadow-md transition-all duration-200 hover:border-border ${className}`}>
    <div className="flex items-center justify-between mb-1">
      <div className="flex items-center space-x-2">
        <div className={`${color} opacity-70`}>
          {icon}
        </div>
        <span className="text-xs font-medium text-muted-foreground">{label}</span>
      </div>
    </div>
    <div className={`text-sm font-bold ${color} truncate`}>
      {value}
    </div>
    {showProgress && progress !== undefined && (
      <div className="mt-2">
        <Progress value={progress} className="h-1.5" />
      </div>
    )}
  </div>
);

export const TradeCard: React.FC<TradeCardProps> = React.memo(({ 
  trade, 
  onExecute, 
  isExecuting = false 
}) => {
  const getSetupIcon = (setup: string) => {
    switch (setup) {
      case 'MOMENTUM': return <Zap className="h-4 w-4 text-blue-400" />;
      case 'MEAN_REVERSION': return <Target className="h-4 w-4 text-purple-400" />;
      case 'BREAKOUT': return <Target className="h-4 w-4 text-green-400" />;
      case 'RANGE_BOUND': return <Target className="h-4 w-4 text-orange-400" />;
      default: return <Target className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStrategyColor = (strategy: string) => {
    switch (strategy) {
      case 'CALL': return 'bg-green-100 text-green-800';
      case 'PUT': return 'bg-red-100 text-red-800';
      case 'IRON_CONDOR': return 'bg-blue-100 text-blue-800';
      case 'BUTTERFLY': return 'bg-purple-100 text-purple-800';
      case 'CALENDAR': return 'bg-yellow-100 text-yellow-800';
      case 'STRADDLE': return 'bg-pink-100 text-pink-800';
      case 'STRANGLE': return 'bg-indigo-100 text-indigo-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Format expiration date properly
  const formatExpiration = (trade: TradeOpportunity): string => {
    if (trade.expiration) {
      const expDate = new Date(trade.expiration);
      return `Exp: ${expDate.toISOString().split('T')[0]}`;
    }
    return `Exp: ${trade.days_to_expiration}d`;
  };

  // Get bias icon and color - no white backgrounds, consistent with other cards
  const getBiasDisplay = (bias?: string) => {
    switch (bias?.toUpperCase()) {
      case 'BULLISH': 
        return { icon: <TrendingUp className="h-3 w-3" />, color: 'text-green-600', bg: '' };
      case 'BEARISH': 
        return { icon: <TrendingDown className="h-3 w-3" />, color: 'text-red-600', bg: '' };
      case 'NEUTRAL': 
        return { icon: <Activity className="h-3 w-3" />, color: 'text-blue-600', bg: '' };
      default: 
        return { icon: <Activity className="h-3 w-3" />, color: 'text-gray-600', bg: '' };
    }
  };

  const biasDisplay = getBiasDisplay(trade.bias);

  return (
    <Card className="hover:shadow-xl transition-all duration-300 border border-border/50 hover:border-border bg-gradient-to-br from-card to-card/80 backdrop-blur-sm">
      {/* Clean Header */}
      <CardHeader className="pb-4 border-b border-border/30">
        <div className="flex items-center justify-between">
          {/* Symbol + Price */}
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-primary/10 to-primary/5">
              <DollarSign className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-foreground">
                {trade.symbol} - ${trade.underlying_price?.toFixed(2) || 'N/A'}
              </CardTitle>
              {/* Strategy Details Line */}
              <div className="text-sm text-muted-foreground mt-1">
                {getStrategyStrikesDisplay(trade)}
              </div>
              {/* Breakeven Display */}
              {getBreakevenDisplay(trade) && (
                <div className="text-xs text-blue-600 font-medium mt-1">
                  {getBreakevenDisplay(trade)}
                </div>
              )}
            </div>
          </div>
          
          {/* Expiration Date (replacing "34d") */}
          <div className="text-right">
            <div className="text-sm font-medium text-muted-foreground">
              {formatExpiration(trade)}
            </div>
            <Badge className={getStrategyColor(trade.strategy_type)} variant="secondary">
              {trade.strategy_type.replace('_', ' ')}
            </Badge>
          </div>
        </div>
        
        {/* Quality Badge */}
        <div className="mt-3">
          <DataQualityBadge trade={trade} />
        </div>
      </CardHeader>

      <CardContent className="p-6 space-y-6">
        {/* Main Metrics - 4 Cards in Row */}
        <div className="grid grid-cols-4 gap-3">
          <MetricCard
            icon={getMetricIcon('pop')}
            label="POP"
            value={`${((trade.probability_profit || 0) * 100).toFixed(1)}%`}
            color="text-green-600"
            progress={(trade.probability_profit || 0) * 100}
            showProgress={true}
          />
          <MetricCard
            icon={getMetricIcon('premium')}
            label="Premium"
            value={`$${trade.premium?.toFixed(2) || 'N/A'}`}
            color="text-blue-600"
          />
          <MetricCard
            icon={getMetricIcon('max_loss')}
            label="Max Loss"
            value={`$${trade.max_loss?.toFixed(0) || 'N/A'}`}
            color="text-red-600"
          />
          <MetricCard
            icon={getMetricIcon('p50')}
            label="P50 Profit"
            value={`$${(trade.expected_value || 0).toFixed(0)}`}
            color="text-green-600"
          />
        </div>

        {/* Secondary Metrics - 4 Cards in Row */}
        <div className="grid grid-cols-4 gap-3">
          <MetricCard
            icon={biasDisplay.icon}
            label="Bias"
            value={trade.bias || 'Neutral'}
            color={biasDisplay.color}
            className={biasDisplay.bg}
          />
          <MetricCard
            icon={getMetricIcon('volatility')}
            label="Vol"
            value={getVolatilityLevel(trade)}
            color="text-purple-600"
          />
          <MetricCard
            icon={getMetricIcon('rsi')}
            label="RSI"
            value={trade.rsi?.toFixed(1) || 'N/A'}
            color="text-orange-600"
            progress={trade.rsi || 50}
            showProgress={true}
          />
          <MetricCard
            icon={getMetricIcon('delta')}
            label="Delta"
            value={trade.delta?.toFixed(3) || 'N/A'}
            color="text-cyan-600"
          />
        </div>

        {/* Greeks Row - 4 Cards */}
        <div className="grid grid-cols-4 gap-3">
          <MetricCard
            icon={getMetricIcon('theta')}
            label="Theta"
            value={trade.theta?.toFixed(3) || 'N/A'}
            color="text-purple-600"
          />
          <MetricCard
            icon={getMetricIcon('vega')}
            label="Vega"
            value={trade.vega?.toFixed(3) || 'N/A'}
            color="text-indigo-600"
          />
          <MetricCard
            icon={getMetricIcon('gamma')}
            label="Gamma"
            value={trade.gamma?.toFixed(3) || 'N/A'}
            color="text-yellow-600"
          />
          <MetricCard
            icon={getMetricIcon('liquidity')}
            label="Liquidity"
            value={trade.liquidity_score?.toFixed(1) || 'N/A'}
            color="text-teal-600"
            progress={((trade.liquidity_score || 0) / 10) * 100}
            showProgress={true}
          />
        </div>

        {/* Support/Resistance Levels */}
        {trade.support_resistance && (
          <div className="bg-gradient-to-r from-muted/30 to-muted/10 p-4 rounded-lg border border-dashed border-muted-foreground/30">
            <div className="text-sm font-semibold mb-3 flex items-center">
              <BarChart3 className="h-4 w-4 mr-2 text-muted-foreground" />
              Key Levels
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center justify-between p-2 bg-green-50 rounded">
                <span className="text-sm text-muted-foreground">Support:</span>
                <span className="font-bold text-green-600">
                  ${trade.support_resistance.support.toFixed(2)}
                </span>
              </div>
              <div className="flex items-center justify-between p-2 bg-red-50 rounded">
                <span className="text-sm text-muted-foreground">Resistance:</span>
                <span className="font-bold text-red-600">
                  ${trade.support_resistance.resistance.toFixed(2)}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Execute Button */}
        <Button 
          onClick={() => onExecute(trade)}
          disabled={isExecuting}
          className="w-full bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white font-medium py-3 shadow-lg hover:shadow-xl transition-all duration-200"
          size="lg"
        >
          {isExecuting ? (
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Executing Trade...
            </div>
          ) : (
            <div className="flex items-center">
              <Zap className="h-4 w-4 mr-2" />
              Execute Trade
            </div>
          )}
        </Button>
      </CardContent>
    </Card>
  );
});

TradeCard.displayName = 'TradeCard';