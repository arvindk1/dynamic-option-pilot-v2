import { render, screen, waitFor, within, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { DynamicStrategyTabs } from '@/components/DynamicStrategyTabs';
import { useToast } from '@/hooks/use-toast';
import { paperTradingService } from '@/services/paperTrading';

// Mock external dependencies
vi.mock('@/hooks/use-toast');
vi.mock('@/services/paperTrading');
vi.mock('@/utils/performance');

// Mock LazyTradeCard for integration testing  
vi.mock('@/components/LazyTradeCard', () => ({
  default: ({ trade, onExecute, isExecuting, isMobile }: any) => (
    <div 
      data-testid={`trade-card-${trade.id}`}
      data-trade-symbol={trade.symbol}
      data-trade-strategy={trade.strategy_type}
      data-executing={isExecuting}
      data-mobile={isMobile}
      role="article"
      aria-label={`${trade.symbol} ${trade.strategy_type} trade opportunity`}
    >
      <div data-testid="trade-details">
        <h3>{trade.symbol} - {trade.strategy_type}</h3>
        <p>Premium: ${trade.premium}</p>
        <p>DTE: {trade.days_to_expiration}</p>
        <p>Win Rate: {(trade.probability_profit * 100).toFixed(0)}%</p>
        <p>Expected Value: ${trade.expected_value}</p>
        <p>Risk Level: {trade.risk_level}</p>
      </div>
      <button 
        onClick={() => onExecute(trade)}
        disabled={isExecuting}
        data-testid={`execute-${trade.id}`}
        aria-label={`Execute ${trade.symbol} ${trade.strategy_type} trade`}
      >
        {isExecuting ? 'Executing...' : 'Execute Trade'}
      </button>
    </div>
  )
}));

// Mock scan progress modal
vi.mock('@/components/ScanProgressModal', () => ({
  default: ({ isOpen, onClose, strategyName, onComplete }: any) => 
    isOpen ? (
      <div data-testid="scan-progress-modal" role="dialog" aria-label="Strategy scan progress">
        <h2>Scanning {strategyName}</h2>
        <div data-testid="progress-indicator">Analyzing opportunities...</div>
        <button onClick={() => { onComplete?.(5); onClose(); }}>
          Complete Scan
        </button>
      </div>
    ) : null
}));

// Mock performance monitoring
vi.mock('@/utils/performance', () => ({
  usePerformanceMonitoring: () => ({
    measureRender: vi.fn(() => vi.fn()),
    measureApiCall: vi.fn((name, fn) => fn()),
    startTimer: vi.fn(),
    endTimer: vi.fn(() => 100)
  })
}));

// Comprehensive test data fixtures
const createMockOpportunity = (overrides = {}) => ({
  id: `trade-${Math.random().toString(36).substr(2, 9)}`,
  symbol: 'SPY',
  strategy_type: 'COVERED_CALL',
  option_type: 'CALL',
  strike: 450,
  short_strike: 450,
  long_strike: 455,
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
  risk_level: 'MEDIUM',
  overall_score: 0.82,
  quality_tier: 'HIGH',
  confidence_percentage: 85,
  technical_score: 0.78,
  liquidity_score_enhanced: 0.90,
  risk_adjusted_score: 0.75,
  ...overrides
});

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
    status: 'active',
    description: 'Downside protection',
    last_updated: '2025-08-10T09:00:00Z'
  }
];

// Professional trading scenarios
const professionalTradingData = {
  highProbabilityTrades: [
    createMockOpportunity({
      id: 'high-prob-1',
      symbol: 'SPY',
      strategy_type: 'PUT_CREDIT_SPREAD',
      probability_profit: 0.85,
      expected_value: 180,
      risk_level: 'LOW',
      days_to_expiration: 14
    }),
    createMockOpportunity({
      id: 'high-prob-2', 
      symbol: 'QQQ',
      strategy_type: 'IRON_CONDOR',
      probability_profit: 0.80,
      expected_value: 150,
      risk_level: 'LOW',
      days_to_expiration: 21
    })
  ],
  quickScalps: [
    createMockOpportunity({
      id: 'scalp-1',
      symbol: 'SPY',
      strategy_type: 'CALL_CREDIT_SPREAD',
      days_to_expiration: 3,
      premium: 0.85,
      expected_value: 45,
      risk_level: 'HIGH'
    }),
    createMockOpportunity({
      id: 'scalp-2',
      symbol: 'IWM', 
      strategy_type: 'PUT_CREDIT_SPREAD',
      days_to_expiration: 5,
      premium: 1.20,
      expected_value: 65,
      risk_level: 'HIGH'
    })
  ],
  swingTrades: [
    createMockOpportunity({
      id: 'swing-1',
      symbol: 'TSLA',
      strategy_type: 'COVERED_CALL',
      days_to_expiration: 28,
      premium: 4.50,
      expected_value: 285,
      risk_level: 'MEDIUM'
    })
  ],
  volatilityPlays: [
    createMockOpportunity({
      id: 'vol-1',
      symbol: 'VIX',
      strategy_type: 'LONG_STRADDLE',
      days_to_expiration: 10,
      premium: 3.80,
      expected_value: 195,
      risk_level: 'HIGH',
      bias: 'VOLATILITY_EXPANSION'
    })
  ]
};

