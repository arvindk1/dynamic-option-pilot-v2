import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign,
  Clock,
  Target,
  Activity,
  ChevronDown,
  ChevronUp,
  Eye,
  Bookmark,
  Play,
  BarChart3,
  Shield,
  Zap,
  Info
} from 'lucide-react';
import { 
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface EnhancedTradeOpportunity {
  id: string;
  symbol: string;
  strategy_type: string;
  strategy?: string;  // Backend-formatted display name
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
  trade_setup: string;
  risk_level: string;
  score: number;
  educational_content?: {
    strategy_name: string;
    best_for: string;
    when_to_use: string;
    profit_mechanism: string;
    risk_level: string;
    typical_duration: string;
  };
  trade_reasoning?: {
    why_now: string[];
    market_factors: string[];
    technical_factors: string[];
    risk_factors: string[];
    probability_edge: string;
  };
}

interface EnhancedTradingCardProps {
  opportunity: EnhancedTradeOpportunity;
  onExecute?: (opportunity: EnhancedTradeOpportunity) => void;
  onAnalyze?: (opportunity: EnhancedTradeOpportunity) => void;
  onSave?: (opportunity: EnhancedTradeOpportunity) => void;
  showAdvanced?: boolean;
  compact?: boolean;
}

export const EnhancedTradingCard: React.FC<EnhancedTradingCardProps> = ({
  opportunity,
  onExecute,
  onAnalyze,
  onSave,
  showAdvanced = true,
  compact = false
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showEducation, setShowEducation] = useState(false);

  // Format helpers
  const formatCurrency = useCallback((value: number) => 
    new Intl.NumberFormat('en-US', { 
      style: 'currency', 
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2 
    }).format(value), []);

  const formatPercent = useCallback((value: number) => 
    `${value.toFixed(1)}%`, []);

  const formatDelta = useCallback((value: number) => 
    value.toFixed(3), []);

  // Get risk level styling
  const getRiskStyling = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case 'low': return { color: 'bg-green-100 text-green-800 border-green-200', icon: <Shield className="h-3 w-3" /> };
      case 'medium': return { color: 'bg-yellow-100 text-yellow-800 border-yellow-200', icon: <Activity className="h-3 w-3" /> };
      case 'high': return { color: 'bg-red-100 text-red-800 border-red-200', icon: <Zap className="h-3 w-3" /> };
      default: return { color: 'bg-gray-100 text-gray-800 border-gray-200', icon: <Target className="h-3 w-3" /> };
    }
  };

  // Get bias styling
  const getBiasStyling = (bias: string) => {
    switch (bias.toLowerCase()) {
      case 'bullish': return { color: 'text-green-600', icon: <TrendingUp className="h-4 w-4" /> };
      case 'bearish': return { color: 'text-red-600', icon: <TrendingDown className="h-4 w-4" /> };
      default: return { color: 'text-gray-600', icon: <Activity className="h-4 w-4" /> };
    }
  };

  const riskStyling = getRiskStyling(opportunity.risk_level);
  const biasStyling = getBiasStyling(opportunity.bias);

  // Strike display helper
  const getStrikeDisplay = () => {
    if (opportunity.short_strike && opportunity.long_strike) {
      return `${opportunity.short_strike}/${opportunity.long_strike}`;
    }
    return opportunity.strike?.toString() || 'N/A';
  };

  // Strategy display helper
  const getStrategyDisplay = () => {
    // Use the backend-formatted 'strategy' field if available, otherwise fallback to transforming strategy_type
    const displayName = opportunity.strategy || opportunity.strategy_type.replace('_', ' ');
    const optionType = opportunity.option_type || '';
    return `${displayName} ${optionType}`.trim();
  };

  return (
    <TooltipProvider>
      <Card className={`trading-card relative overflow-hidden transition-all duration-200 hover:shadow-md border ${
        opportunity.score >= 4 ? 'border-green-200 bg-green-50/30' : 
        opportunity.score >= 3 ? 'border-blue-200 bg-blue-50/30' : 
        'border-gray-200'
      } ${compact ? 'text-sm' : ''}`}>
        {/* Score Indicator */}
        <div className={`absolute top-2 right-2 w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
          opportunity.score >= 4 ? 'bg-green-500 text-white' :
          opportunity.score >= 3 ? 'bg-blue-500 text-white' :
          'bg-gray-400 text-white'
        }`}>
          {opportunity.score.toFixed(1)}
        </div>

        <CardHeader className={compact ? 'pb-3' : 'pb-4'}>
          {/* Primary Information - Always Visible */}
          <div className="space-y-3">
            {/* Header Row */}
            <div className="flex items-start justify-between pr-10">
              <div>
                <h3 className={`font-bold ${compact ? 'text-lg' : 'text-xl'} text-foreground`}>
                  {opportunity.symbol} {getStrategyDisplay()}
                </h3>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-sm text-muted-foreground">
                    Strike: {getStrikeDisplay()} • {opportunity.days_to_expiration}d
                  </span>
                </div>
              </div>
            </div>

            {/* Key Metrics Row - Most Important Info */}
            <div className="grid grid-cols-3 gap-3">
              <Tooltip>
                <TooltipTrigger>
                  <div className="text-center p-2 bg-green-50 rounded-lg border border-green-200">
                    <div className="text-lg font-bold text-green-700">
                      {formatPercent(opportunity.probability_profit)}
                    </div>
                    <div className="text-xs text-green-600">Prob. Profit</div>
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Probability this trade will be profitable at expiration</p>
                </TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger>
                  <div className="text-center p-2 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="text-lg font-bold text-blue-700">
                      {formatCurrency(opportunity.expected_value)}
                    </div>
                    <div className="text-xs text-blue-600">Expected Value</div>
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Expected profit/loss based on probability analysis</p>
                </TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger>
                  <div className="text-center p-2 bg-red-50 rounded-lg border border-red-200">
                    <div className="text-lg font-bold text-red-700">
                      {formatCurrency(opportunity.max_loss)}
                    </div>
                    <div className="text-xs text-red-600">Max Risk</div>
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Maximum possible loss for this strategy</p>
                </TooltipContent>
              </Tooltip>
            </div>

            {/* Secondary Metrics Row */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Badge variant="outline" className={riskStyling.color}>
                  {riskStyling.icon}
                  {opportunity.risk_level}
                </Badge>
                
                <div className={`flex items-center gap-1 ${biasStyling.color}`}>
                  {biasStyling.icon}
                  <span className="text-sm font-medium">{opportunity.bias}</span>
                </div>

                <Tooltip>
                  <TooltipTrigger>
                    <div className="flex items-center gap-1">
                      <BarChart3 className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">{opportunity.liquidity_score}/10</span>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Liquidity Score: Higher scores indicate better execution</p>
                  </TooltipContent>
                </Tooltip>
              </div>

              <div className="text-sm text-muted-foreground">
                Premium: {formatCurrency(opportunity.premium)}
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Quick Actions */}
          <div className="flex items-center gap-2">
            <Button 
              onClick={() => onExecute?.(opportunity)}
              className="flex-1 bg-primary hover:bg-primary/90"
            >
              <Play className="h-4 w-4 mr-2" />
              Execute Trade
            </Button>
            
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => onAnalyze?.(opportunity)}
            >
              <Eye className="h-4 w-4" />
            </Button>
            
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => onSave?.(opportunity)}
            >
              <Bookmark className="h-4 w-4" />
            </Button>

            {showAdvanced && (
              <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
                <CollapsibleTrigger asChild>
                  <Button variant="ghost" size="sm">
                    {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </Button>
                </CollapsibleTrigger>
              </Collapsible>
            )}
          </div>

          {/* Expandable Details */}
          {showAdvanced && (
            <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
              <CollapsibleContent className="space-y-4">
                <Separator />
                
                {/* Greeks Panel */}
                <div className="space-y-3">
                  <h4 className="font-semibold flex items-center gap-2">
                    <Activity className="h-4 w-4" />
                    Greeks & Risk Metrics
                  </h4>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                    <div>
                      <span className="text-muted-foreground">Delta:</span>
                      <span className="ml-2 font-mono">{formatDelta(opportunity.delta)}</span>
                    </div>
                    {opportunity.gamma && (
                      <div>
                        <span className="text-muted-foreground">Gamma:</span>
                        <span className="ml-2 font-mono">{formatDelta(opportunity.gamma)}</span>
                      </div>
                    )}
                    {opportunity.theta && (
                      <div>
                        <span className="text-muted-foreground">Theta:</span>
                        <span className="ml-2 font-mono">{formatDelta(opportunity.theta)}</span>
                      </div>
                    )}
                    {opportunity.vega && (
                      <div>
                        <span className="text-muted-foreground">Vega:</span>
                        <span className="ml-2 font-mono">{formatDelta(opportunity.vega)}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Market Context */}
                <div className="space-y-3">
                  <h4 className="font-semibold flex items-center gap-2">
                    <Target className="h-4 w-4" />
                    Market Context
                  </h4>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Underlying:</span>
                      <span className="ml-2 font-mono">{formatCurrency(opportunity.underlying_price)}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">RSI:</span>
                      <span className="ml-2 font-mono">{opportunity.rsi.toFixed(1)}</span>
                    </div>
                    {opportunity.implied_volatility && (
                      <div>
                        <span className="text-muted-foreground">IV:</span>
                        <span className="ml-2 font-mono">{formatPercent(opportunity.implied_volatility * 100)}</span>
                      </div>
                    )}
                    {opportunity.macd_signal && (
                      <div>
                        <span className="text-muted-foreground">MACD:</span>
                        <span className="ml-2">{opportunity.macd_signal}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Trade Reasoning */}
                {opportunity.trade_reasoning && (
                  <div className="space-y-3">
                    <h4 className="font-semibold flex items-center gap-2">
                      <Info className="h-4 w-4" />
                      Why This Trade?
                    </h4>
                    
                    <div className="text-sm space-y-2">
                      {opportunity.trade_reasoning.why_now.length > 0 && (
                        <div>
                          <span className="font-medium text-green-600">Opportunity: </span>
                          {opportunity.trade_reasoning.why_now[0]}
                        </div>
                      )}
                      
                      {opportunity.trade_reasoning.market_factors.length > 0 && (
                        <div>
                          <span className="font-medium text-blue-600">Market: </span>
                          {opportunity.trade_reasoning.market_factors[0]}
                        </div>
                      )}
                      
                      {opportunity.trade_reasoning.technical_factors.length > 0 && (
                        <div>
                          <span className="font-medium text-purple-600">Technical: </span>
                          {opportunity.trade_reasoning.technical_factors[0]}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Educational Content Toggle */}
                {opportunity.educational_content && (
                  <div className="pt-2">
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => setShowEducation(!showEducation)}
                      className="w-full"
                    >
                      {showEducation ? 'Hide' : 'Show'} Strategy Guide
                      {showEducation ? <ChevronUp className="h-4 w-4 ml-2" /> : <ChevronDown className="h-4 w-4 ml-2" />}
                    </Button>
                    
                    {showEducation && (
                      <div className="mt-3 p-3 bg-muted/50 rounded-lg text-sm space-y-2">
                        <div>
                          <span className="font-medium">Strategy:</span>
                          <span className="ml-2">{opportunity.educational_content.strategy_name}</span>
                        </div>
                        <div>
                          <span className="font-medium">Best For:</span>
                          <span className="ml-2">{opportunity.educational_content.best_for}</span>
                        </div>
                        <div>
                          <span className="font-medium">When to Use:</span>
                          <span className="ml-2">{opportunity.educational_content.when_to_use}</span>
                        </div>
                        <div>
                          <span className="font-medium">Profit Mechanism:</span>
                          <span className="ml-2">{opportunity.educational_content.profit_mechanism}</span>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </CollapsibleContent>
            </Collapsible>
          )}
        </CardContent>
      </Card>
    </TooltipProvider>
  );
};

export default EnhancedTradingCard;