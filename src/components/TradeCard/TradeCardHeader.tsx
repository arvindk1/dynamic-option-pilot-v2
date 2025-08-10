import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { AlertTriangle, Calendar, Timer } from 'lucide-react';

interface TradeOpportunity {
  symbol: string;
  strategy_type: string;
  days_to_expiration: number;
  expiration: string;
  earnings_days?: number;
  overall_score?: number;
  quality_tier?: 'HIGH' | 'MEDIUM' | 'LOW';
  confidence_percentage?: number;
}

interface TradeCardHeaderProps {
  trade: TradeOpportunity;
}

const TradeCardHeader: React.FC<TradeCardHeaderProps> = ({ trade }) => {
  // Score badge logic
  const getScoreBadge = () => {
    const score = trade.overall_score || 0;
    const tier = trade.quality_tier || 'LOW';
    const confidence = trade.confidence_percentage || 0;
    
    let grade = 'C';
    let color = 'bg-slate-100 text-slate-700 border-slate-300';
    
    if (score >= 75 || tier === 'HIGH') {
      grade = 'A';
      color = 'bg-emerald-100 text-emerald-800 border-emerald-300';
    } else if (score >= 50 || tier === 'MEDIUM') {
      grade = 'B';
      color = 'bg-amber-100 text-amber-800 border-amber-300';
    }
    
    return { grade, color, score: score.toFixed(0), confidence: confidence.toFixed(0) };
  };

  const scoreBadge = getScoreBadge();
  
  // Format expiration nicely
  const formatExpiration = (expirationDate: string) => {
    const date = new Date(expirationDate);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <TooltipProvider>
      <div className="flex items-center justify-between p-4 pb-2">
      {/* Left: Symbol, Strategy, DTE */}
      <div className="flex items-center space-x-3">
        {/* Symbol - Prominent */}
        <div className="text-lg font-bold text-gray-900">
          {trade.symbol}
        </div>
        
        {/* Strategy - Secondary */}
        <Badge variant="secondary" className="text-xs">
          {trade.strategy_type.replace('_', ' ')}
        </Badge>
        
        {/* DTE - Tertiary info */}
        <div className="flex items-center text-xs text-gray-500">
          <Calendar className="w-3 h-3 mr-1" />
          {trade.days_to_expiration}d • {formatExpiration(trade.expiration)}
        </div>
        
        {/* Earnings Warning - Critical info (only if earnings before expiry) */}
        {trade.earnings_days !== undefined && trade.earnings_days <= 7 && trade.earnings_days < trade.days_to_expiration && (
          <Tooltip>
            <TooltipTrigger>
              <Badge variant="outline" className="text-xs bg-amber-50 text-amber-700 border-amber-300 cursor-help">
                <AlertTriangle className="w-3 h-3 mr-1" />
                Earnings {trade.earnings_days}d
              </Badge>
            </TooltipTrigger>
            <TooltipContent side="bottom">
              <div className="text-center max-w-48">
                <div className="font-semibold">⚠ Earnings Risk</div>
                <div className="text-xs mt-1">
                  Earnings in {trade.earnings_days} day{trade.earnings_days !== 1 ? 's' : ''} • 
                  Expiry in {trade.days_to_expiration} days
                </div>
                <div className="text-xs mt-1 opacity-80">
                  Options may experience high volatility and price gaps around earnings
                </div>
              </div>
            </TooltipContent>
          </Tooltip>
        )}
      </div>

      {/* Right: Big Score Badge */}
      <div className={`px-3 py-2 rounded-lg border-2 ${scoreBadge.color} flex items-center space-x-2`}>
        <div className="text-center">
          <div className="text-xl font-bold leading-none">
            {scoreBadge.grade}
          </div>
          <div className="text-xs opacity-75 leading-none">
            {scoreBadge.score}
          </div>
        </div>
        <div className="text-xs opacity-75">
          {scoreBadge.confidence}%
        </div>
      </div>
      </div>
    </TooltipProvider>
  );
};

export default React.memo(TradeCardHeader);