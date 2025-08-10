import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { LazyTradeCard } from '@/components/LazyTradeCard';

// Mock the lazy-loaded components
vi.mock('@/components/TradeCard/NewTradeCard', () => ({
  default: ({ trade, onExecute, isExecuting }: any) => (
    <div data-testid="new-trade-card">
      <span>New Trade Card: {trade.symbol}</span>
      <button 
        onClick={() => onExecute(trade)} 
        disabled={isExecuting}
        data-testid="execute-new"
      >
        {isExecuting ? 'Executing...' : 'Execute'}
      </button>
    </div>
  )
}));

vi.mock('@/components/TradeCard/TradeCard', () => ({
  CompactTradeCard: ({ trade, onExecute, isExecuting }: any) => (
    <div data-testid="compact-trade-card">
      <span>Compact Trade Card: {trade.symbol}</span>
      <button 
        onClick={() => onExecute(trade)} 
        disabled={isExecuting}
        data-testid="execute-compact"
      >
        {isExecuting ? 'Executing...' : 'Execute'}
      </button>
    </div>
  )
}));

// Test data fixture
const mockTradeOpportunity = {
  id: 'test-trade-1',
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
  risk_level: 'MEDIUM',
  // Enhanced scoring fields
  overall_score: 0.82,
  quality_tier: 'HIGH' as const,
  confidence_percentage: 85,
  technical_score: 0.78,
  liquidity_score_enhanced: 0.90,
  risk_adjusted_score: 0.75
};

