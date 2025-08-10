/**
 * Strategy-aware option display system
 * 
 * This component intelligently displays option structures based on each strategy's
 * specific requirements. Different strategies have different numbers of legs and
 * need different display formats.
 */

import React from 'react';
import { Badge } from '@/components/ui/badge';

interface OptionLeg {
  type: 'CALL' | 'PUT' | 'STOCK';
  position: 'LONG' | 'SHORT';
  strike?: number;
  expiration?: string;
  quantity: number;
}

interface TradeOpportunity {
  strategy_type: string;
  symbol: string;
  strike?: number;
  short_strike?: number;
  long_strike?: number;
  underlying_price: number;
  expiration?: string;
  days_to_expiration?: number;
}

interface StrategyDisplayProps {
  trade: TradeOpportunity;
  compact?: boolean;
}

// Strategy complexity classification
const STRATEGY_STRUCTURES = {
  // Single-leg strategies (1 option)
  'NAKED_CALL': { legs: 1, hasStock: false, type: 'naked' },
  'NAKED_PUT': { legs: 1, hasStock: false, type: 'naked' },
  'NAKED_OPTION': { legs: 1, hasStock: false, type: 'naked' },
  'SINGLE_OPTION': { legs: 1, hasStock: false, type: 'naked' },
  
  // Stock + option strategies (2 positions)
  'COVERED_CALL': { legs: 1, hasStock: true, type: 'covered' },
  'PROTECTIVE_PUT': { legs: 1, hasStock: true, type: 'protective' },
  
  // Two-leg option strategies
  'VERTICAL_SPREAD': { legs: 2, hasStock: false, type: 'spread' },
  'CREDIT_SPREAD': { legs: 2, hasStock: false, type: 'spread' },
  'DEBIT_SPREAD': { legs: 2, hasStock: false, type: 'spread' },
  'CALENDAR_SPREAD': { legs: 2, hasStock: false, type: 'calendar' },
  
  // Three-leg strategies
  'COLLAR': { legs: 2, hasStock: true, type: 'collar' }, // Stock + put + call
  'BUTTERFLY': { legs: 3, hasStock: false, type: 'butterfly' },
  
  // Four-leg strategies
  'IRON_CONDOR': { legs: 4, hasStock: false, type: 'condor' },
  'IRON_BUTTERFLY': { legs: 3, hasStock: false, type: 'butterfly' },
  
  // Straddles/Strangles
  'STRADDLE': { legs: 2, hasStock: false, type: 'volatility' },
  'STRANGLE': { legs: 2, hasStock: false, type: 'volatility' },
  
  // Theta strategies
  'THETA_HARVESTING': { legs: 4, hasStock: false, type: 'condor' },
  'RSI_COUPON': { legs: 1, hasStock: false, type: 'naked' },
};

const getStrategyStructure = (strategyType: string) => {
  return STRATEGY_STRUCTURES[strategyType as keyof typeof STRATEGY_STRUCTURES] || 
         { legs: 1, hasStock: false, type: 'unknown' };
};

// Strategy-specific display components
const SingleLegDisplay: React.FC<{ trade: TradeOpportunity }> = ({ trade }) => {
  const strike = trade.strike || trade.short_strike || trade.long_strike;
  const optionType = trade.strategy_type.includes('CALL') ? 'CALL' : 
                    trade.strategy_type.includes('PUT') ? 'PUT' : 'OPTION';
  
  return (
    <div className="flex items-center space-x-2">
      <Badge variant="outline" className="text-xs">
        {optionType}
      </Badge>
      <span className="font-medium">${strike}</span>
    </div>
  );
};

const CoveredCallDisplay: React.FC<{ trade: TradeOpportunity }> = ({ trade }) => {
  const callStrike = trade.short_strike || trade.strike;
  
  return (
    <div className="space-y-1">
      <div className="flex items-center space-x-2 text-sm">
        <Badge variant="secondary" className="text-xs">STOCK</Badge>
        <span>100 shares @ ${trade.underlying_price.toFixed(2)}</span>
      </div>
      <div className="flex items-center space-x-2">
        <Badge variant="outline" className="text-xs bg-red-50 text-red-700">SHORT CALL</Badge>
        <span className="font-medium">${callStrike}</span>
      </div>
    </div>
  );
};

