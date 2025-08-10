import { render, screen, waitFor, fireEvent, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { DynamicStrategyTabs } from '@/components/DynamicStrategyTabs';
import { useStrategies } from '@/contexts/StrategyContext';
import { useToast } from '@/hooks/use-toast';
import { paperTradingService } from '@/services/paperTrading';

// Mock dependencies
vi.mock('@/contexts/StrategyContext');
vi.mock('@/hooks/use-toast');
vi.mock('@/services/paperTrading');
vi.mock('@/utils/performance');

// Mock child components to isolate testing
vi.mock('@/components/LazyTradeCard', () => ({
  default: ({ trade, onExecute, isExecuting }: any) => (
    <div 
      data-testid={`trade-card-${trade.id}`}
      data-trade-symbol={trade.symbol}
      data-trade-strategy={trade.strategy_type}
      data-executing={isExecuting}
    >
      <span>Trade: {trade.symbol} - {trade.strategy_type}</span>
      <button 
        onClick={() => onExecute(trade)}
        disabled={isExecuting}
        data-testid={`execute-${trade.id}`}
      >
        {isExecuting ? 'Executing...' : 'Execute'}
      </button>
    </div>
  )
}));

vi.mock('@/components/ScanProgressModal', () => ({
  default: ({ isOpen, onClose, strategyName, onComplete }: any) => 
    isOpen ? (
      <div data-testid="scan-progress-modal">
        <span>Scanning {strategyName}...</span>
        <button onClick={() => { onComplete(5); onClose(); }}>Complete</button>
      </div>
    ) : null
}));

// Mock performance monitoring
const mockMeasureRender = vi.fn(() => vi.fn());
vi.mock('@/utils/performance', () => ({
  usePerformanceMonitoring: () => ({
    measureRender: mockMeasureRender
  })
}));

// Test data fixtures
const mockStrategies = [
  {
    id: 'ThetaCropWeekly',
    name: 'Theta Crop Weekly',
    category: 'income_generation',
    status: 'active',
    description: 'Weekly theta decay strategy',
    last_updated: '2025-08-10T10:00:00Z'
  },
  {
    id: 'IronCondor',
    name: 'Iron Condor',
    category: 'volatility_trading',
    status: 'active',
    description: 'Neutral volatility strategy',
    last_updated: '2025-08-10T10:00:00Z'
  },
  {
    id: 'ProtectivePut',
    name: 'Protective Put',
    category: 'risk_management',
    status: 'inactive',
    description: 'Downside protection',
    last_updated: '2025-08-10T09:00:00Z'
  }
];

const mockTradeOpportunities = [
  {
    id: 'trade-1',
    symbol: 'SPY',
    strategy_type: 'COVERED_CALL',
    strike: 450,
    expiration: '2025-08-17',
    days_to_expiration: 7,
    premium: 2.50,
    max_loss: -1000,
    max_profit: 250,
    probability_profit: 0.75,
    expected_value: 125,
    delta: -0.30,
    liquidity_score: 0.85,
    underlying_price: 448.50,
    bias: 'BULLISH',
    rsi: 65,
    trade_setup: 'High IV, support level',
    risk_level: 'MEDIUM'
  },
  {
    id: 'trade-2', 
    symbol: 'QQQ',
    strategy_type: 'IRON_CONDOR',
    short_strike: 380,
    long_strike: 385,
    expiration: '2025-08-24',
    days_to_expiration: 14,
    premium: 1.80,
    max_loss: -320,
    max_profit: 180,
    probability_profit: 0.65,
    expected_value: 85,
    delta: 0.05,
    liquidity_score: 0.90,
    underlying_price: 382.50,
    bias: 'NEUTRAL',
    rsi: 52,
    trade_setup: 'Range bound, high IV',
    risk_level: 'LOW'
  }
];

const mockOpportunitiesByStrategy = {
  'ThetaCropWeekly': { opportunities: [mockTradeOpportunities[0]] },
  'IronCondor': { opportunities: [mockTradeOpportunities[1]] },
  'ProtectivePut': { opportunities: [] }
};

const mockLoadingOpportunities = {
  'ThetaCropWeekly': false,
  'IronCondor': false,
  'ProtectivePut': false
};

describe('DynamicStrategyTabs', () => {
  const mockToast = vi.fn();
  const mockRefreshAllOpportunities = vi.fn();
  const mockRefreshStrategyWithProgress = vi.fn();
  const mockGetStrategiesByCategory = vi.fn();
  const mockGetAllOpportunities = vi.fn();
  const mockGetOpportunitiesByCategory = vi.fn();
  const mockGetStrategyOpportunities = vi.fn();

  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks();

    // Setup mock implementations
    (useStrategies as any).mockReturnValue({
      strategies: mockStrategies,
      categories: ['income_generation', 'volatility_trading', 'risk_management'],
      loading: false,
      error: null,
      opportunitiesByStrategy: mockOpportunitiesByStrategy,
      loadingOpportunities: mockLoadingOpportunities,
      activeScanJobs: [],
      getStrategiesByCategory: mockGetStrategiesByCategory,
      getAllOpportunities: mockGetAllOpportunities,
      getOpportunitiesByCategory: mockGetOpportunitiesByCategory,
      getStrategyOpportunities: mockGetStrategyOpportunities,
      refreshAllOpportunities: mockRefreshAllOpportunities,
      refreshStrategyWithProgress: mockRefreshStrategyWithProgress
    });

    (useToast as any).mockReturnValue({
      toast: mockToast
    });

    mockGetAllOpportunities.mockReturnValue(mockTradeOpportunities);
    mockGetOpportunitiesByCategory.mockReturnValue([]);
    mockGetStrategiesByCategory.mockReturnValue([]);

    // Mock paperTradingService
    (paperTradingService.executeTrade as any).mockResolvedValue({
      id: 'executed-trade-1',
      symbol: 'SPY',
      success: true
    });

    // Mock performance monitoring
    mockMeasureRender.mockReturnValue(vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Rendering & Basic Functionality', () => {
    it('renders loading state correctly', () => {
      (useStrategies as any).mockReturnValue({
        strategies: [],
        loading: true,
        error: null,
        categories: [],
        opportunitiesByStrategy: {},
        loadingOpportunities: {},
        activeScanJobs: [],
        getStrategiesByCategory: vi.fn(),
        getAllOpportunities: vi.fn(() => []),
        getOpportunitiesByCategory: vi.fn(),
        getStrategyOpportunities: vi.fn(),
        refreshAllOpportunities: vi.fn(),
        refreshStrategyWithProgress: vi.fn()
      });

      render(<DynamicStrategyTabs />);
      
      expect(screen.getByText('Loading trading strategies...')).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('renders error state correctly', () => {
      const errorMessage = 'Failed to connect to trading API';
      (useStrategies as any).mockReturnValue({
        strategies: [],
        loading: false,
        error: errorMessage,
        categories: [],
        opportunitiesByStrategy: {},
        loadingOpportunities: {},
        activeScanJobs: [],
        getStrategiesByCategory: vi.fn(),
        getAllOpportunities: vi.fn(() => []),
        getOpportunitiesByCategory: vi.fn(),
        getStrategyOpportunities: vi.fn(),
        refreshAllOpportunities: vi.fn(),
        refreshStrategyWithProgress: vi.fn()
      });

      render(<DynamicStrategyTabs />);
      
      expect(screen.getByText(`Failed to load trading strategies: ${errorMessage}`)).toBeInTheDocument();
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('renders header with strategy overview', () => {
      render(<DynamicStrategyTabs />);
      
      expect(screen.getByText('Trading Opportunities')).toBeInTheDocument();
      expect(screen.getByText(/2 opportunities across 3 strategies/)).toBeInTheDocument();
      expect(screen.getByText('2 Active')).toBeInTheDocument();
      expect(screen.getByText('3 Categories')).toBeInTheDocument();
    });

    it('renders tab navigation correctly', () => {
      render(<DynamicStrategyTabs />);
      
      // Strategy tabs
      expect(screen.getByRole('tab', { name: /All 2/ })).toBeInTheDocument();
      
      // Trade type tabs
      expect(screen.getByRole('tab', { name: /High Probability/ })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Quick Scalps/ })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Swing Trades/ })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Volatility Plays/ })).toBeInTheDocument();
    });
  });

  describe('Performance Optimization', () => {
    it('measures render performance on component mount', () => {
      render(<DynamicStrategyTabs />);
      
      expect(mockMeasureRender).toHaveBeenCalledWith('main-render');
    });

    it('implements virtualization for large opportunity lists', async () => {
      // Create large dataset to trigger virtualization
      const largeOpportunityList = Array.from({ length: 25 }, (_, i) => ({
        ...mockTradeOpportunities[0],
        id: `trade-${i}`,
        symbol: `SYM${i}`
      }));

      mockGetAllOpportunities.mockReturnValue(largeOpportunityList);
      (useStrategies as any).mockReturnValue({
        ...mockStrategies,
        opportunitiesByStrategy: {
          'ThetaCropWeekly': { opportunities: largeOpportunityList }
        },
        getAllOpportunities: () => largeOpportunityList
      });

      render(<DynamicStrategyTabs />);
      
      // Should only render first 20 items initially
      await waitFor(() => {
        const tradeCards = screen.getAllByTestId(/^trade-card-/);
        expect(tradeCards.length).toBeLessThanOrEqual(20);
      });
    });

    it('handles rapid tab switching without performance degradation', async () => {
      const user = userEvent.setup();
      render(<DynamicStrategyTabs />);
      
      // Switch between tabs rapidly
      const allTab = screen.getByRole('tab', { name: /All/ });
      const highProbTab = screen.getByRole('tab', { name: /High Probability/ });
      
      await user.click(highProbTab);
      await user.click(allTab);
      await user.click(highProbTab);
      
      // Performance monitoring should track each render
      expect(mockMeasureRender).toHaveBeenCalledTimes(1); // Only initial render measured
    });
  });

  describe('Trading Workflow', () => {
    it('displays opportunities correctly', () => {
      render(<DynamicStrategyTabs />);
      
      expect(screen.getByTestId('trade-card-trade-1')).toBeInTheDocument();
      expect(screen.getByTestId('trade-card-trade-2')).toBeInTheDocument();
      expect(screen.getByText('Trade: SPY - COVERED_CALL')).toBeInTheDocument();
      expect(screen.getByText('Trade: QQQ - IRON_CONDOR')).toBeInTheDocument();
    });

    it('executes trades correctly', async () => {
      const mockOnTradeExecuted = vi.fn();
      const user = userEvent.setup();
      
      render(<DynamicStrategyTabs onTradeExecuted={mockOnTradeExecuted} />);
      
      const executeButton = screen.getByTestId('execute-trade-1');
      await user.click(executeButton);
      
      await waitFor(() => {
        expect(paperTradingService.executeTrade).toHaveBeenCalledWith(
          mockTradeOpportunities[0],
          1
        );
        expect(mockOnTradeExecuted).toHaveBeenCalledWith(125); // expected_value
        expect(mockToast).toHaveBeenCalledWith({
          title: "Trade Executed Successfully",
          description: "SPY COVERED_CALL executed for $2.50",
          duration: 5000,
        });
      });
    });

    it('prevents duplicate trade execution', async () => {
      const user = userEvent.setup();
      
      render(<DynamicStrategyTabs />);
      
      const executeButton = screen.getByTestId('execute-trade-1');
      
      // Click rapidly multiple times
      await user.click(executeButton);
      await user.click(executeButton);
      await user.click(executeButton);
      
      // Should only execute once
      await waitFor(() => {
        expect(paperTradingService.executeTrade).toHaveBeenCalledTimes(1);
      });
    });

    it('handles trade execution errors gracefully', async () => {
      const user = userEvent.setup();
      const errorMessage = 'Insufficient buying power';
      
      (paperTradingService.executeTrade as any).mockRejectedValue(
        new Error(errorMessage)
      );
      
      render(<DynamicStrategyTabs />);
      
      const executeButton = screen.getByTestId('execute-trade-1');
      await user.click(executeButton);
      
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: "Trade Execution Failed",
          description: errorMessage,
          variant: "destructive",
          duration: 5000,
        });
      });
    });
  });

  describe('Filtering & Navigation', () => {
    it('filters opportunities by trade type correctly', async () => {
      const user = userEvent.setup();
      
      // Mock high probability trades (>75% win rate)
      mockGetAllOpportunities.mockReturnValue([
        { ...mockTradeOpportunities[0], probability_profit: 0.80 },
        { ...mockTradeOpportunities[1], probability_profit: 0.60 }
      ]);
      
      render(<DynamicStrategyTabs />);
      
      const highProbTab = screen.getByRole('tab', { name: /High Probability/ });
      await user.click(highProbTab);
      
      // Should only show trades with >75% probability
      await waitFor(() => {
        expect(screen.getByTestId('trade-card-trade-1')).toBeInTheDocument();
        expect(screen.queryByTestId('trade-card-trade-2')).not.toBeInTheDocument();
      });
    });

    it('filters quick scalps by DTE correctly', async () => {
      const user = userEvent.setup();
      
      // Mock short-term and long-term trades
      mockGetAllOpportunities.mockReturnValue([
        { ...mockTradeOpportunities[0], days_to_expiration: 5 }, // Quick scalp
        { ...mockTradeOpportunities[1], days_to_expiration: 14 } // Not a scalp
      ]);
      
      render(<DynamicStrategyTabs />);
      
      const quickScalpsTab = screen.getByRole('tab', { name: /Quick Scalps/ });
      await user.click(quickScalpsTab);
      
      await waitFor(() => {
        expect(screen.getByTestId('trade-card-trade-1')).toBeInTheDocument();
        expect(screen.queryByTestId('trade-card-trade-2')).not.toBeInTheDocument();
      });
    });
  });

  describe('Symbol-based Filtering', () => {
    it('filters opportunities by symbol prop', () => {
      render(<DynamicStrategyTabs symbol="QQQ" />);
      
      expect(mockGetStrategyOpportunities).toHaveBeenCalledWith('ThetaCropWeekly', 'QQQ');
      expect(mockGetStrategyOpportunities).toHaveBeenCalledWith('IronCondor', 'QQQ');
    });

    it('uses SPY as default symbol', () => {
      render(<DynamicStrategyTabs />);
      
      expect(mockGetStrategyOpportunities).toHaveBeenCalledWith('ThetaCropWeekly', 'SPY');
      expect(mockGetStrategyOpportunities).toHaveBeenCalledWith('IronCondor', 'SPY');
    });
  });
});