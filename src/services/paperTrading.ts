
// ✅ Make types reflect reality and stay consistent across code paths
interface Trade {
  id: string;
  symbol: string;
  type: 'PUT' | 'CALL' | 'STOCK' | 'PUT_SPREAD' | 'CALL_SPREAD' | 'IRON_CONDOR' | 'STRANGLE' | 'STRADDLE';
  shortStrike: number;
  longStrike: number;
  quantity: number;
  entryCredit: number;          // total credit received (respecting multiplier)
  entryDate: Date;
  expiration?: Date;            // may be undefined
  status: 'OPEN' | 'CLOSED' | 'EXPIRED';
  exitPrice?: number;
  exitDate?: Date;
  pnl?: number;

  // API response fields (pass-through)
  order_id?: string;
  execution_price?: number;
  commission?: number;
  message?: string;
}

interface SpreadOpportunity {
  id: string;
  symbol: string;
  strategy_type: string;
  option_type: 'PUT' | 'CALL';
  strike: number;
  short_strike?: number;
  long_strike?: number;
  expiration: string;              // ISO
  days_to_expiration: number;
  premium: number;                 // per contract
}

// Reflect typical server payload; keep strings for raw dates
interface PositionData {
  order_id?: string;
  id: number;
  symbol: string;
  type?: string;                   // 'PUT' | 'CALL' | 'STOCK' | spread types, etc.
  spread_type?: string;            // e.g. 'PUT_SPREAD'
  short_strike?: number;
  long_strike?: number;
  quantity: number;
  entry_credit?: number;           // total credit or per-contract? normalize later
  entry_price: number;             // per-contract price
  entry_date: string;              // ISO
  expiration?: string | null;
  expiration_date?: string | null; // some backends use this
  status: string;                  // 'OPEN'|'CLOSED'|'EXPIRED'|...
  exit_price?: number;
  exit_date?: string | null;
  pnl?: number;
  current_pnl?: number;
}

interface AccountMetrics {
  account_balance: number;
  buying_power: number;
  total_pnl: number;
  today_pnl: number;
  open_positions: number;

  // Optional extras you attach later:
  performanceHistory?: Array<{ t: string | number; v: number }>;
}

interface SyncResponse {
  message: string;
  positions_updated: number;
  success: boolean;
  rate_limited?: boolean;
}

// ✅ Normalize helpers
const CONTRACT_MULTIPLIER = 100;

const toDateOrUndefined = (v?: string | null): Date | undefined => {
  if (!v || v === 'null') return undefined;
  const d = new Date(v);
  return isNaN(d.getTime()) ? undefined : d;
};

const toMandatoryDateOrNow = (v?: string | null): Date => {
  const d = v ? new Date(v) : new Date();
  return isNaN(d.getTime()) ? new Date() : d;
};

const toTradeType = (raw?: string): Trade['type'] => {
  const t = (raw ?? '').toUpperCase();
  switch (t) {
    case 'PUT':
    case 'CALL':
    case 'STOCK':
    case 'PUT_SPREAD':
    case 'CALL_SPREAD':
    case 'IRON_CONDOR':
    case 'STRANGLE':
    case 'STRADDLE':
      return t;
    default:
      // try mapping spread_type or fallback
      return 'STOCK';
  }
};

const toTradeStatus = (raw: string): Trade['status'] => {
  const s = (raw ?? '').toUpperCase();
  return s === 'OPEN' || s === 'CLOSED' || s === 'EXPIRED' ? s : 'OPEN';
};

const normalizePosition = (p: PositionData): Trade => {
  const expiration = toDateOrUndefined(p.expiration ?? p.expiration_date);
  const entryDate = toMandatoryDateOrNow(p.entry_date);

  // entry_credit ambiguity: some APIs give per-contract vs total.
  // Prefer explicit total 'entry_credit', else compute from entry_price * qty * multiplier.
  const entryCreditTotal =
    typeof p.entry_credit === 'number'
      ? p.entry_credit
      : (p.entry_price ?? 0) * (p.quantity ?? 0) * CONTRACT_MULTIPLIER;

  return {
    id: (p.order_id ?? p.id)?.toString(),
    symbol: p.symbol,
    type: toTradeType(p.spread_type ?? p.type),
    shortStrike: p.short_strike ?? 0,
    longStrike: p.long_strike ?? 0,
    quantity: p.quantity,
    entryCredit: entryCreditTotal,
    entryDate,
    expiration,
    status: toTradeStatus(p.status),
    exitPrice: p.exit_price,
    exitDate: toDateOrUndefined(p.exit_date ?? undefined),
    pnl: typeof p.pnl === 'number' ? p.pnl : (typeof p.current_pnl === 'number' ? p.current_pnl : 0),

    // passthrough
    order_id: p.order_id,
  };
};

// ✅ Tiny fetch helper with timeout + robust error info
const withTimeout = <T>(p: Promise<T>, ms = 15000): Promise<T> => {
  let t: any;
  const timeout = new Promise<never>((_, rej) => (t = setTimeout(() => rej(new Error(`Timeout ${ms}ms`)), ms)));
  return Promise.race([p, timeout]).finally(() => clearTimeout(t));
};