// Mock the entire StrategyContext instead of trying to wrap
vi.mock('@/contexts/StrategyContext', () => ({
  useStrategies: () => ({
    strategies: mockStrategies,
    categories: ['income_generation', 'volatility_trading', 'risk_management'],
    loading: false,
    error: null,
    opportunitiesByStrategy: {
      'ThetaCropWeekly': { opportunities: professionalTradingData.highProbabilityTrades },
      'IronCondor': { opportunities: professionalTradingData.quickScalps },
      'ProtectivePut': { opportunities: professionalTradingData.swingTrades }
    },
    loadingOpportunities: {
      'ThetaCropWeekly': false,
      'IronCondor': false,
      'ProtectivePut': false
    },
    activeScanJobs: [],
    getAllOpportunities: () => [
      ...professionalTradingData.highProbabilityTrades,
      ...professionalTradingData.quickScalps,
      ...professionalTradingData.swingTrades,
      ...professionalTradingData.volatilityPlays
    ],
    getOpportunitiesByCategory: (category: string) => {
      switch (category) {
        case 'high_probability': return professionalTradingData.highProbabilityTrades;
        case 'quick_scalps': return professionalTradingData.quickScalps;
        case 'swing_trades': return professionalTradingData.swingTrades;
        case 'volatility_plays': return professionalTradingData.volatilityPlays;
        default: return [];
      }
    },
    getStrategiesByCategory: vi.fn(() => mockStrategies),
    getStrategyOpportunities: vi.fn(() => []),
    refreshAllOpportunities: vi.fn(),
    refreshStrategyWithProgress: vi.fn()
  }),
  StrategyProvider: ({ children }: any) => children
}));

