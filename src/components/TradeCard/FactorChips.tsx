import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { TrendingUp, TrendingDown, Activity, DollarSign, Timer, Zap } from 'lucide-react';

interface ScoreBreakdown {
  technical?: number;
  liquidity?: number;
  risk_adjusted?: number;
  probability?: number;
  volatility?: number;
  time_decay?: number;
  market_regime?: number;
}

interface TradeOpportunity {
  score_breakdown?: ScoreBreakdown;
  rsi?: number;
  implied_volatility?: number;
  liquidity_score?: number;
  days_to_expiration?: number;
}

interface FactorChipsProps {
  trade: TradeOpportunity;
}

const FactorChips: React.FC<FactorChipsProps> = ({ trade }) => {
  const getFactorData = () => {
    if (!trade.score_breakdown) return [];

    const factors = [
      {
        key: 'technical',
        label: 'Trend',
        value: trade.score_breakdown.technical || 0,
        icon: trade.rsi && trade.rsi > 50 ? TrendingUp : TrendingDown,
        color: trade.rsi && trade.rsi > 50 ? 'text-green-600' : 'text-red-600',
        bgColor: trade.rsi && trade.rsi > 50 ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200',
        tooltip: trade.rsi ? `RSI ${trade.rsi.toFixed(0)} - ${trade.rsi > 70 ? 'Overbought' : trade.rsi < 30 ? 'Oversold' : 'Neutral'}` : 'Technical analysis score'
      },
      {
        key: 'volatility',
        label: 'IV Edge',
        value: trade.score_breakdown.volatility || 0,
        icon: Activity,
        color: 'text-blue-600',
        bgColor: 'bg-blue-50 border-blue-200',
        tooltip: trade.implied_volatility ? `IV ${(trade.implied_volatility * 100).toFixed(0)}% - Volatility advantage` : 'Implied volatility edge'
      },
      {
        key: 'liquidity',
        label: 'Liquidity',
        value: trade.score_breakdown.liquidity || 0,
        icon: DollarSign,
        color: 'text-purple-600',
        bgColor: 'bg-purple-50 border-purple-200',
        tooltip: `Liquidity score ${((trade.liquidity_score || 0) * 100).toFixed(0)} - Execution quality`
      },
      {
        key: 'time_decay',
        label: 'Theta',
        value: trade.score_breakdown.time_decay || 0,
        icon: Timer,
        color: 'text-orange-600',
        bgColor: 'bg-orange-50 border-orange-200',
        tooltip: trade.days_to_expiration ? `${trade.days_to_expiration}d to expiry - Time decay advantage` : 'Time decay benefit'
      },
      {
        key: 'probability',
        label: 'Win Rate',
        value: trade.score_breakdown.probability || 0,
        icon: Zap,
        color: 'text-emerald-600',
        bgColor: 'bg-emerald-50 border-emerald-200',
        tooltip: 'Probability-weighted expected outcome'
      },
      {
        key: 'risk_adjusted',
        label: 'Risk/Reward',
        value: trade.score_breakdown.risk_adjusted || 0,
        icon: Activity,
        color: 'text-indigo-600',
        bgColor: 'bg-indigo-50 border-indigo-200',
        tooltip: 'Risk-adjusted return potential'
      }
    ];

    // Sort by score descending and take top 3
    return factors
      .filter(f => f.value > 0)
      .sort((a, b) => b.value - a.value)
      .slice(0, 3);
  };

  const topFactors = getFactorData();

  if (topFactors.length === 0) {
    return null;
  }

  const getFactorDirection = (value: number) => {
    if (value >= 0.7) return '↑';
    if (value >= 0.4) return '→';
    return '↘';
  };

  return (
    <TooltipProvider>
      <div className="px-4 pb-2">
        <div className="flex flex-wrap gap-2">
          {topFactors.map(factor => {
            const Icon = factor.icon;
            const direction = getFactorDirection(factor.value);
            
            return (
              <Tooltip key={factor.key}>
                <TooltipTrigger>
                  <Badge 
                    variant="outline" 
                    className={`text-xs px-2 py-1 ${factor.bgColor} ${factor.color} border flex items-center space-x-1 cursor-help`}
                  >
                    <Icon className="w-3 h-3" />
                    <span>{factor.label}</span>
                    <span className="font-bold">{direction}</span>
                  </Badge>
                </TooltipTrigger>
                <TooltipContent side="bottom">
                  <div className="text-center">
                    <div className="font-semibold">{factor.label}</div>
                    <div className="text-xs opacity-80">{factor.tooltip}</div>
                    <div className="text-xs mt-1">Score: {(factor.value * 100).toFixed(0)}/100</div>
                  </div>
                </TooltipContent>
              </Tooltip>
            );
          })}
        </div>
      </div>
    </TooltipProvider>
  );
};

export default React.memo(FactorChips);