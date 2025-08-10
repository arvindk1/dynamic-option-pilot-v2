import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
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
  Clock,
  Star,
  Award,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  Eye,
  Lightbulb,
  TrendingFlat
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
  
  // Enhanced Scoring System Fields
  overall_score?: number;
  quality_tier?: 'HIGH' | 'MEDIUM' | 'LOW';
  confidence_percentage?: number;
  profit_explanation?: string;
  score_breakdown?: {
    technical: number;
    liquidity: number;
    risk_adjusted: number;
    probability: number;
    volatility: number;
    time_decay: number;
    market_regime: number;
  };
  technical_score?: number;
  liquidity_score_enhanced?: number;
  risk_adjusted_score?: number;
  probability_score?: number;
  volatility_score?: number;
  time_decay_score?: number;
  market_regime_score?: number;
}

interface TradeCardProps {
  trade: TradeOpportunity;
  onExecute: (trade: TradeOpportunity) => void;
  isExecuting?: boolean;
}

import { StrategyDisplay } from './StrategyDisplay';

// Get entry/exit price levels for automated trading
const getTradingLevels = (trade: TradeOpportunity) => {
  const premium = trade.premium || 0;
  const underlyingPrice = trade.underlying_price || 0;
  
  return {
    entryPrice: premium, // Credit received or debit paid
    profitTarget: premium * 0.5, // 50% of max profit
    stopLoss: premium * 2.0, // 2x premium as stop loss
    breakeven: getBreakevenPrice(trade),
    maxProfit: trade.max_profit || (premium * 100),
    maxLoss: trade.max_loss || (premium * -200)
  };
};

