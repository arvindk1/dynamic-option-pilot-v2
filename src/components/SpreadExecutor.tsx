
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { paperTradingService } from '@/services/paperTrading';
import { useToast } from '@/hooks/use-toast';
import { Zap, TrendingUp, TrendingDown, Activity, Target, Star, DollarSign } from 'lucide-react';

interface SpreadCandidate {
  id: string;
  symbol?: string;
  shortStrike: number;
  longStrike: number;
  credit: number;
  maxLoss: number;
  delta: number;
  probabilityProfit: number;
  expectedValue: number;
  daysToExpiration: number;
  type: 'PUT' | 'CALL';
  underlyingPrice?: number;
  liquidityScore?: number;
  bias?: string;
  rsi?: number;
}

interface SpreadExecutorProps {
  spreadCandidates: SpreadCandidate[];
  onTradeExecuted?: (pnl: number) => void;
  loadingOpportunities?: boolean;
}

export const SpreadExecutor: React.FC<SpreadExecutorProps> = ({ 
  spreadCandidates, 
  onTradeExecuted,
  loadingOpportunities = false
}) => {
  const { toast } = useToast();

  const handleExecuteTrade = async (spread: SpreadCandidate) => {
    try {
      // Create the trade object with proper expiration date
      const tradeOrder = {
        ...spread,
        expiration: new Date(Date.now() + (spread.daysToExpiration * 24 * 60 * 60 * 1000)).toISOString()
      };
      
      const trade = await paperTradingService.executeTrade(tradeOrder, 1);
      
      toast({
        title: "Trade Executed!",
        description: `${spread.type} spread executed for order ${trade.order_id}`,
      });

      // Trigger performance update with actual execution price
      if (onTradeExecuted && trade.execution_price) {
        onTradeExecuted(trade.execution_price * 100); // Convert to dollars
      }
    } catch (error) {
      console.error('Trade execution error:', error);
      toast({
        title: "Execution Failed",
        description: `Failed to execute trade: ${error instanceof Error ? error.message : 'Unknown error'}`,
        variant: "destructive",
      });
    }
  };

  const getBiasIcon = (bias?: string) => {
    switch (bias) {
      case 'BULLISH': return <TrendingUp className="h-4 w-4 text-green-400" />;
      case 'BEARISH': return <TrendingDown className="h-4 w-4 text-red-400" />;
      default: return <Activity className="h-4 w-4 text-yellow-400" />;
    }
  };

  const getBiasColor = (bias?: string) => {
    switch (bias) {
      case 'BULLISH': return 'text-green-400';
      case 'BEARISH': return 'text-red-400';
      default: return 'text-yellow-400';
    }
  };

  const getLiquidityStars = (score?: number) => {
    const stars = Math.min(5, Math.max(1, Math.round((score || 5) / 2)));
    return Array.from({ length: 5 }, (_, i) => (
      <Star 
        key={i} 
        className={`h-3 w-3 ${i < stars ? 'text-yellow-400 fill-current' : 'text-gray-600'}`} 
      />
    ));
  };

  return (
    <div className="space-y-6">
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Target className="h-5 w-5 text-blue-500" />
              <span>Profitable Options Opportunities</span>
              <Badge variant="secondary" className="bg-blue-600 text-white">
                Top 20 Liquid Stocks/ETFs
              </Badge>
            </div>
            {loadingOpportunities && (
              <Badge variant="outline" className="bg-yellow-600 text-white">
                Scanning Markets...
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mb-4 text-sm text-muted-foreground">
            Real-time analysis of the most liquid options from SPY, QQQ, AAPL, TSLA, NVDA, and more.
            Sorted by expected value and probability of profit.
          </div>
          
          {spreadCandidates.length === 0 && !loadingOpportunities ? (
            <div className="text-center py-8">
              <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">No trading opportunities found. Market may be closed or data unavailable.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {spreadCandidates.map((spread) => (
                <div key={spread.id} className="bg-muted p-6 rounded-lg border border-border hover:bg-muted/80 transition-colors">
                  {/* Header Row */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-4">
                      <Badge variant="outline" className="text-lg font-bold">
                        {spread.symbol || 'SPY'}
                      </Badge>
                      <div className="flex items-center space-x-1">
                        {getBiasIcon(spread.bias)}
                        <span className={`text-sm font-medium ${getBiasColor(spread.bias)}`}>
                          {spread.bias || 'NEUTRAL'}
                        </span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <span className="text-xs text-muted-foreground">RSI:</span>
                        <span className="text-sm font-medium">{spread.rsi?.toFixed(1) || '--'}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <span className="text-xs text-muted-foreground">Liquidity:</span>
                        <div className="flex space-x-0.5">
                          {getLiquidityStars(spread.liquidityScore)}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-muted-foreground">Underlying</div>
                      <div className="font-bold">${spread.underlyingPrice?.toFixed(2) || '--'}</div>
                    </div>
                  </div>

                  {/* Main Metrics Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-xs text-muted-foreground mb-1">Strategy</div>
                      <Badge variant={spread.type === 'PUT' ? 'secondary' : 'outline'} className="w-full">
                        {spread.type} Credit Spread
                      </Badge>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-xs text-muted-foreground mb-1">Strikes</div>
                      <div className="font-mono font-bold text-foreground">
                        {spread.shortStrike}/{spread.longStrike}
                      </div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-xs text-muted-foreground mb-1">Credit</div>
                      <div className="text-green-600 font-bold text-lg">
                        ${(spread.credit / 100).toFixed(2)}
                      </div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-xs text-muted-foreground mb-1">Max Loss</div>
                      <div className="text-red-600 font-bold">
                        ${(spread.maxLoss / 100).toFixed(2)}
                      </div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-xs text-muted-foreground mb-1">Delta</div>
                      <div className="font-mono font-medium text-foreground">
                        {spread.delta.toFixed(3)}
                      </div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-xs text-muted-foreground mb-1">DTE</div>
                      <div className="font-medium">{spread.daysToExpiration}d</div>
                    </div>
                  </div>

                  {/* Profitability Metrics */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="bg-background p-3 rounded border">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-muted-foreground">Probability of Profit</span>
                        <span className="text-lg font-bold text-blue-600">
                          {(spread.probabilityProfit * 100).toFixed(1)}%
                        </span>
                      </div>
                      <Progress value={spread.probabilityProfit * 100} className="h-2" />
                    </div>
                    
                    <div className="bg-background p-3 rounded border">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-muted-foreground">Expected Value</span>
                        <span className={`text-lg font-bold ${spread.expectedValue >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          ${(spread.expectedValue / 100).toFixed(2)}
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {spread.expectedValue >= 0 ? 'Profitable trade' : 'Negative expectation'}
                      </div>
                    </div>
                    
                    <div className="bg-background p-3 rounded border">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-muted-foreground">Risk/Reward</span>
                        <span className="text-lg font-bold text-purple-600">
                          {((spread.credit / spread.maxLoss) * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Credit as % of max loss
                      </div>
                    </div>
                  </div>

                  {/* Action Button */}
                  <div className="flex justify-center">
                    <Button 
                      onClick={() => handleExecuteTrade(spread)}
                      className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold px-8 py-2 transition-all duration-200"
                      disabled={loadingOpportunities}
                    >
                      <DollarSign className="h-4 w-4 mr-2" />
                      Execute Trade (Paper)
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
