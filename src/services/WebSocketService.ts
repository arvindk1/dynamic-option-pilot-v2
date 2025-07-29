// Browser-compatible EventEmitter implementation
type EventListener = (...args: unknown[]) => void;

class EventEmitter {
  private events: { [key: string]: EventListener[] } = {};

  on(event: string, listener: EventListener): void {
    if (!this.events[event]) {
      this.events[event] = [];
    }
    this.events[event].push(listener);
  }

  off(event: string, listener: EventListener): void {
    if (!this.events[event]) return;
    this.events[event] = this.events[event].filter(l => l !== listener);
  }

  emit(event: string, ...args: unknown[]): void {
    if (!this.events[event]) return;
    this.events[event].forEach(listener => listener(...args));
  }

  once(event: string, listener: EventListener): void {
    const onceWrapper = (...args: unknown[]) => {
      listener(...args);
      this.off(event, onceWrapper);
    };
    this.on(event, onceWrapper);
  }

  setMaxListeners(n: number): void {
    // No-op for browser compatibility
  }
}

export interface WebSocketMessage {
  type: string;
  data: unknown;
  timestamp: string;
}

export interface MarketDataUpdate {
  symbol: string;
  price: number;
  volume: number;
  timestamp: string;
  atr: number;
  vix?: number;
  change?: number;
  change_percent?: number;
}

export interface OptionChainUpdate {
  symbol: string;
  underlying_price: number;
  timestamp: string;
  calls_count: number;
  puts_count: number;
  expiration: string;
  atm_calls: OptionQuote[];
  atm_puts: OptionQuote[];
}

export interface OptionQuote {
  strike: number;
  bid: number;
  ask: number;
  volume: number;
  open_interest: number;
  delta?: number;
  gamma?: number;
  theta?: number;
  vega?: number;
  implied_volatility?: number;
}

export interface TradingSignals {
  market_bias: string;
  confidence: number;
  signals: {
    [key: string]: {
      value: number;
      signal: string;
    };
  };
  timestamp: string;
  recommendation: {
    action: string;
    reason: string;
  };
}

export interface PositionUpdate {
  position_id: string;
  symbol: string;
  current_value: number;
  pnl: number;
  pnl_percentage: number;
  timestamp: string;
}

export interface HeartbeatData {
  connection_id?: string;
  timestamp: string;
  server_time?: string;
}

export interface SubscriptionResponse {
  status: 'subscribed' | 'unsubscribed';
  symbol: string;
  message?: string;
}

export interface ServerError {
  error: string;
  code?: number;
  details?: string;
}

export enum ConnectionStatus {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error'
}

export class WebSocketService extends EventEmitter {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 1000;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private connectionStatus: ConnectionStatus = ConnectionStatus.DISCONNECTED;
  private subscribedSymbols: Set<string> = new Set();
  private lastHeartbeat: Date | null = null;
  private connectionId: string | null = null;

  constructor(url: string = 'ws://localhost:5173/ws') {
    super();
    this.url = url;
    this.setMaxListeners(50); // Increase max listeners for multiple components
  }

  public getConnectionStatus(): ConnectionStatus {
    return this.connectionStatus;
  }

  public getConnectionId(): string | null {
    return this.connectionId;
  }

  public getSubscribedSymbols(): string[] {
    return Array.from(this.subscribedSymbols);
  }

  public async connect(): Promise<void> {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }

    this.setConnectionStatus(ConnectionStatus.CONNECTING);

    try {
      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);

