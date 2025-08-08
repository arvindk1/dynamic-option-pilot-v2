import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { 
  ChevronDown, 
  ChevronRight, 
  AlertCircle, 
  CheckCircle, 
  Settings, 
  Target,
  Shield,
  TrendingUp,
  Clock
} from 'lucide-react';

interface ParameterSection {
  id: string;
  title: string;
  description: string;
  level: 'essential' | 'intermediate' | 'advanced';
  icon: React.ComponentType<any>;
  parameterCount: number;
  configuredCount: number;
  parameters: any[];
}

interface ProgressiveParameterEditorProps {
  strategy: any;
  userLevel: 'beginner' | 'intermediate' | 'expert';
  onParameterChange: (path: string, value: any) => void;
  layoutMode: 'browsing' | 'editing' | 'testing' | 'comparing';
}

const ProgressiveParameterEditor: React.FC<ProgressiveParameterEditorProps> = ({
  strategy,
  userLevel,
  onParameterChange,
  layoutMode
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['essential']) // Always expand essential section
  );

  const parameterSections: ParameterSection[] = [
    {
      id: 'essential',
      title: 'Essential Parameters',
      description: 'Core settings that define the strategy behavior',
      level: 'essential',
      icon: Target,
      parameterCount: 8,
      configuredCount: 6,
      parameters: [
        { path: 'universe.symbol_types', label: 'Trading Universe', type: 'select' },
        { path: 'timing.dte_range', label: 'DTE Range', type: 'range' },
        { path: 'position_parameters.max_opportunities', label: 'Max Positions', type: 'number' },
        { path: 'entry_signals.allowed_bias', label: 'Market Bias', type: 'select' },
        { path: 'risk_management.max_allocation_percentage', label: 'Portfolio %', type: 'percentage' },
        { path: 'exit_rules.profit_targets[0].level', label: 'Profit Target', type: 'percentage' },
        { path: 'exit_rules.stop_loss_rules[0].trigger', label: 'Stop Loss', type: 'percentage' },
        { path: 'position_parameters.max_position_cost', label: 'Max Cost', type: 'currency' }
      ]
    },
    {
      id: 'entry_signals',
      title: 'Entry Signals',
      description: 'Conditions that trigger strategy entry',
      level: 'intermediate',
      icon: TrendingUp,
      parameterCount: 12,
      configuredCount: 8,
      parameters: [
        { path: 'entry_signals.volatility_max', label: 'Max Volatility', type: 'percentage' },
        { path: 'entry_signals.implied_volatility_rank_max', label: 'Max IV Rank', type: 'number' },
        { path: 'entry_signals.price_consolidation_required', label: 'Price Consolidation', type: 'boolean' }
        // Add more entry signal parameters
      ]
    },
    {
      id: 'exit_rules',
      title: 'Exit Rules',
      description: 'When and how to close positions',
      level: 'intermediate',
      icon: Shield,
      parameterCount: 15,
      configuredCount: 10,
      parameters: [
        { path: 'exit_rules.time_exits[0].value', label: 'Days Before Expiry', type: 'number' },
        { path: 'exit_rules.volatility_exits[0].threshold', label: 'IV Spike Threshold', type: 'percentage' }
        // Add more exit rule parameters
      ]
    },
    {
      id: 'strike_selection',
      title: 'Strike Selection',
      description: 'How strikes are chosen for the strategy',
      level: 'advanced',
      icon: Settings,
      parameterCount: 8,
      configuredCount: 5,
      parameters: [
        { path: 'strike_selection.center_strike', label: 'Center Strike', type: 'select' },
        { path: 'strike_selection.max_wing_width', label: 'Max Wing Width', type: 'number' },
        { path: 'strike_selection.min_wing_width', label: 'Min Wing Width', type: 'number' }
        // Add more strike selection parameters
      ]
    },
    {
      id: 'scoring',
      title: 'Scoring & Optimization',
      description: 'How opportunities are ranked and selected',
      level: 'advanced',
      icon: TrendingUp,
      parameterCount: 10,
      configuredCount: 7,
      parameters: [
        { path: 'scoring.profit_zone_weight', label: 'Profit Zone Weight', type: 'percentage' },
        { path: 'scoring.cost_weight', label: 'Cost Weight', type: 'percentage' },
        { path: 'scoring.liquidity_weight', label: 'Liquidity Weight', type: 'percentage' }
        // Add more scoring parameters
      ]
    }
  ];

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const getSectionVisibility = (section: ParameterSection) => {
    const levelVisibility = {
      beginner: section.level === 'essential',
      intermediate: section.level !== 'advanced',
      expert: true
    };
    return levelVisibility[userLevel];
  };

  const getCompletionColor = (configured: number, total: number) => {
    const percentage = configured / total;
    if (percentage >= 0.8) return 'text-green-600 bg-green-100';
    if (percentage >= 0.5) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getGridColumns = () => {
    switch (layoutMode) {
      case 'editing':
        return 'grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4';
      case 'comparing':
        return 'grid-cols-1 lg:grid-cols-2';
      default:
        return 'grid-cols-1 lg:grid-cols-2 xl:grid-cols-3';
    }
  };

  return (
    <div className="space-y-4">
      {/* Progress Overview */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold">Configuration Progress</h3>
              <p className="text-sm text-muted-foreground">
                {parameterSections.reduce((acc, s) => acc + s.configuredCount, 0)} of{' '}
                {parameterSections.reduce((acc, s) => acc + s.parameterCount, 0)} parameters configured
              </p>
            </div>
            <div className="flex gap-2">
              {userLevel !== 'expert' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    // Show all sections for current user level
                    const newExpanded = new Set<string>();
                    parameterSections.forEach(section => {
                      if (getSectionVisibility(section)) {
                        newExpanded.add(section.id);
                      }
                    });
                    setExpandedSections(newExpanded);
                  }}
                >
                  Expand All
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={() => setExpandedSections(new Set(['essential']))}
              >
                Essential Only
              </Button>
            </div>
          </div>
          
          {/* Section Status Overview */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {parameterSections
              .filter(getSectionVisibility)
              .map(section => (
                <div key={section.id} className="text-center">
                  <div className={`inline-flex items-center justify-center w-10 h-10 rounded-full mb-2 ${
                    getCompletionColor(section.configuredCount, section.parameterCount)
                  }`}>
                    <section.icon className="w-5 h-5" />
                  </div>
                  <div className="text-xs font-medium">{section.title}</div>
                  <div className="text-xs text-muted-foreground">
                    {section.configuredCount}/{section.parameterCount}
                  </div>
                </div>
              ))}
          </div>
        </CardContent>
      </Card>

      {/* Parameter Sections */}
      {parameterSections
        .filter(getSectionVisibility)
        .map(section => (
          <Card key={section.id} className={`${
            section.level === 'essential' ? 'border-blue-200 bg-blue-50/30' : ''
          }`}>
            <Collapsible 
              open={expandedSections.has(section.id)}
              onOpenChange={() => toggleSection(section.id)}
            >
              <CollapsibleTrigger asChild>
                <CardHeader className="cursor-pointer hover:bg-gray-50/50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${
                        section.level === 'essential' ? 'bg-blue-100' : 'bg-gray-100'
                      }`}>
                        <section.icon className={`w-4 h-4 ${
                          section.level === 'essential' ? 'text-blue-600' : 'text-gray-600'
                        }`} />
                      </div>
                      <div>
                        <CardTitle className="text-base flex items-center gap-2">
                          {section.title}
                          {section.level === 'essential' && (
                            <Badge variant="outline" className="text-xs">Required</Badge>
                          )}
                        </CardTitle>
                        <CardDescription className="text-sm">
                          {section.description}
                        </CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className={getCompletionColor(section.configuredCount, section.parameterCount)}>
                        {section.configuredCount}/{section.parameterCount}
                      </Badge>
                      {expandedSections.has(section.id) ? (
                        <ChevronDown className="w-4 h-4" />
                      ) : (
                        <ChevronRight className="w-4 h-4" />
                      )}
                    </div>
                  </div>
                </CardHeader>
              </CollapsibleTrigger>
              
              <CollapsibleContent>
                <CardContent>
                  <div className={`grid gap-4 ${getGridColumns()}`}>
                    {section.parameters.map(param => (
                      <div key={param.path} className="space-y-2">
                        <label className="text-sm font-medium">{param.label}</label>
                        {/* Render parameter input based on type */}
                        <div className="h-10 bg-gray-100 rounded border flex items-center px-3 text-sm text-gray-600">
                          {param.type} input for {param.path}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </CollapsibleContent>
            </Collapsible>
          </Card>
        ))}
    </div>
  );
};

export default ProgressiveParameterEditor;