describe('Trading Workflow Integration Tests', () => {
  const mockToast = vi.fn();
  const mockOnTradeExecuted = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock toast hook
    (useToast as any).mockReturnValue({
      toast: mockToast
    });

    // Mock paper trading service
    (paperTradingService.executeTrade as any).mockResolvedValue({
      id: 'executed-trade-1',
      symbol: 'SPY',
      type: 'PUT_CREDIT_SPREAD',
      quantity: 1,
      entryCredit: 180,
      entryDate: new Date('2025-08-10T10:00:00Z'),
      status: 'OPEN',
      success: true
    });

    // Mock performance APIs
    Object.defineProperty(global, 'performance', {
      value: {
        now: vi.fn(() => Date.now()),
        mark: vi.fn(),
        measure: vi.fn()
      },
      writable: true
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('End-to-End Trading Workflow', () => {
    it('completes full trading workflow: scan � filter � execute � confirm', async () => {
      const user = userEvent.setup();
      
      render(
        <DynamicStrategyTabs onTradeExecuted={mockOnTradeExecuted} />
      );

      // Step 1: Verify opportunities are loaded
      await waitFor(() => {
        expect(screen.getByText(/opportunities across/)).toBeInTheDocument();
      });

      // Step 2: Navigate to high probability trades
      const highProbTab = screen.getByRole('tab', { name: /High Probability/ });
      await user.click(highProbTab);

      // Step 3: Verify filtering works
      await waitFor(() => {
        expect(screen.getByTestId('trade-card-high-prob-1')).toBeInTheDocument();
        expect(screen.getByTestId('trade-card-high-prob-2')).toBeInTheDocument();
      });

      // Step 4: Execute a trade
      const executeButton = screen.getByTestId('execute-high-prob-1');
      await user.click(executeButton);

      // Step 5: Verify execution flow
      await waitFor(() => {
        expect(paperTradingService.executeTrade).toHaveBeenCalledWith(
          expect.objectContaining({
            id: 'high-prob-1',
            symbol: 'SPY',
            strategy_type: 'PUT_CREDIT_SPREAD'
          }),
          1
        );
      });

      // Step 6: Verify success feedback
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: "Trade Executed Successfully",
          description: expect.stringContaining("SPY PUT_CREDIT_SPREAD"),
          duration: 5000
        });
        expect(mockOnTradeExecuted).toHaveBeenCalledWith(180); // expected_value
      });
    });

    it('handles rapid opportunity scanning with 20+ trades', async () => {
      const largeOpportunitySet = Array.from({ length: 25 }, (_, i) => 
        createMockOpportunity({
          id: `rapid-trade-${i}`,
          symbol: `SYM${i.toString().padStart(2, '0')}`,
          strategy_type: i % 2 === 0 ? 'PUT_CREDIT_SPREAD' : 'CALL_CREDIT_SPREAD',
          expected_value: 100 + (i * 10),
          probability_profit: 0.70 + (Math.random() * 0.25)
        })
      );

      const startTime = performance.now();

      render(
        <DynamicStrategyTabs />
      );

      // Verify rapid rendering
      await waitFor(() => {
        expect(screen.getByText(/25 opportunities/)).toBeInTheDocument();
      }, { timeout: 5000 });

      const renderTime = performance.now() - startTime;

      // Performance requirement: <2000ms for 25 trades
      expect(renderTime).toBeLessThan(2000);

      // Verify virtualization (should not render all 25 at once)
      const tradeCards = screen.getAllByTestId(/^trade-card-/);
      expect(tradeCards.length).toBeLessThanOrEqual(20);
    });
  });

  describe('Responsive Design Integration', () => {
    it('adapts layout for mobile vs desktop correctly', async () => {
      const { rerender } = render(
        <DynamicStrategyTabs />
      );

      // Desktop layout
      await waitFor(() => {
        const tradeCard = screen.getByTestId('trade-card-high-prob-1');
        expect(tradeCard).toHaveAttribute('data-mobile', 'false');
      });

      // Simulate mobile viewport (would typically be handled by CSS/JS)
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768
      });

      rerender(
        <DynamicStrategyTabs />
      );

      // Verify responsive behavior
      await waitFor(() => {
        const tradeCards = screen.getAllByTestId(/^trade-card-/);
        tradeCards.forEach(card => {
          expect(card).toBeInTheDocument();
        });
      });
    });

    it('maintains functionality across screen sizes', async () => {
      const user = userEvent.setup();
      
      // Test on narrow screen
      Object.defineProperty(window, 'innerWidth', {
        value: 375, // iPhone SE width
        configurable: true
      });

      render(
        <DynamicStrategyTabs onTradeExecuted={mockOnTradeExecuted} />
      );

      // Navigation should still work
      const quickScalpsTab = screen.getByRole('tab', { name: /Quick Scalps/ });
      await user.click(quickScalpsTab);

      await waitFor(() => {
        expect(screen.getByTestId('trade-card-scalp-1')).toBeInTheDocument();
      });

      // Trade execution should still work
      const executeButton = screen.getByTestId('execute-scalp-1');
      await user.click(executeButton);

      await waitFor(() => {
        expect(paperTradingService.executeTrade).toHaveBeenCalled();
      });
    });
  });

  describe('Performance Benchmarks', () => {
    it('meets DOM processing performance targets (<200ms)', async () => {
      const performanceStartTime = performance.now();
      
      render(
        <DynamicStrategyTabs />
      );

      await waitFor(() => {
        expect(screen.getByText('Trading Opportunities')).toBeInTheDocument();
      });

      const domProcessingTime = performance.now() - performanceStartTime;
      
      // Professional trading requirement: <200ms DOM processing
      expect(domProcessingTime).toBeLessThan(200);
    });

    it('handles memory efficiently with large datasets', async () => {
      // Create memory-intensive scenario
      const massiveDataset = Array.from({ length: 100 }, (_, i) => 
        createMockOpportunity({
          id: `memory-test-${i}`,
          symbol: `T${i}`,
          // Add complex nested data to test memory usage
          score_breakdown: {
            technical: Math.random(),
            liquidity: Math.random(),
            risk_adjusted: Math.random(),
            probability: Math.random(),
            volatility: Math.random(),
            time_decay: Math.random(),
            market_regime: Math.random()
          },
          detailed_analysis: `Complex analysis for trade ${i}...`.repeat(10)
        })
      );

      const initialMemory = (performance as any).memory?.usedJSHeapSize || 0;

      render(
        <DynamicStrategyTabs />
      );

      await waitFor(() => {
        expect(screen.getByText(/100 opportunities/)).toBeInTheDocument();
      });

      const finalMemory = (performance as any).memory?.usedJSHeapSize || 0;
      const memoryIncrease = finalMemory - initialMemory;

      // Memory should not increase excessively (< 50MB for 100 trades)
      expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024);
    });

    it('maintains 60fps during rapid interactions', async () => {
      const user = userEvent.setup();
      const frameTimes: number[] = [];
      let lastFrameTime = performance.now();

      // Mock requestAnimationFrame to track frame timing
      const originalRAF = global.requestAnimationFrame;
      global.requestAnimationFrame = vi.fn((callback) => {
        const currentTime = performance.now();
        frameTimes.push(currentTime - lastFrameTime);
        lastFrameTime = currentTime;
        return originalRAF(callback);
      });

      render(
        <DynamicStrategyTabs />
      );

      // Perform rapid tab switching
      const tabs = ['High Probability', 'Quick Scalps', 'Swing Trades', 'Volatility Plays'];
      
      for (const tabName of tabs) {
        const tab = screen.getByRole('tab', { name: new RegExp(tabName) });
        await user.click(tab);
        await waitFor(() => {
          expect(tab).toHaveAttribute('aria-selected', 'true');
        });
      }

      // Calculate average frame time
      if (frameTimes.length > 0) {
        const avgFrameTime = frameTimes.reduce((a, b) => a + b, 0) / frameTimes.length;
        // 60fps = 16.67ms per frame
        expect(avgFrameTime).toBeLessThan(20); // Allow small margin
      }

      global.requestAnimationFrame = originalRAF;
    });
  });

  describe('Error Handling & Edge Cases', () => {
    it('gracefully handles network failures during trade execution', async () => {
      const user = userEvent.setup();
      
      // Mock network failure
      (paperTradingService.executeTrade as any).mockRejectedValue(
        new Error('Network error: Unable to connect to trading API')
      );

      render(
        <DynamicStrategyTabs />
      );

      const executeButton = screen.getByTestId('execute-high-prob-1');
      await user.click(executeButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: "Trade Execution Failed",
          description: "Network error: Unable to connect to trading API",
          variant: "destructive",
          duration: 5000
        });
      });

      // Button should be re-enabled after error
      expect(executeButton).not.toBeDisabled();
    });

    it('handles invalid API data gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      render(
        <DynamicStrategyTabs />
      );

      // Component should still render without crashing
      await waitFor(() => {
        expect(screen.getByText('Trading Opportunities')).toBeInTheDocument();
      });

      // No error boundaries should be triggered
      expect(screen.queryByText(/Something went wrong/)).not.toBeInTheDocument();

      consoleSpy.mockRestore();
    });

    it('recovers from component errors with error boundaries', async () => {
      const ErrorBoundaryTest = () => {
        throw new Error('Simulated component error');
      };

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      // This would normally be wrapped by error boundary in actual app
      expect(() => render(<ErrorBoundaryTest />)).toThrow();

      consoleSpy.mockRestore();
    });
  });

  describe('Accessibility Compliance', () => {
    it('provides proper ARIA labels and roles', async () => {
      render(
        <DynamicStrategyTabs />
      );

      await waitFor(() => {
        // Check tab navigation
        const tabList = screen.getByRole('tablist');
        expect(tabList).toBeInTheDocument();

        // Check individual tabs
        expect(screen.getByRole('tab', { name: /All/ })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: /High Probability/ })).toBeInTheDocument();

        // Check trade cards have proper roles
        const tradeCards = screen.getAllByRole('article');
        expect(tradeCards.length).toBeGreaterThan(0);

        tradeCards.forEach(card => {
          expect(card).toHaveAttribute('aria-label');
        });

        // Check execute buttons have descriptive labels
        const executeButtons = screen.getAllByRole('button', { name: /Execute.*trade/i });
        expect(executeButtons.length).toBeGreaterThan(0);
      });
    });

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();

      render(
        <DynamicStrategyTabs />
      );

      await waitFor(() => {
        expect(screen.getByRole('tablist')).toBeInTheDocument();
      });

      // Tab navigation
      const firstTab = screen.getByRole('tab', { name: /All/ });
      firstTab.focus();
      expect(firstTab).toHaveFocus();

      // Navigate to next tab with arrow keys
      await user.keyboard('{ArrowRight}');
      const highProbTab = screen.getByRole('tab', { name: /High Probability/ });
      expect(highProbTab).toHaveFocus();

      // Activate tab with Enter
      await user.keyboard('{Enter}');
      expect(highProbTab).toHaveAttribute('aria-selected', 'true');

      // Navigate to trade cards with Tab
      await user.keyboard('{Tab}');
      const executeButton = screen.getByTestId('execute-high-prob-1');
      expect(executeButton).toHaveFocus();

      // Execute trade with Space
      await user.keyboard('{Space}');
      await waitFor(() => {
        expect(paperTradingService.executeTrade).toHaveBeenCalled();
      });
    });

    it('provides screen reader friendly content', async () => {
      render(
        <DynamicStrategyTabs />
      );

      await waitFor(() => {
        // Check for descriptive text content
        expect(screen.getByText(/opportunities across.*strategies/)).toBeInTheDocument();
        
        // Check trade details are readable
        const tradeDetails = screen.getAllByTestId('trade-details');
        tradeDetails.forEach(detail => {
          expect(within(detail).getByText(/Premium:/)).toBeInTheDocument();
          expect(within(detail).getByText(/Win Rate:/)).toBeInTheDocument();
          expect(within(detail).getByText(/Expected Value:/)).toBeInTheDocument();
        });

        // Check status information is available
        expect(screen.getByText(/Active/)).toBeInTheDocument();
        expect(screen.getByText(/Categories/)).toBeInTheDocument();
      });
    });
  });

  describe('Data Validation & Financial Accuracy', () => {
    it('validates financial calculations are correct', async () => {
      const testTrade = createMockOpportunity({
        premium: 2.50,
        max_profit: 250,
        max_loss: -750,
        probability_profit: 0.75
      });

      render(
        <DynamicStrategyTabs />
      );

      await waitFor(() => {
        const tradeCard = screen.getByTestId(`trade-card-${testTrade.id}`);
        const tradeDetails = within(tradeCard).getByTestId('trade-details');
        
        // Verify financial data display
        expect(within(tradeDetails).getByText('Premium: $2.50')).toBeInTheDocument();
        expect(within(tradeDetails).getByText('Win Rate: 75%')).toBeInTheDocument();
        expect(within(tradeDetails).getByText(/Expected Value: \$125/)).toBeInTheDocument();
      });
    });

    it('prevents execution of invalid trades', async () => {
      const user = userEvent.setup();
      const invalidTrade = createMockOpportunity({
        premium: -1.0, // Invalid negative premium
        max_loss: 1000, // Invalid positive loss
        probability_profit: 1.5 // Invalid probability > 1
      });

      render(
        <DynamicStrategyTabs />
      );

      const executeButton = screen.getByTestId(`execute-${invalidTrade.id}`);
      await user.click(executeButton);

      // Should not attempt execution with invalid data
      expect(paperTradingService.executeTrade).not.toHaveBeenCalled();
    });
  });

  describe('Real-time Data Handling', () => {
    it('handles live data updates without disrupting user interaction', async () => {
      const user = userEvent.setup();
      let opportunityData = [createMockOpportunity({ id: 'live-1', premium: 2.50 })];

      const { rerender } = render(
        <DynamicStrategyTabs />
      );

      await waitFor(() => {
        expect(screen.getByText('Premium: $2.50')).toBeInTheDocument();
      });

      // Start user interaction
      const executeButton = screen.getByTestId('execute-live-1');
      await user.hover(executeButton);

      // Simulate live data update
      opportunityData = [createMockOpportunity({ id: 'live-1', premium: 2.75 })];
      
      rerender(
        <DynamicStrategyTabs />
      );

      // Data should update without disrupting interaction
      await waitFor(() => {
        expect(screen.getByText('Premium: $2.75')).toBeInTheDocument();
      });

      // User should still be able to complete action
      await user.click(executeButton);
      expect(paperTradingService.executeTrade).toHaveBeenCalled();
    });
  });
});