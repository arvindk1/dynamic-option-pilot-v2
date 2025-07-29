import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { CollapsibleSection } from "@/components/CollapsibleSection";
import { 
  RefreshCw, Shield, AlertTriangle, TrendingUp, TrendingDown, 
  Target, BarChart3, Activity, Zap, Timer, DollarSign 
} from "lucide-react";

interface Greeks {
  total_delta: number;
  total_gamma: number;
  total_theta: number;
  total_vega: number;
  total_rho: number;
}

interface PositionRisk {
  symbol: string;
  quantity: number;
  market_value: number;
  greeks: Greeks;
  implied_volatility: number;
  days_to_expiration: number;
  moneyness: number;
  risk_contribution: number;
  risk_contribution_percent: number;
}

interface PortfolioRisk {
  portfolio_summary: {
    total_value: number;
    risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    timestamp: string;
  };
  greeks: Greeks;
  var_metrics: {
    var_95: number;
    var_99: number;
    expected_shortfall: number;
    var_95_percent: number;
    var_99_percent: number;
  };
  performance_metrics: {
    max_drawdown: number;
    sharpe_ratio: number;
    sortino_ratio: number;
    beta: number;
    correlation_spy: number;
  };
  position_breakdown: PositionRisk[];
}

interface StressTestResult {
  scenario_type: string;
  scenario_name: string;
  portfolio_pnl: number;
  portfolio_pnl_percent: number;
  max_loss_position: string;
  max_loss_amount: number;
  var_breach: boolean;
  margin_call_risk: boolean;
  recovery_time_estimate_days: number;
  risk_assessment: {
    severity: string;
    action_required: boolean;
  };
}

interface RiskAlert {
  type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  message: string;
  recommendation: string;
}

