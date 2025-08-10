import React, { useState, useCallback, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Slider } from './ui/slider';
import { Switch } from './ui/switch';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Info, Settings, TrendingUp, Shield, Target, Zap, Save, Download, Bookmark } from 'lucide-react';

interface UniversalFormField {
  key: string;
  label: string;
  type: 'number' | 'slider' | 'range' | 'toggle' | 'select' | 'multiselect' | 'display';
  value?: any;
  min?: number;
  max?: number;
  step?: number;
  options?: string[];
  editable?: boolean;
  tooltip?: string;
  format?: 'percentage' | 'currency' | 'days' | 'delta';
}

interface UniversalFormSection {
  id: string;
  title: string;
  icon: React.ReactNode;
  description: string;
  fields: UniversalFormField[];
}

interface UniversalStrategyFormProps {
  strategy: any;
  baseStrategy: any;
  onParameterChange: (key: string, value: any) => void;
}

// Universal parameter mapping - maps any strategy parameter to standard form locations
const createUniversalMapping = (strategy: any, baseStrategy: any): UniversalFormSection[] => {
  const config = strategy.config_data || {};
  const baseConfig = baseStrategy?.complete_config || {};
  
  // Helper to safely get nested values
  const getValue = (path: string, defaultValue: any = null) => {
    return path.split('.').reduce((obj, key) => obj?.[key], config) ?? 
           path.split('.').reduce((obj, key) => obj?.[key], baseConfig) ?? 
           defaultValue;
  };

  // Helper to determine if field should be editable
  const isEditable = (path: string): boolean => {
    const criticalPaths = ['universe.', 'strategy_type', 'module'];
    return !criticalPaths.some(critical => path.includes(critical));
  };

  return [
    {
      id: 'position_params',
      title: 'Position Parameters',
      icon: <Settings className="w-4 h-4" />,
      description: 'Core position sizing and timing',
      fields: [
        {
          key: 'position_parameters.max_opportunities',
          label: 'Max Opportunities',
          type: 'number',
          value: getValue('position_parameters.max_opportunities', getValue('max_opportunities', 3)),
          min: 1,
          max: 20,
          editable: true,
          tooltip: 'Maximum number of opportunities to find'
        },
        {
          key: 'position_parameters.target_dte',
          label: 'Target DTE Range',
          type: 'range',
          value: getValue('position_parameters.target_dtes', getValue('timing.dte_range', [14, 45])),
          min: 1,
          max: 120,
          editable: true,
          format: 'days',
          tooltip: 'Days to expiration range'
        },
        {
          key: 'position_parameters.position_size',
          label: 'Position Size Limit',
          type: 'number',
          value: getValue('position_parameters.position_size_limit', getValue('position_parameters.max_position_size', 1000)),
          min: 100,
          max: 10000,
          editable: true,
          format: 'currency',
          tooltip: 'Maximum position size in dollars'
        },
        {
          key: 'position_parameters.max_allocation',
          label: 'Max Portfolio Allocation',
          type: 'slider',
          value: getValue('risk_management.max_allocation_percentage', getValue('position_parameters.max_allocation', 0.2)),
          min: 0.05,
          max: 0.5,
          step: 0.01,
          editable: true,
          format: 'percentage',
          tooltip: 'Maximum percentage of portfolio'
        }
      ]
    },
    {
      id: 'risk_management',
      title: 'Risk Management',
      icon: <Shield className="w-4 h-4" />,
      description: 'Risk controls and safety limits',
      fields: [
        {
          key: 'risk_management.profit_target',
          label: 'Profit Target',
          type: 'slider',
          value: getValue('exit_rules.profit_targets.0.level', getValue('profit_target', 0.5)),
          min: 0.1,
          max: 2.0,
          step: 0.05,
          editable: true,
          format: 'percentage',
          tooltip: 'Target profit as percentage of premium'
        },
        {
          key: 'risk_management.stop_loss',
          label: 'Stop Loss',
          type: 'slider',
          value: Math.abs(getValue('exit_rules.stop_loss_rules.0.trigger', getValue('stop_loss', -2.0))),
          min: 0.5,
          max: 5.0,
          step: 0.25,
          editable: true,
          format: 'percentage',
          tooltip: 'Maximum loss as percentage of premium'
        },
        {
          key: 'risk_management.max_correlation',
          label: 'Max Position Correlation',
          type: 'slider',
          value: getValue('risk_management.portfolio_correlation_limit', getValue('max_correlation', 0.8)),
          min: 0.5,
          max: 1.0,
          step: 0.05,
          editable: true,
          tooltip: 'Maximum correlation between positions'
        },
        {
          key: 'risk_management.max_drawdown',
          label: 'Max Drawdown Trigger',
          type: 'slider',
          value: getValue('entry_signals.max_drawdown_pct', getValue('max_drawdown', 0.05)),
          min: 0.02,
          max: 0.2,
          step: 0.01,
          editable: true,
          format: 'percentage',
          tooltip: 'Maximum drawdown before position adjustment'
        }
      ]
    },
    {
      id: 'entry_signals',
      title: 'Entry Signals',
      icon: <TrendingUp className="w-4 h-4" />,
      description: 'Market conditions for entry',
      fields: [
        {
          key: 'entry_signals.volatility_requirement',
          label: 'Volatility Requirement',
          type: 'select',
          value: getValue('entry_signals.volatility_requirements', getValue('volatility_filter', 'NORMAL')),
          options: ['LOW', 'NORMAL', 'HIGH', 'ANY'],
          editable: true,
          tooltip: 'Required implied volatility level'
        },
        {
          key: 'entry_signals.market_bias',
          label: 'Market Bias',
          type: 'select',
          value: getValue('entry_signals.required_bias', getValue('entry_signals.bias', 'NEUTRAL')),
          options: ['BULLISH', 'NEUTRAL', 'BEARISH', 'ANY'],
          editable: true,
          tooltip: 'Required market direction bias'
        },
        {
          key: 'entry_signals.signal_strength',
          label: 'Signal Strength',
          type: 'select',
          value: getValue('entry_signals.allowed_strength', getValue('signal_strength', 'MODERATE')),
          options: ['WEAK', 'MODERATE', 'STRONG', 'ANY'],
          editable: true,
          tooltip: 'Required signal strength for entry'
        },
        {
          key: 'entry_signals.volatility_spike_protection',
          label: 'Volatility Spike Protection',
          type: 'toggle',
          value: getValue('entry_signals.volatility_spike_protection', getValue('vol_protection', true)),
          editable: true,
          tooltip: 'Avoid entries during volatility spikes'
        }
      ]
    },
    {
      id: 'exit_rules',
      title: 'Exit Rules',
      icon: <Target className="w-4 h-4" />,
      description: 'Position exit conditions',
      fields: [
        {
          key: 'exit_rules.time_exit_dte',
          label: 'Time Exit DTE',
          type: 'number',
          value: getValue('exit_rules.time_exits.0.value', getValue('exit_dte', 7)),
          min: 1,
          max: 30,
          editable: true,
          format: 'days',
          tooltip: 'Close position when DTE reaches this level'
        },
        {
          key: 'exit_rules.profit_take_percentage',
          label: 'Profit Take %',
          type: 'slider',
          value: getValue('exit_rules.profit_targets.0.percentage', getValue('profit_take', 1.0)),
          min: 0.25,
          max: 1.0,
          step: 0.25,
          editable: true,
          format: 'percentage',
          tooltip: 'Percentage of position to close at profit target'
        },
        {
          key: 'exit_rules.delta_management',
          label: 'Delta Management',
          type: 'toggle',
          value: getValue('exit_rules.delta_management', getValue('delta_management', false)) !== null,
          editable: true,
          tooltip: 'Enable delta-based position adjustments'
        },
        {
          key: 'exit_rules.earnings_exit',
          label: 'Exit Before Earnings',
          type: 'toggle',
          value: getValue('exit_rules.earnings_exit', getValue('earnings_protection', true)),
          editable: true,
          tooltip: 'Close positions before earnings announcements'
        }
      ]
    },
    {
      id: 'strike_selection',
      title: 'Strike Selection',
      icon: <Zap className="w-4 h-4" />,
      description: 'Strike price selection criteria',
      fields: [
        {
          key: 'strike_selection.delta_target',
          label: 'Target Delta',
          type: 'slider',
          value: getValue('strike_selection.delta_target', getValue('position_parameters.delta_target', 0.3)),
          min: 0.05,
          max: 0.95,
          step: 0.01,
          editable: true,
          format: 'delta',
          tooltip: 'Target delta for option selection'
        },
        {
          key: 'strike_selection.moneyness',
          label: 'Preferred Moneyness',
          type: 'select',
          value: getValue('strike_selection.preferred_moneyness', getValue('moneyness', 'ATM')),
          options: ['ITM', 'ATM', 'OTM'],
          editable: true,
          tooltip: 'Preferred strike relationship to underlying price'
        },
        {
          key: 'strike_selection.wing_width',
          label: 'Wing Width (Spreads)',
          type: 'number',
          value: getValue('strike_selection.wing_widths.0', getValue('position_parameters.max_wing_width', 5)),
          min: 1,
          max: 20,
          editable: true,
          tooltip: 'Strike width for spread strategies'
        },
        {
          key: 'strike_selection.liquidity_filter',
          label: 'Minimum Liquidity',
          type: 'number',
          value: getValue('universe.min_option_volume', getValue('liquidity_min', 100)),
          min: 50,
          max: 5000,
          editable: false,
          tooltip: 'Minimum daily option volume required'
        }
      ]
    },
    {
      id: 'advanced',
      title: 'Advanced Settings',
      icon: <Info className="w-4 h-4" />,
      description: 'Scoring and advanced parameters',
      fields: [
        {
          key: 'scoring.probability_weight',
          label: 'Probability Weight',
          type: 'slider',
          value: getValue('scoring.probability_weight', getValue('probability_weight', 1.0)),
          min: 0.1,
          max: 5.0,
          step: 0.1,
          editable: true,
          tooltip: 'Weight given to probability of profit in scoring'
        },
        {
          key: 'scoring.premium_weight',
          label: 'Premium Weight',
          type: 'slider',
          value: getValue('scoring.premium_weight', getValue('premium_weight', 1.0)),
          min: 0.1,
          max: 5.0,
          step: 0.1,
          editable: true,
          tooltip: 'Weight given to premium collected in scoring'
        },
        {
          key: 'scoring.expected_value_multiplier',
          label: 'Expected Value Multiplier',
          type: 'slider',
          value: getValue('scoring.ev_multiplier', getValue('ev_multiplier', 1.0)),
          min: 0.5,
          max: 10.0,
          step: 0.5,
          editable: true,
          tooltip: 'Multiplier for expected value calculation'
        },
        {
          key: 'universe.symbol_count',
          label: 'Universe Size',
          type: 'display',
          value: getValue('universe.preferred_symbols.length', getValue('universe.max_symbols', 'Auto')),
          editable: false,
          tooltip: 'Number of symbols in trading universe'
        }
      ]
    }
  ];
};

