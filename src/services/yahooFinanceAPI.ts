
interface YahooFinanceQuote {
  regularMarketPrice: number;
  regularMarketChange: number;
  regularMarketChangePercent: number;
  regularMarketVolume: number;
  regularMarketTime: number;
}


export class YahooFinanceService {
  private baseUrl = 'https://query1.finance.yahoo.com/v8/finance/chart';
  private fallbackUrl = 'https://query2.finance.yahoo.com/v10/finance/quoteSummary';

  async getQuote(symbol: string): Promise<YahooFinanceQuote | null> {
    try {
      // Try Yahoo Finance Chart API first
      const chartUrl = `${this.baseUrl}/${symbol}?interval=1m&range=1d`;
      
      const response = await fetch(chartUrl, {
        method: 'GET',
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (!data.chart?.result?.[0]) {
        throw new Error('Invalid response format from Yahoo Finance');
      }
      
      const result = data.chart.result[0];
      const meta = result.meta;
      const quotes = result.indicators?.quote?.[0];
      
      if (!meta || !quotes) {
        throw new Error('Missing price data in Yahoo Finance response');
      }
      
      // Get the latest available data
      const timestamps = result.timestamp;
      const closes = quotes.close;
      const volumes = quotes.volume;
      
      if (!timestamps || !closes || timestamps.length === 0) {
        throw new Error('No price data available');
      }
      
      // Find the most recent non-null price
      let latestPrice = meta.regularMarketPrice;
      let latestVolume = meta.regularMarketVolume || 0;
      
      for (let i = closes.length - 1; i >= 0; i--) {
        if (closes[i] !== null && !isNaN(closes[i])) {
          latestPrice = closes[i];
          if (volumes[i] !== null && !isNaN(volumes[i])) {
            latestVolume = volumes[i];
          }
          break;
        }
      }
      
      const previousClose = meta.previousClose || latestPrice;
      const change = latestPrice - previousClose;
      const changePercent = (change / previousClose) * 100;
      
      return {
        regularMarketPrice: Number(latestPrice.toFixed(2)),
        regularMarketChange: Number(change.toFixed(2)),
        regularMarketChangePercent: Number(changePercent.toFixed(4)),
        regularMarketVolume: latestVolume,
        regularMarketTime: Math.floor(Date.now() / 1000)
      };
      
    } catch (error) {
      console.error(`Error fetching real quote for ${symbol}:`, error);
      
      // Try fallback API
      try {
        return await this.getQuoteFallback(symbol);
      } catch (fallbackError) {
        console.error(`Fallback API also failed for ${symbol}:`, fallbackError);
        throw new Error(`Failed to fetch real data for ${symbol}: ${error}`);
      }
    }
  }
  
  private async getQuoteFallback(symbol: string): Promise<YahooFinanceQuote | null> {
    const url = `${this.fallbackUrl}/${symbol}?modules=price`;
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    const priceData = data.quoteSummary?.result?.[0]?.price;
    
    if (!priceData) {
      throw new Error('No price data in fallback response');
    }
    
    return {
      regularMarketPrice: priceData.regularMarketPrice?.raw || 0,
      regularMarketChange: priceData.regularMarketChange?.raw || 0,
      regularMarketChangePercent: priceData.regularMarketChangePercent?.raw || 0,
      regularMarketVolume: priceData.regularMarketVolume?.raw || 0,
      regularMarketTime: priceData.regularMarketTime || Math.floor(Date.now() / 1000)
    };
  }

  async getSPYQuoteAsSPX(): Promise<YahooFinanceQuote | null> {
    // Use SPY as a proxy for SPX since options trading typically uses SPY
    return this.getQuote('SPY');
  }
  
  async getSPYQuote(): Promise<YahooFinanceQuote | null> {
    return this.getQuote('SPY');
  }
  
  async getVIXQuote(): Promise<YahooFinanceQuote | null> {
    return this.getQuote('^VIX');
  }
  
  async getMultipleQuotes(symbols: string[]): Promise<Record<string, YahooFinanceQuote | null>> {
    const results: Record<string, YahooFinanceQuote | null> = {};
    
    // Fetch quotes in parallel
    const promises = symbols.map(async (symbol) => {
      try {
        const quote = await this.getQuote(symbol);
        return { symbol, quote };
      } catch (error) {
        console.error(`Failed to fetch quote for ${symbol}:`, error);
        return { symbol, quote: null };
      }
    });
    
    const responses = await Promise.all(promises);
    
    responses.forEach(({ symbol, quote }) => {
      results[symbol] = quote;
    });
    
    return results;
  }
}

export const yahooFinanceService = new YahooFinanceService();
