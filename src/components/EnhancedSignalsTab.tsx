import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RefreshCw, TrendingUp, TrendingDown, Minus, Eye, BarChart3, Activity } from "lucide-react";

interface Signal {
  name: string;
  value: number;
  bias: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  confidence: number;
  weight: number;
  source: string;
  description: string;
  timestamp: string;
}

interface CompositeSignal {
  symbol: string;
  bias: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  score: number;
  timestamp: string;
  accuracy: {
    '7_day': number | null;
    '30_day': number | null;
  };
  contributing_signals: Signal[];
  summary: {
    total_signals: number;
    bullish_signals: number;
    bearish_signals: number;
    neutral_signals: number;
  };
}

interface SignalPerformance {
  accuracy_metrics: {
    '7_day_accuracy': number | null;
    '30_day_accuracy': number | null;
    total_predictions: number;
  };
  signal_weights: Record<string, number>;
  tracking_period_days: number;
  last_updated: string;
}

const EnhancedSignalsTab: React.FC = React.memo(() => {
  const [compositeSignal, setCompositeSignal] = useState<CompositeSignal | null>(null);
  const [signalPerformance, setSignalPerformance] = useState<SignalPerformance | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchCompositeSignal = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/signals/composite-bias?symbol=SPY');
      if (response.ok) {
        const data = await response.json();
        setCompositeSignal(data);
        setLastUpdate(new Date());
      }
    } catch (error) {
      console.error('Error fetching composite signal:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSignalPerformance = async () => {
    try {
      const response = await fetch('/api/signals/signal-performance');
      if (response.ok) {
        const data = await response.json();
        setSignalPerformance(data);
      }
    } catch (error) {
      console.error('Error fetching signal performance:', error);
    }
  };

  useEffect(() => {
    fetchCompositeSignal();
    fetchSignalPerformance();
    
    // Auto-refresh every 60 seconds
    const interval = setInterval(() => {
      fetchCompositeSignal();
    }, 60000);

    return () => clearInterval(interval);
  }, []);

  const getBiasColor = (bias: string) => {
    switch (bias) {
      case 'BULLISH': return 'text-green-400';
      case 'BEARISH': return 'text-red-400';
      default: return 'text-yellow-400';
    }
  };

  const getBiasIcon = (bias: string) => {
    switch (bias) {
      case 'BULLISH': return <TrendingUp className="w-6 h-6" />;
      case 'BEARISH': return <TrendingDown className="w-6 h-6" />;
      default: return <Minus className="w-6 h-6" />;
    }
  };

  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case 'HIGH': return 'bg-green-600';
      case 'MEDIUM': return 'bg-yellow-600';
      default: return 'bg-gray-600';
    }
  };

  const getSignalSourceBadgeColor = (source: string) => {
    const colors: Record<string, string> = {
      'technical': 'bg-blue-600',
      'market_structure': 'bg-purple-600',
      'volatility': 'bg-orange-600',
      'economic': 'bg-indigo-600',
      'sentiment': 'bg-pink-600'
    };
    return colors[source] || 'bg-gray-600';
  };

  return (
    <div className="space-y-6">
      {/* Header with refresh */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Enhanced Signal Analysis</h2>
          <p className="text-muted-foreground">
            {lastUpdate ? `Last updated: ${lastUpdate.toLocaleTimeString()}` : 'Loading...'}
          </p>
        </div>
        <Button 
          onClick={fetchCompositeSignal} 
          disabled={loading}
          variant="outline"
          size="sm"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Main Composite Signal Card */}
      {compositeSignal && (
        <Card className="bg-gradient-to-br from-card to-card/50 border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Composite Market Bias - {compositeSignal.symbol}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Bias Display */}
              <div className="text-center">
                <div className="flex items-center justify-center gap-2 mb-2">
                  {getBiasIcon(compositeSignal.bias)}
                  <div className={`text-4xl font-bold ${getBiasColor(compositeSignal.bias)}`}>
                    {compositeSignal.bias}
                  </div>
                </div>
                <Badge className={getConfidenceColor(compositeSignal.confidence)}>
                  {compositeSignal.confidence} Confidence
                </Badge>
              </div>

              {/* Score and Metrics */}
              <div className="text-center">
                <div className="text-2xl font-bold text-muted-foreground mb-2">
                  Score: {compositeSignal.score > 0 ? '+' : ''}{compositeSignal.score}
                </div>
                <Progress 
                  value={Math.abs(compositeSignal.score) * 100} 
                  className="w-full"
                />
                <p className="text-sm text-muted-foreground mt-2">
                  Signal Strength
                </p>
              </div>

              {/* Accuracy Metrics */}
              <div className="text-center">
                <div className="text-lg font-semibold text-muted-foreground mb-2">
                  Historical Accuracy
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between">
                    <span className="text-sm">7-day:</span>
                    <span className="text-sm font-bold">
                      {compositeSignal.accuracy['7_day'] !== null 
                        ? `${(compositeSignal.accuracy['7_day'] * 100).toFixed(1)}%`
                        : 'N/A'
                      }
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">30-day:</span>
                    <span className="text-sm font-bold">
                      {compositeSignal.accuracy['30_day'] !== null 
                        ? `${(compositeSignal.accuracy['30_day'] * 100).toFixed(1)}%`
                        : 'N/A'
                      }
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Signal Summary */}
            <div className="mt-6 pt-6 border-t border-border">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                <div className="bg-muted p-3 rounded-lg">
                  <div className="text-lg font-bold">{compositeSignal.summary.total_signals}</div>
                  <div className="text-sm text-muted-foreground">Total Signals</div>
                </div>
                <div className="bg-muted p-3 rounded-lg">
                  <div className="text-lg font-bold text-green-400">{compositeSignal.summary.bullish_signals}</div>
                  <div className="text-sm text-muted-foreground">Bullish</div>
                </div>
                <div className="bg-muted p-3 rounded-lg">
                  <div className="text-lg font-bold text-red-400">{compositeSignal.summary.bearish_signals}</div>
                  <div className="text-sm text-muted-foreground">Bearish</div>
                </div>
                <div className="bg-muted p-3 rounded-lg">
                  <div className="text-lg font-bold text-yellow-400">{compositeSignal.summary.neutral_signals}</div>
                  <div className="text-sm text-muted-foreground">Neutral</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Detailed Signal Analysis */}
      <Tabs defaultValue="individual" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="individual" className="flex items-center gap-2">
            <Eye className="w-4 h-4" />
            Individual Signals
          </TabsTrigger>
          <TabsTrigger value="performance" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Performance
          </TabsTrigger>
        </TabsList>

        {/* Individual Signals Tab */}
        <TabsContent value="individual" className="space-y-4">
          {compositeSignal?.contributing_signals && compositeSignal.contributing_signals.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {compositeSignal.contributing_signals.map((signal, index) => (
                <Card key={index} className="bg-card border-border hover:bg-card/80 transition-colors">
                  <CardHeader className="pb-3">
                    <div className="flex justify-between items-start">
                      <CardTitle className="text-base">{signal.name}</CardTitle>
                      <Badge className={getSignalSourceBadgeColor(signal.source)}>
                        {signal.source}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Value:</span>
                        <span className="font-bold">{signal.value.toFixed(2)}</span>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Bias:</span>
                        <div className="flex items-center gap-1">
                          {getBiasIcon(signal.bias)}
                          <span className={`font-bold text-sm ${getBiasColor(signal.bias)}`}>
                            {signal.bias}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Confidence:</span>
                        <span className="font-bold">{(signal.confidence * 100).toFixed(0)}%</span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Weight:</span>
                        <span className="font-bold">{(signal.weight * 100).toFixed(0)}%</span>
                      </div>

                      <div className="pt-2 border-t border-border">
                        <p className="text-xs text-muted-foreground">{signal.description}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="bg-card border-border">
              <CardContent className="text-center py-8">
                <p className="text-muted-foreground">No individual signals available</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-4">
          {signalPerformance && (
            <>
              {/* Accuracy Metrics */}
              <Card className="bg-card border-border">
                <CardHeader>
                  <CardTitle>Prediction Accuracy</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-green-400 mb-2">
                        {signalPerformance.accuracy_metrics['7_day_accuracy'] !== null 
                          ? `${(signalPerformance.accuracy_metrics['7_day_accuracy'] * 100).toFixed(1)}%`
                          : 'N/A'
                        }
                      </div>
                      <p className="text-sm text-muted-foreground">7-Day Accuracy</p>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-blue-400 mb-2">
                        {signalPerformance.accuracy_metrics['30_day_accuracy'] !== null 
                          ? `${(signalPerformance.accuracy_metrics['30_day_accuracy'] * 100).toFixed(1)}%`
                          : 'N/A'
                        }
                      </div>
                      <p className="text-sm text-muted-foreground">30-Day Accuracy</p>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-purple-400 mb-2">
                        {signalPerformance.accuracy_metrics.total_predictions}
                      </div>
                      <p className="text-sm text-muted-foreground">Total Predictions</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Signal Weights */}
              <Card className="bg-card border-border">
                <CardHeader>
                  <CardTitle>Signal Weights Configuration</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {Object.entries(signalPerformance.signal_weights).map(([signal, weight]) => (
                      <div key={signal} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                        <span className="font-medium capitalize">{signal.replace('_', ' ')}</span>
                        <div className="flex items-center gap-2">
                          <Progress value={weight * 100} className="w-24" />
                          <span className="text-sm font-bold">{(weight * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
});

export default EnhancedSignalsTab;