/**
 * TradingMetricsPanel - Performance metrics and risk analytics
 * Optimized component for displaying trading performance data
 */
import React, { memo, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  BarChart3,
  Shield,
  Target,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Activity
} from 'lucide-react';

interface RiskMetrics {
  portfolio_beta: number;
  portfolio_delta: number;
  portfolio_gamma: number;
  portfolio_theta: number;
  portfolio_vega: number;
  max_loss_per_trade: number;
  concentration_risk: number;
  margin_utilization: number;
  kelly_position_size: number;
  expected_move: number;
  probability_profit: number;
  risk_reward_ratio: number;
  sharpe_ratio: number;
  var_95: number;
  correlation_spy: number;
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
}

interface TradingMetricsPanelProps {
  accountMetrics: AccountMetrics;
  riskMetrics: RiskMetrics | null;
  marketBias: 'BULLISH' | 'NEUTRAL' | 'BEARISH';
  confidence: number;
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

const formatDecimal = (value: number, decimals: number = 2): string => {
  return value.toFixed(decimals);
};

const getBiasColor = (bias: 'BULLISH' | 'NEUTRAL' | 'BEARISH'): string => {
  switch (bias) {
    case 'BULLISH': return 'text-green-600 dark:text-green-400';
    case 'BEARISH': return 'text-red-600 dark:text-red-400';
    default: return 'text-gray-600 dark:text-gray-400';
  }
};

const getBiasIcon = (bias: 'BULLISH' | 'NEUTRAL' | 'BEARISH') => {
  switch (bias) {
    case 'BULLISH': return <TrendingUp className="h-4 w-4" />;
    case 'BEARISH': return <TrendingDown className="h-4 w-4" />;
    default: return <Activity className="h-4 w-4" />;
  }
};

const getRiskLevel = (value: number, thresholds: { low: number; medium: number }): 'low' | 'medium' | 'high' => {
  if (value <= thresholds.low) return 'low';
  if (value <= thresholds.medium) return 'medium';
  return 'high';
};

const getRiskColor = (level: 'low' | 'medium' | 'high'): string => {
  switch (level) {
    case 'low': return 'text-green-600 dark:text-green-400';
    case 'medium': return 'text-yellow-600 dark:text-yellow-400';
    case 'high': return 'text-red-600 dark:text-red-400';
  }
};

export const TradingMetricsPanel = memo<TradingMetricsPanelProps>(({
  accountMetrics,
  riskMetrics,
  marketBias,
  confidence
}) => {
  // Memoize expensive calculations
  const metricsCalculations = useMemo(() => {
    const marginUtilization = (accountMetrics.margin_used / accountMetrics.buying_power) * 100;
    const portfolioAllocation = (accountMetrics.positions_open * 1000) / accountMetrics.account_balance * 100;
    
    return {
      marginUtilization,
      portfolioAllocation,
      riskLevel: getRiskLevel(marginUtilization, { low: 25, medium: 50 }),
      confidenceLevel: confidence * 100
    };
  }, [accountMetrics, confidence]);

  const riskAnalysis = useMemo(() => {
    if (!riskMetrics) return null;

    return {
      deltaRisk: getRiskLevel(Math.abs(riskMetrics.portfolio_delta), { low: 100, medium: 250 }),
      concentrationRisk: getRiskLevel(riskMetrics.concentration_risk, { low: 0.2, medium: 0.4 }),
      marginRisk: getRiskLevel(riskMetrics.margin_utilization, { low: 0.3, medium: 0.6 })
    };
  }, [riskMetrics]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Performance Metrics */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            <CardTitle className="text-lg">Performance Metrics</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Sharpe Ratio */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Sharpe Ratio</span>
              <span className="font-semibold text-gray-900 dark:text-gray-100">
                {formatDecimal(accountMetrics.sharpe_ratio)}
              </span>
            </div>

            {/* Max Drawdown */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Max Drawdown</span>
              <span className="font-semibold text-red-600 dark:text-red-400">
                {formatPercentage(accountMetrics.max_drawdown)}
              </span>
            </div>

            {/* Total Trades */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Total Trades</span>
              <span className="font-semibold text-gray-900 dark:text-gray-100">
                {accountMetrics.total_trades}
              </span>
            </div>

            {/* Win Rate with Progress Bar */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Win Rate</span>
                <span className="font-semibold text-gray-900 dark:text-gray-100">
                  {formatPercentage(accountMetrics.win_rate)}
                </span>
              </div>
              <Progress 
                value={accountMetrics.win_rate * 100} 
                className="h-2"
                max={100}
              />
            </div>

            {/* Market Bias */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Market Bias</span>
              <div className="flex items-center space-x-2">
                <span className={`font-semibold ${getBiasColor(marketBias)}`}>
                  {getBiasIcon(marketBias)}
                </span>
                <Badge variant="outline" className={getBiasColor(marketBias)}>
                  {marketBias}
                </Badge>
              </div>
            </div>

            {/* Confidence Level */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Confidence</span>
                <span className="font-semibold text-gray-900 dark:text-gray-100">
                  {formatPercentage(confidence)}
                </span>
              </div>
              <Progress 
                value={metricsCalculations.confidenceLevel} 
                className="h-2"
                max={100}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Risk Metrics */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center space-x-2">
            <Shield className="h-5 w-5 text-red-600 dark:text-red-400" />
            <CardTitle className="text-lg">Risk Analysis</CardTitle>
            <Badge variant="outline" className={getRiskColor(metricsCalculations.riskLevel)}>
              {metricsCalculations.riskLevel.toUpperCase()}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Margin Utilization */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Margin Used</span>
                <span className="font-semibold text-gray-900 dark:text-gray-100">
                  {formatCurrency(accountMetrics.margin_used)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500 dark:text-gray-500">Utilization</span>
                <span className={`text-xs font-medium ${getRiskColor(metricsCalculations.riskLevel)}`}>
                  {formatPercentage(metricsCalculations.marginUtilization / 100)}
                </span>
              </div>
              <Progress 
                value={metricsCalculations.marginUtilization} 
                className="h-2"
                max={100}
              />
            </div>

            {/* Portfolio Greeks (if available) */}
            {riskMetrics && (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Portfolio Delta</span>
                  <span className={`font-semibold ${getRiskColor(riskAnalysis!.deltaRisk)}`}>
                    {formatDecimal(riskMetrics.portfolio_delta)}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Portfolio Theta</span>
                  <span className="font-semibold text-gray-900 dark:text-gray-100">
                    {formatDecimal(riskMetrics.portfolio_theta)}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">VaR (95%)</span>
                  <span className="font-semibold text-red-600 dark:text-red-400">
                    {formatCurrency(riskMetrics.var_95)}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Risk/Reward</span>
                  <span className="font-semibold text-gray-900 dark:text-gray-100">
                    1:{formatDecimal(riskMetrics.risk_reward_ratio, 1)}
                  </span>
                </div>
              </>
            )}

            {/* Market Volatility */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">VIX Level</span>
                <span className="font-semibold text-gray-900 dark:text-gray-100">
                  {formatDecimal(accountMetrics.vix, 1)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">IV Rank</span>
                <span className="font-semibold text-gray-900 dark:text-gray-100">
                  {formatPercentage(accountMetrics.iv_rank)}
                </span>
              </div>
            </div>

            {/* Options Level */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Options Level</span>
              <Badge variant="outline">
                {accountMetrics.options_level}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
});

TradingMetricsPanel.displayName = 'TradingMetricsPanel';

export default TradingMetricsPanel;