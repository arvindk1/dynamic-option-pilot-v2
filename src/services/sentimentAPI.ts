/**
 * Sentiment Analysis API Service
 * 
 * Provides functions to fetch market sentiment data including:
 * - Overall market sentiment
 * - MAG 7 stocks sentiment
 * - Top 20 stocks sentiment
 * - SPY sentiment
 * - LLM-generated market pulse
 */

export interface SentimentScore {
  positive: number;
  negative: number;
  neutral: number;
  compound: number;
  confidence: number;
}

export interface MarketPulse {
  timestamp: string;
  overall_sentiment: SentimentScore;
  mag7_sentiment: Record<string, SentimentScore>;
  top20_sentiment: Record<string, SentimentScore>;
  spy_sentiment: SentimentScore;
  key_themes: string[];
  market_summary: string;
  news_count: number;
  data_sources: string[];
}

export interface QuickSentiment {
  overall_score: number;
  overall_label: string;
  spy_score: number;
  spy_label: string;
  mag7_average: number;
  mag7_label: string;
  last_updated: string;
  market_summary: string;
}

export interface SentimentHistory {
  date: string;
  sentiment_score: number;
  news_count: number;
  key_themes: string[];
}

export interface SymbolSentiment {
  symbol: string;
  sentiment: {
    positive: number;
    negative: number;
    neutral: number;
    compound: number;
    confidence: number;
    label: string;
  };
  last_updated: string;
  news_count: number;
  market_context: string;
}

class SentimentAPIService {
  private baseUrl = this.getBaseUrl();

  private getBaseUrl(): string {
    // Always use relative URLs - let the proxy handle routing
    return '/api/sentiment';
  }

  /**
   * Get comprehensive market sentiment pulse
   */
  async getMarketPulse(forceRefresh: boolean = false): Promise<MarketPulse> {
    try {
      const url = `${this.baseUrl}/pulse${forceRefresh ? '?force_refresh=true' : ''}`;
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching market pulse:', error);
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        throw new TypeError('Unable to connect to sentiment analysis service. Please check if the backend is running.');
      }
      throw new Error(`Failed to fetch market sentiment: ${error}`);
    }
  }

  /**
   * Get quick sentiment overview for widgets
   */
  async getQuickSentiment(): Promise<QuickSentiment> {
    try {
      const response = await fetch(`${this.baseUrl}/quick`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching quick sentiment:', error);
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        throw new TypeError('Unable to connect to sentiment analysis service. Please check if the backend is running.');
      }
      throw new Error(`Failed to fetch quick sentiment: ${error}`);
    }
  }

  /**
   * Get sentiment history for trend analysis
   */
  async getSentimentHistory(days: number = 7): Promise<SentimentHistory[]> {
    try {
      const response = await fetch(`${this.baseUrl}/history?days=${days}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching sentiment history:', error);
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        throw new TypeError('Unable to connect to sentiment analysis service. Please check if the backend is running.');
      }
      throw new Error(`Failed to fetch sentiment history: ${error}`);
    }
  }

  /**
   * Get sentiment for a specific stock symbol
   */
  async getSymbolSentiment(symbol: string, hours: number = 24): Promise<SymbolSentiment> {
    try {
      const response = await fetch(`${this.baseUrl}/symbols/${symbol}?hours=${hours}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Error fetching sentiment for ${symbol}:`, error);
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        throw new TypeError('Unable to connect to sentiment analysis service. Please check if the backend is running.');
      }
      throw new Error(`Failed to fetch sentiment for ${symbol}: ${error}`);
    }
  }

  /**
   * Manually trigger sentiment data refresh
   */
  async refreshSentiment(): Promise<{ status: string; message: string; timestamp: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error refreshing sentiment:', error);
      throw new Error(`Failed to refresh sentiment: ${error}`);
    }
  }

  /**
   * Get sentiment label from numeric score
   */
  getSentimentLabel(score: number): string {
    if (score >= 0.3) return 'Very Positive';
    if (score >= 0.1) return 'Positive';
    if (score >= -0.1) return 'Neutral';
    if (score >= -0.3) return 'Negative';
    return 'Very Negative';
  }

  /**
   * Get sentiment color for UI display
   */
  getSentimentColor(score: number): string {
    if (score >= 0.3) return 'text-green-600';
    if (score >= 0.1) return 'text-green-400';
    if (score >= -0.1) return 'text-gray-500';
    if (score >= -0.3) return 'text-red-400';
    return 'text-red-600';
  }

  /**
   * Get sentiment background color for UI display
   */
  getSentimentBgColor(score: number): string {
    if (score >= 0.3) return 'bg-green-100';
    if (score >= 0.1) return 'bg-green-50';
    if (score >= -0.1) return 'bg-gray-50';
    if (score >= -0.3) return 'bg-red-50';
    return 'bg-red-100';
  }

  /**
   * Format timestamp for display
   */
  formatTimestamp(timestamp: string): string {
    const date = new Date(timestamp);
    return date.toLocaleString();
  }

  /**
   * Calculate sentiment trend from history
   */
  calculateTrend(history: SentimentHistory[]): { trend: 'up' | 'down' | 'stable'; change: number } {
    if (history.length < 2) {
      return { trend: 'stable', change: 0 };
    }

    const recent = history.slice(-3);
    const older = history.slice(-6, -3);

    const recentAvg = recent.reduce((sum, item) => sum + item.sentiment_score, 0) / recent.length;
    const olderAvg = older.length > 0 
      ? older.reduce((sum, item) => sum + item.sentiment_score, 0) / older.length 
      : recentAvg;

    const change = recentAvg - olderAvg;

    if (Math.abs(change) < 0.05) {
      return { trend: 'stable', change };
    }

    return {
      trend: change > 0 ? 'up' : 'down',
      change
    };
  }

  /**
   * Group MAG 7 stocks by sentiment
   */
  groupMAG7BySentiment(mag7Sentiment: Record<string, SentimentScore>): {
    positive: string[];
    neutral: string[];
    negative: string[];
  } {
    const groups = { positive: [], neutral: [], negative: [] };

    Object.entries(mag7Sentiment).forEach(([symbol, sentiment]) => {
      if (sentiment.compound >= 0.1) {
        groups.positive.push(symbol);
      } else if (sentiment.compound <= -0.1) {
        groups.negative.push(symbol);
      } else {
        groups.neutral.push(symbol);
      }
    });

    return groups;
  }

  /**
   * Get top performing stocks by sentiment
   */
  getTopPerformers(stockSentiments: Record<string, SentimentScore>, count: number = 5): Array<{
    symbol: string;
    score: number;
    label: string;
  }> {
    return Object.entries(stockSentiments)
      .map(([symbol, sentiment]) => ({
        symbol,
        score: sentiment.compound,
        label: this.getSentimentLabel(sentiment.compound)
      }))
      .sort((a, b) => b.score - a.score)
      .slice(0, count);
  }
}

export const sentimentAPI = new SentimentAPIService();