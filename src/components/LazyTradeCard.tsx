import React, { lazy, Suspense } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

// Lazy load the heavy TradeCard components
const NewTradeCard = lazy(() => import('./TradeCard/NewTradeCard'));
const CompactTradeCard = lazy(() => import('./TradeCard/TradeCard').then(module => ({ 
  default: module.CompactTradeCard 
})));

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
  earnings_days?: number;
  
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

interface LazyTradeCardProps {
  trade: TradeOpportunity;
  onExecute: (trade: TradeOpportunity) => void;
  isExecuting?: boolean;
  isMobile?: boolean;
}

// Skeleton loader matching TradeCard structure
const TradeCardSkeleton: React.FC = () => (
  <Card className="border border-border/50 bg-white">
    {/* Header skeleton */}
    <div className="p-4 pb-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Skeleton className="h-6 w-16" /> {/* Symbol */}
          <Skeleton className="h-5 w-20" /> {/* Strategy */}
          <Skeleton className="h-4 w-12" /> {/* DTE */}
        </div>
        <Skeleton className="h-12 w-16" /> {/* Score badge */}
      </div>
    </div>
    
    {/* Factor chips skeleton */}
    <div className="px-4 pb-2">
      <div className="flex space-x-2">
        <Skeleton className="h-6 w-16" />
        <Skeleton className="h-6 w-20" />
        <Skeleton className="h-6 w-18" />
      </div>
    </div>
    
    {/* Risk row skeleton */}
    <div className="px-4 pb-3 border-b border-gray-100">
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center">
          <Skeleton className="h-3 w-12 mx-auto mb-1" />
          <Skeleton className="h-4 w-16 mx-auto" />
        </div>
        <div className="text-center">
          <Skeleton className="h-3 w-12 mx-auto mb-1" />
          <Skeleton className="h-4 w-16 mx-auto" />
        </div>
        <div className="text-center">
          <Skeleton className="h-3 w-12 mx-auto mb-1" />
          <Skeleton className="h-4 w-16 mx-auto" />
        </div>
      </div>
    </div>
    
    {/* Actions skeleton */}
    <div className="px-4 pb-4">
      <div className="flex justify-between mb-3">
        <div className="flex space-x-2">
          <Skeleton className="h-8 w-20" />
          <Skeleton className="h-8 w-20" />
        </div>
        <div className="flex space-x-2">
          <Skeleton className="h-8 w-12" />
          <Skeleton className="h-8 w-24" />
        </div>
      </div>
      <Skeleton className="h-10 w-full" /> {/* Stats row */}
    </div>
  </Card>
);

/**
 * Lazy-loaded TradeCard with performance optimizations:
 * - Lazy loading reduces initial bundle size
 * - Skeleton provides instant visual feedback
 * - Mobile/desktop switching without heavy loading
 */
export const LazyTradeCard: React.FC<LazyTradeCardProps> = ({
  trade,
  onExecute,
  isExecuting = false,
  isMobile = false
}) => {
  return (
    <Suspense fallback={<TradeCardSkeleton />}>
      {isMobile ? (
        <CompactTradeCard 
          trade={trade} 
          onExecute={onExecute} 
          isExecuting={isExecuting} 
        />
      ) : (
        <NewTradeCard 
          trade={trade} 
          onExecute={onExecute} 
          isExecuting={isExecuting} 
        />
      )}
    </Suspense>
  );
};

export default LazyTradeCard;