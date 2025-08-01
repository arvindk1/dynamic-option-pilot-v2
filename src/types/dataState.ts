/**
 * Data State Management for Trading Platform
 * 
 * Defines the different states of data throughout the system
 * to ensure transparency and proper handling of data sources.
 */

export enum DataState {
  DEMO = 'demo',           // Clearly labeled test/development data
  SANDBOX = 'sandbox',     // Broker sandbox/paper trading data
  LIVE = 'live',          // Real broker integration data
  UNAVAILABLE = 'unavailable' // Service not connected or failed
}

export interface DataStateIndicator {
  data_state: DataState;
  warning?: string;
  demo_notice?: string;
  is_demo?: boolean;
  last_updated: string;
}

export interface TradingDataWithState<T = any> {
  data: T;
  data_state: DataState;
  confidence: number; // 0-1 scale indicating data reliability
  last_updated: string;
  warning?: string;
  demo_notice?: string;
  is_demo?: boolean;
}

/**
 * Type guard to check if data has state indicators
 */
export function hasDataStateIndicator(data: any): data is DataStateIndicator {
  return data && typeof data === 'object' && 'data_state' in data;
}

/**
 * Type guard to check if data is demo data
 */
export function isDemoData(data: any): boolean {
  return hasDataStateIndicator(data) && 
         (data.data_state === DataState.DEMO || data.is_demo === true);
}

/**
 * Get display label for data state
 */
export function getDataStateLabel(state: DataState): string {
  switch (state) {
    case DataState.DEMO:
      return 'DEMO MODE';
    case DataState.SANDBOX:
      return 'SANDBOX';
    case DataState.LIVE:
      return 'LIVE';
    case DataState.UNAVAILABLE:
      return 'UNAVAILABLE';
    default:
      return 'UNKNOWN';
  }
}

/**
 * Get color class for data state
 */
export function getDataStateColor(state: DataState): string {
  switch (state) {
    case DataState.DEMO:
      return 'text-yellow-600 bg-yellow-100 border-yellow-300';
    case DataState.SANDBOX:
      return 'text-blue-600 bg-blue-100 border-blue-300';
    case DataState.LIVE:
      return 'text-green-600 bg-green-100 border-green-300';
    case DataState.UNAVAILABLE:
      return 'text-red-600 bg-red-100 border-red-300';
    default:
      return 'text-gray-600 bg-gray-100 border-gray-300';
  }
}