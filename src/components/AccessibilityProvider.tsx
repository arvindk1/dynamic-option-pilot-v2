import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { toast } from '@/components/ui/use-toast';

interface AccessibilitySettings {
  highContrast: boolean;
  reducedMotion: boolean;
  largeText: boolean;
  screenReaderMode: boolean;
  keyboardNavigation: boolean;
  focusVisible: boolean;
  announcements: boolean;
}

interface AccessibilityContextType {
  settings: AccessibilitySettings;
  updateSetting: (key: keyof AccessibilitySettings, value: boolean) => void;
  announceToScreenReader: (message: string, priority?: 'polite' | 'assertive') => void;
  isHighContrast: boolean;
  isReducedMotion: boolean;
  isLargeText: boolean;
}

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined);

export const useAccessibility = () => {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error('useAccessibility must be used within AccessibilityProvider');
  }
  return context;
};

interface AccessibilityProviderProps {
  children: ReactNode;
}

export const AccessibilityProvider: React.FC<AccessibilityProviderProps> = ({ children }) => {
  const [settings, setSettings] = useState<AccessibilitySettings>(() => {
    // Load from localStorage or use defaults
    const saved = localStorage.getItem('accessibility-settings');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error('Failed to parse accessibility settings:', e);
      }
    }

    // Check system preferences
    return {
      highContrast: window.matchMedia('(prefers-contrast: high)').matches,
      reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
      largeText: false,
      screenReaderMode: false,
      keyboardNavigation: true,
      focusVisible: true,
      announcements: true
    };
  });

  // Screen reader announcement region
  const [announceRegion, setAnnounceRegion] = useState<HTMLElement | null>(null);

  useEffect(() => {
    // Create ARIA live region for announcements
    const region = document.createElement('div');
    region.setAttribute('aria-live', 'polite');
    region.setAttribute('aria-atomic', 'true');
    region.className = 'sr-only';
    region.id = 'accessibility-announcements';
    document.body.appendChild(region);
    setAnnounceRegion(region);

    return () => {
      if (region.parentNode) {
        region.parentNode.removeChild(region);
      }
    };
  }, []);

  useEffect(() => {
    // Save to localStorage
    localStorage.setItem('accessibility-settings', JSON.stringify(settings));

    // Apply CSS classes to document
    const root = document.documentElement;
    
    // High contrast mode
    if (settings.highContrast) {
      root.classList.add('high-contrast');
    } else {
      root.classList.remove('high-contrast');
    }

    // Reduced motion
    if (settings.reducedMotion) {
      root.classList.add('reduced-motion');
    } else {
      root.classList.remove('reduced-motion');
    }

    // Large text
    if (settings.largeText) {
      root.classList.add('large-text');
    } else {
      root.classList.remove('large-text');
    }

    // Focus visible
    if (settings.focusVisible) {
      root.classList.add('focus-visible');
    } else {
      root.classList.remove('focus-visible');
    }

  }, [settings]);

  // Listen for system preference changes
  useEffect(() => {
    const contrastQuery = window.matchMedia('(prefers-contrast: high)');
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

    const handleContrastChange = (e: MediaQueryListEvent) => {
      updateSetting('highContrast', e.matches);
    };

    const handleMotionChange = (e: MediaQueryListEvent) => {
      updateSetting('reducedMotion', e.matches);
    };

    contrastQuery.addEventListener('change', handleContrastChange);
    motionQuery.addEventListener('change', handleMotionChange);

    return () => {
      contrastQuery.removeEventListener('change', handleContrastChange);
      motionQuery.removeEventListener('change', handleMotionChange);
    };
  }, []);

  const updateSetting = (key: keyof AccessibilitySettings, value: boolean) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));

    // Announce important changes
    if (settings.announcements) {
      const messages = {
        highContrast: value ? 'High contrast mode enabled' : 'High contrast mode disabled',
        reducedMotion: value ? 'Reduced motion enabled' : 'Reduced motion disabled',
        largeText: value ? 'Large text enabled' : 'Large text disabled',
        screenReaderMode: value ? 'Screen reader mode enabled' : 'Screen reader mode disabled'
      };

      if (key in messages) {
        announceToScreenReader(messages[key as keyof typeof messages]);
      }
    }
  };

  const announceToScreenReader = (
    message: string, 
    priority: 'polite' | 'assertive' = 'polite'
  ) => {
    if (!settings.announcements || !announceRegion) return;

    // Set priority
    announceRegion.setAttribute('aria-live', priority);
    
    // Clear and set new message
    announceRegion.textContent = '';
    setTimeout(() => {
      announceRegion.textContent = message;
    }, 10);

    // Clear after announcement
    setTimeout(() => {
      announceRegion.textContent = '';
      announceRegion.setAttribute('aria-live', 'polite');
    }, 3000);
  };

  const contextValue: AccessibilityContextType = {
    settings,
    updateSetting,
    announceToScreenReader,
    isHighContrast: settings.highContrast,
    isReducedMotion: settings.reducedMotion,
    isLargeText: settings.largeText
  };

  return (
    <AccessibilityContext.Provider value={contextValue}>
      {children}
    </AccessibilityContext.Provider>
  );
};