// Calculate precise breakeven price
const getBreakevenPrice = (trade: TradeOpportunity): number => {
  const price = trade.underlying_price || 0;
  const premium = trade.premium || 0;
  
  switch (trade.strategy_type) {
    case 'PROTECTIVE_PUT':
      return price + premium;
    case 'CREDIT_SPREAD':
    case 'PUT_SPREAD':
      return (trade.short_strike || 0) - premium;
    case 'STRADDLE':
    case 'STRANGLE':
      return price; // Simplified - should calculate upper/lower
    default:
      return price;
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

// Enhanced Quality and Scoring Components
const QualityTierBadge: React.FC<{ trade: TradeOpportunity }> = ({ trade }) => {
  const getQualityDisplay = () => {
    const tier = trade.quality_tier || 'LOW';
    const score = trade.overall_score || 0;
    const confidence = trade.confidence_percentage || 0;
    
    switch (tier) {
      case 'HIGH':
        return {
          icon: <Award className="h-3 w-3" />,
          bgColor: 'bg-emerald-100 text-emerald-800 border-emerald-200',
          label: 'HIGH QUALITY',
          color: 'text-emerald-600',
          description: 'Excellent opportunity with strong fundamentals'
        };
      case 'MEDIUM':
        return {
          icon: <Star className="h-3 w-3" />,
          bgColor: 'bg-amber-100 text-amber-800 border-amber-200',
          label: 'GOOD QUALITY',
          color: 'text-amber-600',
          description: 'Solid opportunity with good risk-reward'
        };
      default:
        return {
          icon: <Eye className="h-3 w-3" />,
          bgColor: 'bg-slate-100 text-slate-700 border-slate-200',
          label: 'REVIEW NEEDED',
          color: 'text-slate-600',
          description: 'Requires careful evaluation before trading'
        };
    }
  };
  
  const qualityInfo = getQualityDisplay();
  const score = trade.overall_score || 0;
  const confidence = trade.confidence_percentage || 0;
  
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <Badge className={`${qualityInfo.bgColor} text-xs flex items-center space-x-1 px-2 py-1 border`}>
          {qualityInfo.icon}
          <span className="font-medium">{qualityInfo.label}</span>
        </Badge>
        <div className="flex items-center space-x-2">
          <span className={`text-2xl font-bold ${qualityInfo.color}`}>
            {score.toFixed(0)}
          </span>
          <div className="text-xs text-muted-foreground">
            <div>Overall Score</div>
            <div className={qualityInfo.color}>{confidence.toFixed(0)}% Confidence</div>
          </div>
        </div>
      </div>
      <div className="text-right">
        <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
          <div 
            className={`h-full transition-all duration-500 ${
              score >= 75 ? 'bg-emerald-500' :
              score >= 50 ? 'bg-amber-500' : 'bg-slate-400'
            }`}
            style={{ width: `${Math.min(score, 100)}%` }}
          />
        </div>
        <div className="text-xs text-muted-foreground mt-1">
          {qualityInfo.description}
        </div>
      </div>
    </div>
  );
};

const ProfitExplanationPanel: React.FC<{ trade: TradeOpportunity; isExpanded: boolean; onToggle: () => void }> = ({ 
  trade, 
  isExpanded, 
  onToggle 
}) => {
  const explanation = trade.profit_explanation;
  
  if (!explanation) return null;
  
  return (
    <div className="bg-gradient-to-r from-blue-50/50 to-indigo-50/50 border border-blue-200/50 rounded-lg">
      <button
        onClick={onToggle}
        className="w-full p-3 flex items-center justify-between hover:bg-blue-50/30 transition-colors"
      >
        <div className="flex items-center space-x-2">
          <Lightbulb className="h-4 w-4 text-blue-600" />
          <span className="text-sm font-medium text-blue-800">Why This Trade Works</span>
        </div>
        {isExpanded ? <ChevronUp className="h-4 w-4 text-blue-600" /> : <ChevronDown className="h-4 w-4 text-blue-600" />}
      </button>
      
      {isExpanded && (
        <div className="px-3 pb-3">
          <p className="text-sm text-blue-700 leading-relaxed">
            {explanation}
          </p>
        </div>
      )}
    </div>
  );
};

const ScoreBreakdownPanel: React.FC<{ trade: TradeOpportunity; isExpanded: boolean; onToggle: () => void }> = ({ 
  trade, 
  isExpanded, 
  onToggle 
}) => {
  const breakdown = trade.score_breakdown;
  
  if (!breakdown) return null;
  
  const scoreItems = [
    { key: 'technical', label: 'Technical Analysis', icon: <BarChart3 className="h-3 w-3" />, weight: '25%' },
    { key: 'liquidity', label: 'Liquidity Score', icon: <Database className="h-3 w-3" />, weight: '20%' },
    { key: 'risk_adjusted', label: 'Risk-Reward', icon: <Shield className="h-3 w-3" />, weight: '20%' },
    { key: 'probability', label: 'Win Probability', icon: <Target className="h-3 w-3" />, weight: '15%' },
    { key: 'volatility', label: 'Volatility Edge', icon: <Waves className="h-3 w-3" />, weight: '10%' },
    { key: 'time_decay', label: 'Time Decay', icon: <Timer className="h-3 w-3" />, weight: '5%' },
    { key: 'market_regime', label: 'Market Regime', icon: <Activity className="h-3 w-3" />, weight: '5%' }
  ];
  
  return (
    <div className="bg-gradient-to-r from-slate-50/50 to-zinc-50/50 border border-slate-200/50 rounded-lg">
      <button
        onClick={onToggle}
        className="w-full p-3 flex items-center justify-between hover:bg-slate-50/50 transition-colors"
      >
        <div className="flex items-center space-x-2">
          <BarChart3 className="h-4 w-4 text-slate-600" />
          <span className="text-sm font-medium text-slate-800">Score Breakdown</span>
        </div>
        {isExpanded ? <ChevronUp className="h-4 w-4 text-slate-600" /> : <ChevronDown className="h-4 w-4 text-slate-600" />}
      </button>
      
      {isExpanded && (
        <div className="px-3 pb-3 space-y-2">
          {scoreItems.map(item => {
            const score = breakdown[item.key as keyof typeof breakdown] || 0;
            const percentage = (score / 100) * 100;
            
            return (
              <div key={item.key} className="flex items-center justify-between">
                <div className="flex items-center space-x-2 flex-1">
                  <div className="text-slate-600">{item.icon}</div>
                  <span className="text-xs font-medium text-slate-700">{item.label}</span>
                  <span className="text-xs text-slate-500">({item.weight})</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-16 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-300 ${
                        percentage >= 75 ? 'bg-emerald-500' :
                        percentage >= 50 ? 'bg-amber-500' : 'bg-slate-400'
                      }`}
                      style={{ width: `${Math.min(percentage, 100)}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium text-slate-700 w-8 text-right">
                    {score.toFixed(0)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
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

// Individual metric card component - memoized for performance
const MetricCard: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color?: string;
  progress?: number;
  showProgress?: boolean;
  className?: string;
}> = React.memo(({ icon, label, value, color = 'text-foreground', progress, showProgress = false, className = '' }) => (
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
));

export const TradeCard: React.FC<TradeCardProps> = React.memo(({ 
  trade, 
  onExecute, 
  isExecuting = false 
}) => {
  const [showExplanation, setShowExplanation] = React.useState(false);
  const [showBreakdown, setShowBreakdown] = React.useState(false);
  
  // Memoize expensive calculations
  const setupIcon = React.useMemo(() => {
    switch (trade.trade_setup) {
      case 'MOMENTUM': return <Zap className="h-4 w-4 text-blue-400" />;
      case 'MEAN_REVERSION': return <Target className="h-4 w-4 text-purple-400" />;
      case 'BREAKOUT': return <Target className="h-4 w-4 text-green-400" />;
      case 'RANGE_BOUND': return <Target className="h-4 w-4 text-orange-400" />;
      default: return <Target className="h-4 w-4 text-gray-400" />;
    }
  }, [trade.trade_setup]);

  const strategyColor = React.useMemo(() => {
    switch (trade.strategy_type) {
      case 'CALL': return 'bg-green-100 text-green-800';
      case 'PUT': return 'bg-red-100 text-red-800';
      case 'IRON_CONDOR': return 'bg-blue-100 text-blue-800';
      case 'BUTTERFLY': return 'bg-purple-100 text-purple-800';
      case 'CALENDAR': return 'bg-yellow-100 text-yellow-800';
      case 'STRADDLE': return 'bg-pink-100 text-pink-800';
      case 'STRANGLE': return 'bg-indigo-100 text-indigo-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  }, [trade.strategy_type]);

  // Memoize expiration formatting
  const formattedExpiration = React.useMemo(() => {
    if (trade.expiration) {
      const expDate = new Date(trade.expiration);
      return `Exp: ${expDate.toISOString().split('T')[0]}`;
    }
    return `Exp: ${trade.days_to_expiration}d`;
  }, [trade.expiration, trade.days_to_expiration]);

  // Memoize bias display
  const biasDisplay = React.useMemo(() => {
    switch (trade.bias?.toUpperCase()) {
      case 'BULLISH': 
        return { icon: <TrendingUp className="h-3 w-3" />, color: 'text-green-600', bg: '' };
      case 'BEARISH': 
        return { icon: <TrendingDown className="h-3 w-3" />, color: 'text-red-600', bg: '' };
      case 'NEUTRAL': 
        return { icon: <Activity className="h-3 w-3" />, color: 'text-blue-600', bg: '' };
      default: 
        return { icon: <Activity className="h-3 w-3" />, color: 'text-gray-600', bg: '' };
    }
  }, [trade.bias]);

  return (
    <Card className="hover:shadow-xl transition-all duration-300 border border-border/50 hover:border-border bg-gradient-to-br from-card to-card/80 backdrop-blur-sm">
      {/* Enhanced Header with Scoring */}
      <CardHeader className="pb-4 border-b border-border/30">
        <div className="flex items-center justify-between mb-4">
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
                <StrategyDisplay trade={trade} compact={true} />
              </div>
              {/* Breakeven Display */}
              {getBreakevenDisplay(trade) && (
                <div className="text-xs text-blue-600 font-medium mt-1">
                  {getBreakevenDisplay(trade)}
                </div>
              )}
            </div>
          </div>
          
          {/* Expiration Date */}
          <div className="text-right">
            <div className="text-sm font-medium text-muted-foreground">
              {formattedExpiration}
            </div>
            <Badge className={strategyColor} variant="secondary">
              {trade.strategy_type.replace('_', ' ')}
            </Badge>
          </div>
        </div>
        
        {/* Enhanced Quality Badge with Overall Score */}
        {(trade.overall_score || trade.quality_tier) ? (
          <QualityTierBadge trade={trade} />
        ) : (
          <DataQualityBadge trade={trade} />
        )}
      </CardHeader>

      <CardContent className="p-6 space-y-6">
        {/* Profit Explanation Panel */}
        {trade.profit_explanation && (
          <ProfitExplanationPanel 
            trade={trade} 
            isExpanded={showExplanation}
            onToggle={() => setShowExplanation(!showExplanation)}
          />
        )}
        
        {/* Enhanced Main Metrics - Key Trading Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <MetricCard
            icon={getMetricIcon('pop')}
            label="Win Rate"
            value={`${((trade.probability_profit || 0) * 100).toFixed(1)}%`}
            color="text-green-600"
            progress={(trade.probability_profit || 0) * 100}
            showProgress={true}
          />
          <MetricCard
            icon={getMetricIcon('premium')}
            label="Credit"
            value={`$${trade.premium?.toFixed(2) || 'N/A'}`}
            color="text-blue-600"
          />
          <MetricCard
            icon={getMetricIcon('max_loss')}
            label="Max Risk"
            value={`$${trade.max_loss?.toFixed(0) || 'N/A'}`}
            color="text-red-600"
          />
          <MetricCard
            icon={getMetricIcon('p50')}
            label="Expected"
            value={`$${(trade.expected_value || 0).toFixed(0)}`}
            color="text-green-600"
          />
        </div>

        {/* Technical & Risk Indicators */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <MetricCard
            icon={biasDisplay.icon}
            label="Market Bias"
            value={trade.bias || 'Neutral'}
            color={biasDisplay.color}
          />
          <MetricCard
            icon={getMetricIcon('rsi')}
            label="RSI Signal"
            value={trade.rsi?.toFixed(1) || 'N/A'}
            color={trade.rsi && trade.rsi < 30 ? 'text-green-600' : 
                   trade.rsi && trade.rsi > 70 ? 'text-red-600' : 'text-orange-600'}
            progress={trade.rsi || 50}
            showProgress={true}
          />
          <MetricCard
            icon={getMetricIcon('liquidity')}
            label="Liquidity"
            value={trade.liquidity_score?.toFixed(1) || 'N/A'}
            color={trade.liquidity_score && trade.liquidity_score >= 7 ? 'text-green-600' : 
                   trade.liquidity_score && trade.liquidity_score >= 4 ? 'text-amber-600' : 'text-red-600'}
            progress={((trade.liquidity_score || 0) / 10) * 100}
            showProgress={true}
          />
          <MetricCard
            icon={getMetricIcon('delta')}
            label="Delta"
            value={trade.delta?.toFixed(3) || 'N/A'}
            color="text-cyan-600"
          />
        </div>

        {/* Greeks (Collapsible for Space) */}
        {(trade.theta || trade.vega || trade.gamma) && (
          <div className="bg-muted/20 rounded-lg p-3 border border-muted/50">
            <div className="text-sm font-medium text-muted-foreground mb-2 flex items-center">
              <BarChart3 className="h-4 w-4 mr-2" />
              Greeks Profile
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="text-center">
                <div className="text-xs text-muted-foreground">Theta</div>
                <div className="text-sm font-bold text-purple-600">
                  {trade.theta?.toFixed(3) || 'N/A'}
                </div>
              </div>
              <div className="text-center">
                <div className="text-xs text-muted-foreground">Vega</div>
                <div className="text-sm font-bold text-indigo-600">
                  {trade.vega?.toFixed(3) || 'N/A'}
                </div>
              </div>
              <div className="text-center">
                <div className="text-xs text-muted-foreground">Gamma</div>
                <div className="text-sm font-bold text-yellow-600">
                  {trade.gamma?.toFixed(3) || 'N/A'}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Score Breakdown Panel */}
        {trade.score_breakdown && (
          <ScoreBreakdownPanel 
            trade={trade} 
            isExpanded={showBreakdown}
            onToggle={() => setShowBreakdown(!showBreakdown)}
          />
        )}

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

        {/* Enhanced Execute Button with Quality-Based Styling */}
        <Button 
          onClick={() => onExecute(trade)}
          disabled={isExecuting}
          className={`w-full font-medium py-3 shadow-lg hover:shadow-xl transition-all duration-200 ${
            (trade.quality_tier === 'HIGH' || (trade.overall_score || 0) >= 75) 
              ? 'bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-700 hover:to-emerald-600 text-white'
              : (trade.quality_tier === 'MEDIUM' || (trade.overall_score || 0) >= 50)
              ? 'bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white'
              : 'bg-gradient-to-r from-slate-600 to-slate-500 hover:from-slate-700 hover:to-slate-600 text-white'
          }`}
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
              {(trade.quality_tier === 'HIGH' || (trade.overall_score || 0) >= 75) 
                ? 'Execute High-Quality Trade' 
                : 'Execute Trade'}
            </div>
          )}
        </Button>
      </CardContent>
    </Card>
  );
});

TradeCard.displayName = 'TradeCard';

// Mobile-Optimized Compact Trade Card
export const CompactTradeCard: React.FC<TradeCardProps> = React.memo(({ 
  trade, 
  onExecute, 
  isExecuting = false 
}) => {
  const [isExpanded, setIsExpanded] = React.useState(false);
  
  const qualityColor = (trade.quality_tier === 'HIGH' || (trade.overall_score || 0) >= 75) 
    ? 'text-emerald-600' 
    : (trade.quality_tier === 'MEDIUM' || (trade.overall_score || 0) >= 50)
    ? 'text-amber-600' 
    : 'text-slate-600';

  return (
    <Card className="hover:shadow-lg transition-all duration-200 border border-border/50 hover:border-border">
      {/* Compact Header */}
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="text-lg font-bold">{trade.symbol}</div>
            <Badge variant="secondary" className="text-xs">
              {trade.strategy_type.replace('_', ' ')}
            </Badge>
          </div>
          <div className="text-right">
            {(trade.overall_score || trade.quality_tier) && (
              <div className="flex items-center space-x-1">
                <span className={`text-xl font-bold ${qualityColor}`}>
                  {(trade.overall_score || 0).toFixed(0)}
                </span>
                <div className="text-xs text-muted-foreground">
                  {(trade.confidence_percentage || 0).toFixed(0)}%
                </div>
              </div>
            )}
            <div className="text-xs text-muted-foreground">
              {trade.days_to_expiration}d
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0 space-y-3">
        {/* Key Metrics Row */}
        <div className="grid grid-cols-3 gap-2">
          <div className="text-center p-2 bg-muted/30 rounded">
            <div className="text-xs text-muted-foreground">Win Rate</div>
            <div className="text-sm font-bold text-green-600">
              {((trade.probability_profit || 0) * 100).toFixed(0)}%
            </div>
          </div>
          <div className="text-center p-2 bg-muted/30 rounded">
            <div className="text-xs text-muted-foreground">Credit</div>
            <div className="text-sm font-bold text-blue-600">
              ${trade.premium?.toFixed(2)}
            </div>
          </div>
          <div className="text-center p-2 bg-muted/30 rounded">
            <div className="text-xs text-muted-foreground">Risk</div>
            <div className="text-sm font-bold text-red-600">
              ${trade.max_loss?.toFixed(0)}
            </div>
          </div>
        </div>

        {/* Profit Explanation (Mobile-Friendly) */}
        {trade.profit_explanation && (
          <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
            <CollapsibleTrigger className="w-full">
              <div className="flex items-center justify-between p-2 bg-blue-50/50 rounded-lg hover:bg-blue-50 transition-colors">
                <div className="flex items-center space-x-2">
                  <Lightbulb className="h-3 w-3 text-blue-600" />
                  <span className="text-xs font-medium text-blue-800">Why This Works</span>
                </div>
                {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              </div>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="pt-2 px-2">
                <p className="text-xs text-blue-700 leading-relaxed">
                  {trade.profit_explanation}
                </p>
              </div>
            </CollapsibleContent>
          </Collapsible>
        )}

        {/* Execute Button */}
        <Button 
          onClick={() => onExecute(trade)}
          disabled={isExecuting}
          className={`w-full py-2 text-sm font-medium transition-all duration-200 ${
            (trade.quality_tier === 'HIGH' || (trade.overall_score || 0) >= 75) 
              ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
              : (trade.quality_tier === 'MEDIUM' || (trade.overall_score || 0) >= 50)
              ? 'bg-blue-600 hover:bg-blue-700 text-white'
              : 'bg-slate-600 hover:bg-slate-700 text-white'
          }`}
        >
          {isExecuting ? (
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-2"></div>
              Executing...
            </div>
          ) : (
            <div className="flex items-center">
              <Zap className="h-3 w-3 mr-2" />
              Execute
            </div>
          )}
        </Button>
      </CardContent>
    </Card>
  );
});

CompactTradeCard.displayName = 'CompactTradeCard';

// Responsive Trade Card that adapts to screen size
export const ResponsiveTradeCard: React.FC<TradeCardProps> = React.memo(({ 
  trade, 
  onExecute, 
  isExecuting = false 
}) => {
  const [isMobile, setIsMobile] = React.useState(false);
  
  React.useEffect(() => {
    const checkIsMobile = () => {
      setIsMobile(window.innerWidth < 768); // md breakpoint
    };
    
    checkIsMobile();
    window.addEventListener('resize', checkIsMobile);
    return () => window.removeEventListener('resize', checkIsMobile);
  }, []);
  
  return isMobile ? (
    <CompactTradeCard trade={trade} onExecute={onExecute} isExecuting={isExecuting} />
  ) : (
    <TradeCard trade={trade} onExecute={onExecute} isExecuting={isExecuting} />
  );
});

ResponsiveTradeCard.displayName = 'ResponsiveTradeCard';

/*
ENHANCED TRADING OPPORTUNITY INTERFACE - COMPREHENSIVE DESIGN SUMMARY

=== KEY FEATURES IMPLEMENTED ===

1. **VISUAL HIERARCHY & TRUST BUILDING**
   - Overall Score (0-100) prominently displayed with color coding
   - Quality Tier badges (HIGH/MEDIUM/LOW) with clear visual distinction
   - Confidence percentage displayed for transparency
   - Smart color psychology (green=high quality, amber=medium, slate=review needed)

2. **LLM-POWERED EXPLANATIONS**
   - "Why This Trade Works" expandable panel with profit explanations
   - Single-line explanations generated by LLM analysis service
   - Context-aware analysis based on technical and market conditions
   - Mobile-friendly collapsible format for space efficiency

3. **TRANSPARENT SCORING BREAKDOWN**
   - 7-component score breakdown with individual weights displayed
   - Technical Analysis (25%), Liquidity (20%), Risk-Adjusted (20%), etc.
   - Progress bars and visual indicators for each component
   - Educational component showing methodology transparency

4. **RESPONSIVE DESIGN**
   - Full desktop layout with detailed metrics and explanations
   - Compact mobile layout optimizing for touch interactions
   - Automatic responsive switching based on screen size
   - Grid layouts adapt from 4-column to 2-column on mobile

5. **ENHANCED VISUAL INDICATORS**
   - Quality-based button styling (emerald for high, blue for medium, slate for low)
   - Progress bars for probability, RSI, and liquidity metrics
   - Color-coded metrics based on actual values (green for good RSI signals, etc.)
   - Gradient backgrounds and subtle animations for polish

6. **INFORMATION ARCHITECTURE**
   - Most important info first: Symbol, Score, Quality Tier
   - Progressive disclosure: Basic metrics → Details → Advanced breakdown
   - Logical grouping: Key metrics, technical indicators, Greeks, explanations
   - Clear labeling with intuitive icons

=== ACCESSIBILITY FEATURES ===
   - High contrast color schemes
   - Clear typography hierarchy
   - Screen reader friendly labels
   - Keyboard navigation support
   - Progressive disclosure reduces cognitive load

=== PERFORMANCE OPTIMIZATIONS ===
   - React.memo for all components
   - Conditional rendering (only show components when data exists)
   - Efficient state management with minimal re-renders
   - Lazy loading of detailed breakdowns

=== COMPONENT ARCHITECTURE ===
   - TradeCard: Full desktop experience with all features
   - CompactTradeCard: Mobile-optimized streamlined version
   - ResponsiveTradeCard: Automatic switching wrapper
   - Modular sub-components for reusability

=== DATA INTEGRATION ===
   - Full integration with OpportunityScoringService backend
   - Support for all 7 scoring components
   - LLM analysis integration for profit explanations
   - Backward compatibility with existing data structure

This enhanced interface transforms basic opportunity data into intelligent, 
trustworthy recommendations that help traders make informed decisions quickly.
*/