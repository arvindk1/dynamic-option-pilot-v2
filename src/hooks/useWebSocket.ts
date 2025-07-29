import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  webSocketService, 
  ConnectionStatus, 
  MarketDataUpdate, 
  OptionChainUpdate, 
  TradingSignals, 
  PositionUpdate 
} from '../services/WebSocketService';

export interface UseWebSocketOptions {
  autoConnect?: boolean;
  symbols?: string[];
  onError?: (error: Error | string) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export interface WebSocketState {
  status: ConnectionStatus;
  connected: boolean;
  lastHeartbeat: Date | null;
  connectionId: string | null;
  error: string | null;
}

export interface UseWebSocketReturn {
  // Connection state
  state: WebSocketState;
  
  // Connection methods
  connect: () => Promise<void>;
  disconnect: () => void;
  
  // Subscription methods
  subscribe: (symbol: string) => Promise<void>;
  unsubscribe: (symbol: string) => Promise<void>;
  
  // Data getters
  marketData: Map<string, MarketDataUpdate>;
  optionChains: Map<string, OptionChainUpdate>;
  signals: TradingSignals | null;
  positions: Map<string, PositionUpdate>;
  
  // Utility methods
  isSubscribed: (symbol: string) => boolean;
  getSubscribedSymbols: () => string[];
}

export const useWebSocket = (options: UseWebSocketOptions = {}): UseWebSocketReturn => {
  // DISABLED FOR V2.0 - WebSocket functionality completely disabled to prevent error spam
  // Return mock state and data without attempting any connections
  
  // State - always disconnected
  const [state] = useState<WebSocketState>({
    status: ConnectionStatus.DISCONNECTED,
    connected: false,
    lastHeartbeat: null,
    connectionId: null,
    error: null
  });

  // Data state - empty but functional
  const [marketData] = useState<Map<string, MarketDataUpdate>>(new Map());
  const [optionChains] = useState<Map<string, OptionChainUpdate>>(new Map());
  const [signals] = useState<TradingSignals | null>(null);
  const [positions] = useState<Map<string, PositionUpdate>>(new Map());

  // Refs to track subscriptions - disabled but kept for compatibility
  const subscribedSymbols = useRef<Set<string>>(new Set());

  // Connection methods - all no-ops
  const connect = useCallback(async () => {
    // NO-OP: WebSocket disabled for v2.0
    return Promise.resolve();
  }, []);

  const disconnect = useCallback(() => {
    // NO-OP: WebSocket disabled for v2.0
  }, []);

  // Subscription methods - all no-ops
  const subscribe = useCallback(async (symbol: string) => {
    // NO-OP: WebSocket disabled for v2.0
    return Promise.resolve();
  }, []);

  const unsubscribe = useCallback(async (symbol: string) => {
    // NO-OP: WebSocket disabled for v2.0  
    return Promise.resolve();
  }, []);

  // Utility methods
  const isSubscribed = useCallback((symbol: string) => {
    return false; // Always false since WebSocket is disabled
  }, []);

  const getSubscribedSymbols = useCallback(() => {
    return []; // Always empty since WebSocket is disabled
  }, []);

  // NO EVENT HANDLERS - WebSocket disabled for v2.0

  return {
    state,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    marketData,
    optionChains,
    signals,
    positions,
    isSubscribed,
    getSubscribedSymbols
  };
};

// Specialized hooks for common use cases - DISABLED for v2.0
export const useMarketData = (symbol: string) => {
  // Return null - no WebSocket data available
  return null;
};

export const useOptionChain = (symbol: string) => {
  // Return null - no WebSocket data available
  return null;
};

export const useTradingSignals = () => {
  // Return mock signals data
  return { 
    signals: {
      market_bias: 'NEUTRAL',
      confidence: 0.5,
      signals: {},
      timestamp: new Date().toISOString(),
      recommendation: {
        action: 'HOLD',
        reason: 'WebSocket disabled in v2.0 - using polling data'
      }
    }, 
    connected: false 
  };
};

export const usePositions = () => {
  // Return empty positions map
  return { positions: new Map(), connected: false };
};