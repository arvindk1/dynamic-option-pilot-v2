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

// Backend API response interface (what we actually receive)
interface BackendSignalResponse {
  symbol: string;
  composite_bias: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  bias_strength: number;
  confidence: number;
  individual_signals: Record<string, {
    bias: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
    strength: number;
    value: number;
  }>;
  last_updated: string;
  scan_time?: string;
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

// Data transformation functions
const transformConfidenceToString = (confidence: number): 'HIGH' | 'MEDIUM' | 'LOW' => {
  if (confidence >= 0.8) return 'HIGH';
  if (confidence >= 0.6) return 'MEDIUM';
  return 'LOW';
};

const getSignalSourceFromName = (name: string): string => {
  const sourceMap: Record<string, string> = {
    'rsi': 'technical',
    'macd': 'technical',
    'volume': 'market_structure',
    'momentum': 'technical',
    'volatility': 'volatility',
    'sentiment': 'sentiment',
    'economic': 'economic'
  };
  return sourceMap[name.toLowerCase()] || 'technical';
};

const getSignalDescription = (name: string, value: number, bias: string): string => {
  const descriptions: Record<string, (value: number, bias: string) => string> = {
    'rsi': (v, b) => `RSI at ${v.toFixed(1)} indicates ${b.toLowerCase()} momentum`,
    'macd': (v, b) => `MACD signal ${v > 0 ? 'above' : 'below'} zero, showing ${b.toLowerCase()} trend`,
    'volume': (v, b) => `Volume analysis suggests ${b.toLowerCase()} pressure`,
    'momentum': (v, b) => `Price momentum indicator showing ${b.toLowerCase()} direction`
  };
  
  const descFn = descriptions[name.toLowerCase()];
  return descFn ? descFn(value, bias) : `${name} indicator showing ${bias.toLowerCase()} signal`;
};

const transformBackendResponse = (backendData: BackendSignalResponse): CompositeSignal => {
  // Safely extract properties with defaults
  const symbol = backendData?.symbol || 'UNKNOWN';
  const bias = backendData?.composite_bias || 'NEUTRAL';
  const biasStrength = backendData?.bias_strength || 0;
  const confidenceNum = backendData?.confidence || 0;
  const individualSignals = backendData?.individual_signals || {};
  const timestamp = backendData?.last_updated || backendData?.scan_time || new Date().toISOString();

  // Transform individual signals to contributing_signals array
  const contributing_signals: Signal[] = Object.entries(individualSignals).map(([name, signal]) => ({
    name: name.toUpperCase(),
    value: signal?.value || 0,
    bias: signal?.bias || 'NEUTRAL',
    confidence: signal?.strength || 0,
    weight: signal?.strength || 0, // Use strength as weight since we don't have separate weight
    source: getSignalSourceFromName(name),
    description: getSignalDescription(name, signal?.value || 0, signal?.bias || 'NEUTRAL'),
    timestamp: timestamp
  }));

  // Calculate summary statistics
  const total_signals = contributing_signals.length;
  const bullish_signals = contributing_signals.filter(s => s.bias === 'BULLISH').length;
  const bearish_signals = contributing_signals.filter(s => s.bias === 'BEARISH').length;
  const neutral_signals = contributing_signals.filter(s => s.bias === 'NEUTRAL').length;

  return {
    symbol,
    bias,
    confidence: transformConfidenceToString(confidenceNum),
    score: biasStrength,
    timestamp,
    accuracy: {
      '7_day': null, // Backend doesn't provide this yet
      '30_day': null // Backend doesn't provide this yet
    },
    contributing_signals,
    summary: {
      total_signals,
      bullish_signals,
      bearish_signals,
      neutral_signals
    }
  };
};

// Safe property access helper
function safeAccess<T>(obj: any, path: string[], defaultValue: T): T {
  try {
    let current = obj;
    for (const key of path) {
      if (current === null || current === undefined) return defaultValue;
      current = current[key];
    }
    return current !== null && current !== undefined ? current : defaultValue;
  } catch {
    return defaultValue;
  }
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
        const backendData: BackendSignalResponse = await response.json();
        // Transform backend response to frontend interface
        const transformedData = transformBackendResponse(backendData);
        setCompositeSignal(transformedData);
        setLastUpdate(new Date());
      } else {
        console.error('Failed to fetch composite signal:', response.status, response.statusText);
        // Set empty state instead of crashing
        setCompositeSignal(null);
      }
    } catch (error) {
      console.error('Error fetching composite signal:', error);
      // Set empty state instead of crashing
      setCompositeSignal(null);
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

      {/* Loading State */}
      {loading && !compositeSignal && (
        <Card className="bg-gradient-to-br from-card to-card/50 border-border">
          <CardContent className="text-center py-8">
            <div className="flex items-center justify-center gap-2">
              <RefreshCw className="w-6 h-6 animate-spin" />
              <p className="text-muted-foreground">Loading signal data...</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error State */}
      {!loading && !compositeSignal && (
        <Card className="bg-gradient-to-br from-card to-card/50 border-border border-red-500/20">
          <CardContent className="text-center py-8">
            <p className="text-muted-foreground">Failed to load signal data</p>
            <Button 
              onClick={fetchCompositeSignal} 
              className="mt-4"
              variant="outline"
              size="sm"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry
            </Button>
          </CardContent>
        </Card>
      )}

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
                  {getBiasIcon(safeAccess(compositeSignal, ['bias'], 'NEUTRAL'))}
                  <div className={`text-4xl font-bold ${getBiasColor(safeAccess(compositeSignal, ['bias'], 'NEUTRAL'))}`}>
                    {safeAccess(compositeSignal, ['bias'], 'NEUTRAL')}
                  </div>
                </div>
                <Badge className={getConfidenceColor(safeAccess(compositeSignal, ['confidence'], 'LOW'))}>
                  {safeAccess(compositeSignal, ['confidence'], 'LOW')} Confidence
                </Badge>
              </div>

              {/* Score and Metrics */}
              <div className="text-center">
                <div className="text-2xl font-bold text-muted-foreground mb-2">
                  Score: {safeAccess(compositeSignal, ['score'], 0) > 0 ? '+' : ''}{safeAccess(compositeSignal, ['score'], 0).toFixed(2)}
                </div>
                <Progress 
                  value={Math.min(Math.abs(safeAccess(compositeSignal, ['score'], 0)) * 100, 100)} 
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
                      {(() => {
                        const accuracy = safeAccess(compositeSignal, ['accuracy', '7_day'], null);
                        return accuracy !== null ? `${(accuracy * 100).toFixed(1)}%` : 'N/A';
                      })()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">30-day:</span>
                    <span className="text-sm font-bold">
                      {(() => {
                        const accuracy = safeAccess(compositeSignal, ['accuracy', '30_day'], null);
                        return accuracy !== null ? `${(accuracy * 100).toFixed(1)}%` : 'N/A';
                      })()}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Signal Summary */}
            <div className="mt-6 pt-6 border-t border-border">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                <div className="bg-muted p-3 rounded-lg">
                  <div className="text-lg font-bold">{safeAccess(compositeSignal, ['summary', 'total_signals'], 0)}</div>
                  <div className="text-sm text-muted-foreground">Total Signals</div>
                </div>
                <div className="bg-muted p-3 rounded-lg">
                  <div className="text-lg font-bold text-green-400">{safeAccess(compositeSignal, ['summary', 'bullish_signals'], 0)}</div>
                  <div className="text-sm text-muted-foreground">Bullish</div>
                </div>
                <div className="bg-muted p-3 rounded-lg">
                  <div className="text-lg font-bold text-red-400">{safeAccess(compositeSignal, ['summary', 'bearish_signals'], 0)}</div>
                  <div className="text-sm text-muted-foreground">Bearish</div>
                </div>
                <div className="bg-muted p-3 rounded-lg">
                  <div className="text-lg font-bold text-yellow-400">{safeAccess(compositeSignal, ['summary', 'neutral_signals'], 0)}</div>
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
          {(() => {
            const signals = safeAccess(compositeSignal, ['contributing_signals'], []);
            return signals && signals.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {signals.map((signal: Signal, index: number) => (
                  <Card key={index} className="bg-card border-border hover:bg-card/80 transition-colors">
                    <CardHeader className="pb-3">
                      <div className="flex justify-between items-start">
                        <CardTitle className="text-base">{safeAccess(signal, ['name'], 'Unknown Signal')}</CardTitle>
                        <Badge className={getSignalSourceBadgeColor(safeAccess(signal, ['source'], 'technical'))}>
                          {safeAccess(signal, ['source'], 'technical')}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">Value:</span>
                          <span className="font-bold">{safeAccess(signal, ['value'], 0).toFixed(2)}</span>
                        </div>
                        
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">Bias:</span>
                          <div className="flex items-center gap-1">
                            {getBiasIcon(safeAccess(signal, ['bias'], 'NEUTRAL'))}
                            <span className={`font-bold text-sm ${getBiasColor(safeAccess(signal, ['bias'], 'NEUTRAL'))}`}>
                              {safeAccess(signal, ['bias'], 'NEUTRAL')}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">Confidence:</span>
                          <span className="font-bold">{(safeAccess(signal, ['confidence'], 0) * 100).toFixed(0)}%</span>
                        </div>

                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">Weight:</span>
                          <span className="font-bold">{(safeAccess(signal, ['weight'], 0) * 100).toFixed(0)}%</span>
                        </div>

                        <div className="pt-2 border-t border-border">
                          <p className="text-xs text-muted-foreground">{safeAccess(signal, ['description'], 'No description available')}</p>
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
                  {!compositeSignal && <p className="text-sm text-muted-foreground mt-2">Loading signal data...</p>}
                </CardContent>
              </Card>
            );
          })()}
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
                        {(() => {
                          const accuracy = safeAccess(signalPerformance, ['accuracy_metrics', '7_day_accuracy'], null);
                          return accuracy !== null ? `${(accuracy * 100).toFixed(1)}%` : 'N/A';
                        })()}
                      </div>
                      <p className="text-sm text-muted-foreground">7-Day Accuracy</p>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-blue-400 mb-2">
                        {(() => {
                          const accuracy = safeAccess(signalPerformance, ['accuracy_metrics', '30_day_accuracy'], null);
                          return accuracy !== null ? `${(accuracy * 100).toFixed(1)}%` : 'N/A';
                        })()}
                      </div>
                      <p className="text-sm text-muted-foreground">30-Day Accuracy</p>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-purple-400 mb-2">
                        {safeAccess(signalPerformance, ['accuracy_metrics', 'total_predictions'], 0)}
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
                    {(() => {
                      const weights = safeAccess(signalPerformance, ['signal_weights'], {});
                      return Object.entries(weights).map(([signal, weight]) => (
                        <div key={signal} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                          <span className="font-medium capitalize">{signal.replace('_', ' ')}</span>
                          <div className="flex items-center gap-2">
                            <Progress value={Math.min((weight as number) * 100, 100)} className="w-24" />
                            <span className="text-sm font-bold">{((weight as number) * 100).toFixed(0)}%</span>
                          </div>
                        </div>
                      ));
                    })()}
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