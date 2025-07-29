
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
  // API response fields
  order_id?: string;
  execution_price?: number;
  commission?: number;
  message?: string;
}

interface SpreadOpportunity {
  id: string;
  symbol: string;
  strategy_type: string;
  option_type: string;
  strike: number;
  short_strike?: number;
  long_strike?: number;
  expiration: string;
  days_to_expiration: number;
  premium: number;
}

interface PositionData {
  order_id?: string;
  id: number;
  symbol: string;
  type?: string;
  spread_type?: string;
  short_strike: number;
  long_strike: number;
  quantity: number;
  entry_credit?: number;
  entry_price: number;
  entry_date: string;
  expiration?: string;
  expiration_date?: string;
  status: string;
  exit_price?: number;
  exit_date?: string;
}

interface AccountMetrics {
  account_balance: number;
  buying_power: number;
  total_pnl: number;
  today_pnl: number;
  open_positions: number;
  // Add other expected metrics fields
}

interface SyncResponse {
  message: string;
  positions_updated: number;
  success: boolean;
  rate_limited?: boolean;
}

export class RealTradingService {
  private baseUrl = 'http://localhost:8000/api';
  private listeners: ((trades: Trade[]) => void)[] = [];

  constructor() {
    // Don't load trades immediately in constructor to avoid race conditions
    // Components will call loadTrades() when needed
    
    // Removed automatic polling - positions will be updated via component-triggered syncs
    // This prevents excessive background API calls when no one is actively viewing positions
  }

  async executeTrade(spread: SpreadOpportunity, quantity: number): Promise<Trade> {
    try {
      const response = await fetch(`${this.baseUrl}/trading/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id: spread.id,
          symbol: spread.symbol,
          strategy_type: spread.strategy_type,
          option_type: spread.option_type,
          strike: spread.strike,
          short_strike: spread.short_strike,
          long_strike: spread.long_strike,
          expiration: spread.expiration,
          days_to_expiration: spread.days_to_expiration,
          premium: spread.premium,
          quantity: quantity,
        })
      });
      
      if (!response || !response.ok) {
        const errorData = await response?.json();
        throw new Error(`HTTP ${response?.status}: ${errorData?.detail}`);
      }
      
      const trade = await response.json();
      
      // Reload all trades to get updated data
      await this.loadTrades();
      
      return trade;
    } catch (error) {
      console.error('Error executing trade:', error);
      throw new Error(`Failed to execute trade: ${error}`);
    }
  }

  async closeTrade(tradeId: string, exitPrice: number): Promise<{message?: string, cancelled_orders?: string[], cancelled_count?: number}> {
    try {
      const response = await fetch(`${this.baseUrl}/positions/close/${tradeId}?exit_price=${exitPrice}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (!response || !response.ok) {
        const errorData = await response?.json();
        throw new Error(errorData?.detail || `HTTP ${response?.status}: ${response?.statusText}`);
      }
      
      const result = await response.json();
      
      // Reload all trades to get updated data
      await this.loadTrades();
      
      return {
        message: result.message,
        cancelled_orders: result.cancelled_orders,
        cancelled_count: result.cancelled_count
      };
    } catch (error) {
      console.error('Error closing trade:', error);
      throw error;
    }
  }

  private trades: Trade[] = [];
  
  async loadTrades(): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/positions/?sync=false`);
      
      if (!response || !response.ok) {
        throw new Error(`HTTP response not ok: ${response?.status}: ${response?.statusText}`);
      }
      
      const data = await response.json();
      this.trades = data.map((position: PositionData) => {
        // Parse expiration date properly, handling null/undefined
        let expirationDate: Date | undefined;
        const expDateString = position.expiration || position.expiration_date;
        if (expDateString && expDateString !== 'null') {
          expirationDate = new Date(expDateString);
          // Check if date is valid
          if (isNaN(expirationDate.getTime())) {
            expirationDate = undefined;
          }
        }

        // Parse entry date properly
        let entryDate: Date;
        try {
          entryDate = new Date(position.entry_date);
          if (isNaN(entryDate.getTime())) {
            entryDate = new Date(); // Fallback to current date
          }
        } catch {
          entryDate = new Date(); // Fallback to current date
        }

        return {
          id: position.order_id || position.id.toString(),
          symbol: position.symbol,
          type: (position.type || position.spread_type || 'STOCK').toUpperCase(),
          shortStrike: position.short_strike || 0,
          longStrike: position.long_strike || 0,
          quantity: position.quantity,
          entryCredit: position.entry_credit || (position.entry_price * position.quantity),
          entryDate: entryDate,
          expiration: expirationDate,
          status: position.status.toUpperCase(),
          exitPrice: position.exit_price,
          exitDate: position.exit_date ? new Date(position.exit_date) : undefined,
          pnl: position.pnl || position.current_pnl || 0
        };
      });
      
      this.notifyListeners();
    } catch (error) {
      console.error('Error loading trades:', error);
      // Don't throw error, just log it - UI should handle empty state
    }
  }
  
  getTrades(): Trade[] {
    return [...this.trades];
  }

  getOpenTrades(): Trade[] {
    return this.trades.filter(t => t.status === 'OPEN');
  }

  async syncPositions(): Promise<SyncResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/positions/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response || !response.ok) {
        throw new Error(`HTTP response not ok: ${response?.status}: ${response?.statusText}`);
      }
      
      const syncResult = await response.json();
      
      // Handle rate limiting gracefully
      if (syncResult.status === 'rate_limited') {
        console.warn('Position sync rate limited:', syncResult.message);
        // Return the rate limited response instead of treating it as an error
        return {
          message: syncResult.message,
          positions_updated: 0,
          success: false,
          rate_limited: true
        };
      }
      
      console.log('Position sync result:', syncResult);
      return {
        message: syncResult.message || 'Sync completed',
        positions_updated: syncResult.sync_results?.synced_positions || 0,
        success: syncResult.status === 'success'
      };
    } catch (error) {
      console.error('Error syncing positions:', error);
      throw error;
    }
  }

  async getAccountMetrics(): Promise<AccountMetrics> {
    try {
      const response = await fetch(`${this.baseUrl}/dashboard/metrics`);
      
      if (!response || !response.ok) {
        throw new Error(`HTTP response not ok: ${response?.status}: ${response?.statusText}`);
      }
      
      const metrics = await response.json();
      
      // Also fetch performance history data for charts
      try {
        const perfResponse = await fetch(`${this.baseUrl}/dashboard/performance?days=30`);
        if (perfResponse.ok) {
          const perfData = await perfResponse.json();
          metrics.performanceHistory = perfData.data;
        }
      } catch (perfError) {
        console.warn('Failed to fetch performance history:', perfError);
        metrics.performanceHistory = [];
      }
      
      return metrics;
    } catch (error) {
      console.error('Error fetching account metrics:', error);
      return {
        totalPnL: 0,
        winRate: 0,
        avgWin: 0,
        avgLoss: 0,
        accountValue: 0,
        dailyPnL: 0,
        performanceHistory: []
      };
    }
  }

  subscribe(listener: (trades: Trade[]) => void): () => void {
    this.listeners.push(listener);
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => listener(this.getTrades()));
  }
}

export const tradingService = new RealTradingService();

// Keep old export for backward compatibility during transition
export const paperTradingService = tradingService;
