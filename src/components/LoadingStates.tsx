import React from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import { 
  Loader2, 
  Activity, 
  TrendingUp, 
  BarChart3, 
  DollarSign,
  Shield,
  Target,
  Brain,
  Newspaper
} from 'lucide-react';

// Base loading spinner component
export const LoadingSpinner: React.FC<{
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  className?: string;
}> = ({ size = 'md', text, className = '' }) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8'
  };

  return (
    <div className={`flex items-center justify-center space-x-2 ${className}`}>
      <Loader2 className={`animate-spin ${sizeClasses[size]}`} />
      {text && <span className="text-sm text-muted-foreground">{text}</span>}
    </div>
  );
};

// Trading card loading skeleton
export const TradingCardSkeleton: React.FC<{ count?: number }> = ({ count = 1 }) => (
  <>
    {Array.from({ length: count }).map((_, index) => (
      <Card key={index} className="trading-card-skeleton">
        <CardHeader className="pb-4">
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <Skeleton className="h-6 w-32" />
              <Skeleton className="h-4 w-48" />
            </div>
            <Skeleton className="h-8 w-8 rounded-full" />
          </div>
          
          {/* Key metrics skeletons */}
          <div className="grid grid-cols-3 gap-3 mt-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="text-center p-2 bg-muted/30 rounded-lg border">
                <Skeleton className="h-6 w-16 mx-auto mb-1" />
                <Skeleton className="h-3 w-20 mx-auto" />
              </div>
            ))}
          </div>
          
          {/* Secondary info skeleton */}
          <div className="flex items-center justify-between mt-3">
            <div className="flex items-center gap-3">
              <Skeleton className="h-6 w-16" />
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-12" />
            </div>
            <Skeleton className="h-4 w-24" />
          </div>
        </CardHeader>
        
        <CardContent>
          {/* Action buttons skeleton */}
          <div className="flex items-center gap-2">
            <Skeleton className="h-9 flex-1" />
            <Skeleton className="h-9 w-9" />
            <Skeleton className="h-9 w-9" />
            <Skeleton className="h-9 w-9" />
          </div>
        </CardContent>
      </Card>
    ))}
  </>
);

// Dashboard section loading states
export const DashboardLoadingState: React.FC<{ 
  section: 'overview' | 'trades' | 'positions' | 'risk' | 'sentiment' | 'economic' | 'signals';
}> = ({ section }) => {
  const getSectionIcon = () => {
    const iconMap = {
      overview: Activity,
      trades: TrendingUp,
      positions: DollarSign,
      risk: Shield,
      sentiment: Brain,
      economic: BarChart3,
      signals: Target
    };
    
    const Icon = iconMap[section];
    return <Icon className="h-5 w-5" />;
  };

  const getSectionTitle = () => {
    const titleMap = {
      overview: 'Loading Overview',
      trades: 'Loading Trading Opportunities',
      positions: 'Loading Positions',
      risk: 'Loading Risk Analysis',
      sentiment: 'Loading Market Sentiment',
      economic: 'Loading Economic Data',
      signals: 'Loading Trading Signals'
    };
    
    return titleMap[section];
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center space-x-2">
            {getSectionIcon()}
            <Skeleton className="h-6 w-48" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-12">
            <div className="text-center space-y-4">
              <LoadingSpinner size="lg" />
              <div className="space-y-2">
                <p className="text-lg font-medium">{getSectionTitle()}</p>
                <p className="text-sm text-muted-foreground">
                  Please wait while we fetch the latest data...
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Specific loading states for different components
export const MarketDataLoadingState: React.FC = () => (
  <Card>
    <CardHeader>
      <div className="flex items-center space-x-2">
        <Activity className="h-5 w-5 text-blue-500" />
        <Skeleton className="h-6 w-32" />
      </div>
    </CardHeader>
    <CardContent>
      <div className="space-y-4">
        {/* Chart area */}
        <Skeleton className="h-64 w-full" />
        
        {/* Stats row */}
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="text-center">
              <Skeleton className="h-8 w-16 mx-auto mb-2" />
              <Skeleton className="h-4 w-20 mx-auto" />
            </div>
          ))}
        </div>
      </div>
    </CardContent>
  </Card>
);

export const OptionsChainLoadingState: React.FC = () => (
  <Card>
    <CardHeader>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Target className="h-5 w-5 text-green-500" />
          <Skeleton className="h-6 w-40" />
        </div>
        <Skeleton className="h-6 w-24" />
      </div>
    </CardHeader>
    <CardContent>
      <div className="space-y-4">
        {/* Header row */}
        <div className="grid grid-cols-7 gap-2 pb-2 border-b">
          {['Calls', 'Strike', 'Puts', 'Vol', 'OI', 'IV', 'Delta'].map((header) => (
            <Skeleton key={header} className="h-4 w-full" />
          ))}
        </div>
        
        {/* Data rows */}
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="grid grid-cols-7 gap-2">
            {Array.from({ length: 7 }).map((_, j) => (
              <Skeleton key={j} className="h-6 w-full" />
            ))}
          </div>
        ))}
      </div>
    </CardContent>
  </Card>
);

