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

interface PortfolioRisk {
  portfolio_value: number;
  total_risk: number;
  risk_percentage: number;
  var_95: number;
  var_99: number;
  expected_shortfall: number;
  beta: number;
  correlation_spy: number;
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  risk_by_strategy: {
    [key: string]: {
      risk: number;
      percentage: number;
    };
  };
  risk_by_symbol: {
    [key: string]: {
      risk: number;
      percentage: number;
    };
  };
  last_updated: string;
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
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchPortfolioRisk = async () => {
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

  const getRiskLevel = (riskPercentage: number): 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' => {
    if (riskPercentage <= 3) return 'LOW';
    if (riskPercentage <= 7) return 'MEDIUM';
    if (riskPercentage <= 12) return 'HIGH';
    return 'CRITICAL';
  };

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
      case 'HIGH': return 'text-red-400 border-red-600';
      case 'MEDIUM': return 'text-yellow-400 border-yellow-600';
      case 'LOW': return 'text-green-400 border-green-600';
      default: return 'text-gray-400 border-gray-600';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="w-6 h-6 animate-spin mr-2" />
        Loading risk data...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Last Update */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Risk Management</h2>
          {lastUpdate && (
            <p className="text-sm text-muted-foreground">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </p>
          )}
        </div>
        <Button 
          onClick={fetchPortfolioRisk} 
          size="sm" 
          variant="outline"
          className="flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </Button>
      </div>

      {/* Risk Alerts */}
      {riskAlerts.length > 0 && (
        <div className="space-y-2">
          {riskAlerts.map((alert, index) => (
            <Alert key={index} className={getSeverityColor(alert.severity)}>
              <AlertTriangle className="w-4 h-4" />
              <AlertTitle>{alert.type} Risk Alert</AlertTitle>
              <AlertDescription>
                <div>{alert.message}</div>
                <div className="mt-2 text-sm font-medium">Recommendation: {alert.recommendation}</div>
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
                  <div className={`text-2xl font-bold ${getRiskLevelColor(getRiskLevel(portfolioRisk.risk_percentage))}`}>
                    {getRiskLevel(portfolioRisk.risk_percentage)}
                  </div>
                </div>
                <Badge className={getRiskLevelBadge(getRiskLevel(portfolioRisk.risk_percentage))}>
                  Risk Level
                </Badge>
              </div>

              {/* Portfolio Value */}
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400 mb-2">
                  ${portfolioRisk.portfolio_value.toLocaleString()}
                </div>
                <p className="text-sm text-muted-foreground">Portfolio Value</p>
              </div>

              {/* VaR 95% */}
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-400 mb-2">
                  ${portfolioRisk.var_95.toLocaleString()}
                </div>
                <p className="text-sm text-muted-foreground">
                  95% VaR ({(portfolioRisk.var_95 / portfolioRisk.portfolio_value * 100).toFixed(1)}%)
                </p>
              </div>

              {/* Max Drawdown */}
              <div className="text-center">
                <div className="text-2xl font-bold text-red-400 mb-2">
                  {(portfolioRisk.max_drawdown * 100).toFixed(1)}%
                </div>
                <p className="text-sm text-muted-foreground">Max Drawdown</p>
              </div>
            </div>
            </CardContent>
          </Card>
        )}
      </CollapsibleSection>

      {/* Detailed Risk Analysis Tabs */}
      <CollapsibleSection 
        title="Risk Analysis" 
        icon={<BarChart3 className="w-5 h-5" />}
        defaultOpen={false}
      >
        <Tabs defaultValue="breakdown" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="breakdown" className="flex items-center gap-2">
            <Target className="w-4 h-4" />
            Risk Breakdown
          </TabsTrigger>
          <TabsTrigger value="var" className="flex items-center gap-2">
            <Zap className="w-4 h-4" />
            VaR Analysis
          </TabsTrigger>
          <TabsTrigger value="performance" className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Performance
          </TabsTrigger>
        </TabsList>

        {/* Risk Breakdown Tab */}
        <TabsContent value="breakdown" className="space-y-4">
          {portfolioRisk && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Risk Breakdown by Strategy</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {Object.entries(portfolioRisk.risk_by_strategy).map(([strategy, risk]) => (
                      <div key={strategy} className="bg-muted p-4 rounded-lg text-center">
                        <div className="text-2xl font-bold text-blue-400">
                          ${risk.risk.toLocaleString()}
                        </div>
                        <div className="text-sm text-muted-foreground">{strategy.replace('_', ' ').toUpperCase()}</div>
                        <div className="text-xs text-muted-foreground">{risk.percentage.toFixed(1)}% of total risk</div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Risk Breakdown by Symbol</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {Object.entries(portfolioRisk.risk_by_symbol).map(([symbol, risk]) => (
                      <div key={symbol} className="bg-muted p-4 rounded-lg text-center">
                        <div className="text-2xl font-bold text-purple-400">
                          ${risk.risk.toLocaleString()}
                        </div>
                        <div className="text-sm text-muted-foreground">{symbol}</div>
                        <div className="text-xs text-muted-foreground">{risk.percentage.toFixed(1)}% of total risk</div>
                      </div>
                    ))}
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
                          ${portfolioRisk.var_95.toLocaleString()}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {(portfolioRisk.var_95 / portfolioRisk.portfolio_value * 100).toFixed(1)}% of portfolio
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span>99% VaR (1-day):</span>
                      <div className="text-right">
                        <div className="text-lg font-bold text-red-400">
                          ${portfolioRisk.var_99.toLocaleString()}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {(portfolioRisk.var_99 / portfolioRisk.portfolio_value * 100).toFixed(1)}% of portfolio
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span>Expected Shortfall:</span>
                      <span className="text-lg font-bold text-red-400">
                        ${portfolioRisk.expected_shortfall.toLocaleString()}
                      </span>
                    </div>
                  </div>
                  
                  <div className="mt-4">
                    <div className="flex justify-between mb-2">
                      <span>Risk Utilization</span>
                      <span>{(portfolioRisk.var_95 / portfolioRisk.portfolio_value * 100 / 5 * 100).toFixed(1)}%</span>
                    </div>
                    <Progress 
                      value={Math.min(100, portfolioRisk.var_95 / portfolioRisk.portfolio_value * 100 / 5 * 100)} 
                      className="h-2" 
                    />
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-4">
          {portfolioRisk && (
            <Card>
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="text-center bg-muted p-4 rounded-lg">
                    <div className="text-2xl font-bold text-green-400">
                      {portfolioRisk.sharpe_ratio}
                    </div>
                    <div className="text-sm text-muted-foreground">Sharpe Ratio</div>
                  </div>
                  
                  <div className="text-center bg-muted p-4 rounded-lg">
                    <div className="text-2xl font-bold text-blue-400">
                      {portfolioRisk.volatility}
                    </div>
                    <div className="text-sm text-muted-foreground">Volatility</div>
                  </div>
                  
                  <div className="text-center bg-muted p-4 rounded-lg">
                    <div className="text-2xl font-bold text-purple-400">
                      {portfolioRisk.beta}
                    </div>
                    <div className="text-sm text-muted-foreground">Beta</div>
                  </div>
                  
                  <div className="text-center bg-muted p-4 rounded-lg">
                    <div className="text-2xl font-bold text-yellow-400">
                      {portfolioRisk.correlation_spy}
                    </div>
                    <div className="text-sm text-muted-foreground">SPY Correlation</div>
                  </div>
                </div>
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