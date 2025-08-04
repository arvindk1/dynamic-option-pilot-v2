import { useState, useCallback, useEffect } from 'react';
import { dataThrottleService } from '@/services/dataThrottle';

interface ApiOpportunity {
  id: string;
  symbol: string;
  short_strike?: number;
  long_strike?: number;
  strike?: number;
  premium: number;
  max_loss: number;
  delta: number;
  probability_profit: number;
  expected_value: number;
  days_to_expiration: number;
  underlying_price: number;
  liquidity_score: number;
  bias: string;
  rsi: number;
}

interface SpreadCandidate {
  id: string;
  symbol?: string;
  shortStrike: number;
  longStrike: number;
  credit: number;
  maxLoss: number;
  delta: number;
  probabilityProfit: number;
  expectedValue: number;
  daysToExpiration: number;
  type: 'PUT' | 'CALL';
  underlyingPrice?: number;
  liquidityScore?: number;
  bias?: string;
  rsi?: number;
}

interface EnhancedTradeOpportunity {
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
}

interface EnhancedTradeCategories {
  high_probability: EnhancedTradeOpportunity[];
  quick_scalps: EnhancedTradeOpportunity[];
  swing_trades: EnhancedTradeOpportunity[];
  volatility_plays: EnhancedTradeOpportunity[];
  thetacrop: EnhancedTradeOpportunity[];
}

export const useTradingOpportunities = (isDemoMode: boolean, demoModeInitialized: boolean) => {
  const [spreadCandidates, setSpreadCandidates] = useState<SpreadCandidate[]>([]);
  const [enhancedOpportunities, setEnhancedOpportunities] = useState<EnhancedTradeOpportunity[]>([]);
  const [tradeCategories, setTradeCategories] = useState<EnhancedTradeCategories>({
    high_probability: [],
    quick_scalps: [],
    swing_trades: [],
    volatility_plays: [],
    thetacrop: []
  });
  const [loadingOpportunities, setLoadingOpportunities] = useState(false);
  const [dataSourceInfo, setDataSourceInfo] = useState<{
    underlying_data: string;
    options_pricing: string;
    expiration_dates: string;
    disclaimer: string;
  } | null>(null);
  const [scanMethodology, setScanMethodology] = useState<{
    universe: string[];
    symbols_scanned: number;
    total_symbols: number;
    strategies: string[];
    filters: Record<string, string>;
    expiration_range: string;
    refresh_rate: string;
  } | null>(null);

  const loadTradingOpportunities = useCallback(async () => {
    setLoadingOpportunities(true);
    try {
      const endpoint = isDemoMode ? '/api/demo/opportunities' : '/api/trading/opportunities';

      const data = await dataThrottleService.getData(
        `trading-opportunities-${isDemoMode}`,
        async () => {
          const response = await fetch(endpoint);
          if (response.ok) {
            return await response.json();
          }
          throw new Error('Failed to fetch trading opportunities');
        },
        240000 // Cache for 4 minutes
      );

      if (data) {
        setEnhancedOpportunities(data.opportunities || []);

        if (data.categories) {
          setTradeCategories(data.categories);
        }

        if (data.data_source_info) {
          setDataSourceInfo(data.data_source_info);
        }
        if (data.scan_methodology) {
          setScanMethodology(data.scan_methodology);
        }

        const rawOpportunities = data.opportunities || [];
        const candidates = rawOpportunities.map((opp: ApiOpportunity) => ({
          id: opp.id,
          symbol: opp.symbol,
          shortStrike: opp.short_strike || opp.strike,
          longStrike: opp.long_strike || (opp.strike ? opp.strike - 5 : 0),
          credit: opp.premium,
          maxLoss: opp.max_loss * 100,
          delta: opp.delta,
          probabilityProfit: opp.probability_profit,
          expectedValue: opp.expected_value * 100,
          daysToExpiration: opp.days_to_expiration,
          type: 'PUT', // This is a placeholder, should be derived from the opportunity
          underlyingPrice: opp.underlying_price,
          liquidityScore: opp.liquidity_score,
          bias: opp.bias,
          rsi: opp.rsi
        }));
        setSpreadCandidates(candidates);
      }
    } catch (error) {
      console.error('Failed to load trading opportunities:', error);
      setSpreadCandidates([]);
    } finally {
      setLoadingOpportunities(false);
    }
  }, [isDemoMode]);

  useEffect(() => {
    if (demoModeInitialized) {
      loadTradingOpportunities();
      const interval = setInterval(loadTradingOpportunities, 300000); // Update every 5 minutes
      return () => clearInterval(interval);
    }
  }, [demoModeInitialized, loadTradingOpportunities]);

  return {
    spreadCandidates,
    enhancedOpportunities,
    tradeCategories,
    loadingOpportunities,
    dataSourceInfo,
    scanMethodology,
    loadTradingOpportunities
  };
};
