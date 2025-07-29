import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  BarChart3,
  Brain,
  Newspaper,
  TrendingUp,
  Target,
  Settings,
  Zap,
  Shield,
  DollarSign
} from 'lucide-react';

interface TieredNavigationProps {
  activeTab: string;
  onTabChange: (value: string) => void;
  children: React.ReactNode;
}

interface MainTab {
  id: string;
  label: string;
  icon: React.ReactNode;
  subTabs?: {
    value: string;
    label: string;
    icon?: React.ReactNode;
    className?: string;
  }[];
  directTab?: string; // For tabs that don't have sub-tabs
}

const mainTabs: MainTab[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: <BarChart3 className="h-4 w-4" />,
    subTabs: [
      { value: 'overview', label: 'Overview' },
      { value: 'commentary', label: 'Commentary', icon: <Newspaper className="h-4 w-4" /> }
    ]
  },
  {
    id: 'trading',
    label: 'Trading',
    icon: <TrendingUp className="h-4 w-4" />,
    subTabs: [
      { value: 'trades', label: 'Execution', className: 'trades-tab' },
      { value: 'positions', label: 'Positions', className: 'positions-tab' },
      { value: 'signals', label: 'Signals' }
    ]
  },
  {
    id: 'analytics',
    label: 'Analytics',
    icon: <Brain className="h-4 w-4" />,
    subTabs: [
      { value: 'sentiment', label: 'Sentiment', icon: <Brain className="h-4 w-4" /> },
      { value: 'risk', label: 'Risk', icon: <Shield className="h-4 w-4" />, className: 'analytics-tab' },
      { value: 'ai-coach', label: 'AI Coach', icon: <Brain className="h-4 w-4" /> },
      { value: 'economic', label: 'Economic', icon: <BarChart3 className="h-4 w-4" /> }
    ]
  },
  {
    id: 'tools',
    label: 'Tools',
    icon: <Settings className="h-4 w-4" />,
    subTabs: [
      { value: 'config', label: 'Settings' }
    ]
  }
];

export const TieredNavigation: React.FC<TieredNavigationProps> = React.memo(({
  activeTab,
  onTabChange,
  children
}) => {
  // Find which main tab contains the active tab
  const activeMainTab = mainTabs.find(mainTab => 
    mainTab.subTabs?.some(subTab => subTab.value === activeTab) ||
    mainTab.directTab === activeTab
  );

  const activeMainTabId = activeMainTab?.id || 'dashboard';

  // Handle main tab clicks - switch to first sub-tab or direct tab
  const handleMainTabClick = React.useCallback((mainTab: MainTab) => {
    if (mainTab.subTabs && mainTab.subTabs.length > 0) {
      // If current main tab is clicked and we're already in it, don't change
      if (activeMainTabId === mainTab.id) return;
      // Switch to first sub-tab of this main tab
      onTabChange(mainTab.subTabs[0].value);
    } else if (mainTab.directTab) {
      onTabChange(mainTab.directTab);
    }
  }, [activeMainTabId, onTabChange]);

  return (
    <Tabs value={activeTab} onValueChange={onTabChange} className="space-y-6">
      <div className="space-y-2">
        {/* Main Tabs Row */}
        <div className="flex space-x-2 bg-gradient-to-r from-card/50 to-card/30 p-2 rounded-xl backdrop-blur-sm border border-border/40 shadow-lg" role="tablist" aria-label="Main navigation">
          {mainTabs.map((mainTab) => (
            <button
              key={mainTab.id}
              onClick={() => handleMainTabClick(mainTab)}
              className={`flex items-center space-x-2 px-6 py-3 rounded-lg text-sm font-semibold transition-all duration-300 ${
                activeMainTabId === mainTab.id
                  ? 'bg-primary text-primary-foreground shadow-lg transform scale-105'
                  : 'text-muted-foreground hover:text-foreground hover:bg-background/80 hover:shadow-md hover:scale-102'
              }`}
              role="tab"
              aria-selected={activeMainTabId === mainTab.id}
            >
              {mainTab.icon}
              <span>{mainTab.label}</span>
            </button>
          ))}
        </div>

        {/* Sub-tabs Row - Only show if active main tab has sub-tabs */}
        {activeMainTab?.subTabs && (
          <TabsList className="w-full bg-gradient-to-r from-muted/10 to-muted/5 h-auto p-2 justify-start rounded-xl backdrop-blur-sm border border-border/30 shadow-md" role="tablist" aria-label="Sub navigation">
            {activeMainTab.subTabs.map((subTab) => (
              <TabsTrigger
                key={subTab.value}
                value={subTab.value}
                className={`flex items-center space-x-2 px-4 py-2.5 rounded-lg font-medium transition-all duration-200 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-md data-[state=active]:scale-105 hover:bg-background/50 ${subTab.className || ''}`}
                role="tab"
                aria-controls={`${subTab.value}-panel`}
              >
                {subTab.icon}
                <span>{subTab.label}</span>
              </TabsTrigger>
            ))}
          </TabsList>
        )}
      </div>

      {children}
    </Tabs>
  );
});