      // Wait for connection to be established
      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Connection timeout'));
        }, 10000);

        this.once('connected', () => {
          clearTimeout(timeout);
          resolve();
        });

        this.once('error', (error) => {
          clearTimeout(timeout);
          reject(error);
        });
      });

    } catch (error) {
      this.setConnectionStatus(ConnectionStatus.ERROR);
      throw error;
    }
  }

  public disconnect(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.setConnectionStatus(ConnectionStatus.DISCONNECTED);
    this.subscribedSymbols.clear();
    this.connectionId = null;
  }

  public async subscribe(symbol: string): Promise<void> {
    if (this.connectionStatus !== ConnectionStatus.CONNECTED) {
      throw new Error('WebSocket not connected');
    }

    const message = {
      type: 'subscribe',
      data: { symbol }
    };

    this.send(message);
    this.subscribedSymbols.add(symbol);
  }

  public async unsubscribe(symbol: string): Promise<void> {
    if (this.connectionStatus !== ConnectionStatus.CONNECTED) {
      throw new Error('WebSocket not connected');
    }

    const message = {
      type: 'unsubscribe',
      data: { symbol }
    };

    this.send(message);
    this.subscribedSymbols.delete(symbol);
  }

  public async resubscribeAll(): Promise<void> {
    const symbols = Array.from(this.subscribedSymbols);
    this.subscribedSymbols.clear();
    
    for (const symbol of symbols) {
      await this.subscribe(symbol);
    }
  }

  private handleOpen(): void {
    console.log('WebSocket connected');
    this.setConnectionStatus(ConnectionStatus.CONNECTED);
    this.reconnectAttempts = 0;
    this.startHeartbeat();
    this.emit('connected');
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      this.handleIncomingMessage(message);
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  private handleClose(event: CloseEvent): void {
    console.log('WebSocket closed:', event.code, event.reason);
    this.setConnectionStatus(ConnectionStatus.DISCONNECTED);
    this.stopHeartbeat();
    this.emit('disconnected');
    
    // Attempt to reconnect if not intentionally closed
    if (event.code !== 1000) {
      this.attemptReconnect();
    }
  }

  private handleError(error: Event): void {
    console.error('WebSocket error:', error);
    this.setConnectionStatus(ConnectionStatus.ERROR);
    this.emit('error', error);
  }

  private handleIncomingMessage(message: WebSocketMessage): void {
    this.lastHeartbeat = new Date();

    switch (message.type) {
      case 'heartbeat':
        this.handleHeartbeat(message.data);
        break;

      case 'market_data':
        this.handleMarketData(message.data);
        break;

      case 'option_chain':
        this.handleOptionChain(message.data);
        break;

      case 'signals':
        this.handleSignals(message.data);
        break;

      case 'position_update':
        this.handlePositionUpdate(message.data);
        break;

      case 'subscribe':
        this.handleSubscriptionResponse(message.data);
        break;

      case 'unsubscribe':
        this.handleUnsubscriptionResponse(message.data);
        break;

      case 'error':
        this.handleServerError(message.data);
        break;

      default:
        console.warn('Unknown message type:', message.type);
    }
  }

  private handleHeartbeat(data: HeartbeatData): void {
    if (data.connection_id) {
      this.connectionId = data.connection_id;
    }
    this.emit('heartbeat', data);
  }

  private handleMarketData(data: MarketDataUpdate): void {
    this.emit('marketData', data);
    this.emit(`marketData:${data.symbol}`, data);
  }

  private handleOptionChain(data: OptionChainUpdate): void {
    this.emit('optionChain', data);
    this.emit(`optionChain:${data.symbol}`, data);
  }

  private handleSignals(data: TradingSignals): void {
    this.emit('signals', data);
  }

  private handlePositionUpdate(data: PositionUpdate): void {
    this.emit('positionUpdate', data);
    this.emit(`positionUpdate:${data.position_id}`, data);
  }

  private handleSubscriptionResponse(data: SubscriptionResponse): void {
    if (data.status === 'subscribed') {
      console.log(`Subscribed to ${data.symbol}`);
    }
  }

  private handleUnsubscriptionResponse(data: SubscriptionResponse): void {
    if (data.status === 'unsubscribed') {
      console.log(`Unsubscribed from ${data.symbol}`);
    }
  }

  private handleServerError(data: ServerError): void {
    console.error('Server error:', data.error);
    this.emit('serverError', data);
  }

  private send(message: Record<string, unknown>): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, message not sent:', message);
    }
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.connectionStatus === ConnectionStatus.CONNECTED) {
        this.send({
          type: 'heartbeat',
          data: { timestamp: new Date().toISOString() }
        });
      }
    }, 30000); // Send heartbeat every 30 seconds
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.setConnectionStatus(ConnectionStatus.ERROR);
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
    this.setConnectionStatus(ConnectionStatus.RECONNECTING);

    setTimeout(async () => {
      try {
        await this.connect();
        await this.resubscribeAll();
      } catch (error) {
        console.error('Reconnection failed:', error);
        this.attemptReconnect();
      }
    }, delay);
  }

  private setConnectionStatus(status: ConnectionStatus): void {
    if (this.connectionStatus !== status) {
      this.connectionStatus = status;
      this.emit('statusChange', status);
    }
  }

  // Convenience methods for common subscriptions
  public async subscribeToSPY(): Promise<void> {
    await this.subscribe('SPY');
  }
  
  public async subscribeToSPX(): Promise<void> {
    // Use SPY as proxy for SPX since it's more liquid for options trading
    await this.subscribe('SPY');
  }

  public async subscribeToVIX(): Promise<void> {
    try {
      // VIX not supported by Alpaca - log warning and skip
      console.warn('VIX subscriptions not supported by current data provider. Use UVXY as volatility proxy.');
      // Could fall back to Yahoo Finance API for VIX data if needed
      // await this.subscribe('^VIX');
    } catch (error) {
      console.error('Failed to subscribe to VIX:', error);
      throw new Error('VIX subscriptions not supported by current data provider');
    }
  }

  public async subscribeToMultiple(symbols: string[]): Promise<void> {
    for (const symbol of symbols) {
      await this.subscribe(symbol);
    }
  }

  // Health check methods
  public isConnected(): boolean {
    return this.connectionStatus === ConnectionStatus.CONNECTED;
  }

  public getLastHeartbeat(): Date | null {
    return this.lastHeartbeat;
  }

  public getConnectionHealth(): {
    status: ConnectionStatus;
    connected: boolean;
    lastHeartbeat: Date | null;
    subscribedSymbols: string[];
    connectionId: string | null;
  } {
    return {
      status: this.connectionStatus,
      connected: this.isConnected(),
      lastHeartbeat: this.lastHeartbeat,
      subscribedSymbols: this.getSubscribedSymbols(),
      connectionId: this.connectionId
    };
  }
}

// Export singleton instance with proper URL for Vite proxy
// For v2.0, disable WebSocket and use polling instead
export const webSocketService = new WebSocketService('ws://localhost:8000/ws');