const formatValue = (value: any, format?: string): string => {
  if (value === null || value === undefined) return 'N/A';
  
  switch (format) {
    case 'percentage':
      return `${(typeof value === 'number' ? value * 100 : value).toFixed(1)}%`;
    case 'currency':
      return `$${value.toLocaleString()}`;
    case 'days':
      return Array.isArray(value) ? `${value[0]}-${value[1]} days` : `${value} days`;
    case 'delta':
      return `Δ${value.toFixed(2)}`;
    default:
      return Array.isArray(value) ? value.join(', ') : String(value);
  }
};

// Preset management functions
const PRESET_STORAGE_KEY = 'strategy_parameter_presets';

const savePresetToStorage = (presetName: string, config: any) => {
  const existingPresets = JSON.parse(localStorage.getItem(PRESET_STORAGE_KEY) || '{}');
  existingPresets[presetName] = {
    config_data: config,
    strategy_type: config.strategy_type || 'unknown',
    saved_at: new Date().toISOString()
  };
  localStorage.setItem(PRESET_STORAGE_KEY, JSON.stringify(existingPresets));
};

const loadPresetsFromStorage = (): Record<string, any> => {
  try {
    return JSON.parse(localStorage.getItem(PRESET_STORAGE_KEY) || '{}');
  } catch {
    return {};
  }
};

