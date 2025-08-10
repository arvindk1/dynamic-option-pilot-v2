import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { RealTradingService, tradingService } from '@/services/paperTrading';

// Mock global fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock data fixtures
const mockTradeOpportunity = {
  id: 'test-opportunity-1',
  symbol: 'SPY',
  strategy_type: 'COVERED_CALL',
  option_type: 'CALL' as const,
  strike: 450,
  short_strike: 450,
  long_strike: 455,
  expiration: '2025-08-17',
  days_to_expiration: 7,
  premium: 2.50
};

const mockPositionData = [
  {
    id: 1,
    order_id: 'order-123',
    symbol: 'SPY',
    type: 'COVERED_CALL',
    short_strike: 450,
    long_strike: 455,
    quantity: 1,
    entry_price: 2.50,
    entry_date: '2025-08-10T10:00:00Z',
    expiration: '2025-08-17T16:00:00Z',
    status: 'OPEN',
    pnl: 50
  },
  {
    id: 2,
    order_id: 'order-456',
    symbol: 'QQQ',
    spread_type: 'IRON_CONDOR',
    short_strike: 380,
    long_strike: 385,
    quantity: 2,
    entry_credit: 360,
    entry_date: '2025-08-09T14:30:00Z',
    expiration_date: '2025-08-24T16:00:00Z',
    status: 'OPEN',
    current_pnl: -25
  }
];

const mockAccountMetrics = {
  account_balance: 100000,
  buying_power: 80000,
  total_pnl: 5000,
  today_pnl: 250,
  open_positions: 5
};

