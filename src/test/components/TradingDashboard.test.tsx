import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import TradingDashboard from '@/components/TradingDashboard'
import { ThemeProvider } from '@/contexts/ThemeContext'

// Mock the child components that depend on external APIs
vi.mock('@/components/RealTimeChart', () => ({
  RealTimeChart: () => <div data-testid="real-time-chart">Real Time Chart</div>
}))

vi.mock('@/components/EnhancedTradeExecutor', () => ({
  EnhancedTradeExecutor: () => <div data-testid="trade-executor">Trade Executor</div>
}))

vi.mock('@/components/RSICouponCard', () => ({
  RSICouponCard: () => <div data-testid="rsi-coupon-card">RSI Coupon Card</div>
}))

vi.mock('@/hooks/useRealTimeData', () => ({
  useRealTimeData: () => ({
    marketData: {
      price: 450.50,
      volume: 1000000,
      change: 2.50,
      changePercent: 0.56,
      timestamp: new Date()
    },
    performanceData: [],
    accountValue: 100000,
    isMarketOpen: true,
    addPerformancePoint: vi.fn(),
    signals: {
      market_bias: 'BULLISH',
      confidence: 0.75,
      signals: {},
      recommendation: {
        action: 'BUY',
        reason: 'Strong bullish signals'
      }
    },
    connectionStatus: 'connected',
    usingWebSocket: true,
    wsConnected: true
  })
}))

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <ThemeProvider>
        {component}
      </ThemeProvider>
    </BrowserRouter>
  )
}

describe('TradingDashboard', () => {
  beforeEach(() => {
    // Mock fetch for API calls
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        account_balance: 100000,
        buying_power: 80000,
        total_pnl: 5000
      })
    })
  })

  it('renders main dashboard tabs', () => {
    renderWithProviders(<TradingDashboard />)
    
    expect(screen.getByText('Overview')).toBeInTheDocument()
    expect(screen.getByText('Sentiment')).toBeInTheDocument()
    expect(screen.getByText('Signals')).toBeInTheDocument()
    expect(screen.getByText('Trades')).toBeInTheDocument()
    expect(screen.getByText('Positions')).toBeInTheDocument()
    expect(screen.getByText('Risk')).toBeInTheDocument()
    expect(screen.getByText('Config')).toBeInTheDocument()
  })

  it('displays market data when available', () => {
    renderWithProviders(<TradingDashboard />)
    
    // Should display the real-time chart component
    expect(screen.getByTestId('real-time-chart')).toBeInTheDocument()
  })

  it('shows account balance section', () => {
    renderWithProviders(<TradingDashboard />)
    
    // Should have account metrics section (with more flexible matching)
    expect(screen.getByText(/Account/i)).toBeInTheDocument()
  })

  it('renders without crashing when data is loading', () => {
    renderWithProviders(<TradingDashboard />)
    
    // Component should render even when data is loading
    expect(screen.getByRole('tablist')).toBeInTheDocument()
  })
})