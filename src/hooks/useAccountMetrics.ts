import { useState, useCallback, useEffect } from 'react';
import { dataThrottleService } from '@/services/dataThrottle';

interface AccountMetrics {
  account_balance: number;
  cash: number;
  buying_power: number;
  account_status: string;
  margin_used: number;
  total_pnl: number;
  win_rate: number;
  total_trades: number;
  positions_open: number;
  max_drawdown: number;
  sharpe_ratio: number;
  vix: number;
  iv_rank: number;
  options_level: string;
  data_state?: string;
  warning?: string;
  demo_notice?: string;
  is_demo?: boolean;
  last_updated?: string;
}

export const useAccountMetrics = (isDemoMode: boolean, demoModeInitialized: boolean) => {
  const [accountMetrics, setAccountMetrics] = useState<AccountMetrics>({
    account_balance: 0,
    cash: 0,
    buying_power: 0,
    account_status: 'LOADING',
    margin_used: 0,
    total_pnl: 0,
    win_rate: 0,
    total_trades: 0,
    positions_open: 0,
    max_drawdown: 0,
    sharpe_ratio: 0,
    vix: 0,
    iv_rank: 0,
    options_level: 'Unknown'
  });

  const loadAccountMetrics = useCallback(async () => {
    try {
      const endpoint = isDemoMode ? '/api/demo/account/metrics' : '/api/dashboard/metrics';

      const metrics = await dataThrottleService.getData(
        `account-metrics-${isDemoMode}`,
        async () => {
          const response = await fetch(endpoint);
          if (response.ok) {
            return await response.json();
          }
          throw new Error('Failed to fetch account metrics');
        },
        180000 // Cache for 3 minutes
      );

      if (metrics) {
        setAccountMetrics({
          account_balance: metrics.account_balance || 0,
          cash: metrics.cash || 0,
          buying_power: metrics.buying_power || 0,
          account_status: metrics.account_status || 'UNKNOWN',
          margin_used: metrics.margin_used || 0,
          total_pnl: metrics.total_pnl || 0,
          win_rate: metrics.win_rate || 0,
          total_trades: metrics.total_trades || 0,
          positions_open: metrics.positions_open || 0,
          max_drawdown: metrics.max_drawdown || 0,
          sharpe_ratio: metrics.sharpe_ratio || 0,
          options_level: metrics.options_level || 'Level 1',
          vix: metrics.vix || 18.5,
          iv_rank: metrics.iv_rank || 45,
          data_state: metrics.data_state,
          warning: metrics.warning,
          demo_notice: metrics.demo_notice,
          is_demo: metrics.is_demo,
          last_updated: metrics.last_updated
        });
      }
    } catch (error) {
      console.error('Failed to load account metrics:', error);
    }
  }, [isDemoMode]);

  useEffect(() => {
    if (demoModeInitialized) {
      loadAccountMetrics();
      const interval = setInterval(loadAccountMetrics, 300000); // Update every 5 minutes
      return () => clearInterval(interval);
    }
  }, [demoModeInitialized, loadAccountMetrics]);

  return { accountMetrics, loadAccountMetrics };
};
