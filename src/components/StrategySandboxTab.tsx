import React, { useState, useEffect } from 'react';
import { Plus, Play, Settings, TrendingUp, Clock, CheckCircle } from 'lucide-react';
import { useTheme } from '@/contexts/ThemeContext';

// System strategy interface
interface SystemStrategy {
  id: string;
  name: string;
  description: string;
  risk_level: string;
  min_dte: number;
  max_dte: number;
  enabled: boolean;
  category: string;
  last_scan: string;
  total_opportunities: number;
}

// Strategy sandbox interfaces
interface StrategyConfig {
  id: string;
  strategy_id: string;
  name: string;
  config_data: any;
  version: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  deployed_at?: string;
  test_run_count: number;
}

interface TestResult {
  success: boolean;
  opportunities: any[];
  opportunities_count: number;
  execution_time_ms: number;
  performance_metrics: {
    total_opportunities: number;
    avg_probability_profit: number;
    avg_expected_value: number;
    avg_premium: number;
    risk_reward_ratio: number;
  };
  timestamp: string;
  symbols_tested?: string[];
}

export const StrategiesTab: React.FC = () => {
  const { theme } = useTheme();
  const [strategies, setStrategies] = useState<StrategyConfig[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<StrategyConfig | null>(null);
  const [availableStrategies, setAvailableStrategies] = useState<SystemStrategy[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [showCreateView, setShowCreateView] = useState(false);
  const [isLoadingStrategies, setIsLoadingStrategies] = useState(true);

  // Load user's sandbox strategies and available base strategies
  useEffect(() => {
    loadStrategies();
    loadAvailableStrategies();
  }, []);

  const loadStrategies = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/sandbox/strategies/');
      if (response.ok) {
        const data = await response.json();
        setStrategies(data);
        
        // Select first strategy by default
        if (data.length > 0 && !selectedStrategy) {
          setSelectedStrategy(data[0]);
        }
      }
    } catch (error) {
      console.error('Error loading strategies:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadAvailableStrategies = async () => {
    try {
      setIsLoadingStrategies(true);
      const response = await fetch('/api/strategies/');
      if (response.ok) {
        const data = await response.json();
        setAvailableStrategies(data.strategies);
      }
    } catch (error) {
      console.error('Error loading available strategies:', error);
    } finally {
      setIsLoadingStrategies(false);
    }
  };

  const createNewStrategy = () => {
    setShowCreateView(true);
    setSelectedStrategy(null);
  };

  const handleStrategyCreated = () => {
    // Reload strategies when a new one is created
    loadStrategies();
    setShowCreateView(false);
    setIsCreating(false);
  };

  const themeClasses = {
    container: theme === 'dark' 
      ? 'bg-gray-900 text-white' 
      : 'bg-gray-50 text-gray-900',
    header: theme === 'dark'
      ? 'bg-gray-800 border-gray-700'
      : 'bg-white border-gray-200',
    sidebar: theme === 'dark'
      ? 'bg-gray-800 border-gray-700'
      : 'bg-white border-gray-200',
    card: theme === 'dark'
      ? 'bg-gray-800 border-gray-600 hover:bg-gray-700'
      : 'bg-white border-gray-200 hover:bg-gray-50',
    text: {
      primary: theme === 'dark' ? 'text-white' : 'text-gray-900',
      secondary: theme === 'dark' ? 'text-gray-300' : 'text-gray-600',
      muted: theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
    }
  };

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center h-96 ${themeClasses.container}`}>
        <div className="text-center">
          <Clock className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-500" />
          <p className={themeClasses.text.secondary}>Loading strategies...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`h-full flex flex-col ${themeClasses.container}`}>
      {/* Header */}
      <div className={`${themeClasses.header} border-b px-6 py-4`}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className={`text-2xl font-bold ${themeClasses.text.primary}`}>Strategy Sandbox</h1>
            <p className={`${themeClasses.text.secondary} mt-1`}>
              Develop, test, and optimize your trading strategies safely
            </p>
          </div>
          <button
            onClick={createNewStrategy}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Strategy
          </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Strategy List Sidebar */}
        <div className={`w-80 ${themeClasses.sidebar} border-r flex flex-col`}>
          <div className={`p-4 border-b ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'}`}>
            <h2 className={`font-semibold ${themeClasses.text.primary}`}>Your Strategies</h2>
            <p className={`text-sm ${themeClasses.text.secondary} mt-1`}>{strategies.length} strategies</p>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            {strategies.length === 0 ? (
              <div className={`p-4 text-center ${themeClasses.text.muted}`}>
                <Settings className={`w-8 h-8 mx-auto mb-2 ${themeClasses.text.muted}`} />
                <p className="text-sm">No strategies yet</p>
                <p className={`text-xs ${themeClasses.text.muted} mt-1`}>Create your first strategy to get started</p>
              </div>
            ) : (
              <div className="space-y-2 p-4">
                {strategies.map((strategy) => (
                  <StrategyCard
                    key={strategy.id}
                    strategy={strategy}
                    isSelected={selectedStrategy?.id === strategy.id}
                    onClick={() => setSelectedStrategy(strategy)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex">
          {(showCreateView || !selectedStrategy) ? (
              <EmptyStrategyView 
                availableStrategies={availableStrategies}
                onCreateNew={handleStrategyCreated}
                showBackButton={showCreateView && strategies.length > 0}
                isLoadingStrategies={isLoadingStrategies}
                onBack={() => {
                  setShowCreateView(false);
                  if (strategies.length > 0) {
                    setSelectedStrategy(strategies[0]);
                  }
                }}
              />
          ) : (
            <StrategyEditor
              strategy={selectedStrategy}
              onStrategyUpdate={(updated) => {
                setStrategies(prev => 
                  prev.map(s => s.id === updated.id ? updated : s)
                );
                setSelectedStrategy(updated);
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
};

// Strategy card component for the sidebar
const StrategyCard: React.FC<{
  strategy: StrategyConfig;
  isSelected: boolean;
  onClick: () => void;
}> = ({ strategy, isSelected, onClick }) => {
  const { theme } = useTheme();
  
  const getStatusColor = (isActive: boolean) => {
    if (theme === 'dark') {
      return isActive ? 'text-green-400 bg-green-900' : 'text-gray-400 bg-gray-700';
    }
    return isActive ? 'text-green-600 bg-green-100' : 'text-gray-600 bg-gray-100';
  };

  const getStatusIcon = (isActive: boolean) => {
    return isActive ? CheckCircle : Settings;
  };

  const StatusIcon = getStatusIcon(strategy.is_active);

  const cardClasses = theme === 'dark' 
    ? (isSelected 
        ? 'border-blue-400 bg-blue-900/20 shadow-sm' 
        : 'border-gray-600 hover:border-gray-500 hover:bg-gray-700/50')
    : (isSelected
        ? 'border-blue-500 bg-blue-50 shadow-sm'
        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50');

  const textClasses = {
    primary: theme === 'dark' ? 'text-white' : 'text-gray-900',
    secondary: theme === 'dark' ? 'text-gray-300' : 'text-gray-600',
    muted: theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
  };

  return (
    <div
      onClick={onClick}
      className={`p-4 rounded-lg border cursor-pointer transition-all ${cardClasses}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className={`font-medium ${textClasses.primary} truncate`}>{strategy.name}</h3>
            <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full ${getStatusColor(strategy.is_active)}`}>
              <StatusIcon className="w-3 h-3" />
              {strategy.is_active ? 'Live' : 'Testing'}
            </span>
          </div>
          <p className={`text-sm ${textClasses.secondary} mt-1`}>{strategy.strategy_id}</p>
          <div className={`flex items-center gap-4 mt-2 text-xs ${textClasses.muted}`}>
            <span className="flex items-center gap-1">
              <Play className="w-3 h-3" />
              {strategy.test_run_count} tests
            </span>
            <span>v{strategy.version}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// Strategy editor component (right side)
const StrategyEditor: React.FC<{
  strategy: StrategyConfig;
  onStrategyUpdate: (strategy: StrategyConfig) => void;
}> = ({ strategy, onStrategyUpdate }) => {
  const [isRunningTest, setIsRunningTest] = useState(false);
  const [lastTestResult, setLastTestResult] = useState<TestResult | null>(null);
  const [currentStrategy, setCurrentStrategy] = useState<StrategyConfig>(strategy);

  // Update currentStrategy when strategy prop changes
  useEffect(() => {
    setCurrentStrategy(strategy);
  }, [strategy]);

  // Run a test for this sandbox strategy configuration
  const runStrategyTest = async () => {
    try {
      setIsRunningTest(true);
      const response = await fetch(`/api/sandbox/test/run/${strategy.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          max_opportunities: 10,
          use_cached_data: true
        })
      });

      if (response.ok) {
        const testResult = await response.json();
        setLastTestResult(testResult);
        
        // Update strategy test count
        const updatedStrategy = { ...strategy, test_run_count: strategy.test_run_count + 1 };
        onStrategyUpdate(updatedStrategy);
      }
    } catch (error) {
      console.error('Error running test:', error);
    } finally {
      setIsRunningTest(false);
    }
  };

  // Handle parameter changes
  const handleParameterChange = async (parameter: string, value: any) => {
    // Handle nested parameter paths like 'trading.target_dte_range'
    const keys = parameter.split('.');
    const newConfigData = { ...currentStrategy.config_data };
    let current = newConfigData;
    
    // Navigate to the parent object
    for (let i = 0; i < keys.length - 1; i++) {
      if (!current[keys[i]]) current[keys[i]] = {};
      current = current[keys[i]];
    }
    
    // Set the final value
    current[keys[keys.length - 1]] = value;
    
    const updatedStrategy = {
      ...currentStrategy,
      config_data: newConfigData
    };
    
    setCurrentStrategy(updatedStrategy);
    
    // Persist changes to backend
    try {
      const response = await fetch(`/api/sandbox/strategies/${strategy.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          config_data: updatedStrategy.config_data
        })
      });
      
      if (response.ok) {
        onStrategyUpdate(updatedStrategy);
      }
    } catch (error) {
      console.error('Error saving parameter changes:', error);
    }
  };

  const { theme } = useTheme();
  
  const themeClasses = {
    configPanel: theme === 'dark' 
      ? 'bg-gray-900 border-gray-700' 
      : 'bg-white border-gray-200',
    aiPanel: theme === 'dark'
      ? 'bg-gray-800 border-gray-700'
      : 'bg-gray-50 border-gray-200',
    text: {
      primary: theme === 'dark' ? 'text-white' : 'text-gray-900',
      secondary: theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
    }
  };

  return (
    <div className="flex-1 flex">
      {/* Strategy Configuration Panel (Left) */}
      <div className={`flex-1 ${themeClasses.configPanel} border-r`}>
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className={`text-xl font-semibold ${themeClasses.text.primary}`}>{strategy.name}</h2>
              <p className={themeClasses.text.secondary}>{strategy.strategy_id}</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={runStrategyTest}
                disabled={isRunningTest}
                className="flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg transition-colors"
              >
                {isRunningTest ? (
                  <>
                    <Clock className="w-4 h-4 animate-spin" />
                    Testing...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Run Test
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Strategy Parameters */}
          <StrategyParametersPanel 
            strategy={currentStrategy} 
            onParameterChange={handleParameterChange}
          />

          {/* Test Results */}
          {lastTestResult && (
            <TestResultsPanel result={lastTestResult} />
          )}
        </div>
      </div>

      {/* AI Assistant Panel (Right) */}
      <div className={`w-80 ${themeClasses.aiPanel} border-l`}>
        <AIAssistantPanel strategy={strategy} />
      </div>
    </div>
  );
};

// Strategy parameters panel with editing capabilities
const StrategyParametersPanel: React.FC<{ 
  strategy: StrategyConfig,
  onParameterChange?: (parameter: string, value: any) => void 
}> = ({ strategy, onParameterChange }) => {
  const { theme } = useTheme();
  const [isEditing, setIsEditing] = useState(false);
  const [editedConfig, setEditedConfig] = useState(strategy.config_data);
  const [universes, setUniverses] = useState<any[]>([]);
  const [selectedUniverse, setSelectedUniverse] = useState('');

  // Load available universes
  useEffect(() => {
    const loadUniverses = async () => {
      try {
        const response = await fetch('/api/sandbox/data/universes');
        if (response.ok) {
          const data = await response.json();
          setUniverses(Object.entries(data.universes).map(([key, info]: [string, any]) => ({
            id: key,
            ...info
          })));
          
          // Set current universe if it matches
          const currentSymbols = strategy.config_data.universe?.primary_symbols || [];
          console.log('Current symbols:', currentSymbols);
          console.log('Available universes:', Object.keys(data.universes));
          
          if (currentSymbols.length > 0) {
            // Try to match current symbols to a universe
            const matchingUniverse = Object.keys(data.universes).find(key => {
              // Simple heuristic - if first symbol matches common universe patterns
              if (key === 'mag7' && currentSymbols.includes('AAPL')) return true;
              if (key === 'etfs' && currentSymbols.includes('SPY')) return true;
              if (key === 'thetacrop' && currentSymbols.includes('QQQ')) return true;
              return false;
            });
            console.log('Matching universe:', matchingUniverse);
            if (matchingUniverse) setSelectedUniverse(matchingUniverse);
          }
        }
      } catch (error) {
        console.error('Error loading universes:', error);
      }
    };
    loadUniverses();
  }, [strategy]);

  const handleUniverseChange = async (universeId: string) => {
    if (!universeId) return;
    
    try {
      const response = await fetch(`/api/sandbox/data/universe/${universeId}`);
      if (response.ok) {
        const data = await response.json();
        const newConfig = {
          ...editedConfig,
          universe: {
            ...editedConfig.universe,
            primary_symbols: data.symbols
          }
        };
        setEditedConfig(newConfig);
        setSelectedUniverse(universeId);
        
        if (onParameterChange) {
          onParameterChange('universe.primary_symbols', data.symbols);
        }
      }
    } catch (error) {
      console.error('Error loading universe symbols:', error);
    }
  };

  const handleParameterEdit = (path: string, value: any) => {
    const keys = path.split('.');
    const newConfig = { ...editedConfig };
    let current = newConfig;
    
    for (let i = 0; i < keys.length - 1; i++) {
      if (!current[keys[i]]) current[keys[i]] = {};
      current = current[keys[i]];
    }
    current[keys[keys.length - 1]] = value;
    
    setEditedConfig(newConfig);
    if (onParameterChange) {
      onParameterChange(path, value);
    }
  };

  const config = isEditing ? editedConfig : strategy.config_data;

  const themeClasses = {
    title: theme === 'dark' ? 'text-white' : 'text-gray-900',
    parametersBg: theme === 'dark' ? 'bg-gray-800' : 'bg-gray-50',
    sectionTitle: theme === 'dark' ? 'text-gray-300' : 'text-gray-700',
    input: theme === 'dark' 
      ? 'border-gray-600 bg-gray-700 text-white focus:ring-blue-400 focus:border-blue-400' 
      : 'border-gray-300 bg-white text-gray-900 focus:ring-blue-500 focus:border-blue-500',
    select: theme === 'dark'
      ? 'border-gray-600 bg-gray-700 text-white focus:ring-blue-400 appearance-none cursor-pointer'
      : 'border-gray-300 bg-white text-gray-900 focus:ring-blue-500 appearance-none cursor-pointer'
  };

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className={`font-medium ${themeClasses.title}`}>Strategy Parameters</h3>
        <button
          onClick={() => {
            console.log('Toggle editing mode from', isEditing, 'to', !isEditing);
            setIsEditing(!isEditing);
          }}
          className={`px-3 py-1 text-xs rounded-lg transition-colors ${
            isEditing 
              ? 'bg-green-100 text-green-800 hover:bg-green-200'
              : 'bg-blue-100 text-blue-800 hover:bg-blue-200'
          }`}
        >
          {isEditing ? 'Save Changes' : 'Edit Parameters'}
        </button>
      </div>
      
      <div className={`space-y-4 ${themeClasses.parametersBg} p-4 rounded-lg`}>
        {/* Universe Selection */}
        <div>
          <h4 className={`font-medium text-sm ${themeClasses.sectionTitle} mb-2`}>Trading Universe</h4>
          {/* Debug info */}
          <div className="text-xs text-gray-500 mb-1">
            Debug: isEditing={isEditing ? 'true' : 'false'}, selectedUniverse="{selectedUniverse}", universes.length={universes.length}
          </div>
          {isEditing ? (
            <div className="space-y-2">
              <div className="relative">
                <select
                  value={selectedUniverse}
                  onChange={(e) => handleUniverseChange(e.target.value)}
                  className={`block w-full px-3 py-2 pr-10 border rounded-md text-sm focus:outline-none focus:ring-2 ${themeClasses.select}`}
                >
                  <option value="">Select Universe...</option>
                  {universes.map((universe) => (
                    <option key={universe.id} value={universe.id}>
                      {universe.name} ({universe.typical_count} symbols)
                    </option>
                  ))}
                </select>
                {/* Custom dropdown arrow */}
                <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                  <svg className={`w-4 h-4 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
              <div className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                {selectedUniverse && universes.find(u => u.id === selectedUniverse)?.description}
              </div>
            </div>
          ) : (
            <div className="flex flex-wrap gap-1">
              {config.universe?.primary_symbols?.map((symbol: string) => (
                <span key={symbol} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                  {symbol}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Trading Parameters */}
        {config.trading && (
          <div>
            <h4 className={`font-medium text-sm ${themeClasses.sectionTitle} mb-2`}>Trading Rules</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <ParameterField
                label="DTE Range"
                value={config.trading.target_dte_range?.join('-') || 'N/A'}
                isEditing={isEditing}
                onEdit={(value) => handleParameterEdit('trading.target_dte_range', value.split('-').map(Number))}
              />
              <ParameterField
                label="Delta Target"
                value={config.trading.delta_target || 'N/A'}
                isEditing={isEditing}
                onEdit={(value) => handleParameterEdit('trading.delta_target', parseFloat(value))}
              />
              <ParameterField
                label="Max Positions"
                value={config.trading.max_positions || 'N/A'}
                isEditing={isEditing}
                onEdit={(value) => handleParameterEdit('trading.max_positions', parseInt(value))}
              />
              <ParameterField
                label="Wing Widths"
                value={config.trading.wing_widths?.map((w: number) => `$${w}`).join(', ') || 'N/A'}
                isEditing={isEditing}
                onEdit={(value) => handleParameterEdit('trading.wing_widths', value.split(',').map((v: string) => parseInt(v.replace('$', '').trim())))}
              />
            </div>
          </div>
        )}

        {/* Risk Parameters */}
        {config.risk && (
          <div>
            <h4 className={`font-medium text-sm ${themeClasses.sectionTitle} mb-2`}>Risk Management</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <ParameterField
                label="Profit Target"
                value={`${(config.risk.profit_target * 100).toFixed(0)}%`}
                isEditing={isEditing}
                onEdit={(value) => handleParameterEdit('risk.profit_target', parseFloat(value) / 100)}
              />
              <ParameterField
                label="Loss Limit"
                value={`${(config.risk.loss_limit * 100).toFixed(0)}%`}
                isEditing={isEditing}
                onEdit={(value) => handleParameterEdit('risk.loss_limit', parseFloat(value) / 100)}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Parameter field component for inline editing
const ParameterField: React.FC<{
  label: string;
  value: any;
  isEditing: boolean;
  onEdit?: (value: string) => void;
}> = ({ label, value, isEditing, onEdit }) => {
  const { theme } = useTheme();
  const [editValue, setEditValue] = useState(String(value));

  const themeClasses = {
    label: theme === 'dark' ? 'text-gray-300' : 'text-gray-600',
    value: theme === 'dark' ? 'text-white' : 'text-gray-900',
    input: theme === 'dark' 
      ? 'border-gray-600 bg-gray-700 text-white focus:ring-blue-400' 
      : 'border-gray-300 bg-white text-gray-900 focus:ring-blue-500'
  };

  return (
    <div>
      <span className={themeClasses.label}>{label}:</span>
      {isEditing && onEdit ? (
        <input
          type="text"
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onBlur={() => onEdit(editValue)}
          className={`ml-2 px-2 py-1 border rounded text-xs w-20 focus:outline-none focus:ring-1 ${themeClasses.input}`}
        />
      ) : (
        <span className={`ml-2 font-medium ${themeClasses.value}`}>{value}</span>
      )}
    </div>
  );
};

// Test results panel
const TestResultsPanel: React.FC<{ result: TestResult }> = ({ result }) => {
  const { theme } = useTheme();
  
  const themeClasses = {
    container: theme === 'dark' ? 'bg-green-900/20 border-green-700' : 'bg-green-50 border-green-200',
    header: theme === 'dark' ? 'text-green-400' : 'text-green-800',
    text: theme === 'dark' ? 'text-gray-300' : 'text-gray-600',
    accent: theme === 'dark' ? 'text-green-400' : 'text-green-700',
    cardBg: theme === 'dark' ? 'bg-gray-800 border-gray-600' : 'bg-white border-gray-200'
  };

  return (
    <div className="mb-6">
      <h3 className={`font-medium mb-4 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>Latest Test Results</h3>
      
      <div className={`${themeClasses.container} border rounded-lg p-4`}>
        <div className="flex items-center gap-2 mb-3">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <span className={`font-medium ${themeClasses.header}`}>Test Completed Successfully</span>
        </div>
        
        <div className="grid grid-cols-2 gap-4 text-sm mb-4">
          <div>
            <span className={themeClasses.text}>Opportunities Found:</span>
            <span className={`ml-2 font-bold ${themeClasses.accent}`}>{result.opportunities_count}</span>
          </div>
          <div>
            <span className={themeClasses.text}>Execution Time:</span>
            <span className="ml-2 font-medium">{result.execution_time_ms}ms</span>
          </div>
          <div>
            <span className={themeClasses.text}>Avg Win Rate:</span>
            <span className="ml-2 font-medium">
              {result.performance_metrics?.avg_probability_profit 
                ? (result.performance_metrics.avg_probability_profit * 100).toFixed(1) + '%'
                : 'N/A'}
            </span>
          </div>
          <div>
            <span className={themeClasses.text}>Avg Premium:</span>
            <span className="ml-2 font-medium">
              {result.performance_metrics?.avg_premium 
                ? '$' + result.performance_metrics.avg_premium.toFixed(2)
                : 'N/A'}
            </span>
          </div>
        </div>

        {/* Display Individual Opportunities */}
        {result.opportunities && result.opportunities.length > 0 && (
          <div className="mt-4">
            <h4 className={`font-medium text-sm mb-2 ${themeClasses.header}`}>Opportunities Found:</h4>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {result.opportunities.map((opp, index) => (
                <div key={opp.id || index} className={`${themeClasses.cardBg} border rounded p-3 text-sm`}>
                  <div className="flex justify-between items-start">
                    <div>
                      <span className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                        {opp.symbol}
                      </span>
                      <span className={`ml-2 text-xs px-2 py-1 rounded ${theme === 'dark' ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800'}`}>
                        {opp.strategy_type}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className={`font-medium ${themeClasses.accent}`}>
                        {(opp.probability_profit * 100).toFixed(1)}% win rate
                      </div>
                      <div className={`text-xs ${themeClasses.text}`}>
                        ${opp.premium?.toFixed(2) || 'N/A'} premium
                      </div>
                    </div>
                  </div>
                  <div className={`mt-2 text-xs ${themeClasses.text} grid grid-cols-2 gap-2`}>
                    <div>DTE: {opp.days_to_expiration}</div>
                    <div>Expected: ${opp.expected_value?.toFixed(0) || 'N/A'}</div>
                    <div>Max Loss: ${opp.max_loss?.toFixed(0) || 'N/A'}</div>
                    <div>Liquidity: {opp.liquidity_score?.toFixed(1) || 'N/A'}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// AI Assistant panel
const AIAssistantPanel: React.FC<{ strategy: StrategyConfig }> = ({ strategy }) => {
  const { theme } = useTheme();
  const [messages, setMessages] = useState<Array<{role: string, content: string, timestamp: string}>>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch(`/api/sandbox/ai/chat/${strategy.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          include_context: true
        })
      });

      if (response.ok) {
        const aiResponse = await response.json();
        const aiMessage = {
          role: 'assistant',
          content: aiResponse.response,
          timestamp: aiResponse.timestamp
        };
        setMessages(prev => [...prev, aiMessage]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const themeClasses = {
    border: theme === 'dark' ? 'border-gray-700' : 'border-gray-200',
    title: theme === 'dark' ? 'text-white' : 'text-gray-900',
    subtitle: theme === 'dark' ? 'text-gray-300' : 'text-gray-600',
    emptyText: theme === 'dark' ? 'text-gray-400' : 'text-gray-500',
    messageAssistant: theme === 'dark' ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-200',
    input: theme === 'dark' 
      ? 'border-gray-600 bg-gray-700 text-white focus:ring-blue-400 focus:border-blue-400' 
      : 'border-gray-300 bg-white text-gray-900 focus:ring-blue-500 focus:border-blue-500'
  };

  return (
    <div className="h-full flex flex-col">
      <div className={`p-4 border-b ${themeClasses.border}`}>
        <h3 className={`font-medium ${themeClasses.title}`}>AI Strategy Assistant</h3>
        <p className={`text-sm ${themeClasses.subtitle} mt-1`}>Ask questions about your strategy</p>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className={`text-center ${themeClasses.emptyText} mt-8`}>
            <TrendingUp className={`w-8 h-8 mx-auto mb-2 ${themeClasses.emptyText}`} />
            <p className="text-sm">Ask me about your strategy!</p>
            <p className={`text-xs ${themeClasses.emptyText} mt-1`}>
              Try "How does this strategy look?" or "What can I improve?"
            </p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div key={index} className={`${
              message.role === 'user' ? 'ml-4' : 'mr-4'
            }`}>
              <div className={`p-3 rounded-lg ${
                message.role === 'user' 
                  ? 'bg-blue-600 text-white ml-auto max-w-xs' 
                  : `${themeClasses.messageAssistant} border max-w-sm`
              }`}>
                <p className="text-sm">{message.content}</p>
              </div>
              <p className="text-xs text-gray-500 mt-1 text-right">
                {new Date(message.timestamp).toLocaleTimeString()}
              </p>
            </div>
          ))
        )}
        {isLoading && (
          <div className="mr-4">
            <div className={`${themeClasses.messageAssistant} border p-3 rounded-lg max-w-sm`}>
              <div className="flex items-center gap-2">
                <Clock className={`w-4 h-4 animate-spin ${themeClasses.emptyText}`} />
                <span className={`text-sm ${themeClasses.emptyText}`}>Thinking...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Message Input */}
      <div className={`p-4 border-t ${themeClasses.border}`}>
        <div className="flex gap-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Type your question..."
            className={`flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:border-transparent text-sm ${themeClasses.input}`}
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !inputMessage.trim()}
            className="px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-colors"
          >
            <Play className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

// Empty state when no strategy is selected
const EmptyStrategyView: React.FC<{ 
  availableStrategies: SystemStrategy[];
  onCreateNew: () => void;
  showBackButton?: boolean;
  onBack?: () => void;
  isLoadingStrategies?: boolean;
}> = ({ availableStrategies, onCreateNew, showBackButton = false, onBack, isLoadingStrategies = false }) => {
  
  const createSandboxStrategy = async (baseStrategy: SystemStrategy) => {
    try {
      // Create a new sandbox configuration based on the selected base strategy
      const response = await fetch('/api/sandbox/strategies/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          strategy_id: baseStrategy.id,
          name: `${baseStrategy.name} - Custom`,
          config_data: {
            // Load default parameters from the base strategy
            universe: {
              universe_name: "thetacrop", // Default universe
            },
            trading: {
              target_dte_range: [baseStrategy.min_dte, baseStrategy.max_dte],
              max_positions: 5
            },
            risk: {
              profit_target: 0.5,
              loss_limit: -2.0
            }
          }
        })
      });

      if (response.ok) {
        const newStrategy = await response.json();
        // Notify parent that a new strategy was created
        onCreateNew();
      }
    } catch (error) {
      console.error('Error creating sandbox strategy:', error);
    }
  };
  const { theme } = useTheme();
  
  const themeClasses = {
    container: theme === 'dark' ? 'bg-gray-900' : 'bg-white',
    title: theme === 'dark' ? 'text-white' : 'text-gray-900',
    text: theme === 'dark' ? 'text-gray-300' : 'text-gray-600',
    icon: theme === 'dark' ? 'text-gray-500' : 'text-gray-400'
  };

  return (
    <div className={`flex-1 flex flex-col ${themeClasses.container}`}>
      {showBackButton && (
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
          >
            ← Back to Your Strategies
          </button>
        </div>
      )}
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center max-w-2xl">
          <Settings className={`w-16 h-16 mx-auto mb-4 ${themeClasses.icon}`} />
          <h2 className={`text-xl font-semibold ${themeClasses.title} mb-2`}>Strategy Sandbox</h2>
          <p className={`${themeClasses.text} mb-6`}>
            Create and test your trading strategies in a safe environment. 
            Select a base strategy below to customize and test with your own parameters.
          </p>
          
          {isLoadingStrategies ? (
            <div className={`p-4 ${themeClasses.text} text-center`}>
              <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
              Loading available strategies...
            </div>
          ) : availableStrategies.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-8">
              {availableStrategies.map((strategy) => (
                <div
                  key={strategy.id}
                  className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                    theme === 'dark' 
                      ? 'border-gray-600 hover:border-gray-500 bg-gray-800' 
                      : 'border-gray-200 hover:border-gray-300 bg-white'
                  }`}
                  onClick={() => createSandboxStrategy(strategy)}
                >
                  <h3 className={`font-medium ${themeClasses.title} mb-1`}>{strategy.name}</h3>
                  <p className={`text-sm ${themeClasses.text} mb-2`}>{strategy.description}</p>
                  <div className="flex items-center justify-between text-xs">
                    <span className={`px-2 py-1 rounded ${
                      theme === 'dark' ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-700'
                    }`}>
                      {strategy.category}
                    </span>
                    <span className={themeClasses.text}>
                      {strategy.total_opportunities} opportunities
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className={`p-4 ${themeClasses.text} text-center`}>
              <p>No strategies available. Please check your connection and try again.</p>
              <button 
                onClick={() => window.location.reload()} 
                className="mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Reload Page
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StrategiesTab;