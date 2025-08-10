import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock WebSocket for testing
global.WebSocket = class MockWebSocket {
  readyState = 1
  onopen: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null

  constructor(url: string) {
    // Mock WebSocket constructor
  }

  send(data: string | ArrayBufferLike | Blob | ArrayBufferView): void {
    // Mock send method
  }

  close(code?: number, reason?: string): void {
    // Mock close method
  }

  addEventListener() {}
  removeEventListener() {}
  dispatchEvent() { return true }
}

// Mock fetch for API calls
global.fetch = vi.fn()

// Mock localStorage
Object.defineProperty(window, 'localStorage', {
  value: {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
  },
  writable: true,
})

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
}

// Mock performance API
Object.defineProperty(global, 'performance', {
  value: {
    now: vi.fn(() => Date.now()),
    mark: vi.fn(),
    measure: vi.fn(),
    getEntriesByType: vi.fn(() => []),
    memory: {
      usedJSHeapSize: 1024 * 1024 * 10, // 10MB
      totalJSHeapSize: 1024 * 1024 * 50, // 50MB
      jsHeapSizeLimit: 1024 * 1024 * 100 // 100MB
    }
  },
  writable: true
});

// Mock requestAnimationFrame
Object.defineProperty(global, 'requestAnimationFrame', {
  value: vi.fn((callback) => {
    return setTimeout(callback, 16);
  }),
  writable: true
});

Object.defineProperty(global, 'cancelAnimationFrame', {
  value: vi.fn((id) => {
    clearTimeout(id);
  }),
  writable: true
});

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock window dimensions
Object.defineProperty(window, 'innerWidth', {
  writable: true,
  configurable: true,
  value: 1024,
});

Object.defineProperty(window, 'innerHeight', {
  writable: true,
  configurable: true,
  value: 768,
});

// Mock HTMLElement.prototype.scrollIntoView
HTMLElement.prototype.scrollIntoView = vi.fn();

// Mock window.getComputedStyle
window.getComputedStyle = vi.fn(() => ({
  getPropertyValue: vi.fn(() => ''),
})) as any;