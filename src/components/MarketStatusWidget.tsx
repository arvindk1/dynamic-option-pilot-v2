import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  TrendingUp, 
  TrendingDown, 
  Clock, 
  Activity,
  Minus,
  AlertCircle
} from 'lucide-react';

interface MarketIndexData {
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  last_updated: string;
}

interface MarketSessionStatus {
  session_status: string;
  session_name: string;
  current_time_et: string;
  next_market_open: string | null;
  is_trading_hours: boolean;
  volume_expectation: string;
  liquidity_note: string;
  spx_data: MarketIndexData;
  nasdaq_data: MarketIndexData;
  dow_data: MarketIndexData;
}

interface MarketStatusWidgetProps {
  compact?: boolean;
}

export const MarketStatusWidget: React.FC<MarketStatusWidgetProps> = ({ compact = false }) => {
  const [sessionStatus, setSessionStatus] = useState<MarketSessionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSessionStatus = async () => {
    try {
      const response = await fetch('/api/market-commentary/session-status');
      if (response.ok) {
        const data = await response.json();
        setSessionStatus(data);
        setError(null);
      } else {
        throw new Error('Failed to fetch session status');
      }
    } catch (err) {
      setError('Unable to load market status');
      console.error('Market status error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessionStatus();
    
    // Update every 2 minutes (reduced from 30 seconds to minimize API calls)
    const interval = setInterval(fetchSessionStatus, 120000);
    return () => clearInterval(interval);
  }, []);

  const getSessionStatusColor = (status: string) => {
    switch (status) {
      case 'REGULAR_HOURS':
        return 'bg-green-600 text-white';
      case 'PRE_MARKET':
      case 'AFTER_HOURS':
        return 'bg-blue-600 text-white';
      case 'CLOSED':
        return 'bg-red-600 text-white';
      default:
        return 'bg-gray-600 text-white';
    }
  };

  const getPriceIcon = (change: number) => {
    if (change > 0) return <TrendingUp className="h-4 w-4 text-green-400" />;
    if (change < 0) return <TrendingDown className="h-4 w-4 text-red-400" />;
    return <Minus className="h-4 w-4 text-gray-400" />;
  };

  const getPriceColor = (change: number) => {
    if (change > 0) return 'text-green-400';
    if (change < 0) return 'text-red-400';
    return 'text-gray-400';
  };

  if (loading) {
    return compact ? (
      <div className="text-sm text-muted-foreground">Loading market data...</div>
    ) : (
      <Card>
        <CardContent className="p-4">
          <div className="text-center text-muted-foreground">Loading market status...</div>
        </CardContent>
      </Card>
    );
  }

  if (error || !sessionStatus) {
    return compact ? (
      <div className="text-sm text-red-400">Market data unavailable</div>
    ) : (
      <Card>
        <CardContent className="p-4">
          <div className="text-center text-red-400 flex items-center justify-center gap-2">
            <AlertCircle className="h-4 w-4" />
            {error || 'Market data unavailable'}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (compact) {
    // Compact version for header
    return (
      <div className="flex items-center space-x-4">
        {/* Market Session Status */}
        <Badge className={getSessionStatusColor(sessionStatus.session_status)}>
          <Clock className="h-3 w-3 mr-1" />
          {sessionStatus.session_status === 'REGULAR_HOURS' ? 'Market Open' :
           sessionStatus.session_status === 'PRE_MARKET' ? 'Pre-Market' :
           sessionStatus.session_status === 'AFTER_HOURS' ? 'After Hours' :
           'Market Closed'}
        </Badge>

        {/* Major Indices Price Data */}
        <div className="text-right space-y-2">
          {/* SPX */}
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-muted-foreground">SPX</span>
              {getPriceIcon(sessionStatus.spx_data.change)}
              <span className={`text-sm font-bold ${getPriceColor(sessionStatus.spx_data.change)}`}>
                ${sessionStatus.spx_data.price.toFixed(2)}
              </span>
            </div>
            <div className={`text-xs ${getPriceColor(sessionStatus.spx_data.change)}`}>
              {sessionStatus.spx_data.change >= 0 ? '+' : ''}{sessionStatus.spx_data.change.toFixed(2)} 
              ({sessionStatus.spx_data.change_percent >= 0 ? '+' : ''}{sessionStatus.spx_data.change_percent.toFixed(2)}%)
            </div>
          </div>
          
          {/* NASDAQ Index (^IXIC) */}
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-muted-foreground">NASDAQ</span>
              {getPriceIcon(sessionStatus.nasdaq_data.change)}
              <span className={`text-sm font-bold ${getPriceColor(sessionStatus.nasdaq_data.change)}`}>
                {sessionStatus.nasdaq_data.price.toFixed(0)}
              </span>
            </div>
            <div className={`text-xs ${getPriceColor(sessionStatus.nasdaq_data.change)}`}>
              {sessionStatus.nasdaq_data.change >= 0 ? '+' : ''}{sessionStatus.nasdaq_data.change.toFixed(2)} 
              ({sessionStatus.nasdaq_data.change_percent >= 0 ? '+' : ''}{sessionStatus.nasdaq_data.change_percent.toFixed(2)}%)
            </div>
          </div>
          
          {/* DOW Index (^DJI) */}
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-muted-foreground">DOW</span>
              {getPriceIcon(sessionStatus.dow_data.change)}
              <span className={`text-sm font-bold ${getPriceColor(sessionStatus.dow_data.change)}`}>
                {sessionStatus.dow_data.price.toFixed(0)}
              </span>
            </div>
            <div className={`text-xs ${getPriceColor(sessionStatus.dow_data.change)}`}>
              {sessionStatus.dow_data.change >= 0 ? '+' : ''}{sessionStatus.dow_data.change.toFixed(2)} 
              ({sessionStatus.dow_data.change_percent >= 0 ? '+' : ''}{sessionStatus.dow_data.change_percent.toFixed(2)}%)
            </div>
          </div>
          
          <div className="text-xs text-muted-foreground pt-1">
            {sessionStatus.session_status === 'REGULAR_HOURS' ? 'Regular Hours' :
             sessionStatus.session_status === 'PRE_MARKET' ? 'Pre-Market' :
             sessionStatus.session_status === 'AFTER_HOURS' ? 'After Hours' :
             'Last Close'}
          </div>
        </div>
      </div>
    );
  }

  // Full version for overview tab
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Market Status
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current Session */}
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold">{sessionStatus.session_name}</h3>
            <p className="text-sm text-muted-foreground">
              {new Date(sessionStatus.current_time_et).toLocaleString('en-US', {
                timeZone: 'America/New_York',
                dateStyle: 'medium',
                timeStyle: 'short'
              })} ET
            </p>
          </div>
          <Badge className={getSessionStatusColor(sessionStatus.session_status)}>
            {sessionStatus.session_status?.replace('_', ' ') || 'Unknown'}
          </Badge>
        </div>

        {/* Major Indices Data */}
        <div className="space-y-4">
          {/* S&P 500 (SPX) */}
          <div className="bg-muted rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h4 className="font-semibold text-lg">S&P 500 (SPX)</h4>
                <div className="flex items-center gap-2">
                  <Badge 
                    variant="outline" 
                    className="border-blue-400 text-blue-400"
                  >
                    📈 Large Cap Index
                  </Badge>
                </div>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-2">
                  {getPriceIcon(sessionStatus.spx_data.change)}
                  <span className={`text-2xl font-bold ${getPriceColor(sessionStatus.spx_data.change)}`}>
                    ${sessionStatus.spx_data.price.toFixed(2)}
                  </span>
                </div>
                <div className={`text-sm ${getPriceColor(sessionStatus.spx_data.change)}`}>
                  {sessionStatus.spx_data.change >= 0 ? '+' : ''}{sessionStatus.spx_data.change.toFixed(2)} 
                  ({sessionStatus.spx_data.change_percent >= 0 ? '+' : ''}{sessionStatus.spx_data.change_percent.toFixed(2)}%)
                </div>
              </div>
            </div>
          </div>
          
          {/* NASDAQ (QQQ) */}
          <div className="bg-muted rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h4 className="font-semibold text-lg">NASDAQ Index</h4>
                <div className="flex items-center gap-2">
                  <Badge 
                    variant="outline" 
                    className="border-purple-400 text-purple-400"
                  >
                    💻 Tech Index
                  </Badge>
                </div>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-2">
                  {getPriceIcon(sessionStatus.nasdaq_data.change)}
                  <span className={`text-2xl font-bold ${getPriceColor(sessionStatus.nasdaq_data.change)}`}>
                    {sessionStatus.nasdaq_data.price.toFixed(0)}
                  </span>
                </div>
                <div className={`text-sm ${getPriceColor(sessionStatus.nasdaq_data.change)}`}>
                  {sessionStatus.nasdaq_data.change >= 0 ? '+' : ''}{sessionStatus.nasdaq_data.change.toFixed(2)} 
                  ({sessionStatus.nasdaq_data.change_percent >= 0 ? '+' : ''}{sessionStatus.nasdaq_data.change_percent.toFixed(2)}%)
                </div>
              </div>
            </div>
          </div>
          
          {/* DOW (DIA) */}
          <div className="bg-muted rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h4 className="font-semibold text-lg">Dow Jones Index</h4>
                <div className="flex items-center gap-2">
                  <Badge 
                    variant="outline" 
                    className="border-green-400 text-green-400"
                  >
                    🏭 Industrial Index
                  </Badge>
                </div>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-2">
                  {getPriceIcon(sessionStatus.dow_data.change)}
                  <span className={`text-2xl font-bold ${getPriceColor(sessionStatus.dow_data.change)}`}>
                    {sessionStatus.dow_data.price.toFixed(0)}
                  </span>
                </div>
                <div className={`text-sm ${getPriceColor(sessionStatus.dow_data.change)}`}>
                  {sessionStatus.dow_data.change >= 0 ? '+' : ''}{sessionStatus.dow_data.change.toFixed(2)} 
                  ({sessionStatus.dow_data.change_percent >= 0 ? '+' : ''}{sessionStatus.dow_data.change_percent.toFixed(2)}%)
                </div>
              </div>
            </div>
          </div>
          
          {/* Session Status */}
          <div className="bg-slate-800 rounded-lg p-3 text-center">
            <Badge 
              className={
                sessionStatus.session_status === 'PRE_MARKET' ? 'bg-blue-600 text-white' :
                sessionStatus.session_status === 'AFTER_HOURS' ? 'bg-orange-600 text-white' :
                sessionStatus.session_status === 'REGULAR_HOURS' ? 'bg-green-600 text-white' :
                'bg-gray-600 text-white'
              }
            >
              {sessionStatus.session_status === 'PRE_MARKET' ? '🌅 Pre-Market Session' :
               sessionStatus.session_status === 'AFTER_HOURS' ? '🌆 After Hours Session' :
               sessionStatus.session_status === 'REGULAR_HOURS' ? '🏛️ Regular Trading Hours' :
               '🌙 Market Closed'}
            </Badge>
            <div className="text-xs text-muted-foreground mt-2">
              {sessionStatus.session_status === 'PRE_MARKET' ? 'vs Friday Close' :
               sessionStatus.session_status === 'AFTER_HOURS' ? 'vs Session Open' :
               sessionStatus.session_status === 'REGULAR_HOURS' ? 'vs Previous Close' :
               'Last Session Close'}
            </div>
          </div>
        </div>

        {/* Trading Context */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium">Volume Expectation:</span>
            <p className="text-muted-foreground">{sessionStatus.volume_expectation}</p>
          </div>
          <div>
            <span className="font-medium">Liquidity:</span>
            <p className="text-muted-foreground">{sessionStatus.liquidity_note}</p>
          </div>
        </div>

        {/* Next Market Open */}
        {sessionStatus.next_market_open && (
          <div className="text-sm">
            <span className="font-medium">Next Market Open:</span>
            <p className="text-muted-foreground">
              {new Date(sessionStatus.next_market_open).toLocaleString('en-US', {
                timeZone: 'America/New_York',
                dateStyle: 'medium',
                timeStyle: 'short'
              })} ET
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default MarketStatusWidget;