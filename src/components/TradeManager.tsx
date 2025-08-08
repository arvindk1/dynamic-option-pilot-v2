
import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { paperTradingService } from '@/services/paperTrading';
import { CheckCircle, Clock, X, DollarSign, RefreshCw, BarChart3, TrendingUp, TrendingDown } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface Trade {
  id: string;
  symbol: string;
  type: 'PUT' | 'CALL' | 'PUT_SPREAD' | 'CALL_SPREAD' | 'IRON_CONDOR' | 'STRANGLE' | 'STRADDLE' | 'STOCK';
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
  // Options-specific fields for professional trading
  delta?: number;
  gamma?: number;
  theta?: number;
  vega?: number;
  impliedVolatility?: number;
  openInterest?: number;
  volume?: number;
  strategy?: string;
  maxProfit?: number;
  maxLoss?: number;
  breakEvenPoints?: number[];
  assignmentRisk?: 'LOW' | 'MEDIUM' | 'HIGH';
}

export const TradeManager: React.FC = () => {
  console.log('🔄 TradeManager component render');
  
  const [trades, setTrades] = useState<Trade[]>([]);
  const [closingTrade, setClosingTrade] = useState<string | null>(null);
  const [exitPrice, setExitPrice] = useState('');
  const [isSync, setIsSync] = useState(false);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);
  const [lastClick, setLastClick] = useState(0);
  const { toast } = useToast();
  
  // Use ref to avoid lastSyncTime dependency churn
  const lastSyncRef = React.useRef<Date | null>(null);
  useEffect(() => { lastSyncRef.current = lastSyncTime }, [lastSyncTime]);

  console.log('📊 TradeManager state:', { 
    tradesCount: trades.length, 
    isSync, 
    lastSyncTime: lastSyncTime?.toISOString(), 
    closingTrade 
  });

  // Sync with best practices: 
  // - On component mount
  // - When user returns to tab (visibility change)
  // - Every 2 minutes if actively viewing
  // - After any trade action
  const performSync = useCallback(async (showToast: boolean = false) => {
    console.log('🚀 performSync called:', { showToast, isSync, lastSyncTime: lastSyncTime?.toISOString() });
    
    if (isSync) {
      console.log('⏳ performSync blocked - already syncing');
      return; // Prevent concurrent syncs
    }
    
    // Client-side rate limiting: don't sync if last sync was less than 10 seconds ago
    const last = lastSyncRef.current;
    if (last && Date.now() - last.getTime() < 10000) {
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
      console.log('🔄 Starting sync...');
      setIsSync(true);
      // Sync positions first to update the database with Alpaca data
      const syncResult = await paperTradingService.syncPositions();
      console.log('✅ Sync result:', syncResult);
      
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
      console.log('📥 Loading trades after sync...');
      await paperTradingService.loadTrades();
      const loadedTrades = paperTradingService.getTrades();
      console.log('📊 Loaded trades:', loadedTrades.length);
      setTrades(loadedTrades);
      setLastSyncTime(new Date());
      console.log('🕒 Updated lastSyncTime:', new Date().toISOString());
      
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
  }, [isSync, toast]); // ref removes lastSyncTime churn
  
  console.log('🔄 performSync useCallback recreated - deps changed:', { isSync, toast });

  // Debounced manual sync to prevent spam clicking
  const onManualSync = useCallback(() => {
    const now = Date.now();
    if (now - lastClick < 1500) return; // 1.5 second debounce
    setLastClick(now);
    performSync(true);
  }, [lastClick, performSync]);

  // Performance optimizations - memoized calculations
  const now = React.useMemo(() => Date.now(), []); // stable within render
  
  const { openCount, closedCount } = React.useMemo(() => {
    let o = 0, c = 0;
    for (const t of trades) {
      if (t.status === 'OPEN') o++;
      else if (t.status === 'CLOSED') c++;
    }
    return { openCount: o, closedCount: c };
  }, [trades]);

  useEffect(() => {
    console.log('🏁 TradeManager main useEffect triggered');
    const unsubscribe = paperTradingService.subscribe(setTrades);
    
    // Load trades immediately without sync first
    console.log('📥 Initial trade loading...');
    paperTradingService.loadTrades().then(() => {
      const initialTrades = paperTradingService.getTrades();
      console.log('📊 Initial trades loaded:', initialTrades.length);
      setTrades(initialTrades);
      // Then perform sync to get updated data
      console.log('🚀 Triggering initial sync...');
      performSync(false);
    }).catch(console.error);
    
    return () => {
      console.log('🧹 TradeManager main useEffect cleanup');
      unsubscribe();
    };
  }, [performSync]);

  // Sync on visibility change (user returns to tab)
  useEffect(() => {
    if (typeof document === 'undefined') return; // SSR safety
    
    console.log('👁️ TradeManager visibility useEffect triggered');
    const handleVisibilityChange = () => {
      console.log('👁️ Visibility change detected, hidden:', document.hidden);
      if (!document.hidden && lastSyncTime) {
        const timeSinceLastSync = Date.now() - lastSyncTime.getTime();
        console.log('⏰ Time since last sync:', timeSinceLastSync, 'ms');
        // Sync if it's been more than 1 minute since last sync
        if (timeSinceLastSync > 60000) {
          console.log('🚀 Triggering visibility-based sync...');
          performSync(false);
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      console.log('🧹 TradeManager visibility useEffect cleanup');
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [performSync]);

  // Periodic sync every 15 minutes when actively viewing (further reduced frequency)
  useEffect(() => {
    console.log('⏰ TradeManager periodic sync useEffect triggered');
    const interval = setInterval(() => {
      console.log('⏰ Periodic sync check triggered');
      if (!document.hidden && lastSyncTime) {
        const timeSinceLastSync = Date.now() - lastSyncTime.getTime();
        console.log('⏰ Periodic check - time since last sync:', timeSinceLastSync, 'ms');
        // Only sync if it's been more than 10 minutes since last sync
        if (timeSinceLastSync > 600000) { // 10 minutes
          console.log('🚀 Triggering periodic sync...');
          performSync(false);
        }
      }
    }, 900000); // Check every 15 minutes

    return () => {
      console.log('🧹 TradeManager periodic sync useEffect cleanup');
      clearInterval(interval);
    };
  }, [performSync]);

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

  // Professional options strategy identification
  const getStrategyType = (trade: Trade) => {
    if (trade.strategy) return trade.strategy;
    
    if (trade.type === 'STOCK') return 'Equity Position';
    
    // Detect strategy based on strikes
    if (trade.shortStrike && trade.longStrike && trade.shortStrike !== trade.longStrike) {
      if (trade.type.includes('PUT')) return 'Put Spread';
      if (trade.type.includes('CALL')) return 'Call Spread';
      return `${trade.type} Spread`;
    }
    
    return `Single ${trade.type}`;
  };

  // Get DTE urgency level for professional display
  const getDTEUrgency = (dte: number) => {
    if (dte <= 0) return { level: 'EXPIRED', color: 'text-red-600 bg-red-100', label: 'EXPIRED' };
    if (dte <= 3) return { level: 'CRITICAL', color: 'text-red-500 bg-red-50', label: 'CRITICAL' };
    if (dte <= 7) return { level: 'HIGH', color: 'text-orange-500 bg-orange-50', label: 'HIGH URGENCY' };
    if (dte <= 14) return { level: 'MEDIUM', color: 'text-yellow-500 bg-yellow-50', label: 'MEDIUM' };
    if (dte <= 30) return { level: 'LOW', color: 'text-green-500 bg-green-50', label: 'NORMAL' };
    return { level: 'EXTENDED', color: 'text-blue-500 bg-blue-50', label: 'EXTENDED' };
  };

  // Format Greeks for professional display
  const formatGreeks = (trade: Trade) => {
    if (trade.type === 'STOCK') return null;
    
    return {
      delta: trade.delta ? (trade.delta * 100).toFixed(1) : '--',
      gamma: trade.gamma ? (trade.gamma * 100).toFixed(2) : '--',
      theta: trade.theta ? trade.theta.toFixed(2) : '--',
      vega: trade.vega ? (trade.vega * 100).toFixed(1) : '--'
    };
  };

  // Get assignment risk color
  const getAssignmentRiskColor = (risk?: string) => {
    switch (risk) {
      case 'HIGH': return 'text-red-500 bg-red-100';
      case 'MEDIUM': return 'text-yellow-500 bg-yellow-100';
      case 'LOW': return 'text-green-500 bg-green-100';
      default: return 'text-slate-500 bg-slate-100';
    }
  };

  return (
    <Card className="bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 border border-slate-700/50 shadow-2xl">
      <CardHeader className="pb-6 bg-gradient-to-r from-slate-800/50 to-slate-900/50 rounded-t-lg">
        <CardTitle className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-green-500/20 rounded-lg">
              <DollarSign className="h-6 w-6 text-green-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Position Management</h2>
              <p className="text-sm text-muted-foreground">Active trading positions and order management</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            {/* Position Summary */}
            <div className="flex items-center gap-3">
              <Badge variant="default" className="bg-blue-600 text-white px-3 py-1.5 shadow-lg">
                <Clock className="h-4 w-4 mr-1" />
                {trades.filter(t => t.status === 'OPEN').length} Open Positions
              </Badge>
              <Badge variant="secondary" className="bg-green-600 text-white px-3 py-1.5 shadow-lg">
                <CheckCircle className="h-4 w-4 mr-1" />
                {trades.filter(t => t.status === 'CLOSED').length} Closed
              </Badge>
            </div>
            
            {/* Sync Controls */}
            <div className="flex items-center gap-2 bg-card/50 border border-border/50 rounded-lg px-3 py-2">
              {lastSyncTime && (
                <span className="text-xs text-muted-foreground">
                  Last sync: {lastSyncTime.toLocaleTimeString()}
                </span>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={onManualSync}
                disabled={isSync}
                className="h-8 w-8 p-0 hover:bg-accent/50"
              >
                <RefreshCw className={`h-4 w-4 ${isSync ? 'animate-spin text-blue-400' : 'text-muted-foreground'}`} />
              </Button>
            </div>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {trades.length === 0 ? (
            <div className="text-center py-16 px-8">
              <div className="max-w-md mx-auto">
                <div className="p-4 bg-slate-800/50 rounded-full w-16 h-16 mx-auto mb-6 flex items-center justify-center">
                  <DollarSign className="h-8 w-8 text-slate-400" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">No Active Positions</h3>
                <p className="text-slate-400 mb-6">
                  You haven't executed any trades yet. Navigate to the Trading tab to explore available opportunities and execute your first position.
                </p>
                <Button 
                  variant="outline" 
                  className="border-slate-600 text-slate-300 hover:bg-slate-700"
                  onClick={() => window.location.hash = '#trading'}
                >
                  <BarChart3 className="h-4 w-4 mr-2" />
                  View Trading Opportunities
                </Button>
              </div>
            </div>
          ) : (
            trades.map((trade) => (
              <div key={trade.id} className="position-card position-gradient p-6 rounded-lg border border-slate-600/50 shadow-lg">
                <div className="position-grid grid items-start">
                  <div className="space-y-2">
                    <div className="position-label">Asset</div>
                    <div className="flex items-center gap-2">
                      <div className="position-value-large truncate">{trade.symbol}</div>
                      {trade.type === 'STOCK' && <Badge variant="default" className="bg-blue-600 text-white text-xs">Stock</Badge>}
                      {trade.type === 'ETF' && <Badge variant="default" className="bg-purple-600 text-white text-xs">ETF</Badge>}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Strategy Type</div>
                    <div className="flex flex-col gap-1 min-w-0">
                      <Badge 
                        variant="secondary" 
                        className={`font-medium text-xs px-3 py-1 truncate ${
                          trade.type === 'PUT' || trade.type.includes('PUT') 
                            ? 'bg-red-600/20 text-red-300 border-red-600/50' 
                            : trade.type === 'CALL' || trade.type.includes('CALL')
                            ? 'bg-green-600/20 text-green-300 border-green-600/50'
                            : 'bg-blue-600/20 text-blue-300 border-blue-600/50'
                        }`}
                      >
                        {getStrategyType(trade)}
                      </Badge>
                      {/* Assignment Risk for Short Options */}
                      {trade.assignmentRisk && trade.type !== 'STOCK' && (
                        <Badge 
                          variant="outline" 
                          className={`text-xs px-2 py-0.5 truncate ${getAssignmentRiskColor(trade.assignmentRisk)}`}
                        >
                          {trade.assignmentRisk} Assignment Risk
                        </Badge>
                      )}
                    </div>
                  </div>
                  <div className="space-y-2 min-w-0">
                    <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Strike Prices</div>
                    <div className="font-mono text-sm text-white truncate">
                      {trade.type === 'STOCK' ? (
                        <span className="text-slate-400">N/A</span>
                      ) : (
                        (trade.shortStrike && trade.longStrike && trade.shortStrike !== 0 && trade.longStrike !== 0) ? (
                          <div className="flex flex-col gap-1">
                            <span className="text-xs text-slate-400">Short/Long</span>
                            <span className="text-white font-semibold">{trade.shortStrike}/{trade.longStrike}</span>
                          </div>
                        ) : (
                          <span className="text-slate-400">Not Available</span>
                        )
                      )}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Position Size</div>
                    <div className="text-white font-semibold">{trade.quantity} {trade.quantity === 1 ? 'Contract' : 'Contracts'}</div>
                  </div>
                  <div className="space-y-2">
                    <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Entry Credit</div>
                    <div className="text-emerald-400 font-bold text-lg">${trade.entryCredit}</div>
                  </div>
                  <div className="space-y-2">
                    <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Current P&L</div>
                    <div className={`font-bold text-lg ${trade.pnl && trade.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {trade.pnl ? (
                        <div className="flex items-center gap-1">
                          {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(0)}
                          <span className="text-xs text-slate-400">
                            ({trade.pnl >= 0 ? '+' : ''}{((trade.pnl / trade.entryCredit) * 100).toFixed(1)}%)
                          </span>
                        </div>
                      ) : (
                        <span className="text-slate-400">--</span>
                      )}
                    </div>
                  </div>
                </div>
                
                {/* Status and Actions Section */}
                <div className="mt-6 pt-4 border-t border-slate-600/30">
                  <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                    {/* Status Indicator */}
                    <div className="flex items-center gap-3">
                      <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Status</div>
                      <Badge 
                        variant="secondary" 
                        className={`${getStatusColor(trade.status)} font-medium px-3 py-1.5 shadow-lg`}
                      >
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(trade.status)}
                          <span className="font-semibold">{trade.status}</span>
                        </div>
                      </Badge>
                    </div>
                    
                    {/* Action Buttons */}
                    {trade.status === 'OPEN' && (
                      <div className="flex items-center gap-3">
                        {closingTrade === trade.id ? (
                          <div className="flex items-center gap-3 bg-slate-800/50 p-3 rounded-lg border border-slate-600/50">
                            <div>
                              <Label htmlFor={`exit-price-${trade.id}`} className="text-xs text-slate-400 mb-1 block">
                                Exit Price
                              </Label>
                              <Input
                                id={`exit-price-${trade.id}`}
                                type="number"
                                placeholder="0.00"
                                value={exitPrice}
                                onChange={(e) => setExitPrice(e.target.value)}
                                className="bg-slate-700 border-slate-500 text-white w-24 text-sm"
                              />
                            </div>
                            <div className="flex gap-2">
                              <Button 
                                size="sm" 
                                onClick={() => handleCloseTrade(trade.id)}
                                className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg"
                              >
                                <CheckCircle className="h-4 w-4 mr-1" />
                                Confirm
                              </Button>
                              <Button 
                                size="sm" 
                                variant="outline"
                                onClick={() => setClosingTrade(null)}
                                className="border-slate-500 text-slate-300 hover:bg-slate-700"
                              >
                                <X className="h-4 w-4 mr-1" />
                                Cancel
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <Button 
                            onClick={() => setClosingTrade(trade.id)}
                            className="bg-red-600 hover:bg-red-700 text-white shadow-lg px-6 py-2"
                          >
                            <X className="h-4 w-4 mr-2" />
                            Close Position
                          </Button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Enhanced Trade Details */}
                <div className="mt-4 pt-4 border-t border-slate-600/20">
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
                    <div className="space-y-1">
                      <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Entry Date</div>
                      <div className="text-white font-medium">
                        {trade.entryDate && !isNaN(trade.entryDate.getTime()) 
                          ? trade.entryDate.toLocaleDateString('en-US', { 
                              month: 'short', 
                              day: 'numeric', 
                              year: 'numeric' 
                            })
                          : 'Invalid Date'
                        }
                      </div>
                    </div>
                    <div className="space-y-1">
                      <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Days Held</div>
                      <div className="text-white font-medium">
                        {calculateDaysHeld(trade.entryDate)} days
                      </div>
                    </div>
                    <div className="space-y-1">
                      <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Expiration</div>
                      <div className="text-white font-medium">
                        {trade.type === 'STOCK' ? (
                          <span className="text-slate-400">N/A</span>
                        ) : (
                          trade.expiration && !isNaN(trade.expiration.getTime()) 
                            ? trade.expiration.toLocaleDateString('en-US', { 
                                month: 'short', 
                                day: 'numeric', 
                                year: 'numeric' 
                              })
                            : 'Invalid Date'
                        )}
                      </div>
                    </div>
                    <div className="space-y-1">
                      <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Days to Expiry</div>
                      <div className="flex flex-col gap-1">
                        {trade.type === 'STOCK' ? (
                          <span className="text-slate-400 font-medium">N/A</span>
                        ) : (
                          <>
                            <div className={`font-bold text-lg ${
                              calculateDaysToExpiration(trade.expiration) <= 7 ? 'text-red-400' :
                              calculateDaysToExpiration(trade.expiration) <= 21 ? 'text-yellow-400' : 
                              'text-green-400'
                            }`}>
                              {calculateDaysToExpiration(trade.expiration)} days
                            </div>
                            {(() => {
                              const dte = calculateDaysToExpiration(trade.expiration);
                              const urgency = getDTEUrgency(dte);
                              if (urgency.level !== 'NORMAL' && urgency.level !== 'EXTENDED') {
                                return (
                                  <Badge 
                                    variant="outline" 
                                    className={`text-xs px-2 py-0.5 ${urgency.color} border-current`}
                                  >
                                    {urgency.label}
                                  </Badge>
                                );
                              }
                              return null;
                            })()}
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Greeks Section - Options Only */}
                {trade.type !== 'STOCK' && formatGreeks(trade) && (
                  <div className="mt-4 pt-4 border-t border-slate-600/20">
                    <div className="mb-3">
                      <h4 className="text-sm font-medium text-slate-300">Greeks & Risk Metrics</h4>
                    </div>
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                      {(() => {
                        const greeks = formatGreeks(trade);
                        return (
                          <>
                            <div className="text-center">
                              <div className="text-xs text-slate-400 mb-1">Delta</div>
                              <div className={`font-semibold ${
                                trade.delta && Math.abs(trade.delta) > 0.5 ? 'text-yellow-400' : 'text-slate-200'
                              }`}>
                                {greeks?.delta}
                              </div>
                            </div>
                            <div className="text-center">
                              <div className="text-xs text-slate-400 mb-1">Gamma</div>
                              <div className="font-semibold text-slate-200">{greeks?.gamma}</div>
                            </div>
                            <div className="text-center">
                              <div className="text-xs text-slate-400 mb-1">Theta</div>
                              <div className={`font-semibold ${
                                trade.theta && trade.theta < -0.05 ? 'text-red-400' : 'text-slate-200'
                              }`}>
                                {greeks?.theta}
                              </div>
                            </div>
                            <div className="text-center">
                              <div className="text-xs text-slate-400 mb-1">Vega</div>
                              <div className={`font-semibold ${
                                trade.vega && Math.abs(trade.vega) > 0.1 ? 'text-purple-400' : 'text-slate-200'
                              }`}>
                                {greeks?.vega}
                              </div>
                            </div>
                          </>
                        );
                      })()}
                    </div>
                    
                    {/* Additional Options Data */}
                    {(trade.impliedVolatility || trade.volume || trade.openInterest) && (
                      <div className="mt-3 pt-3 border-t border-slate-600/20">
                        <div className="grid grid-cols-3 gap-4 text-center">
                          {trade.impliedVolatility && (
                            <div>
                              <div className="text-xs text-slate-400 mb-1">IV</div>
                              <div className="text-sm font-medium text-slate-200">
                                {(trade.impliedVolatility * 100).toFixed(1)}%
                              </div>
                            </div>
                          )}
                          {trade.volume && (
                            <div>
                              <div className="text-xs text-slate-400 mb-1">Volume</div>
                              <div className="text-sm font-medium text-slate-200">
                                {trade.volume.toLocaleString()}
                              </div>
                            </div>
                          )}
                          {trade.openInterest && (
                            <div>
                              <div className="text-xs text-slate-400 mb-1">Open Interest</div>
                              <div className="text-sm font-medium text-slate-200">
                                {trade.openInterest.toLocaleString()}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
};