const UniversalStrategyForm: React.FC<UniversalStrategyFormProps> = React.memo(({ 
  strategy, 
  baseStrategy, 
  onParameterChange 
}) => {
  const [activeSection, setActiveSection] = useState('position_params');
  const [savedPresets, setSavedPresets] = useState(loadPresetsFromStorage());
  const [showPresets, setShowPresets] = useState(false);
  const [presetName, setPresetName] = useState('');
  
  const sections = React.useMemo(() => 
    createUniversalMapping(strategy, baseStrategy), 
    [strategy, baseStrategy]
  );

  // Debounced parameter change to prevent scan spam
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  const handleFieldChange = useCallback((key: string, value: any) => {
    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    
    // Set new timer for 350ms debounce (good balance for UX)
    debounceTimerRef.current = setTimeout(() => {
      onParameterChange(key, value);
    }, 350);
  }, [onParameterChange]);

  // Cleanup timer on unmount
  React.useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  // Preset management handlers
  const handleSavePreset = () => {
    if (!presetName.trim()) return;
    savePresetToStorage(presetName, strategy.config_data);
    setSavedPresets(loadPresetsFromStorage());
    setPresetName('');
    alert(`Preset "${presetName}" saved successfully!`);
  };

  const handleLoadPreset = (preset: any) => {
    // Apply all preset parameters
    Object.keys(preset.config_data || {}).forEach(key => {
      const value = preset.config_data[key];
      if (typeof value === 'object' && value !== null) {
        // Handle nested objects
        Object.keys(value).forEach(subKey => {
          onParameterChange(`${key}.${subKey}`, value[subKey]);
        });
      } else {
        onParameterChange(key, value);
      }
    });
    setShowPresets(false);
  };

  const renderField = (field: UniversalFormField) => {
    const { key, label, type, value, min, max, step, options, editable, tooltip, format } = field;
    const isDisabled = !editable;

    if (type === 'display') {
      return (
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700">{label}</label>
          <div className="flex items-center gap-2">
            <Badge variant="outline">{formatValue(value, format)}</Badge>
            {tooltip && <Info className="w-4 h-4 text-gray-400" title={tooltip} />}
          </div>
        </div>
      );
    }

    if (type === 'toggle') {
      return (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">{label}</label>
            {tooltip && <Info className="w-4 h-4 text-gray-400" title={tooltip} />}
          </div>
          <Switch
            checked={Boolean(value)}
            onCheckedChange={(checked) => handleFieldChange(key, checked)}
            disabled={isDisabled}
          />
        </div>
      );
    }

    if (type === 'select') {
      return (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">{label}</label>
            {tooltip && <Info className="w-4 h-4 text-gray-400" title={tooltip} />}
          </div>
          <Select
            value={String(value)}
            onValueChange={(newValue) => handleFieldChange(key, newValue)}
            disabled={isDisabled}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {options?.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      );
    }

    if (type === 'slider') {
      return (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">{label}</label>
              {tooltip && <Info className="w-4 h-4 text-gray-400" title={tooltip} />}
            </div>
            <Badge variant="outline">{formatValue(value, format)}</Badge>
          </div>
          <Slider
            value={[Number(value) || 0]}
            onValueChange={([newValue]) => handleFieldChange(key, newValue)}
            min={min}
            max={max}
            step={step}
            disabled={isDisabled}
            className={isDisabled ? 'opacity-50' : ''}
          />
          <div className="flex justify-between text-xs text-gray-500">
            <span>{formatValue(min, format)}</span>
            <span>{formatValue(max, format)}</span>
          </div>
        </div>
      );
    }

    if (type === 'range') {
      const rangeValue = Array.isArray(value) ? value : [min, max];
      return (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">{label}</label>
              {tooltip && <Info className="w-4 h-4 text-gray-400" title={tooltip} />}
            </div>
            <Badge variant="outline">{formatValue(rangeValue, format)}</Badge>
          </div>
          <Slider
            value={rangeValue}
            onValueChange={(newValue) => handleFieldChange(key, newValue)}
            min={min}
            max={max}
            step={step}
            disabled={isDisabled}
            className={isDisabled ? 'opacity-50' : ''}
          />
          <div className="flex justify-between text-xs text-gray-500">
            <span>{formatValue(min, format)}</span>
            <span>{formatValue(max, format)}</span>
          </div>
        </div>
      );
    }

    // Default to number input
    return (
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">{label}</label>
          {tooltip && <Info className="w-4 h-4 text-gray-400" title={tooltip} />}
        </div>
        <Input
          type="number"
          value={Number(value) || 0}
          onChange={(e) => handleFieldChange(key, Number(e.target.value))}
          min={min}
          max={max}
          step={step}
          disabled={isDisabled}
          className={isDisabled ? 'bg-gray-50' : ''}
        />
      </div>
    );
  };

  return (
    <div className="w-full space-y-6">
      {/* Section Navigation */}
      <div className="flex flex-wrap gap-2">
        {sections.map((section) => (
          <Button
            key={section.id}
            variant={activeSection === section.id ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActiveSection(section.id)}
            className="flex items-center gap-2"
          >
            {section.icon}
            {section.title}
          </Button>
        ))}
      </div>

      {/* Active Section Content */}
      {sections.map((section) => (
        activeSection === section.id && (
          <Card key={section.id}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {section.icon}
                {section.title}
              </CardTitle>
              <p className="text-sm text-gray-600">{section.description}</p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {section.fields.map((field) => (
                  <div key={field.key}>
                    {renderField(field)}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )
      ))}

      {/* Presets Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bookmark className="w-4 h-4" />
            Parameter Presets
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Save Preset */}
          <div className="flex gap-2">
            <Input
              placeholder="Enter preset name..."
              value={presetName}
              onChange={(e) => setPresetName(e.target.value)}
              className="flex-1"
            />
            <Button onClick={handleSavePreset} disabled={!presetName.trim()} className="flex items-center gap-2">
              <Save className="w-4 h-4" />
              Save
            </Button>
          </div>

          {/* Load Presets */}
          <div className="space-y-2">
            <Button 
              variant="outline" 
              onClick={() => setShowPresets(!showPresets)}
              className="flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Load Preset ({Object.keys(savedPresets).length} available)
            </Button>
            
            {showPresets && Object.keys(savedPresets).length > 0 && (
              <div className="border rounded-lg p-3 bg-gray-50 max-h-48 overflow-y-auto">
                {Object.entries(savedPresets).map(([name, preset]: [string, any]) => (
                  <div key={name} className="flex items-center justify-between py-2 border-b last:border-b-0">
                    <div>
                      <div className="font-medium">{name}</div>
                      <div className="text-xs text-gray-500">
                        {preset.strategy_type} • {new Date(preset.saved_at).toLocaleDateString()}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleLoadPreset(preset)}
                      className="text-xs"
                    >
                      Load
                    </Button>
                  </div>
                ))}
              </div>
            )}
            
            {showPresets && Object.keys(savedPresets).length === 0 && (
              <div className="text-center py-4 text-gray-500">
                No presets saved yet. Save your current parameters as a preset above.
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Strategy Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Configuration Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="font-medium">Strategy:</span>
              <div>{baseStrategy?.strategy_name || strategy.strategy_id}</div>
            </div>
            <div>
              <span className="font-medium">Risk Level:</span>
              <div>
                <Badge variant="outline">
                  {baseStrategy?.complete_config?.educational_content?.risk_level || 'Medium'}
                </Badge>
              </div>
            </div>
            <div>
              <span className="font-medium">Max Opportunities:</span>
              <div>{strategy.config_data?.position_parameters?.max_opportunities || 3}</div>
            </div>
            <div>
              <span className="font-medium">Status:</span>
              <div>
                <Badge variant="outline" className="text-green-600">
                  Active
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
});

export default UniversalStrategyForm;