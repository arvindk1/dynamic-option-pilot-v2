
import React from 'react';
import TradingDashboard from '@/components/TradingDashboard';
import { TradingErrorBoundary } from '@/components/TradingErrorBoundary';

const Index = () => {
  console.log('🎯 Index component rendering...');
  
  return (
    <div className="trading-dashboard">
      <TradingErrorBoundary>
        <TradingDashboard />
      </TradingErrorBoundary>
    </div>
  );
};

export default Index;