describe('RealTradingService', () => {
  let service: RealTradingService;

  beforeEach(() => {
    vi.clearAllMocks();
    service = new RealTradingService();
    
    // Setup default successful responses
    mockFetch.mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue({}),
      text: vi.fn().mockResolvedValue(''),
      clone: function() { return this; }
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Trade Execution', () => {
    it('executes trades successfully', async () => {
      const mockExecutionResult = {
        id: 'executed-trade-1',
        symbol: 'SPY',
        type: 'COVERED_CALL',
        shortStrike: 450,
        longStrike: 455,
        quantity: 1,
        entryCredit: 250,
        entryDate: new Date('2025-08-10T10:00:00Z'),
        status: 'OPEN',
        order_id: 'order-789'
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue(mockExecutionResult),
        clone: function() { return this; }
      });

      const result = await service.executeTrade(mockTradeOpportunity, 1);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/trading/execute',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...mockTradeOpportunity,
            quantity: 1
          })
        })
      );

      expect(result.id).toBe('executed-trade-1');
      expect(result.symbol).toBe('SPY');
    });

    it('handles execution errors gracefully', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: vi.fn().mockResolvedValue({
          detail: 'Insufficient buying power'
        }),
        clone: function() { return this; }
      });

      await expect(service.executeTrade(mockTradeOpportunity, 1))
        .rejects.toThrow('HTTP Insufficient buying power');
    });

    it('handles timeout errors', async () => {
      mockFetch.mockImplementation(() => 
        new Promise(resolve => setTimeout(resolve, 25000)) // Longer than timeout
      );

      await expect(service.executeTrade(mockTradeOpportunity, 1))
        .rejects.toThrow('Timeout 20000ms');
    }, 25000);

    it('normalizes position data from API response', async () => {
      const apiResponse = {
        id: 'pos-123',
        symbol: 'SPY',
        spread_type: 'COVERED_CALL',
        short_strike: 450,
        quantity: 1,
        entry_credit: 250,
        entry_date: '2025-08-10T10:00:00Z',
        status: 'open',
        entry_date: '2025-08-10T10:00:00Z'
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue(apiResponse),
        clone: function() { return this; }
      });

      const result = await service.executeTrade(mockTradeOpportunity, 1);

      expect(result.id).toBe('pos-123');
      expect(result.status).toBe('OPEN'); // Normalized to uppercase
      expect(result.entryCredit).toBe(250);
      expect(result.entryDate).toBeInstanceOf(Date);
    });
  });

  describe('Position Management', () => {
    it('loads trades successfully', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue(mockPositionData),
        clone: function() { return this; }
      });

      await service.loadTrades();
      const trades = service.getTrades();

      expect(trades).toHaveLength(2);
      expect(trades[0].symbol).toBe('SPY');
      expect(trades[1].symbol).toBe('QQQ');
    });

    it('filters open trades correctly', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue([
          { ...mockPositionData[0], status: 'OPEN' },
          { ...mockPositionData[1], status: 'CLOSED' }
        ]),
        clone: function() { return this; }
      });

      await service.loadTrades();
      const openTrades = service.getOpenTrades();

      expect(openTrades).toHaveLength(1);
      expect(openTrades[0].status).toBe('OPEN');
    });

    it('handles loading errors gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      mockFetch.mockRejectedValue(new Error('Network error'));

      await service.loadTrades();
      const trades = service.getTrades();

      expect(trades).toHaveLength(0);
      expect(consoleSpy).toHaveBeenCalledWith('Error loading trades:', expect.any(Error));
      
      consoleSpy.mockRestore();
    });

    it('normalizes entry credit calculations', async () => {
      const positionWithEntryPrice = {
        id: 1,
        symbol: 'SPY',
        type: 'CALL',
        quantity: 2,
        entry_price: 3.50, // Per contract
        entry_date: '2025-08-10T10:00:00Z',
        status: 'OPEN'
        // No entry_credit field
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue([positionWithEntryPrice]),
        clone: function() { return this; }
      });

      await service.loadTrades();
      const trades = service.getTrades();

      // Should calculate: 3.50 * 2 * 100 = 700
      expect(trades[0].entryCredit).toBe(700);
    });
  });

  describe('Trade Closing', () => {
    it('closes trades successfully', async () => {
      const closeResponse = {
        message: 'Trade closed successfully',
        cancelled_orders: ['order-123'],
        cancelled_count: 1
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue(closeResponse),
        clone: function() { return this; }
      });

      const result = await service.closeTrade('trade-123', 1.50);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/positions/close/trade-123?exit_price=1.5',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        })
      );

      expect(result.message).toBe('Trade closed successfully');
      expect(result.cancelled_count).toBe(1);
    });

    it('handles closing errors', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        text: vi.fn().mockResolvedValue('Position not found'),
        clone: function() { return this; }
      });

      await expect(service.closeTrade('invalid-trade', 1.50))
        .rejects.toThrow('HTTP 404 Not Found  Position not found');
    });
  });

  describe('Position Synchronization', () => {
    it('syncs positions successfully', async () => {
      const syncResponse = {
        status: 'success',
        message: 'Positions synchronized',
        sync_results: {
          synced_positions: 3
        }
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue(syncResponse),
        clone: function() { return this; }
      });

      const result = await service.syncPositions();

      expect(result.success).toBe(true);
      expect(result.positions_updated).toBe(3);
      expect(result.message).toBe('Positions synchronized');
    });

    it('handles rate limiting', async () => {
      const rateLimitResponse = {
        status: 'rate_limited',
        message: 'Rate limit exceeded, try again later'
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue(rateLimitResponse),
        clone: function() { return this; }
      });

      const result = await service.syncPositions();

      expect(result.success).toBe(false);
      expect(result.rate_limited).toBe(true);
      expect(result.message).toBe('Rate limit exceeded, try again later');
    });
  });

  describe('Account Metrics', () => {
    it('fetches account metrics successfully', async () => {
      const performanceData = {
        data: [
          { t: '2025-08-01', v: 98000 },
          { t: '2025-08-02', v: 99500 },
          { t: '2025-08-03', v: 100000 }
        ]
      };

      // Mock metrics call
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: vi.fn().mockResolvedValue(mockAccountMetrics),
          clone: function() { return this; }
        })
        // Mock performance call
        .mockResolvedValueOnce({
          ok: true,
          json: vi.fn().mockResolvedValue(performanceData),
          clone: function() { return this; }
        });

      const metrics = await service.getAccountMetrics();

      expect(metrics.account_balance).toBe(100000);
      expect(metrics.buying_power).toBe(80000);
      expect(metrics.total_pnl).toBe(5000);
      expect(metrics.performanceHistory).toHaveLength(3);
    });

    it('provides default values when metrics unavailable', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      mockFetch.mockRejectedValue(new Error('API unavailable'));

      const metrics = await service.getAccountMetrics();

      expect(metrics.account_balance).toBe(0);
      expect(metrics.buying_power).toBe(0);
      expect(metrics.total_pnl).toBe(0);
      expect(metrics.today_pnl).toBe(0);
      expect(metrics.open_positions).toBe(0);
      expect(metrics.performanceHistory).toEqual([]);
      
      consoleSpy.mockRestore();
    });
  });

  describe('Subscription System', () => {
    it('notifies listeners when trades update', async () => {
      const listener1 = vi.fn();
      const listener2 = vi.fn();
      
      const unsubscribe1 = service.subscribe(listener1);
      const unsubscribe2 = service.subscribe(listener2);

      mockFetch.mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue(mockPositionData),
        clone: function() { return this; }
      });

      await service.loadTrades();

      expect(listener1).toHaveBeenCalledWith(expect.arrayContaining([
        expect.objectContaining({ symbol: 'SPY' }),
        expect.objectContaining({ symbol: 'QQQ' })
      ]));
      expect(listener2).toHaveBeenCalledWith(expect.arrayContaining([
        expect.objectContaining({ symbol: 'SPY' }),
        expect.objectContaining({ symbol: 'QQQ' })
      ]));

      unsubscribe1();
      unsubscribe2();
    });

    it('handles listener errors gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const faultyListener = vi.fn().mockImplementation(() => {
        throw new Error('Listener error');
      });
      
      service.subscribe(faultyListener);

      mockFetch.mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue(mockPositionData),
        clone: function() { return this; }
      });

      await service.loadTrades();

      expect(faultyListener).toHaveBeenCalled();
      expect(consoleSpy).toHaveBeenCalledWith('Listener error:', expect.any(Error));
      
      consoleSpy.mockRestore();
    });

    it('removes listeners correctly', async () => {
      const listener = vi.fn();
      const unsubscribe = service.subscribe(listener);
      
      unsubscribe();

      mockFetch.mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue(mockPositionData),
        clone: function() { return this; }
      });

      await service.loadTrades();

      expect(listener).not.toHaveBeenCalled();
    });
  });

  describe('Performance & Reliability', () => {
    it('respects timeout settings', async () => {
      const slowResponse = new Promise(resolve => {
        setTimeout(() => resolve({
          ok: true,
          json: vi.fn().mockResolvedValue({}),
          clone: function() { return this; }
        }), 5000);
      });

      mockFetch.mockReturnValue(slowResponse);

      const startTime = Date.now();
      
      await expect(service.loadTrades())
        .rejects.toThrow('Timeout');

      const elapsed = Date.now() - startTime;
      expect(elapsed).toBeLessThan(4000); // Should timeout before 4s
    }, 10000);

    it('handles concurrent requests correctly', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue(mockPositionData),
        clone: function() { return this; }
      });

      // Execute multiple concurrent operations
      const promises = [
        service.loadTrades(),
        service.getAccountMetrics(),
        service.syncPositions()
      ];

      await Promise.all(promises);

      expect(mockFetch).toHaveBeenCalledTimes(4); // loadTrades + metrics + performance + sync
    });
  });

  describe('Integration with Global Service Instance', () => {
    it('provides global service instance', () => {
      expect(tradingService).toBeInstanceOf(RealTradingService);
    });

    it('maintains backward compatibility with paperTradingService', async () => {
      const { paperTradingService } = await import('@/services/paperTrading');
      expect(paperTradingService).toBe(tradingService);
    });
  });
});