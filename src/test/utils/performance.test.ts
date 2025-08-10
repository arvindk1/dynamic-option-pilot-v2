import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { 
  PerformanceMonitor, 
  usePerformanceMonitoring, 
  measurePageLoad,
  useRenderOptimization
} from '@/utils/performance';

// Mock performance APIs
const mockPerformance = {
  now: vi.fn(),
  getEntriesByType: vi.fn(),
  mark: vi.fn(),
  measure: vi.fn()
};

// Mock browser APIs
Object.defineProperty(global, 'performance', {
  value: mockPerformance,
  writable: true
});

// Mock PerformanceObserver
class MockPerformanceObserver {
  private callback: (entries: any) => void;
  
  constructor(callback: (entries: any) => void) {
    this.callback = callback;
  }
  
  observe() {}
  disconnect() {}
  
  // Helper to simulate entries
  simulateEntries(entries: any[]) {
    this.callback({ getEntries: () => entries });
  }
}

global.PerformanceObserver = MockPerformanceObserver as any;

// Mock console methods
const mockConsole = {
  log: vi.fn(),
  warn: vi.fn(),
  error: vi.fn()
};

describe('PerformanceMonitor', () => {
  let monitor: PerformanceMonitor;
  let performanceNowCounter = 0;

  beforeEach(() => {
    vi.clearAllMocks();
    performanceNowCounter = 0;
    
    // Mock performance.now() to return incrementing values
    mockPerformance.now.mockImplementation(() => {
      performanceNowCounter += 100; // Increment by 100ms each call
      return performanceNowCounter;
    });
    
    monitor = PerformanceMonitor.getInstance();
    
    // Mock console methods for each test
    vi.spyOn(console, 'log').mockImplementation(mockConsole.log);
    vi.spyOn(console, 'warn').mockImplementation(mockConsole.warn);
    vi.spyOn(console, 'error').mockImplementation(mockConsole.error);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Singleton Pattern', () => {
    it('returns the same instance', () => {
      const instance1 = PerformanceMonitor.getInstance();
      const instance2 = PerformanceMonitor.getInstance();
      
      expect(instance1).toBe(instance2);
    });
  });

  describe('Timer Functionality', () => {
    it('starts and ends timers correctly', () => {
      monitor.startTimer('test-operation');
      expect(mockPerformance.now).toHaveBeenCalledTimes(1);
      expect(mockConsole.log).toHaveBeenCalledWith('ñ Started: test-operation');
      
      const duration = monitor.endTimer('test-operation');
      expect(mockPerformance.now).toHaveBeenCalledTimes(2);
      expect(duration).toBe(100); // Second call returns 200, first was 100
      expect(mockConsole.log).toHaveBeenCalledWith(' Fast: test-operation took 100.00ms');
    });

    it('warns about slow operations', () => {
      performanceNowCounter = 0;
      mockPerformance.now
        .mockReturnValueOnce(0)     // Start time
        .mockReturnValueOnce(150);  // End time (150ms duration)
      
      monitor.startTimer('slow-operation');
      const duration = monitor.endTimer('slow-operation');
      
      expect(duration).toBe(150);
      expect(mockConsole.warn).toHaveBeenCalledWith('= SLOW: slow-operation took 150.00ms');
    });

    it('handles missing timers gracefully', () => {
      const duration = monitor.endTimer('non-existent-timer');
      
      expect(duration).toBe(0);
      expect(mockConsole.warn).toHaveBeenCalledWith('  Timer "non-existent-timer" was not started');
    });

    it('stores measurements for analysis', () => {
      monitor.startTimer('test-op');
      monitor.endTimer('test-op');
      
      const slowOps = monitor.getSlowOperations(50);
      expect(slowOps).toHaveLength(1);
      expect(slowOps[0].name).toBe('test-op');
      expect(slowOps[0].duration).toBe(100);
    });
  });

  describe('Async Measurement', () => {
    it('measures async operations', async () => {
      const asyncOperation = vi.fn().mockResolvedValue('result');
      
      const result = await monitor.measureAsync('async-test', asyncOperation);
      
      expect(result).toBe('result');
      expect(asyncOperation).toHaveBeenCalledOnce();
      expect(mockConsole.log).toHaveBeenCalledWith('ñ Started: async-test');
    });

    it('measures async operations that throw errors', async () => {
      const failingOperation = vi.fn().mockRejectedValue(new Error('Test error'));
      
      await expect(monitor.measureAsync('failing-async', failingOperation))
        .rejects.toThrow('Test error');
      
      // Should still end the timer even when operation fails
      expect(mockConsole.log).toHaveBeenCalledWith('ñ Started: failing-async');
    });
  });

  describe('Sync Measurement', () => {
    it('measures synchronous operations', () => {
      const syncOperation = vi.fn().mockReturnValue('sync-result');
      
      const result = monitor.measureSync('sync-test', syncOperation);
      
      expect(result).toBe('sync-result');
      expect(syncOperation).toHaveBeenCalledOnce();
    });

    it('measures sync operations that throw errors', () => {
      const failingOperation = vi.fn().mockImplementation(() => {
        throw new Error('Sync error');
      });
      
      expect(() => monitor.measureSync('failing-sync', failingOperation))
        .toThrow('Sync error');
      
      // Should still end the timer
      expect(mockConsole.log).toHaveBeenCalledWith('ñ Started: failing-sync');
    });
  });

  describe('Performance Analysis', () => {
    beforeEach(() => {
      // Add some sample measurements
      performanceNowCounter = 0;
      
      // Fast operation (50ms)
      mockPerformance.now.mockReturnValueOnce(0).mockReturnValueOnce(50);
      monitor.startTimer('fast-op');
      monitor.endTimer('fast-op');
      
      // Slow operation (200ms)  
      mockPerformance.now.mockReturnValueOnce(100).mockReturnValueOnce(300);
      monitor.startTimer('slow-op');
      monitor.endTimer('slow-op');
      
      // Very slow operation (500ms)
      mockPerformance.now.mockReturnValueOnce(300).mockReturnValueOnce(800);
      monitor.startTimer('very-slow-op');
      monitor.endTimer('very-slow-op');
    });

    it('identifies slow operations correctly', () => {
      const slowOps = monitor.getSlowOperations(100);
      
      expect(slowOps).toHaveLength(2);
      expect(slowOps[0].name).toBe('very-slow-op');
      expect(slowOps[0].duration).toBe(500);
      expect(slowOps[1].name).toBe('slow-op');
      expect(slowOps[1].duration).toBe(200);
    });

    it('generates performance reports', () => {
      const report = monitor.getReport();
      
      expect(report).toContain('Performance Report:');
      expect(report).toContain('Total time: 750.00ms'); // 50 + 200 + 500
      expect(report).toContain('Operations: 3');
      expect(report).toContain('Slow operations (>100ms): 2');
      expect(report).toContain('very-slow-op: 500.00ms');
      expect(report).toContain('slow-op: 200.00ms');
    });
  });
});

