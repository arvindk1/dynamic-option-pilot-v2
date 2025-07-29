import React, { useEffect, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Monitor } from 'lucide-react';

interface TabPerformanceData {
  tabName: string;
  loadTime: number;
  lastAccessed: number;
  accessCount: number;
}

export const TabPerformanceMonitor: React.FC<{ 
  activeTab: string;
  onPerformanceData?: (data: TabPerformanceData) => void;
}> = ({ activeTab, onPerformanceData }) => {
  const [performanceData, setPerformanceData] = useState<Map<string, TabPerformanceData>>(new Map());
  const [tabLoadStart, setTabLoadStart] = useState<number>(Date.now());
  const [isTimingActive, setIsTimingActive] = useState<boolean>(true);

  useEffect(() => {
    // Start timing when tab changes
    setTabLoadStart(Date.now());
    setIsTimingActive(true);
  }, [activeTab]);

  useEffect(() => {
    // Only record load completion once per tab switch
    if (!isTimingActive) return;

    const timer = setTimeout(() => {
      const loadTime = Date.now() - tabLoadStart;
      const tabData: TabPerformanceData = {
        tabName: activeTab,
        loadTime,
        lastAccessed: Date.now(),
        accessCount: (performanceData.get(activeTab)?.accessCount || 0) + 1
      };

      setPerformanceData(prev => new Map(prev.set(activeTab, tabData)));
      onPerformanceData?.(tabData);
      setIsTimingActive(false); // Stop the timer after first measurement
    }, 100);

    return () => clearTimeout(timer);
  }, [activeTab, tabLoadStart, isTimingActive, onPerformanceData]);

  // Show performance info only in development
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  const currentTabData = performanceData.get(activeTab);

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <Badge variant="secondary" className="flex items-center space-x-1">
        <Monitor className="h-3 w-3" />
        <span>
          {activeTab}: {currentTabData?.loadTime || 0}ms
        </span>
      </Badge>
    </div>
  );
};