import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  HelpCircle, 
  GitCompare, 
  BarChart3, 
  MessageSquare, 
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Info,
  Target,
  DollarSign
} from 'lucide-react';

interface ContextPanelProps {
  currentParameter?: string;
  strategy?: any;
  baseStrategy?: any;
  testResults?: any;
  minimized: boolean;
  onToggleMinimized: () => void;
}

const SmartContextPanel: React.FC<ContextPanelProps> = ({
  currentParameter,
  strategy,
  baseStrategy,
  testResults,
  minimized,
  onToggleMinimized
}) => {
  const [activeTab, setActiveTab] = useState<'help' | 'comparison' | 'results' | 'ai'>('help');

  // Auto-switch tabs based on context
  useEffect(() => {
    if (testResults && Object.keys(testResults).length > 0) {
      setActiveTab('results');
    } else if (currentParameter) {
      setActiveTab('help');
    } else if (baseStrategy && strategy) {
      setActiveTab('comparison');
    }
  }, [testResults, currentParameter, baseStrategy, strategy]);

  if (minimized) {
    return (
      <div className="w-16 h-full bg-gray-50 border-l flex flex-col items-center py-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleMinimized}
          className="mb-4"
        >
          <HelpCircle className="w-4 h-4" />
        </Button>
        
        {/* Mini indicators */}
        <div className="space-y-2">
          {testResults && (
            <div className="w-3 h-3 bg-green-500 rounded-full" title="Test results available" />
          )}
          {currentParameter && (
            <div className="w-3 h-3 bg-blue-500 rounded-full" title="Parameter help available" />
          )}
          {baseStrategy && (
            <div className="w-3 h-3 bg-purple-500 rounded-full" title="Comparison available" />
          )}
        </div>
      </div>
    );
  }

  const ParameterHelp: React.FC = () => {
    const parameterGuide = getParameterGuide(currentParameter);
    
    return (
      <div className="space-y-4">
        {currentParameter ? (
          <>
            <div>
              <h3 className="font-semibold text-sm mb-2">{parameterGuide.name}</h3>
              <p className="text-sm text-muted-foreground mb-3">{parameterGuide.description}</p>
            </div>

            <div className="space-y-3">
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="font-medium text-blue-900 text-sm mb-1">Recommended Range</h4>
                <p className="text-blue-700 text-sm">{parameterGuide.recommendedRange}</p>
              </div>

              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <h4 className="font-medium text-amber-900 text-sm mb-1">Impact</h4>
                <p className="text-amber-700 text-sm">{parameterGuide.impact}</p>
              </div>

              {parameterGuide.examples && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <h4 className="font-medium text-green-900 text-sm mb-1">Examples</h4>
                  <ul className="text-green-700 text-sm space-y-1">
                    {parameterGuide.examples.map((example, idx) => (
                      <li key={idx}>• {example}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="text-center py-8">
            <HelpCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-sm text-muted-foreground">
              Click on any parameter to see detailed guidance
            </p>
          </div>
        )}
      </div>
    );
  };

  const ComparisonView: React.FC = () => {
    const changes = getConfigurationChanges(baseStrategy, strategy);
    
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-sm">Configuration Changes</h3>
          <Badge variant="outline">{changes.length} changes</Badge>
        </div>

        <div className="space-y-2">
          {changes.map((change, idx) => (
            <div key={idx} className="p-3 border rounded-lg">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium">{change.parameter}</span>
                <Badge className={getChangeImpactColor(change.impact)}>
                  {change.impact}
                </Badge>
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span>{change.oldValue}</span>
                <span>→</span>
                <span className="font-medium">{change.newValue}</span>
              </div>
              {change.impact === 'high' && (
                <div className="mt-2 p-2 bg-amber-50 border border-amber-200 rounded">
                  <p className="text-xs text-amber-700">{change.warning}</p>
                </div>
              )}
            </div>
          ))}
        </div>

        {changes.length === 0 && (
          <div className="text-center py-8">
            <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
            <p className="text-sm text-muted-foreground">
              No changes from base configuration
            </p>
          </div>
        )}
      </div>
    );
  };

  const ResultsView: React.FC = () => {
    if (!testResults) {
      return (
        <div className="text-center py-8">
          <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-sm text-muted-foreground mb-3">
            No test results available
          </p>
          <Button size="sm" variant="outline">
            Run Test
          </Button>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-3">
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-lg font-bold text-green-700">
              {(testResults.avg_probability * 100).toFixed(0)}%
            </div>
            <div className="text-xs text-green-600">Win Rate</div>
          </div>
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-lg font-bold text-blue-700">
              ${testResults.avg_expected_value?.toFixed(0) || '0'}
            </div>
            <div className="text-xs text-blue-600">Expected Value</div>
          </div>
        </div>

        <div className="text-center p-3 bg-purple-50 rounded-lg">
          <div className="text-lg font-bold text-purple-700">
            {testResults.opportunities_found || 0}
          </div>
          <div className="text-xs text-purple-600">Opportunities Found</div>
        </div>

        {/* Performance Analysis */}
        <div className="space-y-3">
          <h4 className="font-medium text-sm">Performance Analysis</h4>
          
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-xs">Risk/Reward Ratio</span>
              <span className="text-xs font-medium">
                {(testResults.risk_reward_ratio || 0).toFixed(2)}
              </span>
            </div>
            <Progress value={(testResults.risk_reward_ratio || 0) * 20} className="h-2" />
          </div>

          {testResults.avg_probability > 0.7 && (
            <div className="p-2 bg-green-50 border border-green-200 rounded">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-600" />
                <span className="text-xs text-green-700">High success probability</span>
              </div>
            </div>
          )}

          {testResults.avg_probability < 0.5 && (
            <div className="p-2 bg-red-50 border border-red-200 rounded">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-600" />
                <span className="text-xs text-red-700">Low success probability - consider adjustments</span>
              </div>
            </div>
          )}
        </div>

        {/* Top Opportunities Preview */}
        {testResults.opportunities && testResults.opportunities.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-medium text-sm">Top Opportunities</h4>
            {testResults.opportunities.slice(0, 3).map((opp: any, idx: number) => (
              <div key={idx} className="p-2 border rounded text-xs">
                <div className="flex justify-between items-center">
                  <span className="font-medium">{opp.symbol}</span>
                  <Badge variant="outline" className="text-xs">
                    {(opp.probability_profit * 100).toFixed(0)}%
                  </Badge>
                </div>
                <div className="text-muted-foreground">
                  DTE: {opp.days_to_expiration} | Premium: ${opp.premium?.toFixed(2) || '0.00'}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const AIAssistant: React.FC = () => (
    <div className="space-y-4">
      <div className="text-center py-8">
        <MessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <p className="text-sm text-muted-foreground mb-3">
          Ask questions about your strategy
        </p>
        <div className="space-y-2">
          <Button size="sm" variant="outline" className="w-full text-xs">
            How does this strategy work?
          </Button>
          <Button size="sm" variant="outline" className="w-full text-xs">
            What can I improve?
          </Button>
          <Button size="sm" variant="outline" className="w-full text-xs">
            Compare to base strategy
          </Button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="h-full bg-white border-l flex flex-col">
      {/* Header with minimize button */}
      <div className="p-3 border-b flex items-center justify-between">
        <h2 className="font-semibold text-sm">Context</h2>
        <Button variant="ghost" size="sm" onClick={onToggleMinimized}>
          <HelpCircle className="w-4 h-4" />
        </Button>
      </div>

      {/* Tab Navigation */}
      <Tabs value={activeTab} onValueChange={(value: any) => setActiveTab(value)} className="flex-1 flex flex-col">
        <TabsList className="grid w-full grid-cols-4 m-3 mb-0">
          <TabsTrigger value="help" className="text-xs">
            <HelpCircle className="w-3 h-3 mr-1" />
            Help
          </TabsTrigger>
          <TabsTrigger value="comparison" className="text-xs">
            <GitCompare className="w-3 h-3 mr-1" />
            Diff
          </TabsTrigger>
          <TabsTrigger value="results" className="text-xs">
            <BarChart3 className="w-3 h-3 mr-1" />
            Results
          </TabsTrigger>
          <TabsTrigger value="ai" className="text-xs">
            <MessageSquare className="w-3 h-3 mr-1" />
            AI
          </TabsTrigger>
        </TabsList>

        <div className="flex-1 overflow-y-auto">
          <TabsContent value="help" className="p-3 pt-0 m-0">
            <ParameterHelp />
          </TabsContent>
          <TabsContent value="comparison" className="p-3 pt-0 m-0">
            <ComparisonView />
          </TabsContent>
          <TabsContent value="results" className="p-3 pt-0 m-0">
            <ResultsView />
          </TabsContent>
          <TabsContent value="ai" className="p-3 pt-0 m-0">
            <AIAssistant />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
};

// Helper functions
function getParameterGuide(parameter?: string) {
  const guides: Record<string, any> = {
    'timing.dte_range': {
      name: 'Days to Expiration Range',
      description: 'Controls how far out in time the strategy looks for options',
      recommendedRange: '14-45 days for most strategies',
      impact: 'Shorter DTE = Higher theta decay, more aggressive. Longer DTE = Lower theta decay, more conservative.',
      examples: [
        '7-14 days: High theta strategies (ThetaCrop)',
        '21-45 days: Moderate theta strategies (Iron Condor)',
        '45-60 days: Conservative long-term strategies'
      ]
    },
    'entry_signals.allowed_bias': {
      name: 'Market Bias',
      description: 'The directional outlook required for strategy entry',
      recommendedRange: 'NEUTRAL for most income strategies',
      impact: 'Determines market conditions needed before opening positions',
      examples: [
        'NEUTRAL: Market expected to stay range-bound',
        'BULLISH: Market expected to trend upward',
        'BEARISH: Market expected to trend downward'
      ]
    }
  };

  return guides[parameter || ''] || {
    name: 'Parameter Guide',
    description: 'Click on a parameter to see specific guidance',
    recommendedRange: 'Varies by strategy',
    impact: 'Parameter-specific impact analysis will appear here'
  };
}

function getConfigurationChanges(baseStrategy: any, customStrategy: any) {
  // Mock implementation - in real app, this would compare configurations
  return [
    {
      parameter: 'DTE Range',
      oldValue: '14-45',
      newValue: '7-45',
      impact: 'high',
      warning: 'Shorter DTE increases theta decay but reduces time for adjustment'
    },
    {
      parameter: 'Max Positions',
      oldValue: '3',
      newValue: '5',
      impact: 'medium'
    }
  ];
}

function getChangeImpactColor(impact: string) {
  switch (impact) {
    case 'high': return 'bg-red-100 text-red-800';
    case 'medium': return 'bg-yellow-100 text-yellow-800';
    case 'low': return 'bg-green-100 text-green-800';
    default: return 'bg-gray-100 text-gray-800';
  }
}

export default SmartContextPanel;