async function fetchJSON<T>(input: RequestInfo, init?: RequestInit & { timeoutMs?: number }): Promise<T> {
  const controller = new AbortController();
  const timeoutMs = init?.timeoutMs ?? 15000;
  const merged: RequestInit = { ...init, signal: controller.signal };

  try {
    const res = await withTimeout(fetch(input, merged), timeoutMs);
    if (!res.ok) {
      let detail = `${res.status} ${res.statusText}`;
      try {
        const j = await res.clone().json();
        detail = j?.detail || j?.message || detail;
      } catch {
        const t = await res.text().catch(() => '');
        if (t) detail = `${detail} — ${t}`;
      }
      throw new Error(`HTTP ${detail}`);
    }
    try {
      return await res.json();
    } catch {
      // empty body or not JSON
      return {} as T;
    }
  } finally {
    controller.abort();
  }
}

export class RealTradingService {
  private baseUrl = 'http://localhost:8000/api';
  private listeners: ((trades: Trade[]) => void)[] = [];

  constructor() {
    // Don't load trades immediately in constructor to avoid race conditions
    // Components will call loadTrades() when needed
    
    // Removed automatic polling - positions will be updated via component-triggered syncs
    // This prevents excessive background API calls when no one is actively viewing positions
  }

  // ---- EXECUTE ----
  async executeTrade(spread: SpreadOpportunity, quantity: number): Promise<Trade> {
    const payload = {
      id: spread.id,
      symbol: spread.symbol,
      strategy_type: spread.strategy_type,
      option_type: spread.option_type,
      strike: spread.strike,
      short_strike: spread.short_strike,
      long_strike: spread.long_strike,
      expiration: spread.expiration,
      days_to_expiration: spread.days_to_expiration,
      premium: spread.premium,
      quantity,
    };

    const trade = await fetchJSON<PositionData | Trade>(`${this.baseUrl}/trading/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      timeoutMs: 20000,
    });

    // Some backends return a position-like object; normalize both cases
    const normalized: Trade = (trade as any).entry_date
      ? normalizePosition(trade as PositionData)
      : (trade as Trade);

    await this.loadTrades();
    return normalized;
  }

  // ---- CLOSE ----
  async closeTrade(tradeId: string, exitPrice: number): Promise<{message?: string; cancelled_orders?: string[]; cancelled_count?: number}> {
    const result = await fetchJSON<{message?: string; cancelled_orders?: string[]; cancelled_count?: number}>(
      `${this.baseUrl}/positions/close/${tradeId}?exit_price=${exitPrice}`,
      { method: 'POST', headers: { 'Content-Type': 'application/json' }, timeoutMs: 20000 }
    );
    await this.loadTrades();
    return result;
  }

  private trades: Trade[] = [];
  
  // ---- LOAD ----
  async loadTrades(): Promise<void> {
    try {
      const data = await fetchJSON<PositionData[]>(`${this.baseUrl}/positions/?sync=false`, { timeoutMs: 15000 });
      this.trades = Array.isArray(data) ? data.map(normalizePosition) : [];
      this.notifyListeners();
    } catch (err) {
      console.error('Error loading trades:', err);
      // keep old trades; UI can render stale or empty state
    }
  }
  
  getTrades(): Trade[] {
    return [...this.trades];
  }

  getOpenTrades(): Trade[] {
    return this.trades.filter(t => t.status === 'OPEN');
  }

  // ---- SYNC ----
  async syncPositions(): Promise<SyncResponse> {
    try {
      const syncResult = await fetchJSON<any>(`${this.baseUrl}/positions/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        timeoutMs: 20000,
      });

      if (syncResult?.status === 'rate_limited') {
        return { message: syncResult.message ?? 'Rate limited', positions_updated: 0, success: false, rate_limited: true };
      }

      return {
        message: syncResult?.message ?? 'Sync completed',
        positions_updated: syncResult?.sync_results?.synced_positions ?? 0,
        success: syncResult?.status === 'success',
      };
    } catch (err) {
      console.error('Error syncing positions:', err);
      // Surface as failure but not rate-limited
      return { message: (err as Error).message ?? 'Sync failed', positions_updated: 0, success: false };
    }
  }

  // ---- METRICS ----
  async getAccountMetrics(): Promise<AccountMetrics> {
    try {
      const metrics = await fetchJSON<AccountMetrics>(`${this.baseUrl}/dashboard/metrics`, { timeoutMs: 15000 });

      try {
        const perf = await fetchJSON<{ data: Array<{ t: string | number; v: number }> }>(
          `${this.baseUrl}/dashboard/performance?days=30`,
          { timeoutMs: 15000 }
        );
        (metrics as AccountMetrics).performanceHistory = Array.isArray(perf?.data) ? perf.data : [];
      } catch (perfError) {
        console.warn('Failed to fetch performance history:', perfError);
        (metrics as AccountMetrics).performanceHistory = [];
      }

      // Ensure required fields exist with sane defaults
      return {
        account_balance: metrics.account_balance ?? 0,
        buying_power: metrics.buying_power ?? 0,
        total_pnl: metrics.total_pnl ?? 0,
        today_pnl: metrics.today_pnl ?? 0,
        open_positions: metrics.open_positions ?? 0,
        performanceHistory: metrics.performanceHistory ?? [],
      };
    } catch (err) {
      console.error('Error fetching account metrics:', err);
      return {
        account_balance: 0,
        buying_power: 0,
        total_pnl: 0,
        today_pnl: 0,
        open_positions: 0,
        performanceHistory: [],
      };
    }
  }

  // ---- SUBSCRIBE ----
  subscribe(listener: (trades: Trade[]) => void): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notifyListeners(): void {
    const snapshot = this.getTrades();
    // prevent mutation surprises
    this.listeners.forEach(l => {
      try { l(snapshot); } catch (e) { console.error('Listener error:', e); }
    });
  }
}

export const tradingService = new RealTradingService();

// Keep old export for backward compatibility during transition
export const paperTradingService = tradingService;
