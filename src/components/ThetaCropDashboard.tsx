import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Alert, AlertDescription } from './ui/alert';
import { Loader2, TrendingUp, DollarSign, Target, AlertTriangle } from 'lucide-react';

interface ThetaCropStatus {
  strategy_name: string;
  status: {
    strategy_status: string;
    active_condors: number;
    weekly_stats: {
      condors_opened: number;
      condors_closed: number;
      total_credit: number;
      realized_pnl: number;
      win_rate: number;
    };
    active_positions: Array<{
      trade_id: string;
      symbol: string;
      dte: number;
      credit_collected: number;
      status: string;
    }>;
    next_scan_time: string;
  };
  methodology: {
    entry_timing: string;
    target_dte: string;
    delta_wings: string;
    wing_width: string;
    min_credit: string;
    exit_rules: string[];
  };
}

interface Opportunity {
  symbol: string;
  score: number;
  setup: {
    expiration: string;
    dte: number;
    strikes: {
      put_long: number;
      put_short: number;
      call_short: number;
      call_long: number;
    };
    estimated_credit: number;
    width: number;
    credit_to_width_ratio: number;
    max_profit: number;
    max_loss: number;
    net_delta: number;
    volatility_rank: number;
  };
  meets_criteria: boolean;
}

export const ThetaCropDashboard: React.FC = () => {
  const [status, setStatus] = useState<ThetaCropStatus | null>(null);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/thetacrop/status');
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      } else {
        throw new Error('Failed to fetch status');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const fetchOpportunities = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/thetacrop/opportunities');
      if (response.ok) {
        const data = await response.json();
        setOpportunities(data.opportunities || []);
      }
    } catch (err) {
      console.error('Failed to fetch opportunities:', err);
    }
  };

  const scanForOpportunities = async () => {
    setScanning(true);
    try {
      const response = await fetch('http://localhost:8000/api/thetacrop/scan', {
        method: 'POST',
      });
      if (response.ok) {
        const data = await response.json();
        await fetchStatus();
        await fetchOpportunities();
        setError(null);
      } else {
        throw new Error('Scan failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Scan failed');
    } finally {
      setScanning(false);
    }
  };

  const executeCondor = async (symbol: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/thetacrop/execute/${symbol}`, {
        method: 'POST',
      });
      if (response.ok) {
        await fetchStatus();
        setError(null);
      } else {
        throw new Error(`Failed to execute ${symbol}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Execution failed');
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await fetchStatus();
      await fetchOpportunities();
      setLoading(false);
    };
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading ThetaCrop Strategy...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="m-4">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'SCANNING': return 'bg-blue-500';
      case 'READY': return 'bg-green-500';
      case 'EXECUTED': return 'bg-purple-500';
      case 'MONITORING': return 'bg-yellow-500';
      case 'FAILED': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">ThetaCrop Weekly</h1>
          <p className="text-gray-600">Alpaca Paper Edition - Weekly Iron Condor Strategy</p>
        </div>
        <Button 
          onClick={scanForOpportunities} 
          disabled={scanning}
          className="bg-green-600 hover:bg-green-700"
        >
          {scanning ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
          {scanning ? 'Scanning...' : 'Scan for Trades'}
        </Button>
      </div>

      {/* Status Cards */}
      {status && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Strategy Status</CardTitle>
            </CardHeader>
            <CardContent>
              <Badge className={`${getStatusColor(status.status.strategy_status)} text-white`}>
                {status.status.strategy_status}
              </Badge>
              <p className="text-xs text-gray-500 mt-1">
                {status.status.active_condors} active condors
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center">
                <DollarSign className="h-4 w-4 mr-1" />
                Total Credit
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                ${status.status.weekly_stats.total_credit.toFixed(2)}
              </div>
              <p className="text-xs text-gray-500">
                From {status.status.weekly_stats.condors_opened} condors
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center">
                <TrendingUp className="h-4 w-4 mr-1" />
                Win Rate
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(status.status.weekly_stats.win_rate * 100).toFixed(0)}%
              </div>
              <p className="text-xs text-gray-500">
                {status.status.weekly_stats.condors_closed} closed
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center">
                <Target className="h-4 w-4 mr-1" />
                Realized P&L
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${
                status.status.weekly_stats.realized_pnl >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                ${status.status.weekly_stats.realized_pnl.toFixed(2)}
              </div>
              <p className="text-xs text-gray-500">Net profit/loss</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs defaultValue="opportunities" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="opportunities">Opportunities</TabsTrigger>
          <TabsTrigger value="positions">Active Positions</TabsTrigger>
          <TabsTrigger value="methodology">Strategy Rules</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        {/* Opportunities Tab */}
        <TabsContent value="opportunities" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Current Iron Condor Opportunities</CardTitle>
              <CardDescription>
                Real-time opportunities for SPY, QQQ, and IWM based on ThetaCrop criteria
              </CardDescription>
            </CardHeader>
            <CardContent>
              {opportunities.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  No opportunities found. Try scanning for new setups.
                </p>
              ) : (
                <div className="space-y-4">
                  {opportunities.map((opp, index) => (
                    <div key={index} className="border rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-lg">{opp.symbol}</h3>
                            <Badge variant={opp.meets_criteria ? "default" : "secondary"}>
                              {opp.meets_criteria ? "✓ Meets Criteria" : "Doesn't Meet Criteria"}
                            </Badge>
                            <span className="text-sm text-gray-500">
                              Score: {opp.score.toFixed(1)}
                            </span>
                          </div>
                          
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
                            <div>
                              <p className="text-sm font-medium">Strikes</p>
                              <p className="text-xs text-gray-600">
                                {opp.setup.strikes.put_long}/{opp.setup.strikes.put_short}/
                                {opp.setup.strikes.call_short}/{opp.setup.strikes.call_long}
                              </p>
                            </div>
                            <div>
                              <p className="text-sm font-medium">Credit</p>
                              <p className="text-xs text-gray-600">
                                ${opp.setup.estimated_credit.toFixed(2)} 
                                ({(opp.setup.credit_to_width_ratio * 100).toFixed(0)}%)
                              </p>
                            </div>
                            <div>
                              <p className="text-sm font-medium">Max P&L</p>
                              <p className="text-xs text-green-600">+${opp.setup.max_profit.toFixed(0)}</p>
                              <p className="text-xs text-red-600">-${opp.setup.max_loss.toFixed(0)}</p>
                            </div>
                            <div>
                              <p className="text-sm font-medium">DTE / Width</p>
                              <p className="text-xs text-gray-600">
                                {opp.setup.dte} days / ${opp.setup.width}
                              </p>
                            </div>
                          </div>
                        </div>
                        
                        {opp.meets_criteria && (
                          <Button 
                            onClick={() => executeCondor(opp.symbol)}
                            size="sm"
                            className="ml-4"
                          >
                            Execute
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Active Positions Tab */}
        <TabsContent value="positions">
          <Card>
            <CardHeader>
              <CardTitle>Active Iron Condors</CardTitle>
              <CardDescription>Currently monitored positions with exit criteria</CardDescription>
            </CardHeader>
            <CardContent>
              {status?.status.active_positions.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No active positions</p>
              ) : (
                <div className="space-y-3">
                  {status?.status.active_positions.map((position) => (
                    <div key={position.trade_id} className="flex justify-between items-center p-3 border rounded">
                      <div>
                        <h4 className="font-medium">{position.symbol}</h4>
                        <p className="text-sm text-gray-600">
                          {position.dte} DTE • Credit: ${position.credit_collected.toFixed(2)}
                        </p>
                      </div>
                      <Badge>{position.status}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Methodology Tab */}
        <TabsContent value="methodology">
          <Card>
            <CardHeader>
              <CardTitle>ThetaCrop Weekly Methodology</CardTitle>
              <CardDescription>Complete strategy rules and criteria</CardDescription>
            </CardHeader>
            <CardContent>
              {status && (
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold mb-2">Entry Rules</h4>
                    <ul className="text-sm space-y-1 text-gray-600">
                      <li>• <strong>Timing:</strong> {status.methodology.entry_timing}</li>
                      <li>• <strong>Target DTE:</strong> {status.methodology.target_dte}</li>
                      <li>• <strong>Wings:</strong> {status.methodology.delta_wings}</li>
                      <li>• <strong>Width:</strong> {status.methodology.wing_width}</li>
                      <li>• <strong>Min Credit:</strong> {status.methodology.min_credit}</li>
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold mb-2">Exit Rules</h4>
                    <ul className="text-sm space-y-1 text-gray-600">
                      {status.methodology.exit_rules.map((rule, index) => (
                        <li key={index}>• {rule}</li>
                      ))}
                    </ul>
                  </div>
                  
                  <div className="bg-blue-50 p-4 rounded">
                    <h4 className="font-semibold mb-2">Paper Trading Benefits</h4>
                    <ul className="text-sm space-y-1 text-gray-600">
                      <li>• Zero commissions on Alpaca</li>
                      <li>• Risk-free strategy testing</li>
                      <li>• Build performance track record</li>
                      <li>• Refine parameters before live trading</li>
                    </ul>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance">
          <Card>
            <CardHeader>
              <CardTitle>Strategy Performance</CardTitle>
              <CardDescription>Track record and key metrics</CardDescription>
            </CardHeader>
            <CardContent>
              {status && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-semibold mb-3">Trade Summary</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span>Total Condors Opened:</span>
                        <span className="font-medium">{status.status.weekly_stats.condors_opened}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Condors Closed:</span>
                        <span className="font-medium">{status.status.weekly_stats.condors_closed}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Win Rate:</span>
                        <span className="font-medium text-green-600">
                          {(status.status.weekly_stats.win_rate * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Total Credit:</span>
                        <span className="font-medium">${status.status.weekly_stats.total_credit.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold mb-3">Next Actions</h4>
                    <div className="space-y-2 text-sm">
                      <p>Next scan: <span className="font-medium">Thursday 11:30 ET</span></p>
                      <p>Paper trade 6+ weeks to validate performance</p>
                      <p>Track metrics for live deployment readiness</p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};