const ProtectivePutDisplay: React.FC<{ trade: TradeOpportunity }> = ({ trade }) => {
  const putStrike = trade.long_strike || trade.strike;
  
  return (
    <div className="space-y-1">
      <div className="flex items-center space-x-2 text-sm">
        <Badge variant="secondary" className="text-xs">STOCK</Badge>
        <span>100 shares @ ${trade.underlying_price.toFixed(2)}</span>
      </div>
      <div className="flex items-center space-x-2">
        <Badge variant="outline" className="text-xs bg-green-50 text-green-700">LONG PUT</Badge>
        <span className="font-medium">${putStrike}</span>
      </div>
    </div>
  );
};

const VerticalSpreadDisplay: React.FC<{ trade: TradeOpportunity }> = ({ trade }) => {
  const longStrike = trade.long_strike;
  const shortStrike = trade.short_strike;
  
  return (
    <div className="space-y-1">
      <div className="flex items-center space-x-2">
        <Badge variant="outline" className="text-xs bg-green-50 text-green-700">LONG</Badge>
        <span>${longStrike}</span>
      </div>
      <div className="flex items-center space-x-2">
        <Badge variant="outline" className="text-xs bg-red-50 text-red-700">SHORT</Badge>
        <span>${shortStrike}</span>
      </div>
    </div>
  );
};

const IronCondorDisplay: React.FC<{ trade: TradeOpportunity }> = ({ trade }) => {
  // Iron Condor: Long Put / Short Put / Short Call / Long Call
  const shortPutStrike = trade.short_strike;
  const shortCallStrike = trade.long_strike;
  const wingWidth = 5; // Could be calculated from actual trade data
  
  const longPutStrike = shortPutStrike ? shortPutStrike - wingWidth : 0;
  const longCallStrike = shortCallStrike ? shortCallStrike + wingWidth : 0;
  
  return (
    <div className="space-y-1">
      <div className="text-xs text-muted-foreground mb-1">4-Leg Iron Condor</div>
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div className="space-y-1">
          <div className="flex items-center space-x-1">
            <Badge className="text-[10px] bg-green-100 text-green-800">LP</Badge>
            <span>${longPutStrike}</span>
          </div>
          <div className="flex items-center space-x-1">
            <Badge className="text-[10px] bg-red-100 text-red-800">SP</Badge>
            <span>${shortPutStrike}</span>
          </div>
        </div>
        <div className="space-y-1">
          <div className="flex items-center space-x-1">
            <Badge className="text-[10px] bg-red-100 text-red-800">SC</Badge>
            <span>${shortCallStrike}</span>
          </div>
          <div className="flex items-center space-x-1">
            <Badge className="text-[10px] bg-green-100 text-green-800">LC</Badge>
            <span>${longCallStrike}</span>
          </div>
        </div>
      </div>
      <div className="text-xs text-muted-foreground">
        Profit Zone: ${shortPutStrike} - ${shortCallStrike}
      </div>
    </div>
  );
};

const StraddleDisplay: React.FC<{ trade: TradeOpportunity }> = ({ trade }) => {
  const atmStrike = trade.short_strike || trade.strike;
  
  return (
    <div className="space-y-1">
      <div className="text-xs text-muted-foreground">At-The-Money Straddle</div>
      <div className="flex items-center justify-center space-x-2">
        <Badge variant="outline" className="text-xs">CALL + PUT</Badge>
        <span className="font-medium">${atmStrike}</span>
      </div>
    </div>
  );
};