// HOC for adding accessibility features to components
export function withAccessibility<P extends object>(
  Component: React.ComponentType<P>
) {
  const AccessibilityEnhancedComponent = (props: P) => {
    const { announceToScreenReader, isHighContrast } = useAccessibility();

    return (
      <Component 
        {...props} 
        announceToScreenReader={announceToScreenReader}
        isHighContrast={isHighContrast}
      />
    );
  };

  AccessibilityEnhancedComponent.displayName = `withAccessibility(${Component.displayName || Component.name})`;
  return AccessibilityEnhancedComponent;
}

// Accessibility settings panel component
export const AccessibilityPanel: React.FC<{
  isOpen: boolean;
  onClose: () => void;
}> = ({ isOpen, onClose }) => {
  const { settings, updateSetting } = useAccessibility();

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      role="dialog"
      aria-labelledby="accessibility-title"
      aria-modal="true"
    >
      <div className="bg-background border rounded-lg p-6 max-w-md w-full m-4 max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 id="accessibility-title" className="text-xl font-bold">
            Accessibility Settings
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-muted rounded"
            aria-label="Close accessibility settings"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-6">
          {/* Visual Settings */}
          <div>
            <h3 className="font-semibold mb-3">Visual Settings</h3>
            <div className="space-y-3">
              <label className="flex items-center justify-between">
                <span>High Contrast Mode</span>
                <input
                  type="checkbox"
                  checked={settings.highContrast}
                  onChange={(e) => updateSetting('highContrast', e.target.checked)}
                  className="sr-only"
                />
                <div 
                  className={`w-11 h-6 rounded-full p-1 cursor-pointer transition-colors ${
                    settings.highContrast ? 'bg-primary' : 'bg-muted'
                  }`}
                  onClick={() => updateSetting('highContrast', !settings.highContrast)}
                >
                  <div 
                    className={`w-4 h-4 rounded-full bg-white transition-transform ${
                      settings.highContrast ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </div>
              </label>

              <label className="flex items-center justify-between">
                <span>Large Text</span>
                <input
                  type="checkbox"
                  checked={settings.largeText}
                  onChange={(e) => updateSetting('largeText', e.target.checked)}
                  className="sr-only"
                />
                <div 
                  className={`w-11 h-6 rounded-full p-1 cursor-pointer transition-colors ${
                    settings.largeText ? 'bg-primary' : 'bg-muted'
                  }`}
                  onClick={() => updateSetting('largeText', !settings.largeText)}
                >
                  <div 
                    className={`w-4 h-4 rounded-full bg-white transition-transform ${
                      settings.largeText ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </div>
              </label>

              <label className="flex items-center justify-between">
                <span>Reduced Motion</span>
                <input
                  type="checkbox"
                  checked={settings.reducedMotion}
                  onChange={(e) => updateSetting('reducedMotion', e.target.checked)}
                  className="sr-only"
                />
                <div 
                  className={`w-11 h-6 rounded-full p-1 cursor-pointer transition-colors ${
                    settings.reducedMotion ? 'bg-primary' : 'bg-muted'
                  }`}
                  onClick={() => updateSetting('reducedMotion', !settings.reducedMotion)}
                >
                  <div 
                    className={`w-4 h-4 rounded-full bg-white transition-transform ${
                      settings.reducedMotion ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </div>
              </label>
            </div>
          </div>

          {/* Navigation Settings */}
          <div>
            <h3 className="font-semibold mb-3">Navigation Settings</h3>
            <div className="space-y-3">
              <label className="flex items-center justify-between">
                <span>Enhanced Focus Indicators</span>
                <input
                  type="checkbox"
                  checked={settings.focusVisible}
                  onChange={(e) => updateSetting('focusVisible', e.target.checked)}
                  className="sr-only"
                />
                <div 
                  className={`w-11 h-6 rounded-full p-1 cursor-pointer transition-colors ${
                    settings.focusVisible ? 'bg-primary' : 'bg-muted'
                  }`}
                  onClick={() => updateSetting('focusVisible', !settings.focusVisible)}
                >
                  <div 
                    className={`w-4 h-4 rounded-full bg-white transition-transform ${
                      settings.focusVisible ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </div>
              </label>

              <label className="flex items-center justify-between">
                <span>Screen Reader Announcements</span>
                <input
                  type="checkbox"
                  checked={settings.announcements}
                  onChange={(e) => updateSetting('announcements', e.target.checked)}
                  className="sr-only"
                />
                <div 
                  className={`w-11 h-6 rounded-full p-1 cursor-pointer transition-colors ${
                    settings.announcements ? 'bg-primary' : 'bg-muted'
                  }`}
                  onClick={() => updateSetting('announcements', !settings.announcements)}
                >
                  <div 
                    className={`w-4 h-4 rounded-full bg-white transition-transform ${
                      settings.announcements ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </div>
              </label>
            </div>
          </div>

          {/* Help Text */}
          <div className="text-sm text-muted-foreground border-t pt-4">
            <p>
              These settings are saved locally and will persist across sessions. 
              Some changes may require a page refresh to take full effect.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="flex-1 bg-primary text-primary-foreground py-2 px-4 rounded hover:bg-primary/90"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AccessibilityProvider;