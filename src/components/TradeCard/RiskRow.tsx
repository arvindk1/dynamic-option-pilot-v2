import React from 'react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { DollarSign, TrendingDown, Calculator } from 'lucide-react';

interface TradeOpportunity {
  max_loss?: number;
  premium?: number;
  underlying_price?: number;
  strike?: number;
  short_strike?: number;
  long_strike?: number;
  strategy_type?: string;
}

interface RiskRowProps {
  trade: TradeOpportunity;
}

const RiskRow: React.FC<RiskRowProps> = ({ trade }) => {
  // Calculate breakeven for different strategy types
  const calculateBreakeven = () => {
    if (!trade.underlying_price || !trade.premium) return null;
    
    const premium = trade.premium;
    const underlyingPrice = trade.underlying_price;
    
    // Simple approximation - in production, use proper options math
    if (trade.strategy_type?.includes('PUT')) {
      return trade.strike ? (trade.strike - premium) : null;
    } else if (trade.strategy_type?.includes('CALL')) {
      return trade.strike ? (trade.strike + premium) : null;
    } else if (trade.strategy_type?.includes('SPREAD')) {
      // For spreads, breakeven is more complex
      const midStrike = trade.short_strike || trade.strike || underlyingPrice;
      return midStrike + (premium * 0.5); // Simplified
    }
    
    return underlyingPrice + premium; // Default fallback
  };

  // Estimate margin requirement (simplified)
  const estimateMargin = () => {
    if (!trade.max_loss && !trade.premium && !trade.underlying_price) return null;
    
    const underlyingPrice = trade.underlying_price || 100;
    
    // Rough margin estimates by strategy type
    if (trade.strategy_type?.includes('CREDIT')) {
      return (trade.max_loss || 0) * 100; // Credit spreads
    } else if (trade.strategy_type?.includes('IRON')) {
      return (trade.max_loss || underlyingPrice * 0.1) * 100; // Iron condors
    } else if (trade.strategy_type?.includes('NAKED')) {
      return underlyingPrice * 20; // 20% of underlying (simplified)
    } else {
      return (trade.max_loss || underlyingPrice * 0.05) * 100; // Conservative default
    }
  };

  const breakeven = calculateBreakeven();
  const estimatedMargin = estimateMargin();

  return (
    <TooltipProvider>
      <div className="px-4 pb-3 border-b border-gray-100">
        <div className="grid grid-cols-3 gap-4 text-center">
          {/* Max Loss */}
          <Tooltip>
            <TooltipTrigger>
              <div className="flex flex-col items-center space-y-1 cursor-help">
                <div className="flex items-center space-x-1 text-xs text-gray-500">
                  <TrendingDown className="w-3 h-3" />
                  <span>Max Loss</span>
                </div>
                <div className="text-sm font-semibold text-red-600">
                  ${trade.max_loss ? Math.abs(trade.max_loss).toFixed(0) : 'N/A'}
                </div>
              </div>
            </TooltipTrigger>
            <TooltipContent>
              Maximum possible loss if trade goes completely wrong
            </TooltipContent>
          </Tooltip>

          {/* Breakeven */}
          <Tooltip>
            <TooltipTrigger>
              <div className="flex flex-col items-center space-y-1 cursor-help">
                <div className="flex items-center space-x-1 text-xs text-gray-500">
                  <DollarSign className="w-3 h-3" />
                  <span>Breakeven</span>
                </div>
                <div className="text-sm font-semibold text-gray-700">
                  {breakeven ? `$${breakeven.toFixed(2)}` : 'Calc'}
                </div>
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <div className="text-center">
                <div>Price where trade breaks even</div>
                {trade.underlying_price && breakeven && (
                  <div className="text-xs mt-1 opacity-80">
                    Current: ${trade.underlying_price.toFixed(2)} 
                    {breakeven > trade.underlying_price 
                      ? ` (+${((breakeven - trade.underlying_price) / trade.underlying_price * 100).toFixed(1)}%)`
                      : ` (${((breakeven - trade.underlying_price) / trade.underlying_price * 100).toFixed(1)}%)`
                    }
                  </div>
                )}
              </div>
            </TooltipContent>
          </Tooltip>

          {/* Estimated Margin */}
          <Tooltip>
            <TooltipTrigger>
              <div className="flex flex-col items-center space-y-1 cursor-help">
                <div className="flex items-center space-x-1 text-xs text-gray-500">
                  <Calculator className="w-3 h-3" />
                  <span>Est. Margin</span>
                </div>
                <div className="text-sm font-semibold text-gray-700">
                  {estimatedMargin ? `$${estimatedMargin.toFixed(0)}` : 'N/A'}
                </div>
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <div className="text-center">
                <div>Estimated margin requirement</div>
                <div className="text-xs mt-1 opacity-80">
                  Varies by broker and account type
                </div>
              </div>
            </TooltipContent>
          </Tooltip>
        </div>
      </div>
    </TooltipProvider>
  );
};

export default React.memo(RiskRow);