const EnhancedRiskTab: React.FC = React.memo(() => {
  const [portfolioRisk, setPortfolioRisk] = useState<PortfolioRisk | null>(null);
  const [stressTests, setStressTests] = useState<StressTestResult[]>([]);
  const [riskAlerts, setRiskAlerts] = useState<RiskAlert[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchPortfolioRisk = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/risk/portfolio-risk');
      if (response.ok) {
        const data = await response.json();
        setPortfolioRisk(data);
        setLastUpdate(new Date());
      }
    } catch (error) {
      console.error('Error fetching portfolio risk:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStressTests = async () => {
    try {
      const response = await fetch('/api/risk/stress-tests');
      if (response.ok) {
        const data = await response.json();
        setStressTests(data.stress_test_results || []);
      }
    } catch (error) {
      console.error('Error fetching stress tests:', error);
    }
  };

  const fetchRiskAlerts = async () => {
    try {
      const response = await fetch('/api/risk/risk-alerts');
      if (response.ok) {
        const data = await response.json();
        setRiskAlerts(data.alerts || []);
      }
    } catch (error) {
      console.error('Error fetching risk alerts:', error);
    }
  };

  useEffect(() => {
    fetchPortfolioRisk();
    fetchStressTests();
    fetchRiskAlerts();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchPortfolioRisk();
      fetchRiskAlerts();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'LOW': return 'text-green-400';
      case 'MEDIUM': return 'text-yellow-400';
      case 'HIGH': return 'text-orange-400';
      case 'CRITICAL': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getRiskLevelBadge = (level: string) => {
    const colors = {
      'LOW': 'bg-green-600',
      'MEDIUM': 'bg-yellow-600',
      'HIGH': 'bg-orange-600',
      'CRITICAL': 'bg-red-600'
    };
    return colors[level as keyof typeof colors] || 'bg-gray-600';
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'LOW': return 'border-green-500';
      case 'MEDIUM': return 'border-yellow-500';
      case 'HIGH': return 'border-orange-500';
      case 'CRITICAL': return 'border-red-500';
      default: return 'border-gray-500';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with refresh */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Shield className="w-6 h-6" />
            Advanced Risk Management
          </h2>
          <p className="text-muted-foreground">
            {lastUpdate ? `Last updated: ${lastUpdate.toLocaleTimeString()}` : 'Loading...'}
          </p>
        </div>
        <Button 
          onClick={() => {
            fetchPortfolioRisk();
            fetchStressTests();
            fetchRiskAlerts();
          }}
          disabled={loading}
          variant="outline"
          size="sm"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Risk Alerts */}
      {riskAlerts.length > 0 && (
        <div className="space-y-2">
          {riskAlerts.map((alert, index) => (
            <Alert key={index} className={getSeverityColor(alert.severity)}>
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle className="flex items-center gap-2">
                {alert.type.replace('_', ' ')}
                <Badge className={getRiskLevelBadge(alert.severity)}>
                  {alert.severity}
                </Badge>
              </AlertTitle>
              <AlertDescription>
                <div>{alert.message}</div>
                <div className="mt-1 text-sm text-muted-foreground">
                  <strong>Recommendation:</strong> {alert.recommendation}
                </div>
              </AlertDescription>
            </Alert>
          ))}
        </div>
      )}

      {/* Main Portfolio Risk Overview */}
      <CollapsibleSection 
        title="Portfolio Overview" 
        icon={<Activity className="w-5 h-5" />}
        defaultOpen={true}
      >
        {portfolioRisk && (
          <Card className="bg-gradient-to-br from-card to-card/50 border-border">
            <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {/* Risk Level */}
              <div className="text-center">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <Shield className="w-6 h-6" />
                  <div className={`text-2xl font-bold ${getRiskLevelColor(portfolioRisk.portfolio_summary.risk_level)}`}>
                    {portfolioRisk.portfolio_summary.risk_level}
                  </div>
                </div>
                <Badge className={getRiskLevelBadge(portfolioRisk.portfolio_summary.risk_level)}>
                  Risk Level
                </Badge>
              </div>

              {/* Portfolio Value */}
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400 mb-2">
                  ${portfolioRisk.portfolio_summary.total_value.toLocaleString()}
                </div>
                <p className="text-sm text-muted-foreground">Portfolio Value</p>
              </div>

              {/* VaR 95% */}
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-400 mb-2">
                  ${portfolioRisk.var_metrics.var_95.toLocaleString()}
                </div>
                <p className="text-sm text-muted-foreground">
                  95% VaR ({portfolioRisk.var_metrics.var_95_percent}%)
                </p>
              </div>

              {/* Max Drawdown */}
              <div className="text-center">
                <div className="text-2xl font-bold text-red-400 mb-2">
                  {portfolioRisk.performance_metrics.max_drawdown}%
                </div>
                <p className="text-sm text-muted-foreground">Max Drawdown</p>
              </div>
            </div>
            </CardContent>
          </Card>
        )}
      </CollapsibleSection>

      {/* Detailed Risk Analysis */}
      <CollapsibleSection 
        title="Detailed Analysis" 
        icon={<BarChart3 className="w-5 h-5" />}
        defaultOpen={false}
      >
        <Tabs defaultValue="greeks" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="greeks" className="flex items-center gap-2">
            <Target className="w-4 h-4" />
            Greeks
          </TabsTrigger>
          <TabsTrigger value="var" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            VaR Analysis
          </TabsTrigger>
          <TabsTrigger value="stress" className="flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Stress Tests
          </TabsTrigger>
          <TabsTrigger value="positions" className="flex items-center gap-2">
            <DollarSign className="w-4 h-4" />
            Position Risk
          </TabsTrigger>
        </TabsList>

        {/* Greeks Tab */}
        <TabsContent value="greeks" className="space-y-4">
          {portfolioRisk && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Portfolio Greeks Exposure</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                    <div className="bg-muted p-4 rounded-lg text-center">
                      <div className="text-2xl font-bold text-blue-400">
                        {portfolioRisk.greeks?.total_delta?.toFixed(0) || '0'}
                      </div>
                      <div className="text-sm text-muted-foreground">Delta</div>
                      <div className="text-xs text-muted-foreground">Directional Risk</div>
                    </div>
                    
                    <div className="bg-muted p-4 rounded-lg text-center">
                      <div className="text-2xl font-bold text-green-400">
                        {portfolioRisk.greeks?.total_gamma?.toFixed(3) || '0.000'}
                      </div>
                      <div className="text-sm text-muted-foreground">Gamma</div>
                      <div className="text-xs text-muted-foreground">Acceleration Risk</div>
                    </div>
                    
                    <div className="bg-muted p-4 rounded-lg text-center">
                      <div className="text-2xl font-bold text-red-400">
                        {portfolioRisk.greeks?.total_theta?.toFixed(0) || '0'}
                      </div>
                      <div className="text-sm text-muted-foreground">Theta</div>
                      <div className="text-xs text-muted-foreground">Time Decay (Daily)</div>
                    </div>
                    
                    <div className="bg-muted p-4 rounded-lg text-center">
                      <div className="text-2xl font-bold text-purple-400">
                        {portfolioRisk.greeks?.total_vega?.toFixed(0) || '0'}
                      </div>
                      <div className="text-sm text-muted-foreground">Vega</div>
                      <div className="text-xs text-muted-foreground">Volatility Risk</div>
                    </div>
                    
                    <div className="bg-muted p-4 rounded-lg text-center">
                      <div className="text-2xl font-bold text-yellow-400">
                        {portfolioRisk.greeks?.total_rho?.toFixed(0) || '0'}
                      </div>
                      <div className="text-sm text-muted-foreground">Rho</div>
                      <div className="text-xs text-muted-foreground">Interest Rate Risk</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Greeks Scenario Analysis */}
              <Card>
                <CardHeader>
                  <CardTitle>Greeks Scenario Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-3">
                      <h4 className="font-semibold">Market Move Scenarios</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between p-2 bg-muted rounded">
                          <span>+1% Market Move:</span>
                          <span className="text-green-400">
                            +${((portfolioRisk.greeks?.total_delta || 0) * 1).toFixed(0)}
                          </span>
                        </div>
                        <div className="flex justify-between p-2 bg-muted rounded">
                          <span>-1% Market Move:</span>
                          <span className="text-red-400">
                            ${((portfolioRisk.greeks?.total_delta || 0) * -1).toFixed(0)}
                          </span>
                        </div>
                        <div className="flex justify-between p-2 bg-muted rounded">
                          <span>One Day Time Decay:</span>
                          <span className="text-red-400">
                            ${portfolioRisk.greeks?.total_theta?.toFixed(0) || '0'}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      <h4 className="font-semibold">Volatility Scenarios</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between p-2 bg-muted rounded">
                          <span>+5% Vol Increase:</span>
                          <span className="text-blue-400">
                            +${((portfolioRisk.greeks?.total_vega || 0) * 5).toFixed(0)}
                          </span>
                        </div>
                        <div className="flex justify-between p-2 bg-muted rounded">
                          <span>-5% Vol Decrease:</span>
                          <span className="text-orange-400">
                            ${((portfolioRisk.greeks?.total_vega || 0) * -5).toFixed(0)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* VaR Analysis Tab */}
        <TabsContent value="var" className="space-y-4">
          {portfolioRisk && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Value at Risk (VaR)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span>95% VaR (1-day):</span>
                      <div className="text-right">
                        <div className="text-lg font-bold text-orange-400">
                          ${portfolioRisk.var_metrics.var_95.toLocaleString()}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {portfolioRisk.var_metrics.var_95_percent}% of portfolio
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span>99% VaR (1-day):</span>
                      <div className="text-right">
                        <div className="text-lg font-bold text-red-400">
                          ${portfolioRisk.var_metrics.var_99.toLocaleString()}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {portfolioRisk.var_metrics.var_99_percent}% of portfolio
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span>Expected Shortfall:</span>
                      <div className="text-lg font-bold text-red-500">
                        ${portfolioRisk.var_metrics.expected_shortfall.toLocaleString()}
                      </div>
                    </div>

                    <div className="pt-4 border-t">
                      <div className="text-sm text-muted-foreground">
                        VaR Utilization (5% limit)
                      </div>
                      <Progress 
                        value={Math.min(100, portfolioRisk.var_metrics.var_95_percent / 5 * 100)} 
                        className="mt-2"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Performance Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between">
                      <span>Sharpe Ratio:</span>
                      <span className="font-bold text-green-400">
                        {portfolioRisk.performance_metrics.sharpe_ratio}
                      </span>
                    </div>
                    
                    <div className="flex justify-between">
                      <span>Sortino Ratio:</span>
                      <span className="font-bold text-blue-400">
                        {portfolioRisk.performance_metrics.sortino_ratio}
                      </span>
                    </div>
                    
                    <div className="flex justify-between">
                      <span>Beta (to SPY):</span>
                      <span className="font-bold">
                        {portfolioRisk.performance_metrics.beta}
                      </span>
                    </div>
                    
                    <div className="flex justify-between">
                      <span>Correlation (SPY):</span>
                      <span className="font-bold">
                        {portfolioRisk.performance_metrics.correlation_spy}
                      </span>
                    </div>
                    
                    <div className="flex justify-between">
                      <span>Max Drawdown:</span>
                      <span className="font-bold text-red-400">
                        {portfolioRisk.performance_metrics.max_drawdown}%
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Stress Tests Tab */}
        <TabsContent value="stress" className="space-y-4">
          {stressTests.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {stressTests.map((test, index) => (
                <Card key={index} className={`border-l-4 ${getSeverityColor(test.risk_assessment.severity)}`}>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span className="text-lg">{test.scenario_name}</span>
                      <Badge className={getRiskLevelBadge(test.risk_assessment.severity)}>
                        {test.risk_assessment.severity}
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span>Portfolio P&L:</span>
                        <span className={`font-bold ${test.portfolio_pnl < 0 ? 'text-red-400' : 'text-green-400'}`}>
                          {test.portfolio_pnl < 0 ? '-' : '+'}${Math.abs(test.portfolio_pnl).toLocaleString()}
                        </span>
                      </div>
                      
                      <div className="flex justify-between">
                        <span>Percentage Impact:</span>
                        <span className={`font-bold ${(test.portfolio_pnl_percent || 0) < 0 ? 'text-red-400' : 'text-green-400'}`}>
                          {(test.portfolio_pnl_percent || 0).toFixed(1)}%
                        </span>
                      </div>
                      
                      {test.max_loss_position && (
                        <div className="flex justify-between">
                          <span>Worst Position:</span>
                          <span className="font-bold text-red-400">
                            {test.max_loss_position}
                          </span>
                        </div>
                      )}
                      
                      <div className="flex gap-2 pt-2">
                        {test.var_breach && (
                          <Badge variant="destructive" className="text-xs">VaR Breach</Badge>
                        )}
                        {test.margin_call_risk && (
                          <Badge variant="destructive" className="text-xs">Margin Risk</Badge>
                        )}
                      </div>
                      
                      {test.recovery_time_estimate_days > 0 && (
                        <div className="text-sm text-muted-foreground">
                          Estimated recovery: {test.recovery_time_estimate_days} days
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="text-center py-8">
                <p className="text-muted-foreground">No stress test results available</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Position Risk Tab */}
        <TabsContent value="positions" className="space-y-4">
          {portfolioRisk?.position_breakdown && portfolioRisk.position_breakdown.length > 0 ? (
            <div className="grid grid-cols-1 gap-4">
              {portfolioRisk.position_breakdown.map((position, index) => (
                <Card key={index} className="hover:bg-card/80 transition-colors">
                  <CardContent className="pt-6">
                    <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
                      <div>
                        <div className="font-bold text-lg">{position.symbol}</div>
                        <div className="text-sm text-muted-foreground">
                          Qty: {position.quantity}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Value: ${position.market_value.toLocaleString()}
                        </div>
                      </div>
                      
                      <div className="text-center">
                        <div className="text-lg font-bold text-blue-400">
                          {position.greeks?.delta?.toFixed(1) || '0.0'}
                        </div>
                        <div className="text-xs text-muted-foreground">Delta</div>
                      </div>
                      
                      <div className="text-center">
                        <div className="text-lg font-bold text-red-400">
                          {position.greeks?.theta?.toFixed(1) || '0.0'}
                        </div>
                        <div className="text-xs text-muted-foreground">Theta</div>
                      </div>
                      
                      <div className="text-center">
                        <div className="text-lg font-bold text-purple-400">
                          {position.greeks?.vega?.toFixed(1) || '0.0'}
                        </div>
                        <div className="text-xs text-muted-foreground">Vega</div>
                      </div>
                      
                      <div className="text-center">
                        <div className="text-lg font-bold">
                          {(position.implied_volatility || 0).toFixed(1)}%
                        </div>
                        <div className="text-xs text-muted-foreground">IV</div>
                      </div>
                      
                      <div className="text-center">
                        <div className="text-lg font-bold">
                          {(position.risk_contribution_percent || 0).toFixed(1)}%
                        </div>
                        <div className="text-xs text-muted-foreground">Risk Share</div>
                        {(position.days_to_expiration || 0) > 0 && (
                          <div className="text-xs text-muted-foreground flex items-center gap-1">
                            <Timer className="w-3 h-3" />
                            {position.days_to_expiration || 0}d
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="text-center py-8">
                <p className="text-muted-foreground">No position risk data available</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
        </Tabs>
      </CollapsibleSection>
    </div>
  );
});

export default EnhancedRiskTab;