import { useEffect, useRef } from 'react';

// Tab importance/usage frequency mapping for smart preloading
const TAB_PRIORITY = {
  'overview': 10,
  'trades': 9,
  'signals': 8,
  'positions': 7,
  'risk': 6,
  'sentiment': 5,
  'ai-coach': 4,
  'economic': 3,
  'commentary': 2,
  'config': 1
};

// Common navigation patterns - which tab users typically visit after each tab
const TAB_PATTERNS = {
  'overview': ['trades', 'signals'],
  'trades': ['positions', 'risk'],
  'signals': ['trades', 'risk'],
  'positions': ['trades', 'risk'],
  'risk': ['positions', 'trades'],
  'sentiment': ['trades', 'signals'],
  'ai-coach': ['trades', 'positions'],
  'economic': ['sentiment', 'trades'],
  'commentary': ['sentiment', 'trades'],
  'config': ['overview']
};

interface UseTabPreloadOptions {
  currentTab: string;
  onPreload?: (tabName: string) => void;
  preloadDelay?: number;
}

export const useTabPreload = ({ 
  currentTab, 
  onPreload,
  preloadDelay = 500 
}: UseTabPreloadOptions) => {
  const preloadTimeoutRef = useRef<NodeJS.Timeout>();
  const preloadedTabsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    // Clear existing timeout
    if (preloadTimeoutRef.current) {
      clearTimeout(preloadTimeoutRef.current);
    }

    // Set up preloading for likely next tabs
    preloadTimeoutRef.current = setTimeout(() => {
      const likelyNextTabs = TAB_PATTERNS[currentTab as keyof typeof TAB_PATTERNS] || [];
      
      for (const tabName of likelyNextTabs) {
        if (!preloadedTabsRef.current.has(tabName)) {
          preloadedTabsRef.current.add(tabName);
          onPreload?.(tabName);
          break; // Preload one at a time to avoid overwhelming
        }
      }
    }, preloadDelay);

    return () => {
      if (preloadTimeoutRef.current) {
        clearTimeout(preloadTimeoutRef.current);
      }
    };
  }, [currentTab, onPreload, preloadDelay]);

  const markTabAsPreloaded = (tabName: string) => {
    preloadedTabsRef.current.add(tabName);
  };

  const isTabPreloaded = (tabName: string) => {
    return preloadedTabsRef.current.has(tabName);
  };

  return {
    markTabAsPreloaded,
    isTabPreloaded,
    preloadedTabs: Array.from(preloadedTabsRef.current)
  };
};