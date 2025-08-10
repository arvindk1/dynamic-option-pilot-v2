import React, { memo } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Sun, Moon } from 'lucide-react';
import { WebSocketStatus } from '@/components/WebSocketStatus';
import { TourTrigger } from '@/components/TradingTour';
import { HelpMenu } from '@/components/HelpMenu';
import { AccountSummaryWidget } from '@/components/AccountSummaryWidget';

// Type definitions
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

interface DashboardHeaderProps {
  theme: string;
  toggleTheme: () => void;
  isDemoMode: boolean;
  onDemoModeToggle: (enabled: boolean) => void;
  onStartTour: () => void;
  isFirstVisit: boolean;
  config: TradingConfig;
  accountMetrics: AccountMetrics;
}

const DashboardHeaderComponent: React.FC<DashboardHeaderProps> = ({
  theme,
  toggleTheme,
  isDemoMode,
  onDemoModeToggle,
  onStartTour,
  isFirstVisit,
  config,
  accountMetrics
}) => {
  return (
    <header className="sticky top-0 z-50 bg-background/95 backdrop-blur-md border-b border-border/40 px-6 py-4 shadow-sm">
      <div className="flex items-center justify-between w-full">
        <div>
          <h1 className="text-3xl lg:text-4xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-emerald-400 bg-clip-text text-transparent">
            Dynamic Options Pilot
          </h1>
          <p className="text-muted-foreground mt-1 text-sm lg:text-base">Algorithmic Options Trading Platform</p>
        </div>
        <div className="flex items-center gap-3 lg:gap-4">
          {/* Demo Mode Toggle */}
          <div className="demo-mode-toggle flex items-center gap-2 px-3 py-2 bg-card/50 border rounded-lg backdrop-blur-sm">
            <Label htmlFor="demo-mode" className="text-xs lg:text-sm font-medium">Demo</Label>
            <Switch
              id="demo-mode"
              checked={isDemoMode}
              onCheckedChange={onDemoModeToggle}
            />
          </div>
        
          {/* Help Menu */}
          <HelpMenu onStartTour={onStartTour} />
          
          {/* Tour Trigger - Show only for first-time visitors */}
          {!isFirstVisit && (
            <TourTrigger onStartTour={onStartTour} variant="link" />
          )}
          
          <Button variant="outline" size="icon" onClick={toggleTheme} className="hover:bg-accent/50">
            {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>
          
          <Badge variant={config.paperTrading ? "secondary" : "destructive"} className="px-2 py-1 text-xs">
            {config.paperTrading ? 'Paper' : 'Live'}
          </Badge>
          
          <WebSocketStatus />
          
          <AccountSummaryWidget accountMetrics={accountMetrics} />
        </div>
      </div>
    </header>
  );
};

// Export with memo for performance optimization
export const DashboardHeader = memo(DashboardHeaderComponent);

// Export types for reuse
export type { TradingConfig, AccountMetrics, DashboardHeaderProps };