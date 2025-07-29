/**
 * Demo Data Service
 * Provides realistic demo data for first-time users and onboarding
 */

interface DemoPosition {
  id: string;
  symbol: string;
  type: string;
  short_strike?: number;
  long_strike?: number;
  strike?: number;
  quantity: number;
  entry_credit: number;
  entry_date: string;
  expiration: string;
  current_value: number;
  pnl: number;
  pnl_percentage: number;
  status: string;
  delta: number;
  theta: number;
  margin_required: number;
  strategy_type: string;
  days_to_expiration: number;
}

interface DemoAccountMetrics {
  account_balance: number;
  cash: number;
  buying_power: number;
  account_status: string;
  account_id: string;
  total_pnl: number;
  pnl_percentage: number;
  win_rate: number;
  total_trades: number;
  winning_trades: number;
  sharpe_ratio: number;
  max_drawdown: number;
  positions_open: number;
  margin_used: number;
  last_updated: string;
}

interface DemoTradeOpportunity {
  id: string;
  symbol: string;
  strategy_type: string;
  option_type: string;
  short_strike?: number;
  long_strike?: number;
  strike?: number;
  expiration: string;
  days_to_expiration: number;
  premium?: number;
  credit?: number;
  probability_profit: number;
  expected_value: number;
  delta: number;
  score: number;
  liquidity: string;
  current_underlying: number;
  signal_strength: string;
  trade_setup: string;
  volatility_rank: number;
  liquidity_score: number;
}

interface DemoTradeCategories {
  high_probability: DemoTradeOpportunity[];
  quick_scalps: DemoTradeOpportunity[];
  swing_trades: DemoTradeOpportunity[];
  volatility_plays: DemoTradeOpportunity[];
  rsi_coupon: DemoTradeOpportunity[];
}

export class DemoDataService {
  