describe('LazyTradeCard', () => {
  const mockOnExecute = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Lazy Loading & Performance', () => {
    it('displays skeleton while loading desktop component', async () => {
      render(
        <LazyTradeCard 
          trade={mockTradeOpportunity}
          onExecute={mockOnExecute}
          isMobile={false}
        />
      );
      
      // Initially shows skeleton - look for the Card component with skeleton structure
      const cardElement = screen.getByRole('article') || screen.getByTestId(/skeleton/) || 
        document.querySelector('.border.border-border\\/50.bg-white');
      expect(cardElement).toBeInTheDocument();
      
      // Wait for lazy component to load
      await waitFor(() => {
        expect(screen.getByTestId('new-trade-card')).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('displays skeleton while loading mobile component', async () => {
      render(
        <LazyTradeCard 
          trade={mockTradeOpportunity}
          onExecute={mockOnExecute}
          isMobile={true}
        />
      );
      
      // Wait for lazy component to load
      await waitFor(() => {
        expect(screen.getByTestId('compact-trade-card')).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('measures loading performance', async () => {
      const startTime = performance.now();
      
      render(
        <LazyTradeCard 
          trade={mockTradeOpportunity}
          onExecute={mockOnExecute}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByTestId('new-trade-card')).toBeInTheDocument();
      });
      
      const endTime = performance.now();
      const loadTime = endTime - startTime;
      
      // Lazy loading should be fast (under 1000ms in test environment)
      expect(loadTime).toBeLessThan(1000);
    });

    it('handles multiple rapid renders without performance issues', async () => {
      const { rerender } = render(
        <LazyTradeCard 
          trade={mockTradeOpportunity}
          onExecute={mockOnExecute}
        />
      );
      
      // Rapidly switch between mobile and desktop
      for (let i = 0; i < 5; i++) {
        rerender(
          <LazyTradeCard 
            trade={mockTradeOpportunity}
            onExecute={mockOnExecute}
            isMobile={i % 2 === 0}
          />
        );
      }
      
      // Should eventually settle on the last render
      await waitFor(() => {
        expect(screen.getByTestId('new-trade-card')).toBeInTheDocument();
      });
    });
  });

  describe('Component Selection Logic', () => {
    it('renders NewTradeCard for desktop', async () => {
      render(
        <LazyTradeCard 
          trade={mockTradeOpportunity}
          onExecute={mockOnExecute}
          isMobile={false}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByTestId('new-trade-card')).toBeInTheDocument();
        expect(screen.queryByTestId('compact-trade-card')).not.toBeInTheDocument();
      });
    });

    it('renders CompactTradeCard for mobile', async () => {
      render(
        <LazyTradeCard 
          trade={mockTradeOpportunity}
          onExecute={mockOnExecute}
          isMobile={true}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByTestId('compact-trade-card')).toBeInTheDocument();
        expect(screen.queryByTestId('new-trade-card')).not.toBeInTheDocument();
      });
    });

    it('defaults to desktop component when isMobile not specified', async () => {
      render(
        <LazyTradeCard 
          trade={mockTradeOpportunity}
          onExecute={mockOnExecute}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByTestId('new-trade-card')).toBeInTheDocument();
      });
    });
  });

  describe('Props Propagation', () => {
    it('passes trade data correctly to NewTradeCard', async () => {
      render(
        <LazyTradeCard 
          trade={mockTradeOpportunity}
          onExecute={mockOnExecute}
          isMobile={false}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByText(`New Trade Card: ${mockTradeOpportunity.symbol}`)).toBeInTheDocument();
      });
    });

    it('passes trade data correctly to CompactTradeCard', async () => {
      render(
        <LazyTradeCard 
          trade={mockTradeOpportunity}
          onExecute={mockOnExecute}
          isMobile={true}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByText(`Compact Trade Card: ${mockTradeOpportunity.symbol}`)).toBeInTheDocument();
      });
    });

    it('passes onExecute callback correctly', async () => {
      const user = userEvent.setup();
      
      render(
        <LazyTradeCard 
          trade={mockTradeOpportunity}
          onExecute={mockOnExecute}
          isMobile={false}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByTestId('new-trade-card')).toBeInTheDocument();
      });
      
      const executeButton = screen.getByTestId('execute-new');
      await user.click(executeButton);
      
      expect(mockOnExecute).toHaveBeenCalledWith(mockTradeOpportunity);
    });

    it('passes isExecuting state correctly', async () => {
      render(
        <LazyTradeCard 
          trade={mockTradeOpportunity}
          onExecute={mockOnExecute}
          isExecuting={true}
          isMobile={false}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByText('Executing...')).toBeInTheDocument();
        expect(screen.getByTestId('execute-new')).toBeDisabled();
      });
    });
  });

  describe('Memory Management', () => {
    it('cleans up resources when unmounted', async () => {
      const { unmount } = render(
        <LazyTradeCard 
          trade={mockTradeOpportunity}
          onExecute={mockOnExecute}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByTestId('new-trade-card')).toBeInTheDocument();
      });
      
      // Unmount should not cause memory leaks
      unmount();
      
      // No assertions needed - just ensure unmount doesn't throw
    });

    it('handles rapid mount/unmount cycles', async () => {
      for (let i = 0; i < 3; i++) {
        const { unmount } = render(
          <LazyTradeCard 
            trade={mockTradeOpportunity}
            onExecute={mockOnExecute}
          />
        );
        
        // Don't wait for full load before unmounting
        unmount();
      }
      
      // Final render should still work
      render(
        <LazyTradeCard 
          trade={mockTradeOpportunity}
          onExecute={mockOnExecute}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByTestId('new-trade-card')).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('handles extremely large trade datasets', async () => {
      const largeTradeData = {
        ...mockTradeOpportunity,
        // Add many optional fields to test rendering performance
        score_breakdown: {
          technical: 0.85,
          liquidity: 0.90,
          risk_adjusted: 0.75,
          probability: 0.80,
          volatility: 0.70,
          time_decay: 0.88,
          market_regime: 0.82
        }
      };
      
      const startTime = performance.now();
      
      render(
        <LazyTradeCard 
          trade={largeTradeData}
          onExecute={mockOnExecute}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByTestId('new-trade-card')).toBeInTheDocument();
      });
      
      const endTime = performance.now();
      
      // Should still load reasonably fast even with large datasets
      expect(endTime - startTime).toBeLessThan(1000);
    });

    it('handles minimal trade data', async () => {
      // Test with minimal required data
      const minimalTrade = {
        id: 'minimal-trade',
        symbol: 'TEST',
        strategy_type: 'CALL',
        expiration: '2025-08-17',
        days_to_expiration: 7,
        premium: 1.0,
        max_loss: -100,
        max_profit: 100,
        probability_profit: 0.5,
        expected_value: 0,
        delta: 0.3,
        liquidity_score: 0.5,
        underlying_price: 100,
        bias: 'NEUTRAL',
        rsi: 50,
        trade_setup: 'Basic test',
        risk_level: 'LOW'
      };
      
      render(
        <LazyTradeCard 
          trade={minimalTrade as any}
          onExecute={mockOnExecute}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByTestId('new-trade-card')).toBeInTheDocument();
      });
    });
  });
});