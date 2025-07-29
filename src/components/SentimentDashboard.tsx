/**
 * Sentiment Dashboard Component
 * 
 * Comprehensive sentiment analysis dashboard featuring:
 * - Market pulse with LLM-generated summary
 * - MAG 7 stocks sentiment grid
 * - Top 20 stocks sentiment overview
 * - SPY sentiment analysis
 * - Sentiment trends and history
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  RefreshCw, 
  Activity,
  Brain,
  NewspaperIcon,
  Clock,
  BarChart3,
  AlertTriangle
} from 'lucide-react';
import { 
  sentimentAPI, 
  MarketPulse, 
  QuickSentiment, 
  SentimentHistory,
  SentimentScore 
} from '@/services/sentimentAPI';

export const SentimentDashboard: React.FC = React.memo(() => {
  const [marketPulse, setMarketPulse] = useState<MarketPulse | null>(null);
  const [quickSentiment, setQuickSentiment] = useState<QuickSentiment | null>(null);
  const [sentimentHistory, setSentimentHistory] = useState<SentimentHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSentimentData();
    
    // Set up auto-refresh every 5 minutes
    const interval = setInterval(() => {
      loadQuickSentiment();
    }, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  const loadSentimentData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Test backend connectivity first
      const healthResponse = await fetch('/health');
      if (!healthResponse.ok) {
        throw new Error('Backend server is not accessible. Please check if the backend is running on http://localhost:8000');
      }
      
      const [pulse, quick, history] = await Promise.all([
        sentimentAPI.getMarketPulse(),
        sentimentAPI.getQuickSentiment(),
        sentimentAPI.getSentimentHistory(7)
      ]);
      
      setMarketPulse(pulse);
      setQuickSentiment(quick);
      setSentimentHistory(history);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Sentiment loading error:', err);
      if (err instanceof TypeError && err.message.includes('Failed to fetch')) {
        setError('Network connection error. Please check:\n• Backend server is running on http://localhost:8000\n• CORS is properly configured\n• No firewall blocking the request');
      } else {
        setError(err instanceof Error ? err.message : 'Failed to load sentiment data');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadQuickSentiment = async () => {
    try {
      const quick = await sentimentAPI.getQuickSentiment();
      setQuickSentiment(quick);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error refreshing quick sentiment:', err);
    }
  };

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      await sentimentAPI.refreshSentiment();
      // Wait a moment for the backend to process
      setTimeout(() => {
        loadSentimentData();
        setRefreshing(false);
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh data');
      setRefreshing(false);
    }
  };

  const getSentimentIcon = (score: number) => {
    if (score >= 0.1) return <TrendingUp className="h-4 w-4 text-green-600" />;
    if (score <= -0.1) return <TrendingDown className="h-4 w-4 text-red-600" />;
    return <Minus className="h-4 w-4 text-slate-400" />;
  };

  const SentimentCard: React.FC<{
    title: string;
    sentiment: SentimentScore;
    subtitle?: string;
  }> = ({ title, sentiment, subtitle }) => (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center justify-between">
          {title}
          {getSentimentIcon(sentiment.compound)}
        </CardTitle>
        {subtitle && <CardDescription className="text-xs">{subtitle}</CardDescription>}
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-2xl font-bold">
              {(sentiment.compound * 100).toFixed(0)}
            </span>
            <Badge variant={sentiment.compound >= 0.1 ? 'default' : sentiment.compound <= -0.1 ? 'destructive' : 'secondary'}>
              {sentimentAPI.getSentimentLabel(sentiment.compound)}
            </Badge>
          </div>
          
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span>Positive</span>
              <span>{(sentiment.positive * 100).toFixed(0)}%</span>
            </div>
            <Progress value={sentiment.positive * 100} className="h-1" />
            
            <div className="flex justify-between text-xs">
              <span>Negative</span>
              <span>{(sentiment.negative * 100).toFixed(0)}%</span>
            </div>
            <Progress value={sentiment.negative * 100} className="h-1 bg-red-100" />
          </div>
          
          <div className="text-xs text-slate-300">
            Confidence: {(sentiment.confidence * 100).toFixed(0)}%
          </div>
        </div>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading sentiment data...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="m-4">
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="flex items-start space-x-2 text-red-400">
              <AlertTriangle className="h-5 w-5 mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="font-semibold text-red-400 mb-2">Sentiment Analysis Error</h3>
                <pre className="text-sm text-red-300 whitespace-pre-wrap">{error}</pre>
              </div>
            </div>
            <div className="flex space-x-2">
              <Button onClick={loadSentimentData} className="bg-blue-600 hover:bg-blue-700">
                Retry Connection
              </Button>
              <Button 
                variant="outline" 
                onClick={() => window.open('http://localhost:8000/docs', '_blank')}
                className="border-blue-400 text-blue-400 hover:bg-blue-950"
              >
                Check Backend Status
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center">
            <Brain className="h-6 w-6 mr-2" />
            Market Sentiment Analysis
          </h1>
          <p className="text-slate-300">
            AI-powered sentiment analysis from news and social media
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          {lastUpdated && (
            <div className="flex items-center text-sm text-slate-300">
              <Clock className="h-4 w-4 mr-1" />
              {lastUpdated.toLocaleTimeString()}
            </div>
          )}
          <Button 
            onClick={handleRefresh} 
            disabled={refreshing}
            variant="outline"
            size="sm"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Quick Overview */}
      {quickSentiment && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Overall Market</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold">
                  {quickSentiment.overall_score.toFixed(2)}
                </span>
                <Badge variant={quickSentiment.overall_score >= 0.1 ? 'default' : quickSentiment.overall_score <= -0.1 ? 'destructive' : 'secondary'}>
                  {quickSentiment.overall_label}
                </Badge>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">SPY Sentiment</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold">
                  {quickSentiment.spy_score.toFixed(2)}
                </span>
                <Badge variant={quickSentiment.spy_score >= 0.1 ? 'default' : quickSentiment.spy_score <= -0.1 ? 'destructive' : 'secondary'}>
                  {quickSentiment.spy_label}
                </Badge>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">MAG 7 Average</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold">
                  {quickSentiment.mag7_average.toFixed(2)}
                </span>
                <Badge variant={quickSentiment.mag7_average >= 0.1 ? 'default' : quickSentiment.mag7_average <= -0.1 ? 'destructive' : 'secondary'}>
                  {quickSentiment.mag7_label}
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Detailed Analysis Tabs */}
      <Tabs defaultValue="pulse" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="pulse" className="flex items-center">
            <Activity className="h-4 w-4 mr-2" />
            Market Pulse
          </TabsTrigger>
          <TabsTrigger value="mag7" className="flex items-center">
            <BarChart3 className="h-4 w-4 mr-2" />
            MAG 7
          </TabsTrigger>
          <TabsTrigger value="top20" className="flex items-center">
            <TrendingUp className="h-4 w-4 mr-2" />
            Top 20
          </TabsTrigger>
          <TabsTrigger value="history" className="flex items-center">
            <Clock className="h-4 w-4 mr-2" />
            History
          </TabsTrigger>
        </TabsList>

        {/* Market Pulse Tab */}
        <TabsContent value="pulse" className="space-y-4">
          {marketPulse && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* LLM-Generated Summary */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Brain className="h-5 w-5 mr-2" />
                    AI Market Pulse
                  </CardTitle>
                  <CardDescription>
                    Generated from {marketPulse.news_count} news articles
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-lg leading-relaxed mb-4">
                    {marketPulse.market_summary}
                  </p>
                  
                  {marketPulse.key_themes.length > 0 && (
                    <div>
                      <h4 className="font-semibold mb-2">Key Themes:</h4>
                      <div className="flex flex-wrap gap-2">
                        {marketPulse.key_themes.map((theme, index) => (
                          <Badge key={index} variant="outline">
                            {theme}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Overall Sentiment */}
              <SentimentCard
                title="Overall Market Sentiment"
                sentiment={marketPulse.overall_sentiment}
                subtitle="Aggregated from all news sources"
              />

              {/* SPY Sentiment */}
              <SentimentCard
                title="SPY Sentiment"
                sentiment={marketPulse.spy_sentiment}
                subtitle="S&P 500 specific sentiment"
              />
            </div>
          )}
        </TabsContent>

        {/* MAG 7 Tab */}
        <TabsContent value="mag7" className="space-y-4">
          {marketPulse && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {Object.entries(marketPulse.mag7_sentiment).map(([symbol, sentiment]) => (
                <SentimentCard
                  key={symbol}
                  title={symbol}
                  sentiment={sentiment}
                  subtitle="MAG 7 Stock"
                />
              ))}
            </div>
          )}
        </TabsContent>

        {/* Top 20 Tab */}
        <TabsContent value="top20" className="space-y-4">
          {marketPulse && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
              {Object.entries(marketPulse.top20_sentiment).map(([symbol, sentiment]) => (
                <SentimentCard
                  key={symbol}
                  title={symbol}
                  sentiment={sentiment}
                  subtitle="Top 20 Stock"
                />
              ))}
            </div>
          )}
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Sentiment History (7 Days)</CardTitle>
              <CardDescription>
                Historical sentiment trends and news volume
              </CardDescription>
            </CardHeader>
            <CardContent>
              {sentimentHistory.length > 0 ? (
                <div className="space-y-4">
                  {sentimentHistory.map((item, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded">
                      <div>
                        <div className="font-medium">
                          {new Date(item.date).toLocaleDateString()}
                        </div>
                        <div className="text-sm text-slate-400">
                          {item.news_count} news articles
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <Badge variant={item.sentiment_score >= 0.1 ? 'default' : item.sentiment_score <= -0.1 ? 'destructive' : 'secondary'}>
                          {sentimentAPI.getSentimentLabel(item.sentiment_score)}
                        </Badge>
                        <span className="font-mono">
                          {item.sentiment_score.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-slate-400 py-8">
                  No historical data available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Data Sources Footer */}
      {marketPulse && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between text-sm text-slate-400">
              <div className="flex items-center space-x-4">
                <span className="flex items-center">
                  <NewspaperIcon className="h-4 w-4 mr-1" />
                  Sources: {marketPulse.data_sources.join(', ')}
                </span>
                <span>
                  Articles: {marketPulse.news_count}
                </span>
              </div>
              <span>
                Last updated: {sentimentAPI.formatTimestamp(marketPulse.timestamp)}
              </span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
});