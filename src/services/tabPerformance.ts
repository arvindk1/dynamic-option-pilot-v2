// Tab performance optimization service
class TabPerformanceService {
  private renderTimes = new Map<string, number>();
  private lastActiveTab = '';
  
  measureTabSwitch(tabName: string): void {
    const startTime = performance.now();
    
    // Use requestAnimationFrame to measure after DOM updates
    requestAnimationFrame(() => {
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      this.renderTimes.set(tabName, renderTime);
      
      // Log performance in development
      if (process.env.NODE_ENV === 'development') {
        console.log(`Tab ${tabName} rendered in ${renderTime.toFixed(2)}ms`);
      }
    });
  }
  
  getTabRenderTime(tabName: string): number | undefined {
    return this.renderTimes.get(tabName);
  }
  
  getAverageRenderTime(): number {
    const times = Array.from(this.renderTimes.values());
    return times.length > 0 ? times.reduce((a, b) => a + b, 0) / times.length : 0;
  }
  
  // Preload critical resources for likely next tabs
  preloadTabResources(tabName: string): void {
    switch (tabName) {
      case 'trades':
        // Preload trading opportunities
        fetch('/api/trading/opportunities').catch(() => {});
        break;
      case 'positions':
        // Preload positions data
        fetch('/api/positions').catch(() => {});
        break;
      case 'risk':
        // Preload risk metrics
        fetch('/api/analytics/risk-metrics').catch(() => {});
        break;
      case 'sentiment':
        // Preload sentiment data
        fetch('/api/sentiment/pulse').catch(() => {});
        break;
    }
  }
}

export const tabPerformanceService = new TabPerformanceService();