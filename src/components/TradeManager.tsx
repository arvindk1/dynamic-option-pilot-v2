
import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { paperTradingService } from '@/services/paperTrading';
import { CheckCircle, Clock, X, DollarSign, RefreshCw } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface Trade {
  id: string;
  symbol: string;
  type: 'PUT' | 'CALL';
  shortStrike: number;
  longStrike: number;
  quantity: number;
  entryCredit: number;
  entryDate: Date;
  expiration: Date;
  status: 'OPEN' | 'CLOSED' | 'EXPIRED';
  exitPrice?: number;
  exitDate?: Date;
  pnl?: number;
}

export const TradeManager: React.FC = () => {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [closingTrade, setClosingTrade] = useState<string | null>(null);
  const [exitPrice, setExitPrice] = useState('');
  const [isSync, setIsSync] = useState(false);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);
  const { toast } = useToast();

  // Sync with best practices: 
  // - On component mount
  // - When user returns to tab (visibility change)
  // - Every 2 minutes if actively viewing
  // - After any trade action
  const performSync = useCallback(async (showToast: boolean = false) => {
    if (isSync) return; // Prevent concurrent syncs
    
    // Client-side rate limiting: don't sync if last sync was less than 10 seconds ago
    if (lastSyncTime && Date.now() - lastSyncTime.getTime() < 10000) {
      console.warn('Client-side rate limit: sync attempted too soon');
      if (showToast) {
        toast({
          title: "Sync Too Frequent",
          description: "Please wait at least 10 seconds between syncs",
          variant: "default",
        });
      }
      return;
    }
    
    try {
      setIsSync(true);
      // Sync positions first to update the database with Alpaca data
      const syncResult = await paperTradingService.syncPositions();
      
      // Handle rate limiting gracefully
      if (syncResult.rate_limited) {
        console.warn('Sync rate limited, skipping for now');
        if (showToast) {
          toast({
            title: "Sync Rate Limited",
            description: syncResult.message,
            variant: "default",
          });
        }
        return; // Don't reload trades or update sync time if rate limited
      }
      
      // Only reload trades if sync was successful or not rate limited
      await paperTradingService.loadTrades();
      setLastSyncTime(new Date());
      
      if (showToast && syncResult.success) {
        toast({
          title: "Positions Synced",
          description: "Your positions have been synchronized with Alpaca",
        });
      }
    } catch (error) {
      console.error('Sync failed:', error);
      if (showToast) {
        toast({
          title: "Sync Failed",
          description: "Failed to sync positions with Alpaca",
          variant: "destructive",
        });
      }
    } finally {
      setIsSync(false);
    }
  }, [isSync, toast, lastSyncTime]);

  useEffect(() => {
    const unsubscribe = paperTradingService.subscribe(setTrades);
    
    // Load trades immediately without sync first
    paperTradingService.loadTrades().then(() => {
      setTrades(paperTradingService.getTrades());
      // Then perform sync to get updated data
      performSync(false);
    }).catch(console.error);
    
    return unsubscribe;
  }, [performSync]);

  // Sync on visibility change (user returns to tab)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden && lastSyncTime) {
        const timeSinceLastSync = Date.now() - lastSyncTime.getTime();
        // Sync if it's been more than 1 minute since last sync
        if (timeSinceLastSync > 60000) {
          performSync(false);
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [lastSyncTime, performSync]);

  // Periodic sync every 15 minutes when actively viewing (further reduced frequency)
  useEffect(() => {
    const interval = setInterval(() => {
      if (!document.hidden && lastSyncTime) {
        const timeSinceLastSync = Date.now() - lastSyncTime.getTime();
        // Only sync if it's been more than 10 minutes since last sync
        if (timeSinceLastSync > 600000) { // 10 minutes
          performSync(false);
        }
      }
    }, 900000); // Check every 15 minutes

    return () => clearInterval(interval);
  }, [performSync, lastSyncTime]);

  const handleCloseTrade = async (tradeId: string) => {
    const price = parseFloat(exitPrice);
    if (isNaN(price) || price <= 0) {
      toast({
        title: "Invalid Price",
        description: "Please enter a valid exit price",
        variant: "destructive",
      });
      return;
    }

    try {
      const result = await paperTradingService.closeTrade(tradeId, price);
      setClosingTrade(null);
      setExitPrice('');
      
      // Show success message with details about cancelled orders if any
      const description = result.cancelled_count && result.cancelled_count > 0
        ? `Position closed successfully. Cancelled ${result.cancelled_count} existing sell order${result.cancelled_count > 1 ? 's' : ''} first.`
        : "Position has been successfully closed";
      
      toast({
        title: "Trade Closed",
        description: description,
      });
      
      // Sync after closing trade to ensure consistency
      await performSync(false);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to close position';
      
      // Check if error is related to existing orders
      const isOrderError = errorMessage.toLowerCase().includes('order') || 
                          errorMessage.toLowerCase().includes('pending') ||
                          errorMessage.toLowerCase().includes('cancel');
      
      toast({
        title: "Close Failed",
        description: isOrderError 
          ? `Unable to close position: ${errorMessage}. Please check for existing orders.`
          : `Failed to close position: ${errorMessage}`,
        variant: "destructive",
      });
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'OPEN': return 'bg-blue-600 text-white';
      case 'CLOSED': return 'bg-green-600 text-white';
      case 'EXPIRED': return 'bg-red-600 text-white';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'OPEN': return <Clock className="h-4 w-4" />;
      case 'CLOSED': return <CheckCircle className="h-4 w-4" />;
      case 'EXPIRED': return <X className="h-4 w-4" />;
      default: return null;
    }
  };

  const calculateDaysHeld = (entryDate: Date) => {
    if (!entryDate || isNaN(entryDate.getTime())) {
      return 0;
    }
    const days = Math.floor((Date.now() - entryDate.getTime()) / (1000 * 60 * 60 * 24));
    return Math.max(0, days); // Ensure non-negative
  };

  const calculateDaysToExpiration = (expiration: Date | undefined) => {
    if (!expiration || isNaN(expiration.getTime())) {
      return 0;
    }
    const days = Math.floor((expiration.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
    return days; // Can be negative for expired options
  };

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <DollarSign className="h-5 w-5 text-green-500" />
            <span>SPY Trade Management</span>
            <Badge variant="secondary" className="bg-blue-600 text-white">
              {trades.filter(t => t.status === 'OPEN').length} Open
            </Badge>
          </div>
          <div className="flex items-center space-x-2">
            {lastSyncTime && (
              <span className="text-xs text-muted-foreground">
                Last sync: {lastSyncTime.toLocaleTimeString()}
              </span>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => performSync(true)}
              disabled={isSync}
              className="h-8 w-8 p-0"
            >
              <RefreshCw className={`h-4 w-4 ${isSync ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {trades.length === 0 ? (
            <div className="text-center py-8 text-slate-200">
              No trades executed yet. Execute some spread candidates to see them here.
            </div>
          ) : (
            trades.map((trade) => (
              <div key={trade.id} className="bg-slate-900 p-4 rounded-lg border border-slate-600">
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4 items-center">
                  <div>
                    <div className="text-sm text-slate-200">Symbol</div>
                    <div className="font-bold">{trade.symbol}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-200">Type</div>
                    <Badge variant={trade.type === 'PUT' || trade.type.includes('PUT') ? 'secondary' : 'outline'}>
                      {trade.type}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-200">Strikes</div>
                    <div className="font-mono">
                      {trade.type === 'STOCK' ? 'N/A' : 
                       (trade.shortStrike && trade.longStrike && trade.shortStrike !== 0 && trade.longStrike !== 0) ?
                       `${trade.shortStrike}/${trade.longStrike}` : '/'
                      }
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-200">Quantity</div>
                    <div>{trade.quantity}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-200">Entry Credit</div>
                    <div className="text-green-400">${trade.entryCredit}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-200">P&L</div>
                    <div className={trade.pnl && trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
                      {trade.pnl ? `$${trade.pnl.toFixed(0)}` : '--'}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-200">Status</div>
                    <Badge variant="secondary" className={getStatusColor(trade.status)}>
                      <div className="flex items-center space-x-1">
                        {getStatusIcon(trade.status)}
                        <span>{trade.status}</span>
                      </div>
                    </Badge>
                  </div>
                  <div>
                    {trade.status === 'OPEN' && (
                      <div className="space-y-2">
                        {closingTrade === trade.id ? (
                          <div className="space-y-2">
                            <Input
                              type="number"
                              placeholder="Exit price"
                              value={exitPrice}
                              onChange={(e) => setExitPrice(e.target.value)}
                              className="bg-slate-800 border-slate-600 text-sm"
                            />
                            <div className="flex space-x-1">
                              <Button 
                                size="sm" 
                                onClick={() => handleCloseTrade(trade.id)}
                                className="bg-green-600 hover:bg-green-700 text-xs"
                              >
                                Confirm
                              </Button>
                              <Button 
                                size="sm" 
                                variant="outline"
                                onClick={() => setClosingTrade(null)}
                                className="text-xs"
                              >
                                Cancel
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <Button 
                            size="sm" 
                            onClick={() => setClosingTrade(trade.id)}
                            className="bg-red-600 hover:bg-red-700"
                          >
                            Close
                          </Button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Additional trade info */}
                <div className="mt-3 pt-3 border-t border-slate-600 text-sm text-slate-200">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>Entry: {trade.entryDate && !isNaN(trade.entryDate.getTime()) ? trade.entryDate.toLocaleDateString() : 'Invalid Date'}</div>
                    <div>Days Held: {calculateDaysHeld(trade.entryDate)}</div>
                    <div>Expiration: {trade.expiration && !isNaN(trade.expiration.getTime()) ? trade.expiration.toLocaleDateString() : trade.type === 'STOCK' ? 'N/A' : 'Invalid Date'}</div>
                    <div>DTE: {trade.type === 'STOCK' ? 'N/A' : calculateDaysToExpiration(trade.expiration)}</div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
};
