import React, { useState, useEffect } from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AlertTriangle, CheckCircle, XCircle, RefreshCw, Activity } from 'lucide-react';

interface DataSource {
  status: 'HEALTHY' | 'DEGRADED' | 'ERROR' | 'OFFLINE';
  last_test: string;
  error?: string;
}

interface SystemStatusData {
  overall_status: 'HEALTHY' | 'DEGRADED' | 'CRITICAL';
  timestamp: string;
  data_sources: {
    yfinance: DataSource;
    database: DataSource;
    opportunity_cache: DataSource;
  };
  health_summary: {
    healthy_sources: number;
    total_sources: number;
    health_percentage: number;
  };
}

export const SystemStatus: React.FC = () => {
  const [systemStatus, setSystemStatus] = useState<SystemStatusData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchSystemStatus = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/system/status');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setSystemStatus(data);
      setLastUpdate(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch system status');
      console.error('System status fetch failed:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemStatus();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchSystemStatus, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'HEALTHY':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'DEGRADED':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'ERROR':
      case 'CRITICAL':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'OFFLINE':
        return <XCircle className="h-4 w-4 text-gray-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'HEALTHY':
        return 'bg-green-500';
      case 'DEGRADED':
        return 'bg-yellow-500';
      case 'ERROR':
      case 'CRITICAL':
        return 'bg-red-500';
      case 'OFFLINE':
        return 'bg-gray-500';
      default:
        return 'bg-gray-400';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>System Status Unavailable</AlertTitle>
        <AlertDescription>
          {error}
          <Button 
            variant="outline" 
            size="sm" 
            className="ml-2" 
            onClick={fetchSystemStatus}
            disabled={loading}
          >
            <RefreshCw className={`h-3 w-3 mr-1 ${loading ? 'animate-spin' : ''}`} />
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  if (!systemStatus) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            System Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center p-4">
            <RefreshCw className="h-5 w-5 animate-spin mr-2" />
            Loading system status...
          </div>
        </CardContent>
      </Card>
    );
  }

  const criticalIssues = Object.entries(systemStatus.data_sources).filter(
    ([, source]) => source.status === 'ERROR' || source.status === 'CRITICAL'
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getStatusIcon(systemStatus.overall_status)}
            System Status
            <Badge 
              variant={systemStatus.overall_status === 'HEALTHY' ? 'default' : 'destructive'}
              className={getStatusColor(systemStatus.overall_status)}
            >
              {systemStatus.overall_status}
            </Badge>
          </div>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={fetchSystemStatus}
            disabled={loading}
          >
            <RefreshCw className={`h-3 w-3 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Overall Health Summary */}
        <div className="flex items-center justify-between text-sm">
          <span>Health: {systemStatus.health_summary.healthy_sources}/{systemStatus.health_summary.total_sources} sources</span>
          <span className="text-muted-foreground">
            {systemStatus.health_summary.health_percentage}%
          </span>
        </div>

        {/* Critical Issues Alert */}
        {criticalIssues.length > 0 && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Critical Issues Detected</AlertTitle>
            <AlertDescription>
              <ul className="mt-2 space-y-1">
                {criticalIssues.map(([name, source]) => (
                  <li key={name} className="text-sm">
                    <strong>{name.replace('_', ' ').toUpperCase()}:</strong> {source.error || 'Service unavailable'}
                  </li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {/* Data Sources Status */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium">Data Sources</h4>
          <div className="grid gap-2">
            {Object.entries(systemStatus.data_sources).map(([name, source]) => (
              <div key={name} className="flex items-center justify-between p-2 bg-muted/50 rounded">
                <div className="flex items-center gap-2">
                  {getStatusIcon(source.status)}
                  <span className="text-sm font-medium">
                    {name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                </div>
                <div className="text-right">
                  <Badge 
                    variant={source.status === 'HEALTHY' ? 'default' : 'destructive'}
                    className={`${getStatusColor(source.status)} text-xs`}
                  >
                    {source.status}
                  </Badge>
                  <div className="text-xs text-muted-foreground mt-1">
                    {formatTimestamp(source.last_test)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Last Update */}
        <div className="text-xs text-muted-foreground text-center pt-2 border-t">
          Last updated: {lastUpdate ? lastUpdate.toLocaleTimeString() : 'Never'}
        </div>
      </CardContent>
    </Card>
  );
};

export default SystemStatus;