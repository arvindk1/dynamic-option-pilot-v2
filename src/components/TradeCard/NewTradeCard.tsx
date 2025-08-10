import React from 'react';
import { Card } from '@/components/ui/card';
import TradeCardHeader from './TradeCardHeader';
import FactorChips from './FactorChips';
import RiskRow from './RiskRow';
import TradeCardActions from './TradeCardActions';

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
  earnings_days?: number; // Days until next earnings (if within 7 days)
  
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

/**
 * New TradeCard with improved visual hierarchy following UX review:
 * 1. Header: SYMBOL • STRATEGY • DTE • Big Score Badge (A/B/C + 0.84)
 * 2. Factor Chips: Top 3 from score_breakdown with tooltips ("Trend ↑", "IV Edge ↑", "Liquidity ↘")
 * 3. Risk Row: Max Loss • Breakeven • Est. Margin (compact, muted)
 * 4. Actions: View Legs / Simulate • Pin
 */
export const NewTradeCard: React.FC<TradeCardProps> = React.memo(({ 
  trade, 
  onExecute, 
  isExecuting = false 
}) => {
  // State for pin functionality (placeholder for future implementation)
  const [isPinned, setIsPinned] = React.useState(false);
  
  const handlePin = (trade: TradeOpportunity, pinned: boolean) => {
    setIsPinned(pinned);
    // TODO: Implement global pin state management via context
    console.log(`Trade ${trade.id} ${pinned ? 'pinned' : 'unpinned'}`);
  };

  return (
    <Card className="hover:shadow-lg transition-all duration-200 border border-border/50 hover:border-border bg-white">
      {/* Header: SYMBOL • STRATEGY • DTE • Big Score Badge (A/B/C + 0.84) */}
      <TradeCardHeader trade={trade} />
      
      {/* Factor Chips: Top 3 from score_breakdown with tooltips */}
      <FactorChips trade={trade} />
      
      {/* Risk Row: Max Loss • Breakeven • Est. Margin (compact, muted) */}
      <RiskRow trade={trade} />
      
      {/* Actions: View Legs / Simulate • Pin */}
      <TradeCardActions 
        trade={trade}
        onExecute={onExecute}
        onPin={handlePin}
        isPinned={isPinned}
        isExecuting={isExecuting}
      />
    </Card>
  );
});

NewTradeCard.displayName = 'NewTradeCard';

export default NewTradeCard;