/**
 * TradingDashboardHeader - Optimized header component for trading dashboard
 * Contains account metrics, market status, and navigation controls
 */
import React, { memo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Activity, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  Settings,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  Moon,
  Sun
} from 'lucide-react';
import { useTheme } from '@/contexts/ThemeContext';
import MarketStatusWidget from '@/components/MarketStatusWidget';
import { WebSocketStatus } from '@/components/WebSocketStatus';
import DemoModeAlert from '@/components/DemoModeAlert';
import { TourTrigger } from '@/components/TradingTour';

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
}

interface TradingDashboardHeaderProps {
  accountMetrics: AccountMetrics;
  isDemoMode: boolean;
  isFirstVisit: boolean;
  onShowTour: () => void;
  onToggleSettings?: () => void;
}

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

const formatPercentage = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`;
};

const getPnLIcon = (pnl: number) => {
  if (pnl > 0) return <TrendingUp className="h-4 w-4 text-green-500" />;
  if (pnl < 0) return <TrendingDown className="h-4 w-4 text-red-500" />;
  return <Minus className="h-4 w-4 text-gray-500" />;
};

const getPnLColor = (pnl: number): string => {
  if (pnl > 0) return 'text-green-600 dark:text-green-400';
  if (pnl < 0) return 'text-red-600 dark:text-red-400';
  return 'text-gray-600 dark:text-gray-400';
};

export const TradingDashboardHeader = memo<TradingDashboardHeaderProps>(({
  accountMetrics,
  isDemoMode,
  isFirstVisit,
  onShowTour,
  onToggleSettings
}) => {
  const { theme, toggleTheme } = useTheme();

  const accountStatus = accountMetrics.account_status === 'ACTIVE' ? 'success' : 'warning';
  const pnlColor = getPnLColor(accountMetrics.total_pnl);

  return (
    <div className="space-y-4">
      {/* Demo Mode Alert */}
      {isDemoMode && <DemoModeAlert />}

      {/* Main Header Card */}
      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950 border-blue-200 dark:border-blue-800">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Activity className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              <CardTitle className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                Trading Dashboard
              </CardTitle>
              <Badge variant={accountStatus} className="ml-2">
                {accountMetrics.account_status}
              </Badge>
            </div>
            
            <div className="flex items-center space-x-2">
              <WebSocketStatus />
              <MarketStatusWidget />
              
              {/* Theme Toggle */}
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleTheme}
                className="h-8 w-8 p-0"
                title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
              >
                {theme === 'dark' ? 
                  <Sun className="h-4 w-4" /> : 
                  <Moon className="h-4 w-4" />
                }
              </Button>

              {/* Settings */}
              {onToggleSettings && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onToggleSettings}
                  className="h-8 w-8 p-0"
                  title="Settings"
                >
                  <Settings className="h-4 w-4" />
                </Button>
              )}

              {/* Tour Trigger */}
              {isFirstVisit && (
                <TourTrigger onStartTour={onShowTour} />
              )}
            </div>
          </div>
        </CardHeader>
        
        <CardContent className="pt-0">
          {/* Account Metrics Row */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {/* Account Balance */}
            <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="flex items-center space-x-2">
                <DollarSign className="h-4 w-4 text-green-600 dark:text-green-400" />
                <div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Balance</p>
                  <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {formatCurrency(accountMetrics.account_balance)}
                  </p>
                </div>
              </div>
            </div>

            {/* Buying Power */}
            <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="flex items-center space-x-2">
                <Activity className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                <div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Buying Power</p>
                  <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {formatCurrency(accountMetrics.buying_power)}
                  </p>
                </div>
              </div>
            </div>

            {/* P&L */}
            <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="flex items-center space-x-2">
                {getPnLIcon(accountMetrics.total_pnl)}
                <div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">P&L</p>
                  <p className={`text-sm font-semibold ${pnlColor}`}>
                    {formatCurrency(accountMetrics.total_pnl)}
                  </p>
                </div>
              </div>
            </div>

            {/* Win Rate */}
            <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />
                <div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Win Rate</p>
                  <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {formatPercentage(accountMetrics.win_rate)}
                  </p>
                </div>
              </div>
            </div>

            {/* Positions */}
            <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="flex items-center space-x-2">
                <Activity className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                <div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Positions</p>
                  <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {accountMetrics.positions_open}
                  </p>
                </div>
              </div>
            </div>

            {/* VIX */}
            <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="h-4 w-4 text-orange-600 dark:text-orange-400" />
                <div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">VIX</p>
                  <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {accountMetrics.vix.toFixed(1)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Warning Message */}
          {accountMetrics.warning && (
            <div className="mt-3 p-2 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  {accountMetrics.warning}
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
});

TradingDashboardHeader.displayName = 'TradingDashboardHeader';

export default TradingDashboardHeader;