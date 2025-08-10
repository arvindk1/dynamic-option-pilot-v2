/**
 * Performance monitoring utilities for the trading platform
 */
import React from 'react';

export class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private timers: Map<string, number> = new Map();
  private measurements: Array<{name: string, duration: number, timestamp: number}> = [];

  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  startTimer(name: string): void {
    this.timers.set(name, performance.now());
    console.log(`⏱️ Started: ${name}`);
  }

  endTimer(name: string): number {
    const startTime = this.timers.get(name);
    if (!startTime) {
      console.warn(`⚠️ Timer "${name}" was not started`);
      return 0;
    }

    const duration = performance.now() - startTime;
    this.timers.delete(name);
    
    this.measurements.push({
      name,
      duration,
      timestamp: Date.now()
    });

    if (duration > 100) {
      console.warn(`🐌 SLOW: ${name} took ${duration.toFixed(2)}ms`);
    } else {
      console.log(`✅ Fast: ${name} took ${duration.toFixed(2)}ms`);
    }

    return duration;
  }

  measureAsync<T>(name: string, asyncFn: () => Promise<T>): Promise<T> {
    this.startTimer(name);
    return asyncFn().finally(() => {
      this.endTimer(name);
    });
  }

  measureSync<T>(name: string, syncFn: () => T): T {
    this.startTimer(name);
    try {
      return syncFn();
    } finally {
      this.endTimer(name);
    }
  }

  getSlowOperations(threshold: number = 100): Array<{name: string, duration: number}> {
    return this.measurements
      .filter(m => m.duration > threshold)
      .sort((a, b) => b.duration - a.duration);
  }

  getReport(): string {
    const slow = this.getSlowOperations();
    const total = this.measurements.reduce((sum, m) => sum + m.duration, 0);
    
    return `
🔍 Performance Report:
Total time: ${total.toFixed(2)}ms
Operations: ${this.measurements.length}
Slow operations (>100ms): ${slow.length}

Slowest operations:
${slow.slice(0, 5).map(op => `  ${op.name}: ${op.duration.toFixed(2)}ms`).join('\n')}
    `.trim();
  }
}

// React hook for component performance monitoring
export const usePerformanceMonitoring = (componentName: string) => {
  const monitor = PerformanceMonitor.getInstance();

  const measureRender = (renderName: string = 'render') => {
    const fullName = `${componentName}.${renderName}`;
    monitor.startTimer(fullName);
    
    return () => monitor.endTimer(fullName);
  };

  const measureApiCall = async <T>(apiName: string, apiCall: () => Promise<T>): Promise<T> => {
    return monitor.measureAsync(`${componentName}.${apiName}`, apiCall);
  };

  return {
    measureRender,
    measureApiCall,
    startTimer: (name: string) => monitor.startTimer(`${componentName}.${name}`),
    endTimer: (name: string) => monitor.endTimer(`${componentName}.${name}`)
  };
};

// Browser performance utilities
export const measurePageLoad = () => {
  const monitor = PerformanceMonitor.getInstance();
  
  // Measure key loading metrics
  window.addEventListener('load', () => {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    
    const metrics = {
      dnsLookup: Math.max(0, navigation.domainLookupEnd - navigation.domainLookupStart),
      tcpConnection: Math.max(0, navigation.connectEnd - navigation.connectStart),
      tlsSetup: navigation.secureConnectionStart > 0 ? Math.max(0, navigation.connectEnd - navigation.secureConnectionStart) : 0,
      requestResponse: Math.max(0, navigation.responseEnd - navigation.requestStart),
      domProcessing: Math.max(0, navigation.domContentLoadedEventEnd - navigation.responseEnd),
      resourceLoading: Math.max(0, navigation.loadEventEnd - navigation.domContentLoadedEventEnd),
      totalLoadTime: Math.max(0, navigation.loadEventEnd - navigation.navigationStart)
    };
    
    console.log(`📊 Page Load Metrics:
- DNS Lookup: ${metrics.dnsLookup.toFixed(2)}ms
- TCP Connection: ${metrics.tcpConnection.toFixed(2)}ms  
- TLS Setup: ${metrics.tlsSetup.toFixed(2)}ms
- Request/Response: ${metrics.requestResponse.toFixed(2)}ms
- DOM Processing: ${metrics.domProcessing.toFixed(2)}ms
- Resource Loading: ${metrics.resourceLoading.toFixed(2)}ms
- Total Load Time: ${metrics.totalLoadTime.toFixed(2)}ms`);

    // Store metrics for potential display
    (window as any).performanceMetrics = metrics;
  });

  // Measure First Contentful Paint
  const observer = new PerformanceObserver((list) => {
    list.getEntries().forEach((entry) => {
      if (entry.name === 'first-contentful-paint') {
        console.log(`🎨 First Contentful Paint: ${entry.startTime.toFixed(2)}ms`);
        (window as any).firstContentfulPaint = entry.startTime;
      }
      if (entry.name === 'largest-contentful-paint') {
        console.log(`🖼️ Largest Contentful Paint: ${entry.startTime.toFixed(2)}ms`);
        (window as any).largestContentfulPaint = entry.startTime;
      }
    });
  });
  
  observer.observe({ entryTypes: ['paint', 'largest-contentful-paint'] });
};

// React performance optimizer hook
export const useRenderOptimization = (componentName: string) => {
  const renderCount = React.useRef(0);
  const lastProps = React.useRef<any>(null);
  
  React.useEffect(() => {
    renderCount.current += 1;
    if (process.env.NODE_ENV === 'development' && renderCount.current > 10) {
      console.warn(`🔄 ${componentName} has rendered ${renderCount.current} times. Consider optimization.`);
    }
  });

  const trackPropsChange = React.useCallback((props: any) => {
    if (process.env.NODE_ENV === 'development' && lastProps.current) {
      const changedProps = Object.keys(props).filter(
        key => props[key] !== lastProps.current[key]
      );
      if (changedProps.length > 0) {
        console.log(`🔄 ${componentName} re-rendered due to props change:`, changedProps);
      }
    }
    lastProps.current = props;
  }, [componentName]);

  return { trackPropsChange, renderCount: renderCount.current };
};

export default PerformanceMonitor;