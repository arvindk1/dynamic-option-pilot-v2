import React, { useState, useEffect, Suspense, lazy } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Loader2 } from 'lucide-react';

interface LazyTabContentProps {
  isActive: boolean;
  children: React.ReactNode;
  loadOnMount?: boolean;
  preload?: boolean;
  className?: string;
}

const LoadingFallback = () => (
  <div className="space-y-6">
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-center space-x-2">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="text-sm text-muted-foreground">Loading tab content...</span>
        </div>
        <div className="space-y-4 mt-4">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-32 w-full" />
        </div>
      </CardContent>
    </Card>
  </div>
);

export const LazyTabContent: React.FC<LazyTabContentProps> = React.memo(({ 
  isActive, 
  children, 
  loadOnMount = false,
  preload = false,
  className = "space-y-6"
}) => {
  const [shouldLoad, setShouldLoad] = useState(loadOnMount);
  const [hasLoaded, setHasLoaded] = useState(loadOnMount);

  useEffect(() => {
    if ((isActive || preload) && !hasLoaded) {
      setShouldLoad(true);
      setHasLoaded(true);
    }
  }, [isActive, preload, hasLoaded]);

  // Don't render anything if not active and hasn't been loaded yet
  if (!isActive && !hasLoaded) {
    return null;
  }

  // Show loading state while loading for the first time
  if (!shouldLoad || (isActive && !hasLoaded)) {
    return <LoadingFallback />;
  }

  return (
    <div 
      className={`${className} tab-content-wrapper`}
      style={{ display: isActive ? 'block' : 'none' }}
      data-state={isActive ? 'active' : 'inactive'}
    >
      <Suspense fallback={<LoadingFallback />}>
        {children}
      </Suspense>
    </div>
  );
});

// Create lazy-loaded tab components
export const LazySentimentDashboard = lazy(() => 
  import('@/components/SentimentDashboard').then(module => ({ 
    default: module.SentimentDashboard 
  }))
);

export const LazyEconomicEventsDashboard = lazy(() => 
  import('@/components/EconomicEventsDashboard').then(module => ({
    default: module.default
  }))
);

export const LazyAITradeCoach = lazy(() => 
  import('@/components/AITradeCoach').then(module => ({
    default: module.default
  }))
);

export const LazyEnhancedSignalsTab = lazy(() => 
  import('@/components/EnhancedSignalsTab').then(module => ({
    default: module.default
  }))
);

export const LazyEnhancedRiskTab = lazy(() => 
  import('@/components/EnhancedRiskTab').then(module => ({
    default: module.default
  }))
);

export const LazyTradeManager = lazy(() => 
  import('@/components/TradeManager').then(module => ({
    default: module.TradeManager
  }))
);

export const LazyMarketCommentary = lazy(() => 
  import('@/components/MarketCommentary').then(module => ({
    default: module.MarketCommentary || module.default
  }))
);