describe('usePerformanceMonitoring Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPerformance.now.mockReturnValue(100);
    
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
  });

  it('provides performance monitoring methods', () => {
    const { result } = renderHook(() => usePerformanceMonitoring('TestComponent'));
    
    expect(result.current.measureRender).toBeInstanceOf(Function);
    expect(result.current.measureApiCall).toBeInstanceOf(Function);
    expect(result.current.startTimer).toBeInstanceOf(Function);
    expect(result.current.endTimer).toBeInstanceOf(Function);
  });

  it('prefixes timer names with component name', () => {
    const { result } = renderHook(() => usePerformanceMonitoring('TestComponent'));
    
    act(() => {
      result.current.startTimer('custom-operation');
    });
    
    expect(console.log).toHaveBeenCalledWith('ñ Started: TestComponent.custom-operation');
  });

  it('measures render performance', () => {
    const { result } = renderHook(() => usePerformanceMonitoring('TestComponent'));
    
    let endRender: Function;
    
    act(() => {
      endRender = result.current.measureRender('initial-render');
    });
    
    expect(console.log).toHaveBeenCalledWith('ñ Started: TestComponent.initial-render');
    
    act(() => {
      endRender();
    });
    
    expect(console.log).toHaveBeenCalledWith(' Fast: TestComponent.initial-render took 0.00ms');
  });

  it('measures API calls', async () => {
    const { result } = renderHook(() => usePerformanceMonitoring('TestComponent'));
    const mockApiCall = vi.fn().mockResolvedValue('api-result');
    
    const apiResult = await act(async () => {
      return result.current.measureApiCall('fetchData', mockApiCall);
    });
    
    expect(apiResult).toBe('api-result');
    expect(console.log).toHaveBeenCalledWith('ñ Started: TestComponent.fetchData');
  });
});

describe('useRenderOptimization Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
  });

  it('tracks render count in development', () => {
    // Mock development environment
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'development';
    
    const { result, rerender } = renderHook(() => 
      useRenderOptimization('OptimizedComponent')
    );
    
    expect(result.current.renderCount).toBe(1);
    
    // Trigger multiple re-renders
    for (let i = 0; i < 12; i++) {
      rerender();
    }
    
    expect(result.current.renderCount).toBe(13);
    expect(console.warn).toHaveBeenCalledWith(
      '= OptimizedComponent has rendered 13 times. Consider optimization.'
    );
    
    // Restore environment
    process.env.NODE_ENV = originalEnv;
  });

  it('tracks prop changes in development', () => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'development';
    
    const { result } = renderHook(() => 
      useRenderOptimization('OptimizedComponent')
    );
    
    const props1 = { data: 'test1', count: 1 };
    const props2 = { data: 'test2', count: 1 }; // data changed
    
    act(() => {
      result.current.trackPropsChange(props1);
    });
    
    act(() => {
      result.current.trackPropsChange(props2);
    });
    
    expect(console.log).toHaveBeenCalledWith(
      '= OptimizedComponent re-rendered due to props change:', 
      ['data']
    );
    
    // Restore environment
    process.env.NODE_ENV = originalEnv;
  });

  it('skips tracking in production', () => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'production';
    
    const { result, rerender } = renderHook(() => 
      useRenderOptimization('ProductionComponent')
    );
    
    // Trigger many re-renders
    for (let i = 0; i < 20; i++) {
      rerender();
    }
    
    // Should not warn in production
    expect(console.warn).not.toHaveBeenCalled();
    
    // Restore environment
    process.env.NODE_ENV = originalEnv;
  });
});