export const RiskAnalysisLoadingState: React.FC = () => (
  <div className="space-y-6">
    {/* Portfolio Greeks */}
    <Card>
      <CardHeader>
        <div className="flex items-center space-x-2">
          <Shield className="h-5 w-5 text-red-500" />
          <Skeleton className="h-6 w-32" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {['Delta', 'Gamma', 'Theta', 'Vega'].map((greek) => (
            <div key={greek} className="text-center p-4 border rounded-lg">
              <Skeleton className="h-8 w-20 mx-auto mb-2" />
              <Skeleton className="h-4 w-16 mx-auto" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
    
    {/* Risk Metrics */}
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-40" />
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center justify-between p-3 bg-muted/30 rounded">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-4 w-20" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  </div>
);

export const AIAnalysisLoadingState: React.FC = () => (
  <Card>
    <CardHeader>
      <div className="flex items-center space-x-2">
        <Brain className="h-5 w-5 text-purple-500 animate-pulse" />
        <Skeleton className="h-6 w-40" />
      </div>
    </CardHeader>
    <CardContent>
      <div className="space-y-4">
        {/* Analysis progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm">Analyzing market conditions...</span>
            <span className="text-sm text-muted-foreground">67%</span>
          </div>
          <Progress value={67} className="h-2" />
        </div>
        
        {/* Content placeholders */}
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex gap-3">
              <Skeleton className="h-2 w-2 rounded-full mt-2" />
              <Skeleton className={`h-4 ${i === 1 ? 'w-full' : i === 2 ? 'w-3/4' : 'w-1/2'}`} />
            </div>
          ))}
        </div>
      </div>
    </CardContent>
  </Card>
);

export const NewsLoadingState: React.FC = () => (
  <Card>
    <CardHeader>
      <div className="flex items-center space-x-2">
        <Newspaper className="h-5 w-5 text-blue-500" />
        <Skeleton className="h-6 w-32" />
      </div>
    </CardHeader>
    <CardContent>
      <div className="space-y-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="border-b pb-4 last:border-b-0">
            <Skeleton className="h-5 w-3/4 mb-2" />
            <Skeleton className="h-4 w-full mb-1" />
            <Skeleton className="h-4 w-2/3" />
            <div className="flex items-center gap-4 mt-2">
              <Skeleton className="h-3 w-16" />
              <Skeleton className="h-3 w-20" />
            </div>
          </div>
        ))}
      </div>
    </CardContent>
  </Card>
);

// Progressive loading with stages
export interface ProgressiveLoadingStage {
  id: string;
  title: string;
  description?: string;
  completed: boolean;
  error?: string;
}

export const ProgressiveLoadingState: React.FC<{
  stages: ProgressiveLoadingStage[];
  currentStage?: string;
  title?: string;
}> = ({ stages, currentStage, title = "Loading Trading Platform" }) => {
  const completedCount = stages.filter(s => s.completed).length;
  const progress = (completedCount / stages.length) * 100;

  return (
    <Card>
      <CardHeader>
        <div className="text-center space-y-2">
          <h2 className="text-lg font-semibold">{title}</h2>
          <Progress value={progress} className="h-2" />
          <p className="text-sm text-muted-foreground">
            {completedCount} of {stages.length} components loaded
          </p>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {stages.map((stage) => (
            <div key={stage.id} className="flex items-center gap-3">
              {stage.error ? (
                <div className="h-4 w-4 rounded-full bg-red-500 flex items-center justify-center">
                  <span className="text-white text-xs">!</span>
                </div>
              ) : stage.completed ? (
                <div className="h-4 w-4 rounded-full bg-green-500 flex items-center justify-center">
                  <span className="text-white text-xs">✓</span>
                </div>
              ) : currentStage === stage.id ? (
                <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
              ) : (
                <div className="h-4 w-4 rounded-full bg-gray-300" />
              )}
              
              <div className="flex-1">
                <div className="text-sm font-medium">{stage.title}</div>
                {stage.description && (
                  <div className="text-xs text-muted-foreground">{stage.description}</div>
                )}
                {stage.error && (
                  <div className="text-xs text-red-600">{stage.error}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default {
  LoadingSpinner,
  TradingCardSkeleton,
  DashboardLoadingState,
  MarketDataLoadingState,
  OptionsChainLoadingState,
  RiskAnalysisLoadingState,
  AIAnalysisLoadingState,
  NewsLoadingState,
  ProgressiveLoadingState
};