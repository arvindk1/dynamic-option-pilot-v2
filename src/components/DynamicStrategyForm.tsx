import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { HelpCircle, Info, Lock, Edit3 } from 'lucide-react';

interface UIMetadata {
  editable: boolean;
  tooltip: string;
  type?: 'number' | 'range' | 'boolean' | 'select' | 'text';
  min?: number;
  max?: number;
  step?: number;
  options?: string[];
  validation?: {
    required?: boolean;
    pattern?: string;
    message?: string;
  };
}

interface StrategyConfig {
  strategy_id: string;
  strategy_name: string;
  description: string;
  ui_metadata: Record<string, UIMetadata>;
  educational_content: {
    best_for: string;
    when_to_use: string;
    risk_level: string;
    profit_mechanism: string;
    max_profit: string;
    max_loss: string;
  };
  tags: {
    risk_level: string;
    profit_potential: string;
    market_outlook: string;
    complexity: string;
  };
  [key: string]: any; // For all the strategy configuration data
}

interface DynamicStrategyFormProps {
  strategy: StrategyConfig;
  onConfigChange: (config: StrategyConfig) => void;
  onTest: (config: StrategyConfig) => void;
  onSave: (config: StrategyConfig) => void;
}

const DynamicStrategyForm: React.FC<DynamicStrategyFormProps> = ({
  strategy,
  onConfigChange,
  onTest,
  onSave
}) => {
  const [config, setConfig] = useState<StrategyConfig>(strategy);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isDirty, setIsDirty] = useState(false);

  const getNestedValue = (obj: any, path: string): any => {
    return path.split('.').reduce((current, key) => current?.[key], obj);
  };

  const setNestedValue = (obj: any, path: string, value: any): any => {
    const keys = path.split('.');
    const lastKey = keys.pop()!;
    const target = keys.reduce((current, key) => {
      if (!current[key]) current[key] = {};
      return current[key];
    }, obj);
    target[lastKey] = value;
    return { ...obj };
  };

  const handleFieldChange = (fieldPath: string, value: any) => {
    const newConfig = setNestedValue({ ...config }, fieldPath, value);
    setConfig(newConfig);
    setIsDirty(true);
    onConfigChange(newConfig);

    // Clear validation error for this field
    if (errors[fieldPath]) {
      setErrors(prev => ({ ...prev, [fieldPath]: '' }));
    }
  };

  const validateField = (fieldPath: string, metadata: UIMetadata, value: any): string => {
    if (metadata.validation?.required && (!value || value === '')) {
      return metadata.validation.message || 'This field is required';
    }

    if (metadata.type === 'number' && typeof value === 'number') {
      if (metadata.min !== undefined && value < metadata.min) {
        return `Value must be at least ${metadata.min}`;
      }
      if (metadata.max !== undefined && value > metadata.max) {
        return `Value must be at most ${metadata.max}`;
      }
    }

    if (metadata.validation?.pattern && !new RegExp(metadata.validation.pattern).test(String(value))) {
      return metadata.validation.message || 'Invalid format';
    }

    return '';
  };

  const renderField = (fieldPath: string, metadata: UIMetadata) => {
    const currentValue = getNestedValue(config, fieldPath);
    const fieldError = errors[fieldPath];
    const isDisabled = !metadata.editable;

    const fieldId = `field-${fieldPath.replace(/\./g, '-')}`;
    const labelText = fieldPath.split('.').pop()?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || '';

    const renderInput = () => {
      switch (metadata.type) {
        case 'number':
          return (
            <Input
              id={fieldId}
              type="number"
              value={currentValue || ''}
              onChange={(e) => handleFieldChange(fieldPath, parseFloat(e.target.value) || 0)}
              min={metadata.min}
              max={metadata.max}
              step={metadata.step || 0.01}
              disabled={isDisabled}
              className={fieldError ? 'border-red-500' : ''}
            />
          );

        case 'range':
          if (Array.isArray(currentValue) && currentValue.length === 2) {
            return (
              <div className="space-y-2">
                <Slider
                  value={currentValue}
                  onValueChange={(value) => handleFieldChange(fieldPath, value)}
                  min={metadata.min || 0}
                  max={metadata.max || 100}
                  step={metadata.step || 1}
                  disabled={isDisabled}
                  className="w-full"
                />
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>{currentValue[0]}</span>
                  <span>{currentValue[1]}</span>
                </div>
              </div>
            );
          }
          return (
            <Input
              id={fieldId}
              type="range"
              value={currentValue || 0}
              onChange={(e) => handleFieldChange(fieldPath, parseInt(e.target.value))}
              min={metadata.min}
              max={metadata.max}
              step={metadata.step || 1}
              disabled={isDisabled}
            />
          );

        case 'boolean':
          return (
            <Switch
              id={fieldId}
              checked={Boolean(currentValue)}
              onCheckedChange={(checked) => handleFieldChange(fieldPath, checked)}
              disabled={isDisabled}
            />
          );

        case 'select':
          return (
            <select
              id={fieldId}
              value={currentValue || ''}
              onChange={(e) => handleFieldChange(fieldPath, e.target.value)}
              disabled={isDisabled}
              className="w-full p-2 border border-input rounded-md bg-background"
            >
              {metadata.options?.map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          );

        default:
          return (
            <Input
              id={fieldId}
              type="text"
              value={currentValue || ''}
              onChange={(e) => handleFieldChange(fieldPath, e.target.value)}
              disabled={isDisabled}
              className={fieldError ? 'border-red-500' : ''}
            />
          );
      }
    };

    return (
      <div key={fieldPath} className="space-y-2">
        <div className="flex items-center gap-2">
          <Label htmlFor={fieldId} className="font-medium">
            {labelText}
          </Label>
          {!metadata.editable && <Lock className="h-3 w-3 text-muted-foreground" />}
          {metadata.editable && <Edit3 className="h-3 w-3 text-blue-600" />}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <HelpCircle className="h-4 w-4 text-muted-foreground" />
              </TooltipTrigger>
              <TooltipContent>
                <p className="max-w-xs">{metadata.tooltip}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
        
        {renderInput()}
        
        {fieldError && (
          <p className="text-sm text-red-600">{fieldError}</p>
        )}
      </div>
    );
  };

  const groupFieldsBySection = () => {
    const sections: Record<string, Array<[string, UIMetadata]>> = {};
    
    Object.entries(strategy.ui_metadata || {}).forEach(([fieldPath, metadata]) => {
      const section = fieldPath.split('.')[0];
      if (!sections[section]) sections[section] = [];
      sections[section].push([fieldPath, metadata]);
    });

    return sections;
  };

  const getSectionTitle = (sectionKey: string): string => {
    const sectionTitles: Record<string, string> = {
      'position_parameters': 'Position Parameters',
      'entry_signals': 'Entry Signals',
      'exit_rules': 'Exit Rules',
      'timing': 'Timing Parameters',
      'strike_selection': 'Strike Selection',
      'scoring': 'Scoring Parameters',
      'risk_management': 'Risk Management',
      'profit_zone_analysis': 'Profit Zone Analysis'
    };
    return sectionTitles[sectionKey] || sectionKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const sections = groupFieldsBySection();

  return (
    <div className="space-y-6">
      {/* Strategy Overview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                {strategy.strategy_name}
                <Badge variant="outline">{strategy.tags?.risk_level || 'UNKNOWN'}</Badge>
                <Badge variant="secondary">{strategy.tags?.complexity || 'INTERMEDIATE'}</Badge>
              </CardTitle>
              <CardDescription>{strategy.description}</CardDescription>
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                onClick={() => onTest(config)}
                disabled={Object.keys(errors).length > 0}
              >
                Test Strategy
              </Button>
              <Button 
                onClick={() => onSave(config)}
                disabled={!isDirty || Object.keys(errors).length > 0}
              >
                Save Configuration
              </Button>
            </div>
          </div>
        </CardHeader>
        
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-semibold mb-2">Best For</h4>
              <p className="text-sm text-muted-foreground">{strategy.educational_content?.best_for}</p>
            </div>
            <div>
              <h4 className="font-semibold mb-2">When to Use</h4>
              <p className="text-sm text-muted-foreground">{strategy.educational_content?.when_to_use}</p>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Max Profit</h4>
              <p className="text-sm text-muted-foreground">{strategy.educational_content?.max_profit}</p>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Max Loss</h4>
              <p className="text-sm text-muted-foreground">{strategy.educational_content?.max_loss}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Dynamic Configuration Sections */}
      {Object.entries(sections).map(([sectionKey, fields]) => (
        <Card key={sectionKey}>
          <CardHeader>
            <CardTitle className="text-lg">{getSectionTitle(sectionKey)}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {fields.map(([fieldPath, metadata]) => renderField(fieldPath, metadata))}
            </div>
          </CardContent>
        </Card>
      ))}

      {/* Validation Summary */}
      {Object.keys(errors).length > 0 && (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            Please fix the validation errors above before testing or saving the strategy.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};

export default DynamicStrategyForm;