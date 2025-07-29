import { useEffect, useCallback, useRef } from 'react';
import { toast } from '@/components/ui/use-toast';

interface KeyboardAction {
  key: string;
  ctrlKey?: boolean;
  metaKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  action: () => void;
  description: string;
  category: 'navigation' | 'trading' | 'analysis' | 'general';
}

interface UseKeyboardNavigationProps {
  onNavigateToTab?: (tabName: string) => void;
  onExecuteTrade?: () => void;
  onQuickAnalysis?: () => void;
  onToggleTheme?: () => void;
  onOpenHelp?: () => void;
  onFocusSearch?: () => void;
  onOpenPositions?: () => void;
  onOpenRisk?: () => void;
  onRefreshData?: () => void;
  onToggleDemoMode?: () => void;
  disabled?: boolean;
}

export const useKeyboardNavigation = ({
  onNavigateToTab,
  onExecuteTrade,
  onQuickAnalysis,
  onToggleTheme,
  onOpenHelp,
  onFocusSearch,
  onOpenPositions,
  onOpenRisk,
  onRefreshData,
  onToggleDemoMode,
  disabled = false
}: UseKeyboardNavigationProps = {}) => {
  const shortcutsRef = useRef<KeyboardAction[]>([]);
  const isEnabledRef = useRef(!disabled);

  // Define keyboard shortcuts
  const shortcuts: KeyboardAction[] = [
    // Navigation shortcuts
    {
      key: '1',
      ctrlKey: true,
      action: () => onNavigateToTab?.('overview'),
      description: 'Go to Overview tab',
      category: 'navigation'
    },
    {
      key: '2',
      ctrlKey: true,
      action: () => onNavigateToTab?.('commentary'),
      description: 'Go to Commentary tab',
      category: 'navigation'
    },
    {
      key: '3',
      ctrlKey: true,
      action: () => onNavigateToTab?.('sentiment'),
      description: 'Go to Sentiment tab',
      category: 'navigation'
    },
    {
      key: '4',
      ctrlKey: true,
      action: () => onNavigateToTab?.('economic'),
      description: 'Go to Economic tab',
      category: 'navigation'
    },
    {
      key: '5',
      ctrlKey: true,
      action: () => onNavigateToTab?.('ai-coach'),
      description: 'Go to AI Coach tab',
      category: 'navigation'
    },
    {
      key: '6',
      ctrlKey: true,
      action: () => onNavigateToTab?.('signals'),
      description: 'Go to Signals tab',
      category: 'navigation'
    },
    {
      key: 't',
      ctrlKey: true,
      action: () => onNavigateToTab?.('trades'),
      description: 'Go to Trades tab',
      category: 'navigation'
    },
    {
      key: 'p',
      ctrlKey: true,
      action: () => onNavigateToTab?.('positions') || onOpenPositions?.(),
      description: 'Go to Positions tab',
      category: 'navigation'
    },
    {
      key: 'r',
      ctrlKey: true,
      action: () => onNavigateToTab?.('risk') || onOpenRisk?.(),
      description: 'Go to Risk tab',
      category: 'navigation'
    },
    {
      key: '0',
      ctrlKey: true,
      action: () => onNavigateToTab?.('config'),
      description: 'Go to Config tab',
      category: 'navigation'
    },
    
    // Trading shortcuts
    {
      key: 'Enter',
      ctrlKey: true,
      action: () => onExecuteTrade?.(),
      description: 'Execute selected trade',
      category: 'trading'
    },
    {
      key: 'a',
      ctrlKey: true,
      shiftKey: true,
      action: () => onQuickAnalysis?.(),
      description: 'Quick analysis',
      category: 'analysis'
    },
    {
      key: 'd',
      ctrlKey: true,
      shiftKey: true,
      action: () => onToggleDemoMode?.(),
      description: 'Toggle demo mode',
      category: 'trading'
    },
    
    // General shortcuts
    {
      key: 'f',
      ctrlKey: true,
      action: () => onFocusSearch?.(),
      description: 'Focus search',
      category: 'general'
    },
    {
      key: 'h',
      ctrlKey: true,
      action: () => onOpenHelp?.(),
      description: 'Open help',
      category: 'general'
    },
    {
      key: 'F5',
      action: (e?: KeyboardEvent) => {
        e?.preventDefault();
        onRefreshData?.();
        toast({
          title: "Data Refreshed",
          description: "Market data and opportunities updated",
        });
      },
      description: 'Refresh data',
      category: 'general'
    },
    {
      key: 'F1',
      action: (e?: KeyboardEvent) => {
        e?.preventDefault();
        showShortcutsHelp();
      },
      description: 'Show keyboard shortcuts',
      category: 'general'
    },
    
    // Theme and UI
    {
      key: 'd',
      ctrlKey: true,
      action: () => onToggleTheme?.(),
      description: 'Toggle dark/light theme',
      category: 'general'
    },
    
    // Escape actions
    {
      key: 'Escape',
      action: () => {
        // Close any open modals, clear selections, etc.
        const activeElement = document.activeElement as HTMLElement;
        if (activeElement && activeElement.blur) {
          activeElement.blur();
        }
        
        // Dispatch custom event for components to listen to
        window.dispatchEvent(new CustomEvent('trading-escape-key'));
      },
      description: 'Close modals/clear selection',
      category: 'general'
    }
  ];

  shortcutsRef.current = shortcuts;

  // Show shortcuts help
  const showShortcutsHelp = useCallback(() => {
    const shortcutsList = shortcutsRef.current
      .reduce((acc, shortcut) => {
        if (!acc[shortcut.category]) {
          acc[shortcut.category] = [];
        }
        acc[shortcut.category].push({
          key: getShortcutDisplayText(shortcut),
          description: shortcut.description
        });
        return acc;
      }, {} as Record<string, Array<{key: string; description: string}>>);

    // Create and show shortcuts modal
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black/50 flex items-center justify-center z-50';
    modal.onclick = (e) => {
      if (e.target === modal) {
        document.body.removeChild(modal);
      }
    };

    const categories = {
      navigation: '🧭 Navigation',
      trading: '📈 Trading',
      analysis: '📊 Analysis',
      general: '⚙️ General'
    };

    modal.innerHTML = `
      <div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto m-4">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-bold">Keyboard Shortcuts</h2>
          <button onclick="this.closest('.fixed').remove()" class="text-gray-500 hover:text-gray-700">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        
        <div class="space-y-6">
          ${Object.entries(categories).map(([key, title]) => {
            const categoryShortcuts = shortcutsList[key as keyof typeof shortcutsList] || [];
            if (categoryShortcuts.length === 0) return '';
            
            return `
              <div>
                <h3 class="font-semibold text-lg mb-3 text-gray-800 dark:text-gray-200">${title}</h3>
                <div class="grid grid-cols-1 gap-2">
                  ${categoryShortcuts.map(({ key, description }) => `
                    <div class="flex items-center justify-between py-2 px-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <span class="text-gray-700 dark:text-gray-300">${description}</span>
                      <kbd class="px-2 py-1 bg-gray-200 dark:bg-gray-600 rounded text-sm font-mono">${key}</kbd>
                    </div>
                  `).join('')}
                </div>
              </div>
            `;
          }).join('')}
        </div>
        
        <div class="mt-6 pt-4 border-t border-gray-200 dark:border-gray-600">
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Press <kbd class="px-1 bg-gray-200 dark:bg-gray-600 rounded">F1</kbd> anytime to see these shortcuts again.
          </p>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    // Focus trap
    const focusableElements = modal.querySelectorAll('button');
    const firstElement = focusableElements[0] as HTMLElement;
    if (firstElement) {
      firstElement.focus();
    }

    // Handle escape key to close
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        document.body.removeChild(modal);
        document.removeEventListener('keydown', handleEscape);
      }
    };
    document.addEventListener('keydown', handleEscape);
  }, []);

  // Get display text for shortcut
  const getShortcutDisplayText = (shortcut: KeyboardAction): string => {
    const parts: string[] = [];
    
    if (shortcut.ctrlKey) parts.push('Ctrl');
    if (shortcut.metaKey) parts.push('Cmd');
    if (shortcut.shiftKey) parts.push('Shift');
    if (shortcut.altKey) parts.push('Alt');
    
    // Format key display
    let keyDisplay = shortcut.key;
    if (keyDisplay === ' ') keyDisplay = 'Space';
    if (keyDisplay === 'Enter') keyDisplay = 'Enter';
    if (keyDisplay === 'Escape') keyDisplay = 'Esc';
    if (keyDisplay === 'F1') keyDisplay = 'F1';
    if (keyDisplay === 'F5') keyDisplay = 'F5';
    
    parts.push(keyDisplay);
    
    return parts.join(' + ');
  };

  // Handle keyboard event
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    // Don't handle shortcuts if disabled
    if (!isEnabledRef.current) return;

    // Don't handle shortcuts when typing in inputs
    const target = event.target as HTMLElement;
    if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
      // Allow some shortcuts even in inputs
      if (event.key === 'Escape') {
        target.blur();
        return;
      }
      return;
    }

    // Find matching shortcut
    const matchingShortcut = shortcutsRef.current.find(shortcut => {
      return (
        shortcut.key === event.key &&
        !!shortcut.ctrlKey === event.ctrlKey &&
        !!shortcut.metaKey === event.metaKey &&
        !!shortcut.shiftKey === event.shiftKey &&
        !!shortcut.altKey === event.altKey
      );
    });

    if (matchingShortcut) {
      event.preventDefault();
      event.stopPropagation();
      
      try {
        matchingShortcut.action(event);
        
        // Show brief feedback for some actions
        if (['1', '2', '3', '4', '5', '6', 't', 'p', 'r', '0'].includes(matchingShortcut.key) && matchingShortcut.ctrlKey) {
          toast({
            description: matchingShortcut.description,
            duration: 1500,
          });
        }
      } catch (error) {
        console.error('Error executing keyboard shortcut:', error);
        toast({
          title: "Shortcut Error",
          description: "Failed to execute keyboard shortcut",
          variant: "destructive",
          duration: 3000,
        });
      }
    }
  }, []);

  // Set up event listeners
  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);

  // Update enabled state
  useEffect(() => {
    isEnabledRef.current = !disabled;
  }, [disabled]);

  // Return useful functions and state
  return {
    shortcuts: shortcutsRef.current,
    showHelp: showShortcutsHelp,
    isEnabled: !disabled,
    categories: ['navigation', 'trading', 'analysis', 'general'] as const
  };
};

// Hook for individual components to register escape handlers
export const useEscapeHandler = (handler: () => void, enabled = true) => {
  useEffect(() => {
    if (!enabled) return;

    const handleEscape = (event: CustomEvent) => {
      handler();
    };

    window.addEventListener('trading-escape-key', handleEscape as EventListener);
    
    return () => {
      window.removeEventListener('trading-escape-key', handleEscape as EventListener);
    };
  }, [handler, enabled]);
};

// Hook for focus management
export const useFocusManagement = () => {
  const trapFocus = useCallback((container: HTMLElement) => {
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement?.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement?.focus();
          e.preventDefault();
        }
      }
    };

    container.addEventListener('keydown', handleTabKey);
    
    return () => {
      container.removeEventListener('keydown', handleTabKey);
    };
  }, []);

  return { trapFocus };
};

export default useKeyboardNavigation;