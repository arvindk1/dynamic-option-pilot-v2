
import { useState, useEffect, useCallback } from 'react';
import { yahooFinanceService } from '@/services/yahooFinanceAPI';
import { tradingService } from '@/services/paperTrading';
import { useWebSocket, useMarketData, useTradingSignals } from './useWebSocket';

interface RealTimeData {
  price: number | null;
  volume: number | null;
  change: number | null;
  changePercent: number | null;
  timestamp: Date;
}

interface PerformanceData {
  date: string;
  pnl: number;
  cumulative: number;
}

interface PerformanceDataPoint {
  date: string;
  pnl: number;
  cumulative_pnl: number;
}

export const useRealTimeData = () => {
  // Move all hooks to top level (React rules compliance)
  const { state: wsState, connect: wsConnect } = useWebSocket({
    autoConnect: false, // Disable WebSocket auto-connect for v2.0 
    symbols: ['SPY'],
    onError: (error) => {
      console.warn('WebSocket error, falling back to polling:', error);
    }
  });
  
  const spyData = useMarketData('SPY');
  const tradingSignalsResult = useTradingSignals();
  
  // Process signals data
  const signals = tradingSignalsResult?.signals || {
    market_bias: 'NEUTRAL',
    confidence: 0.5,
    signals: {},
    recommendation: {
      action: 'HOLD',
      reason: 'Market analysis in progress'
    }
  };
  
  const [marketData, setMarketData] = useState<RealTimeData>({
    price: null,
    volume: null,
    change: null,
    changePercent: null,
    timestamp: new Date()
  });

  const [performanceData, setPerformanceData] = useState<PerformanceData[]>([]);
  const [accountValue, setAccountValue] = useState(0);
  const [isMarketOpen, setIsMarketOpen] = useState(false);
  const [usingWebSocket, setUsingWebSocket] = useState(false);

  // Update market data from WebSocket
  useEffect(() => {
    if (spyData && wsState.connected) {
      setMarketData({
        price: spyData.price,
        volume: spyData.volume,
        change: spyData.change || 0,
        changePercent: spyData.change_percent || 0,
        timestamp: new Date(spyData.timestamp)
      });
      
      // Check if market is open based on data freshness
      const dataAge = Date.now() - new Date(spyData.timestamp).getTime();
      setIsMarketOpen(dataAge < 300000); // Consider fresh if less than 5 minutes old
      setUsingWebSocket(true);
    }
  }, [spyData, wsState.connected]);

  // Fallback to polling if WebSocket fails - Use simulated data when backend unavailable
  const updateMarketDataPolling = useCallback(async () => {
    if (wsState.connected && usingWebSocket) {
      return; // Skip polling if WebSocket is working
    }

    try {
      // Try backend API first - use correct v2 endpoint
      const response = await fetch('http://localhost:8000/market-data/SPY');
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data && data.price) {
        setMarketData({
          price: data.price,
          volume: data.volume || 0,
          change: data.change || 0,
          changePercent: (data.change_percent || 0) / 100,
          timestamp: new Date(data.timestamp || Date.now())
        });
        
        const dataAge = Date.now() - new Date(data.timestamp || Date.now()).getTime();
        setIsMarketOpen(dataAge < 300000);
        setUsingWebSocket(false);
      } else {
        throw new Error('No market data available from backend API');
      }
    } catch (error) {
      // If all fallbacks fail, set data to null/empty
      setMarketData({
        price: null,
        volume: null,
        change: null,
        changePercent: null,
        timestamp: new Date()
      });
      setIsMarketOpen(false);
      setUsingWebSocket(false);
    }
  }, [wsState.connected, usingWebSocket]);

  // Load account data with fallback
  const loadAccountData = useCallback(async () => {
    try {
      const metrics = await tradingService.getAccountMetrics();
      setAccountValue(metrics.account_balance || 0);
    } catch (error) {
      console.error('Failed to load account data:', error);
      // Fallback to demo account value
      setAccountValue(100000); // $100k demo account
    }
  }, []);

  // Load performance data with fallback
  const loadPerformanceData = useCallback(async () => {
    try {
      const response = await fetch('/api/dashboard/performance?days=30');
      if (response.ok) {
        const data = await response.json();
        if (data.data && Array.isArray(data.data)) {
          setPerformanceData(data.data.map((point: PerformanceDataPoint) => ({
            date: point.date,
            pnl: point.pnl,
            cumulative: point.cumulative_pnl
          })));
        }
      }
    } catch (error) {
      console.error('Failed to load performance data:', error);
      // Fallback to demo performance data
      const demoData = [];
      const today = new Date();
      for (let i = 29; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        const dailyPnl = (Math.random() - 0.5) * 500; // Random P&L between -250 and 250
        const cumulative = i === 29 ? dailyPnl : demoData[demoData.length - 1]?.cumulative + dailyPnl || dailyPnl;
        
        demoData.push({
          date: date.toISOString().slice(0, 10),
          pnl: parseFloat(dailyPnl.toFixed(2)),
          cumulative: parseFloat(cumulative.toFixed(2))
        });
      }
      setPerformanceData(demoData);
    }
  }, []);
  
  const addPerformancePoint = useCallback((pnl: number) => {
    const currentDate = new Date().toISOString().slice(0, 7);
    setPerformanceData(prev => {
      const lastPoint = prev[prev.length - 1] || { cumulative: 0 };
      const newPoint = {
        date: currentDate,
        pnl,
        cumulative: lastPoint.cumulative + pnl
      };
      
      // Update account value
      setAccountValue(prev => prev + pnl);
      
      return [...prev, newPoint];
    });
  }, []);

  // Load initial data and set up polling
  useEffect(() => {
    // Load account data and performance data
    loadAccountData();
    loadPerformanceData();
    
    // Initial market data fetch
    updateMarketDataPolling();
    
    // Update every 2 minutes (reduced from 30 seconds to minimize API calls)
    // But skip if WebSocket is working
    const interval = setInterval(() => {
      if (!wsState.connected || !usingWebSocket) {
        updateMarketDataPolling();
      }
    }, 120000);
    
    // Reload account data periodically (reduced frequency)
    const accountInterval = setInterval(() => {
      loadAccountData();
    }, 600000); // Every 10 minutes (reduced from 5)
    
    // Reload performance data less frequently
    const performanceInterval = setInterval(() => {
      loadPerformanceData();
    }, 600000); // Every 10 minutes (reduced from 5)
    
    return () => {
      clearInterval(interval);
      clearInterval(accountInterval);
      clearInterval(performanceInterval);
    };
  }, [updateMarketDataPolling, loadAccountData, loadPerformanceData, wsState.connected, usingWebSocket]);

  // WebSocket reconnection disabled for v2.0 - prevents error spam

  return {
    marketData,
    performanceData,
    accountValue,
    isMarketOpen,
    addPerformancePoint,
    signals,
    // Additional WebSocket-related info
    connectionStatus: wsState.status,
    usingWebSocket,
    wsConnected: wsState.connected
  };
};
