import React from 'react';
import { Button } from '@/components/ui/button';
import { 
  PanelLeftClose, 
  PanelLeftOpen, 
  Minimize2, 
  Maximize2, 
  MessageSquare,
  Focus,
  LayoutGrid
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface LayoutControlsProps {
  layoutMode: 'browsing' | 'editing' | 'testing' | 'comparing';
  onLayoutChange: (mode: 'browsing' | 'editing' | 'testing' | 'comparing') => void;
  leftPanelCollapsed: boolean;
  onToggleLeftPanel: () => void;
  rightPanelMinimized: boolean;
  onToggleRightPanel: () => void;
  parameterCount?: number;
  activeParameters?: number;
}

const LayoutControls: React.FC<LayoutControlsProps> = ({
  layoutMode,
  onLayoutChange,
  leftPanelCollapsed,
  onToggleLeftPanel,
  rightPanelMinimized,
  onToggleRightPanel,
  parameterCount = 0,
  activeParameters = 0
}) => {
  const layoutModes = [
    { 
      id: 'browsing', 
      label: 'Browse', 
      icon: LayoutGrid, 
      description: 'Browse and select strategies',
      layout: '20% | 60% | 20%'
    },
    { 
      id: 'editing', 
      label: 'Edit', 
      icon: Focus, 
      description: 'Focus on parameter editing',
      layout: '5% | 75% | 20%'
    },
    { 
      id: 'testing', 
      label: 'Test', 
      icon: Maximize2, 
      description: 'Test and analyze results',
      layout: '15% | 65% | 20%'
    },
    { 
      id: 'comparing', 
      label: 'Compare', 
      icon: PanelLeftOpen, 
      description: 'Compare configurations',
      layout: '15% | 45% | 40%'
    }
  ] as const;

  return (
    <div className="flex items-center justify-between p-4 bg-gray-50 border-b">
      {/* Layout Mode Selector */}
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-gray-600">Layout:</span>
        {layoutModes.map(({ id, label, icon: Icon, description, layout }) => (
          <Button
            key={id}
            variant={layoutMode === id ? "default" : "outline"}
            size="sm"
            onClick={() => onLayoutChange(id)}
            className="flex items-center gap-1"
            title={`${description} (${layout})`}
          >
            <Icon className="w-3 h-3" />
            {label}
          </Button>
        ))}
      </div>

      {/* Parameter Counter */}
      {parameterCount > 0 && (
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs">
            {activeParameters}/{parameterCount} parameters configured
          </Badge>
        </div>
      )}

      {/* Panel Controls */}
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onToggleLeftPanel}
          title={leftPanelCollapsed ? 'Show strategy list' : 'Hide strategy list'}
        >
          {leftPanelCollapsed ? <PanelLeftOpen className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
          <span className="hidden md:inline ml-1">
            {leftPanelCollapsed ? 'Show' : 'Hide'} List
          </span>
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={onToggleRightPanel}
          title={rightPanelMinimized ? 'Show context panel' : 'Minimize context panel'}
        >
          {rightPanelMinimized ? <MessageSquare className="w-4 h-4" /> : <Minimize2 className="w-4 h-4" />}
          <span className="hidden md:inline ml-1">
            {rightPanelMinimized ? 'Show' : 'Hide'} Context
          </span>
        </Button>
      </div>
    </div>
  );
};

export default LayoutControls;