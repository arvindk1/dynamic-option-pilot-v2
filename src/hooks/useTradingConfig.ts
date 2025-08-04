import { useState } from 'react';

interface TradingConfig {
  brokerPlugin: string;
  paperTrading: boolean;
  symbol: string;
  dteMin: number;
  dteMax: number;
  deltaTarget: number;
  creditThreshold: number;
  maxSpreadWidth: number;
  maxPositions: number;
  positionSizePct: number;
  maxMarginUsage: number;
  maxDrawdown: number;
  kellyFraction: number;
}

export const useTradingConfig = () => {
  const [config, setConfig] = useState<TradingConfig>({
    brokerPlugin: 'alpaca',
    paperTrading: true,
    symbol: 'SPX',
    dteMin: 30,
    dteMax: 45,
    deltaTarget: 0.10,
    creditThreshold: 0.50,
    maxSpreadWidth: 50,
    maxPositions: 5,
    positionSizePct: 0.02,
    maxMarginUsage: 0.50,
    maxDrawdown: 0.15,
    kellyFraction: 0.25
  });

  return { config, setConfig };
};
