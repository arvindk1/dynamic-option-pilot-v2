import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertTriangle, Calendar, TrendingUp, Zap, RefreshCw } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface EconomicEvent {
  id: number;
  event_id: string;
  name: string;
  description: string;
  date: string;
  time: string;
  event_type: string;
  importance: string;
  country: string;
  currency: string;
  actual: string | null;
  forecast: string | null;
  previous: string | null;
  impact_score: number | null;
  volatility_forecast: number | null;
}

interface VolatilityForecast {
  date: string;
  expected_volatility: number;
  events: Array<{
    name: string;
    importance: string;
    impact_score: number;
  }>;
}

interface WeekSummary {
  total_events: number;
  high_impact_events: number;
  total_impact_score: number;
  average_volatility_forecast: number;
  week_start: string;
  week_end: string;
}

const EconomicEventsDashboard: React.FC = React.memo(() => {
  const [upcomingEvents, setUpcomingEvents] = useState<Record<string, EconomicEvent[]>>({});
  const [weekSummary, setWeekSummary] = useState<WeekSummary | null>(null);
  const [volatilityForecast, setVolatilityForecast] = useState<Record<string, VolatilityForecast>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastSync, setLastSync] = useState<string | null>(null);

  const fetchEconomicData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch upcoming events
      const upcomingResponse = await fetch('/api/economic/upcoming?days=7&high_impact_only=false');
      if (!upcomingResponse.ok) throw new Error('Failed to fetch upcoming events');
      const upcomingData = await upcomingResponse.json();
      setUpcomingEvents(upcomingData.upcoming_events || {});

      // Fetch this week's summary
      const weekResponse = await fetch('/api/economic/this-week');
      if (!weekResponse.ok) throw new Error('Failed to fetch week summary');
      const weekData = await weekResponse.json();
      setWeekSummary(weekData.week_summary);

      // Fetch volatility forecast for SPY
      const volatilityResponse = await fetch('/api/economic/volatility-forecast/SPY?days_ahead=7');
      if (!volatilityResponse.ok) throw new Error('Failed to fetch volatility forecast');
      const volatilityData = await volatilityResponse.json();
      setVolatilityForecast(volatilityData.daily_forecasts || {});

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const syncEconomicEvents = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/economic/sync', { method: 'POST' });
      if (!response.ok) throw new Error('Failed to sync events');
      
      const result = await response.json();
      setLastSync(new Date().toLocaleString());
      
      // Refresh data after sync
      await fetchEconomicData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sync failed');
    }
  };

  useEffect(() => {
    fetchEconomicData();
    
    // Auto-refresh every 60 minutes (reduced from 30 minutes to minimize API calls)
    const interval = setInterval(fetchEconomicData, 60 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const getImportanceBadge = (importance: string) => {
    const variants = {
      LOW: 'secondary',
      MEDIUM: 'default',
      HIGH: 'destructive',
      CRITICAL: 'destructive'
    } as const;
    
    const colors = {
      LOW: 'bg-gray-100 text-gray-800',
      MEDIUM: 'bg-blue-100 text-blue-800',
      HIGH: 'bg-orange-100 text-orange-800',
      CRITICAL: 'bg-red-100 text-red-800'
    };

    return (
      <Badge className={colors[importance as keyof typeof colors] || colors.MEDIUM}>
        {importance}
      </Badge>
    );
  };

  const getEventTypeIcon = (eventType: string) => {
    switch (eventType) {
      case 'FOMC':
        return '🏛️';
      case 'INFLATION':
        return '📈';
      case 'EMPLOYMENT':
        return '👥';
      case 'GDP':
        return '🏭';
      case 'EARNINGS':
        return '💼';
      default:
        return '📊';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading && Object.keys(upcomingEvents).length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading economic events...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with sync button */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Economic Events Calendar</h2>
          <p className="text-muted-foreground">
            Track upcoming economic events and their market impact
          </p>
        </div>
        <Button 
          onClick={syncEconomicEvents} 
          disabled={loading}
          variant="outline"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Sync Events
        </Button>
      </div>

      {error && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {lastSync && (
        <p className="text-sm text-muted-foreground">
          Last synced: {lastSync}
        </p>
      )}

      <Tabs defaultValue="upcoming" className="space-y-4">
        <TabsList>
          <TabsTrigger value="upcoming">Upcoming Events</TabsTrigger>
          <TabsTrigger value="week-summary">Week Summary</TabsTrigger>
          <TabsTrigger value="volatility">Volatility Forecast</TabsTrigger>
        </TabsList>

        <TabsContent value="upcoming" className="space-y-4">
          {Object.keys(upcomingEvents).length === 0 ? (
            <Card>
              <CardContent className="flex items-center justify-center h-32">
                <p className="text-muted-foreground">No upcoming events found</p>
              </CardContent>
            </Card>
          ) : (
            Object.entries(upcomingEvents).map(([date, events]) => (
              <Card key={date}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Calendar className="h-5 w-5" />
                    {formatDate(date)}
                    <Badge variant="outline">{events.length} events</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {events.map((event) => (
                      <div key={event.id} className="flex items-start justify-between p-3 border rounded-lg">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-lg">{getEventTypeIcon(event.event_type)}</span>
                            <h4 className="font-semibold">{event.name}</h4>
                            {getImportanceBadge(event.importance)}
                          </div>
                          <p className="text-sm text-muted-foreground mb-2">
                            {event.time} | {event.event_type}
                          </p>
                          {event.forecast && (
                            <div className="flex gap-4 text-sm">
                              {event.forecast && (
                                <span>Forecast: <strong>{event.forecast}</strong></span>
                              )}
                              {event.previous && (
                                <span>Previous: {event.previous}</span>
                              )}
                            </div>
                          )}
                        </div>
                        <div className="text-right">
                          {event.impact_score && (
                            <div className="mb-1">
                              <Badge variant="outline">
                                Impact: {event.impact_score.toFixed(0)}
                              </Badge>
                            </div>
                          )}
                          {event.volatility_forecast && (
                            <div className="text-sm text-muted-foreground">
                              Vol: {event.volatility_forecast.toFixed(1)}%
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="week-summary">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                This Week's Economic Impact
              </CardTitle>
              <CardDescription>
                Summary of economic events and their expected market impact
              </CardDescription>
            </CardHeader>
            <CardContent>
              {weekSummary ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {weekSummary.total_events}
                    </div>
                    <div className="text-sm text-muted-foreground">Total Events</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      {weekSummary.high_impact_events}
                    </div>
                    <div className="text-sm text-muted-foreground">High Impact</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">
                      {weekSummary.total_impact_score.toFixed(0)}
                    </div>
                    <div className="text-sm text-muted-foreground">Total Impact Score</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {weekSummary.average_volatility_forecast.toFixed(1)}%
                    </div>
                    <div className="text-sm text-muted-foreground">Avg Volatility</div>
                  </div>
                </div>
              ) : (
                <p className="text-muted-foreground">No week summary available</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="volatility">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5" />
                SPY Volatility Forecast
              </CardTitle>
              <CardDescription>
                Expected volatility based on upcoming economic events
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(volatilityForecast).map(([date, forecast]) => (
                  <div key={date} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <div className="font-semibold">{formatDate(date)}</div>
                      <div className="text-sm text-muted-foreground">
                        {forecast.events.length} events
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-lg font-bold ${
                        forecast.expected_volatility > 10 ? 'text-red-600' :
                        forecast.expected_volatility > 7 ? 'text-orange-600' :
                        'text-green-600'
                      }`}>
                        {forecast.expected_volatility.toFixed(1)}%
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Expected Vol
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
});

export default EconomicEventsDashboard;