describe('measurePageLoad', () => {
  let mockNavigationTiming: any;
  let mockAddEventListener: any;

  beforeEach(() => {
    vi.clearAllMocks();
    
    mockNavigationTiming = {
      navigationStart: 0,
      domainLookupStart: 10,
      domainLookupEnd: 30,
      connectStart: 30,
      connectEnd: 80,
      secureConnectionStart: 50,
      requestStart: 80,
      responseEnd: 200,
      domContentLoadedEventEnd: 300,
      loadEventEnd: 400
    };
    
    mockPerformance.getEntriesByType.mockImplementation((type) => {
      if (type === 'navigation') {
        return [mockNavigationTiming];
      }
      return [];
    });

    // Mock window.addEventListener
    mockAddEventListener = vi.fn();
    Object.defineProperty(global, 'window', {
      value: { addEventListener: mockAddEventListener },
      configurable: true
    });
    
    vi.spyOn(console, 'log').mockImplementation(() => {});
    
    mockAddEventListener.mockImplementation((event, callback) => {
      if (event === 'load') {
        // Immediately call the callback to simulate page load
        callback();
      }
    });
  });

  it('measures page load metrics', () => {
    measurePageLoad();
    
    expect(console.log).toHaveBeenCalledWith(
      expect.stringContaining('=Ê Page Load Metrics:')
    );
    expect(console.log).toHaveBeenCalledWith(
      expect.stringContaining('DNS Lookup: 20.00ms')
    );
    expect(console.log).toHaveBeenCalledWith(
      expect.stringContaining('TCP Connection: 50.00ms')
    );
    expect(console.log).toHaveBeenCalledWith(
      expect.stringContaining('TLS Setup: 30.00ms')
    );
    expect(console.log).toHaveBeenCalledWith(
      expect.stringContaining('DOM Processing: 100.00ms')
    );
    expect(console.log).toHaveBeenCalledWith(
      expect.stringContaining('Total Load Time: 400.00ms')
    );
  });

  it('stores metrics in window object', () => {
    measurePageLoad();
    
    const metrics = (global.window as any).performanceMetrics;
    expect(metrics).toBeDefined();
    expect(metrics.dnsLookup).toBe(20);
    expect(metrics.tcpConnection).toBe(50);
    expect(metrics.totalLoadTime).toBe(400);
  });

  it('handles missing secure connection timing', () => {
    mockNavigationTiming.secureConnectionStart = 0; // No HTTPS
    
    measurePageLoad();
    
    expect(console.log).toHaveBeenCalledWith(
      expect.stringContaining('TLS Setup: 0.00ms')
    );
  });
});

describe('Performance Edge Cases', () => {
  let monitor: PerformanceMonitor;

  beforeEach(() => {
    monitor = PerformanceMonitor.getInstance();
    vi.clearAllMocks();
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
  });

  it('handles negative time differences', () => {
    mockPerformance.now
      .mockReturnValueOnce(100)  // Start time
      .mockReturnValueOnce(50);  // End time (earlier than start)
    
    monitor.startTimer('negative-time');
    const duration = monitor.endTimer('negative-time');
    
    expect(duration).toBe(-50);
    expect(console.warn).toHaveBeenCalledWith('= SLOW: negative-time took -50.00ms');
  });

  it('handles extremely large durations', () => {
    mockPerformance.now
      .mockReturnValueOnce(0)
      .mockReturnValueOnce(50000); // 50 seconds
    
    monitor.startTimer('extremely-slow');
    const duration = monitor.endTimer('extremely-slow');
    
    expect(duration).toBe(50000);
    expect(console.warn).toHaveBeenCalledWith('= SLOW: extremely-slow took 50000.00ms');
  });

  it('handles concurrent timers with same name', () => {
    monitor.startTimer('concurrent-op');
    monitor.startTimer('concurrent-op'); // Should overwrite the first one
    
    const duration = monitor.endTimer('concurrent-op');
    expect(duration).toBeGreaterThanOrEqual(0);
  });

  it('handles memory pressure with many measurements', () => {
    // Create 1000 measurements
    for (let i = 0; i < 1000; i++) {
      mockPerformance.now.mockReturnValueOnce(i).mockReturnValueOnce(i + 1);
      monitor.startTimer(`operation-${i}`);
      monitor.endTimer(`operation-${i}`);
    }
    
    const slowOps = monitor.getSlowOperations(0);
    expect(slowOps).toHaveLength(1000);
    
    const report = monitor.getReport();
    expect(report).toContain('Operations: 1000');
  });
});