  /**
   * Generate realistic demo positions showing various trade outcomes
   */
  static getDemoPositions(): DemoPosition[] {
    const now = new Date();
    const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    const threeDaysAgo = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000);
    const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);
    const nextWeek = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
    const nextMonth = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);

    return [
      // Winning credit spread
      {
        id: "demo_pos_1",
        symbol: "SPY",
        type: "PUT",
        strategy_type: "CREDIT_SPREAD",
        short_strike: 520,
        long_strike: 510,
        quantity: 2,
        entry_credit: 2.50,
        entry_date: sevenDaysAgo.toISOString(),
        expiration: nextWeek.toISOString(),
        current_value: 0.85,
        pnl: 330, // (2.50 - 0.85) * 100 * 2
        pnl_percentage: 66,
        status: "OPEN",
        delta: -0.08,
        theta: 0.12,
        margin_required: 2000,
        days_to_expiration: 7
      },
      // Losing position (demonstrates risk management)
      {
        id: "demo_pos_2", 
        symbol: "QQQ",
        type: "CALL",
        strategy_type: "SINGLE_OPTION",
        strike: 380,
        quantity: 1,
        entry_credit: 4.20,
        entry_date: threeDaysAgo.toISOString(),
        expiration: tomorrow.toISOString(),
        current_value: 1.50,
        pnl: -270, // (1.50 - 4.20) * 100
        pnl_percentage: -64,
        status: "OPEN",
        delta: 0.25,
        theta: -0.18,
        margin_required: 1000,
        days_to_expiration: 1
      },
      // Closed winning trade
      {
        id: "demo_pos_3",
        symbol: "AAPL",
        type: "PUT",
        strategy_type: "CREDIT_SPREAD", 
        short_strike: 175,
        long_strike: 170,
        quantity: 1,
        entry_credit: 1.80,
        entry_date: new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000).toISOString(),
        expiration: new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        current_value: 0.00,
        pnl: 180, // Full credit kept
        pnl_percentage: 100,
        status: "CLOSED",
        delta: 0,
        theta: 0,
        margin_required: 0,
        days_to_expiration: 0
      },
      // Iron Condor position
      {
        id: "demo_pos_4",
        symbol: "IWM",
        type: "IRON_CONDOR",
        strategy_type: "IRON_CONDOR",
        quantity: 1,
        entry_credit: 3.50,
        entry_date: new Date(now.getTime() - 5 * 24 * 60 * 60 * 1000).toISOString(),
        expiration: nextMonth.toISOString(),
        current_value: 2.80,
        pnl: 70, // (3.50 - 2.80) * 100
        pnl_percentage: 20,
        status: "OPEN",
        delta: 0.02,
        theta: 0.08,
        margin_required: 1500,
        days_to_expiration: 30
      }
    ];
  }

  /**
   * Generate realistic demo account metrics
   */
  static getDemoAccountMetrics(): DemoAccountMetrics {
    return {
      account_balance: 125750.68,
      cash: 95234.50,
      buying_power: 190469.00,
      account_status: "ACTIVE",
      account_id: "DEMO_ACCOUNT_123456",
      total_pnl: 2575.68, // Up from starting 100k
      pnl_percentage: 2.58,
      win_rate: 72.5,
      total_trades: 40,
      winning_trades: 29,
      sharpe_ratio: 1.42,
      max_drawdown: 0.06,
      positions_open: 3,
      margin_used: 4500,
      last_updated: new Date().toISOString()
    };
  }

  /**
   * Generate realistic demo trading opportunities
   */
  static getDemoOpportunities(): DemoTradeOpportunity[] {
    return [
      // High probability credit spread
      {
        id: "demo_opp_1",
        symbol: "SPY",
        strategy_type: "CREDIT_SPREAD",
        option_type: "PUT",
        short_strike: 615,
        long_strike: 605,
        expiration: "2025-08-15",
        days_to_expiration: 28,
        credit: 2.85,
        probability_profit: 0.78,
        expected_value: 195.50,
        delta: -0.12,
        score: 8.4,
        liquidity: "HIGH",
        current_underlying: 627.50,
        signal_strength: "STRONG",
        trade_setup: "MEAN_REVERSION",
        volatility_rank: 35,
        liquidity_score: 9.2
      },
      // Quick scalp opportunity
      {
        id: "demo_opp_2",
        symbol: "QQQ",
        strategy_type: "SINGLE_OPTION",
        option_type: "CALL",
        strike: 385,
        expiration: "2025-07-25",
        days_to_expiration: 6,
        premium: 3.20,
        probability_profit: 0.58,
        expected_value: 85.00,
        delta: 0.35,
        score: 7.1,
        liquidity: "HIGH",
        current_underlying: 382.15,
        signal_strength: "MODERATE",
        trade_setup: "MOMENTUM",
        volatility_rank: 45,
        liquidity_score: 8.8
      },
      // RSI Coupon opportunity
      {
        id: "demo_opp_3",
        symbol: "NVDA",
        strategy_type: "RSI_COUPON",
        option_type: "PUT",
        strike: 115,
        expiration: "2025-08-30",
        days_to_expiration: 42,
        premium: 2.75,
        probability_profit: 0.65,
        expected_value: 138.00,
        delta: 0.32,
        score: 8.7,
        liquidity: "HIGH",
        current_underlying: 118.45,
        signal_strength: "STRONG",
        trade_setup: "OVERSOLD_BOUNCE",
        volatility_rank: 28,
        liquidity_score: 9.5
      },
      // Swing trade iron condor
      {
        id: "demo_opp_4",
        symbol: "IWM",
        strategy_type: "IRON_CONDOR",
        option_type: "IRON_CONDOR",
        expiration: "2025-09-19",
        days_to_expiration: 62,
        credit: 4.50,
        probability_profit: 0.68,
        expected_value: 245.00,
        delta: 0.01,
        score: 7.8,
        liquidity: "MEDIUM",
        current_underlying: 225.80,
        signal_strength: "MODERATE",
        trade_setup: "RANGE_BOUND",
        volatility_rank: 52,
        liquidity_score: 7.2
      }
    ];
  }

  /**
   * Categorize demo opportunities by strategy type
   */
  static getDemoTradeCategories(): DemoTradeCategories {
    const opportunities = this.getDemoOpportunities();
    
    return {
      high_probability: opportunities.filter(opp => opp.probability_profit > 0.75),
      quick_scalps: opportunities.filter(opp => opp.days_to_expiration <= 7),
      swing_trades: opportunities.filter(opp => opp.days_to_expiration > 30),
      volatility_plays: opportunities.filter(opp => opp.volatility_rank > 50),
      rsi_coupon: opportunities.filter(opp => opp.strategy_type === "RSI_COUPON")
    };
  }

  /**
   * Get demo market data
   */
  static getDemoMarketData() {
    return {
      symbol: "SPY",
      price: 627.50,
      volume: 85420,
      change: 2.15,
      change_percent: 0.34,
      atr: 4.65,
      vix: 14.8,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Get demo performance history
   */
  static getDemoPerformanceHistory() {
    const now = new Date();
    const data = [];
    
    // Generate 30 days of performance data
    for (let i = 29; i >= 0; i--) {
      const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
      const dailyPnl = (Math.random() - 0.4) * 200; // Slight positive bias
      const cumulativePnl = 1500 + (29 - i) * 35 + dailyPnl;
      
      data.push({
        date: date.toISOString().split('T')[0],
        pnl: dailyPnl,
        cumulative_pnl: cumulativePnl
      });
    }
    
    return {
      start_date: new Date(now.getTime() - 29 * 24 * 60 * 60 * 1000).toISOString(),
      end_date: now.toISOString(),
      data
    };
  }

  /**
   * Check if user is in demo mode
   */
  static isDemoMode(): boolean {
    return localStorage.getItem('trading_demo_mode') === 'true';
  }

  /**
   * Check if user should be in demo mode based on account balance and first visit status
   * Demo mode defaults to OFF unless it's a new user with zero account balance
   */
  static async shouldEnableDemoMode(): Promise<boolean> {
    // First check if user has explicitly set demo mode preference
    const demoModePreference = localStorage.getItem('trading_demo_mode');
    if (demoModePreference !== null) {
      return demoModePreference === 'true';
    }

    // For new users, check if they have zero account balance
    if (this.isFirstVisit()) {
      try {
        const response = await fetch('/api/dashboard/metrics');
        if (response.ok) {
          const metrics = await response.json();
          const accountBalance = metrics.account_balance || 0;
          // Enable demo mode only for new users with zero balance
          return accountBalance === 0;
        }
      } catch (error) {
        console.log('Could not fetch account metrics, defaulting to demo mode for first visit');
        // If we can't fetch real data, enable demo mode for first-time users
        return true;
      }
    }

    // Default to OFF for existing users
    return false;
  }

  /**
   * Enable demo mode
   */
  static enableDemoMode(): void {
    localStorage.setItem('trading_demo_mode', 'true');
  }

  /**
   * Disable demo mode
   */
  static disableDemoMode(): void {
    localStorage.removeItem('trading_demo_mode');
  }

  /**
   * Check if this is the user's first visit
   */
  static isFirstVisit(): boolean {
    return !localStorage.getItem('trading_visited_before');
  }

  /**
   * Mark that user has visited before
   */
  static markVisited(): void {
    localStorage.setItem('trading_visited_before', 'true');
  }

  /**
   * Check if user should see the tour
   */
  static shouldShowTour(): boolean {
    return this.isFirstVisit() || localStorage.getItem('show_tour') === 'true';
  }

  /**
   * Mark tour as completed
   */
  static completeTour(): void {
    localStorage.setItem('show_tour', 'false');
    this.markVisited();
  }

  /**
   * Request to show tour again
   */
  static requestTour(): void {
    localStorage.setItem('show_tour', 'true');
  }
}