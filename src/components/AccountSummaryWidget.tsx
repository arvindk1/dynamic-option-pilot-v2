import React, { memo } from 'react';
import { Badge } from '@/components/ui/badge';

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

interface AccountSummaryWidgetProps {
  accountMetrics: AccountMetrics;
}

const AccountSummaryWidgetComponent: React.FC<AccountSummaryWidgetProps> = ({
  accountMetrics
}) => {
  return (
    <div className="dashboard-overview hidden lg:block text-right space-y-2 bg-gradient-to-br from-card/40 to-card/20 p-4 rounded-lg backdrop-blur-sm border border-border/50 shadow-lg min-w-[240px]">
      {/* Account Balance - Primary metric */}
      <div className="border-b border-border/30 pb-2">
        <div className="text-2xl font-bold text-emerald-400">${accountMetrics.account_balance.toLocaleString()}</div>
        <div className="text-xs text-muted-foreground">Account Balance</div>
      </div>
      
      {/* Key Trading Metrics */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Cash:</span>
          <span className="text-blue-400 font-medium">${accountMetrics.cash.toLocaleString()}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Buying Power:</span>
          <span className="text-purple-400 font-medium">${accountMetrics.buying_power.toLocaleString()}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">P&L Today:</span>
          <span className={`font-medium ${accountMetrics.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {accountMetrics.total_pnl >= 0 ? '+' : ''}${accountMetrics.total_pnl.toLocaleString()}
          </span>
        </div>
      </div>
      
      {/* Options Level & Status */}
      <div className="pt-2 border-t border-border/30">
        <div className="flex justify-between items-center text-xs">
          <span className="text-muted-foreground">Options Level:</span>
          <Badge variant="secondary" className="text-xs">{accountMetrics.options_level}</Badge>
        </div>
        <div className="flex justify-between items-center text-xs mt-1">
          <span className="text-muted-foreground">Status:</span>
          <Badge variant={accountMetrics.account_status === 'ACTIVE' ? 'default' : 'secondary'} className="text-xs">
            {accountMetrics.account_status}
          </Badge>
        </div>
      </div>
    </div>
  );
};

// Export with memo for performance optimization
export const AccountSummaryWidget = memo(AccountSummaryWidgetComponent);

// Export types for reuse
export type { AccountMetrics, AccountSummaryWidgetProps };