import { renderHook, act } from '@testing-library/react'
import { useRealTimeData } from '@/hooks/useRealTimeData'

// Mock the dependencies
vi.mock('@/services/yahooFinanceAPI', () => ({
  yahooFinanceService: {
    getQuote: vi.fn().mockResolvedValue({
      price: 450.50,
      volume: 1000000,
      change: 2.50,
      changePercent: 0.56
    })
  }
}))

vi.mock('@/services/paperTrading', () => ({
  tradingService: {
    getAccountMetrics: vi.fn().mockResolvedValue({
      account_balance: 100000,
      buying_power: 80000,
      total_pnl: 5000
    })
  }
}))

vi.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    state: { connected: false, status: 'disconnected' },
    connect: vi.fn()
  }),
  useMarketData: () => null,
  useTradingSignals: () => null
}))

describe('useRealTimeData', () => {
  beforeEach(() => {
    // Mock fetch for performance data
    global.fetch = vi.fn().mockImplementation((url) => {
      if (url.includes('/api/dashboard/performance')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            data: [
              { date: '2025-01-18', pnl: 100, cumulative_pnl: 100 },
              { date: '2025-01-19', pnl: 150, cumulative_pnl: 250 }
            ]
          })
        })
      }
      if (url.includes('/api/market/quote')) {
        return Promise.resolve({
          ok: false,
          status: 404,
          statusText: 'Not Found'
        })
      }
      return Promise.reject(new Error('Unknown URL'))
    })
  })

  it('initializes with default values', () => {
    let result: any;
    act(() => {
      result = renderHook(() => useRealTimeData()).result;
    });
    
    expect(result.current.marketData).toBeDefined()
    expect(result.current.performanceData).toEqual([])
    expect(result.current.accountValue).toEqual(0)
    expect(result.current.isMarketOpen).toBe(false)
  })

  it('provides market data interface', () => {
    let result: any;
    act(() => {
      result = renderHook(() => useRealTimeData()).result;
    });
    
    expect(result.current.marketData).toHaveProperty('price')
    expect(result.current.marketData).toHaveProperty('volume')
    expect(result.current.marketData).toHaveProperty('change')
    expect(result.current.marketData).toHaveProperty('changePercent')
    expect(result.current.marketData).toHaveProperty('timestamp')
  })

  it('provides trading signals with default values', () => {
    let result: any;
    act(() => {
      result = renderHook(() => useRealTimeData()).result;
    });
    
    expect(result.current.signals).toBeDefined()
    expect(result.current.signals.market_bias).toBe('NEUTRAL')
    expect(result.current.signals.confidence).toBe(0.5)
  })

  it('provides performance tracking functions', () => {
    let result: any;
    act(() => {
      result = renderHook(() => useRealTimeData()).result;
    });
    
    expect(typeof result.current.addPerformancePoint).toBe('function')
  })

  it('provides connection status information', () => {
    let result: any;
    act(() => {
      result = renderHook(() => useRealTimeData()).result;
    });
    
    expect(result.current.connectionStatus).toBeDefined()
    expect(typeof result.current.usingWebSocket).toBe('boolean')
    expect(typeof result.current.wsConnected).toBe('boolean')
  })
})