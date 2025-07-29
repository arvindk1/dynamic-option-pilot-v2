import { RealTradingService } from '@/services/paperTrading'

const mockFetch = (url: string | Request | undefined, options?: RequestInit) => {
  const urlString = typeof url === 'string' ? url : url?.url || ''

  if (urlString.includes('/api/trading/execute') && options?.body?.includes('FAIL')) {
    return Promise.resolve({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: async () => ({ detail: 'Something went wrong' })
    } as Response)
  }
  
  if (urlString.includes('/api/dashboard/metrics')) {
    return Promise.resolve({
      ok: true,
      json: async () => ({
        account_balance: 100000,
        buying_power: 80000,
        total_pnl: 5000,
        today_pnl: 250,
        open_positions: 3
      })
    } as Response)
  }
  if (urlString.includes('/api/positions/sync')) {
    return Promise.resolve({
      ok: true,
      json: async () => ({
        message: 'Positions synced successfully',
        positions_updated: 5,
        success: true
      })
    } as Response)
  }
  if (urlString.includes('/api/positions')) {
    return Promise.resolve({
      ok: true,
      json: async () => ([]) // Return empty array for positions
    } as Response)
  }
  if (urlString.includes('/api/trading/execute')) {
    return Promise.resolve({
      ok: true,
      json: async () => ({
        id: '123',
        symbol: 'SPY',
        type: 'PUT',
        shortStrike: 440,
        longStrike: 435,
        quantity: 1,
        entryCredit: 1.50,
        entryDate: new Date(),
        expiration: new Date(),
        status: 'OPEN'
      })
    } as Response)
  }
  
  return Promise.resolve({
    ok: true,
    json: async () => ({})
  } as Response)
}

describe('RealTradingService', () => {
  let service: RealTradingService
  
  beforeEach(() => {
    global.fetch = vi.fn(mockFetch)
    
    // Clear any existing intervals
    vi.clearAllTimers()
    vi.useFakeTimers()
    
    service = new RealTradingService()
  })

  afterEach(() => {
    vi.clearAllMocks()
    vi.clearAllTimers()
    vi.useRealTimers()
  })

  describe('executeTrade', () => {
    it('should execute a trade successfully', async () => {
      const spread = {
        id: '123',
        symbol: 'SPY',
        strategy_type: 'put_credit_spread',
        option_type: 'PUT',
        strike: 440,
        short_strike: 440,
        long_strike: 435,
        expiration: '2025-02-21',
        days_to_expiration: 30,
        premium: 1.50
      }

      const result = await service.executeTrade(spread, 1)
      
      expect(result).toBeDefined()
      expect(result.symbol).toBe('SPY')
      expect(result.type).toBe('PUT')
    })

    it('should handle API errors gracefully', async () => {
      const spread = {
        id: 'FAIL', // Special ID to trigger error in mock
        symbol: 'SPY',
        strategy_type: 'put_credit_spread',
        option_type: 'PUT',
        strike: 440,
        short_strike: 440,
        long_strike: 435,
        expiration: '2025-02-21',
        days_to_expiration: 30,
        premium: 1.50
      }

      await expect(service.executeTrade(spread, 1)).rejects.toThrow()
    })
  })

  describe('getAccountMetrics', () => {
    it('should fetch account metrics successfully', async () => {
      const result = await service.getAccountMetrics()
      
      expect(result.account_balance).toBe(100000)
    })
  })

  describe('syncPositions', () => {
    it('should sync positions successfully', async () => {
      const result = await service.syncPositions()
      
      expect(result.success).toBe(true)
    })
  })

  describe('trade management', () => {
    it('should return empty trades list initially', () => {
      const trades = service.getTrades()
      expect(trades).toEqual([])
    })

    it('should return empty open trades initially', () => {
      const openTrades = service.getOpenTrades()
      expect(openTrades).toEqual([])
    })
  })
})
