
import React, { memo } from 'react';
import TradingDashboard from '@/components/TradingDashboard';
import { TradingErrorBoundary } from '@/components/TradingErrorBoundary';

const Index = memo(() => {
  console.log('🎯 Index component rendering...');
  
  return (
    <div className="trading-dashboard">
      <TradingErrorBoundary>
        <TradingDashboard />
      </TradingErrorBoundary>
    </div>
  );
});

Index.displayName = 'Index';

export default Index;
