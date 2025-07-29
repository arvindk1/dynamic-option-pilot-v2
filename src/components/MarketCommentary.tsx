import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { 
  Newspaper, 
  TrendingUp, 
  Activity, 
  Target, 
  AlertTriangle,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  BarChart3,
  Zap
} from 'lucide-react';

interface DailyCommentary {
  date: string;
  timestamp: string;
  headline: string;
  market_overview: string;
  key_themes: string[];
  technical_outlook: string;
  volatility_watch: string;
  trading_implications: string[];
  levels_to_watch: {
    support_levels: number[];
    resistance_levels: number[];
    key_moving_averages: {
      sma_20: number;
      sma_50: number;
      sma_200: number;
    };
  };
  risk_factors: string[];
}

interface MarketCommentaryProps {
  compact?: boolean;
  onNavigateToCommentary?: () => void;
  allowCollapse?: boolean;
}

export const MarketCommentary: React.FC<MarketCommentaryProps> = ({ compact = false, onNavigateToCommentary, allowCollapse = false }) => {
  const [commentary, setCommentary] = useState<DailyCommentary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(!compact);

  const fetchCommentary = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/market-commentary/daily-commentary');
      if (response.ok) {
        const data = await response.json();
        setCommentary(data);
        setError(null);
      } else {
        throw new Error('Failed to fetch market commentary');
      }
    } catch (err) {
      setError('Unable to load market commentary');
      console.error('Market commentary error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCommentary();
  }, []);

  if (loading) {
    return (
      <Card>
        <CardContent className="p-4">
          <div className="text-center text-muted-foreground">Loading market commentary...</div>
        </CardContent>
      </Card>
    );
  }

  if (error || !commentary) {
    return (
      <Card>
        <CardContent className="p-4">
          <div className="text-center text-red-400 flex items-center justify-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            {error || 'Market commentary unavailable'}
            <Button 
              variant="outline" 
              size="sm" 
              onClick={fetchCommentary}
              className="ml-2"
            >
              <RefreshCw className="h-3 w-3" />
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (compact) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Newspaper className="h-5 w-5" />
              Market Commentary
            </CardTitle>
            <Badge variant="outline" className="text-xs">
              {new Date(commentary.date).toLocaleDateString()}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          {/* Headline only */}
          <div className="mb-3">
            <h3 className="font-semibold text-sm text-primary leading-relaxed">
              {commentary.headline}
            </h3>
          </div>

          {/* Brief snippet (first 120 chars) + CTA */}
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground leading-relaxed">
              {commentary.market_overview.substring(0, 120)}
              {commentary.market_overview.length > 120 && '...'}
            </p>
            
            <Button 
              variant="outline" 
              size="sm" 
              className="w-full"
              onClick={() => {
                if (onNavigateToCommentary) {
                  onNavigateToCommentary();
                } else {
                  // Fallback for cases where parent doesn't provide navigation handler
                  window.dispatchEvent(new CustomEvent('navigate-to-commentary'));
                }
              }}
            >
              <Newspaper className="h-3 w-3 mr-2" />
              Read Full Commentary →
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Full version for dedicated section
  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Newspaper className="h-6 w-6" />
              Daily Market Commentary
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="outline">
                {new Date(commentary.date).toLocaleDateString('en-US', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </Badge>
              {allowCollapse && (
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => setExpanded(!expanded)}
                  className="mr-2"
                >
                  {expanded ? (
                    <>
                      <ChevronUp className="h-4 w-4 mr-1" />
                      Collapse
                    </>
                  ) : (
                    <>
                      <ChevronDown className="h-4 w-4 mr-1" />
                      Expand
                    </>
                  )}
                </Button>
              )}
              <Button variant="outline" size="sm" onClick={fetchCommentary}>
                <RefreshCw className="h-4 w-4 mr-1" />
                Refresh
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <h2 className="text-xl font-bold text-primary mb-4">{commentary.headline}</h2>
          <p className="text-muted-foreground leading-relaxed">
            {expanded 
              ? commentary.market_overview 
              : `${commentary.market_overview.substring(0, 200)}${commentary.market_overview.length > 200 ? '...' : ''}`
            }
          </p>
          {!expanded && allowCollapse && (
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => setExpanded(true)}
              className="mt-2 p-0 h-auto text-primary hover:text-primary/80"
            >
              Read more →
            </Button>
          )}
        </CardContent>
      </Card>

      {expanded && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Key Themes */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Key Market Themes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {commentary.key_themes?.map((theme, index) => (
                <li key={index} className="flex items-start gap-3">
                  <span className="text-primary font-semibold mt-1">{index + 1}.</span>
                  <span className="text-sm leading-relaxed">{theme}</span>
                </li>
              )) || <li className="text-muted-foreground">No themes available</li>}
            </ul>
          </CardContent>
        </Card>

        {/* Technical Outlook */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Technical Outlook
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed mb-4">{commentary.technical_outlook}</p>
            
            {/* Key Levels */}
            <div className="space-y-3">
              <div>
                <h5 className="font-medium text-sm text-red-400 mb-1">Support Levels</h5>
                <div className="flex flex-wrap gap-2">
                  {commentary.levels_to_watch?.support_levels?.map((level, index) => (
                    <Badge key={index} variant="outline" className="text-red-400 border-red-400">
                      ${level}
                    </Badge>
                  ))}
                </div>
              </div>
              <div>
                <h5 className="font-medium text-sm text-green-400 mb-1">Resistance Levels</h5>
                <div className="flex flex-wrap gap-2">
                  {commentary.levels_to_watch?.resistance_levels?.map((level, index) => (
                    <Badge key={index} variant="outline" className="text-green-400 border-green-400">
                      ${level}
                    </Badge>
                  ))}
                </div>
              </div>
              <div>
                <h5 className="font-medium text-sm text-blue-400 mb-1">Moving Averages</h5>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline" className="text-blue-400 border-blue-400">
                    20 SMA: ${commentary.levels_to_watch?.key_moving_averages?.sma_20 || 'N/A'}
                  </Badge>
                  <Badge variant="outline" className="text-blue-400 border-blue-400">
                    50 SMA: ${commentary.levels_to_watch?.key_moving_averages?.sma_50 || 'N/A'}
                  </Badge>
                  <Badge variant="outline" className="text-blue-400 border-blue-400">
                    200 SMA: ${commentary.levels_to_watch?.key_moving_averages?.sma_200 || 'N/A'}
                  </Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Volatility Watch */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5" />
              Volatility Watch
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed">{commentary.volatility_watch}</p>
          </CardContent>
        </Card>

        {/* Trading Implications */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Trading Implications
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {commentary.trading_implications?.map((implication, index) => (
                <li key={index} className="flex items-start gap-3">
                  <span className="text-blue-400 font-semibold mt-1">→</span>
                  <span className="text-sm leading-relaxed">{implication}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        {/* Risk Factors */}
        <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-400" />
            Risk Factors to Monitor
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {commentary.risk_factors?.map((risk, index) => (
              <li key={index} className="flex items-start gap-3">
                <span className="text-orange-400 font-semibold mt-1">⚠</span>
                <span className="text-sm leading-relaxed">{risk}</span>
              </li>
            ))}
          </ul>
        </CardContent>
        </Card>
        </div>
      )}
    </div>
  );
};

export default MarketCommentary;