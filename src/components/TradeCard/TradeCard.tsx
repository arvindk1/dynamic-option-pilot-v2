import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Target, 
  DollarSign, 
  Timer, 
  Calendar,
  Zap,
  Database,
  AlertTriangle,
  CheckCircle,
  Info
} from 'lucide-react';
import { TradeCardMetrics } from './TradeCardMetrics';

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

  return (
    <Card className="hover:shadow-lg transition-shadow border-l-4 border-l-blue-500">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center">
            <DollarSign className="h-5 w-5 mr-2 text-green-600" />
            {trade.symbol} - {trade.underlying_price ? `$${trade.underlying_price.toFixed(2)}` : 'N/A'}
          </CardTitle>
          <Badge className={getStrategyColor(trade.strategy_type)}>
            {trade.strategy_type.replace('_', ' ')}
          </Badge>
        </div>
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center text-muted-foreground">
            {getSetupIcon(trade.trade_setup)}
            <span className="ml-1">{trade.trade_setup?.replace('_', ' ') || 'Premium Collection'}</span>
          </div>
          <div className="flex items-center text-muted-foreground">
            <Calendar className="h-4 w-4 mr-1" />
            {trade.expiration || `${trade.days_to_expiration}d`}
          </div>
        </div>
        
        {/* Data Quality Indicator */}
        <div className="pt-2 border-t border-muted/20">
          <DataQualityBadge trade={trade} />
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Strike Information */}
        <div className="grid grid-cols-3 gap-4 text-center bg-muted/50 p-3 rounded">
          {trade.strike && (
            <div>
              <div className="text-xs text-muted-foreground">Strike</div>
              <div className="font-semibold">${trade.strike}</div>
            </div>
          )}
          {trade.short_strike && (
            <div>
              <div className="text-xs text-muted-foreground">Short Strike</div>
              <div className="font-semibold">${trade.short_strike}</div>
            </div>
          )}
          {trade.long_strike && (
            <div>
              <div className="text-xs text-muted-foreground">Long Strike</div>
              <div className="font-semibold">${trade.long_strike}</div>
            </div>
          )}
          <div>
            <div className="text-xs text-muted-foreground">Premium</div>
            <div className="font-semibold text-green-600">${trade.premium?.toFixed(2) || 'N/A'}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Max Loss</div>
            <div className="font-semibold text-red-600">${trade.max_loss?.toFixed(2) || 'N/A'}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Liquidity</div>
            <div className="font-semibold">{trade.liquidity_score?.toFixed(1) || 'N/A'}</div>
          </div>
        </div>

        <TradeCardMetrics trade={trade} />

        {/* Support/Resistance Levels */}
        {trade.support_resistance && (
          <div className="bg-muted/30 p-3 rounded">
            <div className="text-sm font-semibold mb-2">Key Levels</div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Support: </span>
                <span className="font-semibold text-green-600">
                  ${trade.support_resistance.support.toFixed(2)}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Resistance: </span>
                <span className="font-semibold text-red-600">
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
          className="w-full bg-blue-600 hover:bg-blue-700"
        >
          {isExecuting ? (
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Executing...
            </div>
          ) : (
            <>
              <Timer className="h-4 w-4 mr-2" />
              Execute Trade
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
});

TradeCard.displayName = 'TradeCard';