const StrangleDisplay: React.FC<{ trade: TradeOpportunity }> = ({ trade }) => {
  const putStrike = trade.short_strike;
  const callStrike = trade.long_strike;
  
  return (
    <div className="space-y-1">
      <div className="text-xs text-muted-foreground">Strangle</div>
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-1">
          <Badge variant="outline" className="text-xs">PUT</Badge>
          <span>${putStrike}</span>
        </div>
        <div className="flex items-center space-x-1">
          <Badge variant="outline" className="text-xs">CALL</Badge>
          <span>${callStrike}</span>
        </div>
      </div>
    </div>
  );
};

const ButterflyDisplay: React.FC<{ trade: TradeOpportunity }> = ({ trade }) => {
  const centerStrike = trade.short_strike || trade.strike;
  const wingWidth = 5; // Could be calculated
  
  return (
    <div className="space-y-1">
      <div className="text-xs text-muted-foreground">Butterfly Spread</div>
      <div className="flex items-center justify-center space-x-2">
        <span className="text-sm">${centerStrike - wingWidth}</span>
        <Badge variant="secondary" className="text-xs">${centerStrike}</Badge>
        <span className="text-sm">${centerStrike + wingWidth}</span>
      </div>
    </div>
  );
};

const CalendarSpreadDisplay: React.FC<{ trade: TradeOpportunity }> = ({ trade }) => {
  const strike = trade.strike || trade.short_strike;
  const dte = trade.days_to_expiration || 30;
  
  return (
    <div className="space-y-1">
      <div className="text-xs text-muted-foreground">Calendar Spread</div>
      <div className="flex items-center space-x-2">
        <Badge variant="outline" className="text-xs">SAME STRIKE</Badge>
        <span className="font-medium">${strike}</span>
      </div>
      <div className="text-xs text-muted-foreground">
        Near: {dte}d • Far: {dte + 30}d
      </div>
    </div>
  );
};

export const StrategyDisplay: React.FC<StrategyDisplayProps> = ({ trade, compact = false }) => {
  const structure = getStrategyStructure(trade.strategy_type);
  
  // Route to appropriate display component based on strategy type
  const renderStrategyStructure = () => {
    switch (trade.strategy_type) {
      case 'NAKED_CALL':
      case 'NAKED_PUT':
      case 'NAKED_OPTION':
      case 'SINGLE_OPTION':
        return <SingleLegDisplay trade={trade} />;
      
      case 'COVERED_CALL':
        return <CoveredCallDisplay trade={trade} />;
      
      case 'PROTECTIVE_PUT':
        return <ProtectivePutDisplay trade={trade} />;
      
      case 'VERTICAL_SPREAD':
      case 'CREDIT_SPREAD':
      case 'DEBIT_SPREAD':
        return <VerticalSpreadDisplay trade={trade} />;
      
      case 'IRON_CONDOR':
      case 'THETA_HARVESTING':
        return <IronCondorDisplay trade={trade} />;
      
      case 'STRADDLE':
        return <StraddleDisplay trade={trade} />;
      
      case 'STRANGLE':
        return <StrangleDisplay trade={trade} />;
      
      case 'BUTTERFLY':
        return <ButterflyDisplay trade={trade} />;
      
      case 'CALENDAR_SPREAD':
        return <CalendarSpreadDisplay trade={trade} />;
      
      default:
        // Fallback for unknown strategies
        return (
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="text-xs">
              {trade.strategy_type.replace('_', ' ')}
            </Badge>
            <span>${trade.strike || trade.short_strike || 'N/A'}</span>
          </div>
        );
    }
  };

  return (
    <div className={`strategy-display ${compact ? 'compact' : ''}`}>
      {renderStrategyStructure()}
    </div>
  );
};

// Helper function to get strategy complexity info
export const getStrategyInfo = (strategyType: string) => {
  const structure = getStrategyStructure(strategyType);
  
  return {
    legs: structure.legs,
    hasStock: structure.hasStock,
    type: structure.type,
    complexity: structure.legs > 2 ? 'complex' : structure.hasStock ? 'covered' : 'simple'
  };
};

// Export for use in other components
export { STRATEGY_STRUCTURES };