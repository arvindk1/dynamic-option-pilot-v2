import React, { Component, ReactNode } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  AlertTriangle, 
  RefreshCw, 
  ArrowLeft, 
  Bug,
  Wifi,
  Database,
  TrendingDown
} from 'lucide-react';

interface ErrorInfo {
  componentStack: string;
  errorBoundary?: string;
}

interface TradingError {
  type: 'NETWORK' | 'DATA' | 'EXECUTION' | 'VALIDATION' | 'UNKNOWN';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  message: string;
  technicalDetails?: string;
  recoveryActions: RecoveryAction[];
}

interface RecoveryAction {
  label: string;
  action: () => void;
  variant: 'default' | 'destructive' | 'outline' | 'secondary';
  icon?: ReactNode;
}

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  context?: 'trading' | 'data' | 'general';
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  tradingError: TradingError | null;
  retryCount: number;
}

export class TradingErrorBoundary extends Component<Props, State> {
  private maxRetries = 3;
  
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      tradingError: null,
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const tradingError = this.classifyError(error, errorInfo);
    
    this.setState({
      errorInfo,
      tradingError
    });

    // Log error for monitoring
    this.logTradingError(error, errorInfo, tradingError);
    
    // Call optional error handler
    this.props.onError?.(error, errorInfo);
  }

  private classifyError(error: Error, errorInfo: ErrorInfo): TradingError {
    const message = error.message.toLowerCase();
    const stack = error.stack?.toLowerCase() || '';
    
    // Network-related errors
    if (message.includes('network') || message.includes('fetch') || 
        message.includes('websocket') || message.includes('connection')) {
      return {
        type: 'NETWORK',
        severity: 'HIGH',
        message: 'Connection issue detected',
        technicalDetails: error.message,
        recoveryActions: [
          {
            label: 'Retry Connection',
            action: this.handleRetry,
            variant: 'default',
            icon: <Wifi className="h-4 w-4" />
          },
          {
            label: 'Check Network',
            action: () => window.open('https://fast.com', '_blank'),
            variant: 'outline',
            icon: <TrendingDown className="h-4 w-4" />
          }
        ]
      };
    }

    // Data-related errors
    if (message.includes('data') || message.includes('parse') || 
        message.includes('json') || stack.includes('tradingdashboard')) {
      return {
        type: 'DATA',
        severity: 'MEDIUM',
        message: 'Data processing error',
        technicalDetails: error.message,
        recoveryActions: [
          {
            label: 'Refresh Data',
            action: this.handleDataRefresh,
            variant: 'default',
            icon: <Database className="h-4 w-4" />
          },
          {
            label: 'Reset Dashboard',
            action: this.handleReset,
            variant: 'outline',
            icon: <RefreshCw className="h-4 w-4" />
          }
        ]
      };
    }

    // Execution/trading errors
    if (message.includes('execution') || message.includes('trade') || 
        message.includes('order') || stack.includes('executor')) {
      return {
        type: 'EXECUTION',
        severity: 'CRITICAL',
        message: 'Trading execution error',
        technicalDetails: error.message,
        recoveryActions: [
          {
            label: 'Check Positions',
            action: () => window.location.hash = '#positions',
            variant: 'default',
            icon: <ArrowLeft className="h-4 w-4" />
          },
          {
            label: 'Contact Support',
            action: () => window.open('mailto:support@dynamicoptionpilot.com', '_blank'),
            variant: 'destructive',
            icon: <Bug className="h-4 w-4" />
          }
        ]
      };
    }

    // Validation errors
    if (message.includes('validation') || message.includes('invalid') || 
        message.includes('required')) {
      return {
        type: 'VALIDATION',
        severity: 'LOW',
        message: 'Input validation error',
        technicalDetails: error.message,
        recoveryActions: [
          {
            label: 'Try Again',
            action: this.handleRetry,
            variant: 'default',
            icon: <RefreshCw className="h-4 w-4" />
          }
        ]
      };
    }

    // Unknown error
    return {
      type: 'UNKNOWN',
      severity: 'HIGH',
      message: 'An unexpected error occurred',
      technicalDetails: error.message,
      recoveryActions: [
        {
          label: 'Reload Page',
          action: () => window.location.reload(),
          variant: 'default',
          icon: <RefreshCw className="h-4 w-4" />
        },
        {
          label: 'Report Bug',
          action: () => window.open('mailto:support@dynamicoptionpilot.com', '_blank'),
          variant: 'outline',
          icon: <Bug className="h-4 w-4" />
        }
      ]
    };
  }

  private logTradingError = (error: Error, errorInfo: ErrorInfo, tradingError: TradingError) => {
    // In development, log to console
    if (process.env.NODE_ENV === 'development') {
      console.group('🚨 Trading Error Boundary');
      console.error('Error:', error);
      console.error('Error Stack:', error.stack);
      console.error('Error Info:', errorInfo); 
      console.error('Component Stack:', errorInfo.componentStack);
      console.error('Classified Error:', tradingError);
      console.groupEnd();
    }

    // In production, send to monitoring service
    if (process.env.NODE_ENV === 'production') {
      try {
        // Replace with your error monitoring service (e.g., Sentry)
        fetch('/api/errors', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            error: error.message,
            stack: error.stack,
            componentStack: errorInfo.componentStack,
            tradingError,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href
          })
        }).catch(console.error);
      } catch (e) {
        console.error('Failed to log error:', e);
      }
    }
  };

  private handleRetry = () => {
    if (this.state.retryCount < this.maxRetries) {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorInfo: null,
        tradingError: null,
        retryCount: prevState.retryCount + 1
      }));
    } else {
      // Max retries reached, offer different recovery
      this.handleReset();
    }
  };

  private handleDataRefresh = () => {
    // Trigger data refresh
    window.dispatchEvent(new CustomEvent('trading-data-refresh'));
    this.handleRetry();
  };

  private handleReset = () => {
    // Clear any cached data
    localStorage.removeItem('trading-cache');
    sessionStorage.clear();
    
    // Reset error state
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      tradingError: null,
      retryCount: 0
    });
  };

  private getSeverityColor = (severity: TradingError['severity']) => {
    switch (severity) {
      case 'LOW': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'MEDIUM': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'HIGH': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'CRITICAL': return 'text-red-600 bg-red-50 border-red-200';
    }
  };

  render() {
    if (this.state.hasError && this.state.tradingError) {
      const { tradingError } = this.state;
      
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="error-boundary-container p-6 min-h-[400px] flex items-center justify-center">
          <Card className="max-w-2xl w-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <div className={`p-2 rounded-full ${this.getSeverityColor(tradingError.severity)}`}>
                  <AlertTriangle className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-xl font-bold">Trading Platform Error</h2>
                  <p className="text-sm text-muted-foreground font-normal">
                    {tradingError.type} • {tradingError.severity} Priority
                  </p>
                </div>
              </CardTitle>
            </CardHeader>
            
            <CardContent className="space-y-6">
              <Alert className={this.getSeverityColor(tradingError.severity)}>
                <AlertDescription className="text-base">
                  {tradingError.message}
                </AlertDescription>
              </Alert>

              {/* Recovery Actions */}
              <div className="space-y-3">
                <h3 className="font-semibold text-foreground">Recommended Actions:</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {tradingError.recoveryActions.map((action, index) => (
                    <Button
                      key={index}
                      variant={action.variant}
                      onClick={action.action}
                      className="flex items-center gap-2"
                    >
                      {action.icon}
                      {action.label}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Retry Counter */}
              {this.state.retryCount > 0 && (
                <div className="text-sm text-muted-foreground">
                  Retry attempt: {this.state.retryCount} / {this.maxRetries}
                </div>
              )}

              {/* Technical Details (Development) */}
              {process.env.NODE_ENV === 'development' && tradingError.technicalDetails && (
                <details className="text-sm">
                  <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                    Technical Details
                  </summary>
                  <pre className="mt-2 p-3 bg-muted rounded text-xs overflow-auto">
                    {tradingError.technicalDetails}
                  </pre>
                </details>
              )}

              {/* Help Text */}
              <div className="text-sm text-muted-foreground border-t pt-4">
                <p>
                  If the problem persists, please{' '}
                  <button 
                    onClick={() => window.open('mailto:support@dynamicoptionpilot.com', '_blank')}
                    className="underline hover:text-foreground"
                  >
                    contact support
                  </button>
                  {' '}with details about what you were doing when this error occurred.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

// Higher-order component for easy wrapping
export const withTradingErrorBoundary = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  context?: Props['context']
) => {
  const WithErrorBoundary = (props: P) => (
    <TradingErrorBoundary context={context}>
      <WrappedComponent {...props} />
    </TradingErrorBoundary>
  );
  
  WithErrorBoundary.displayName = `withTradingErrorBoundary(${WrappedComponent.displayName || WrappedComponent.name})`;
  return WithErrorBoundary;
};

export default TradingErrorBoundary;