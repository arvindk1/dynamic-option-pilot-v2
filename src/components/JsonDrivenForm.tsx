import React, { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { HelpCircle, Lock, Edit3 } from 'lucide-react';
import { get, set, cloneDeep } from 'lodash';

interface UIMetadata {
  editable: boolean;
  tooltip: string;
  type?: 'number' | 'range' | 'boolean' | 'select' | 'text';
  min?: number;
  max?: number;
  step?: number;
  options?: string[];
  visible?: boolean;
}

interface JsonDrivenFormProps {
  config: any;
  uiMeta: Record<string, UIMetadata>;
  onConfigChange: (newConfig: any) => void;
  title?: string;
  description?: string;
}

const JsonDrivenForm: React.FC<JsonDrivenFormProps> = ({
  config,
  uiMeta,
  onConfigChange,
  title = "Strategy Configuration",
  description = "Customize your strategy parameters"
}) => {
  const [localConfig, setLocalConfig] = useState(config);
  const [isDirty, setIsDirty] = useState(false);

  const updateConfig = (path: string, value: any) => {
    const newConfig = cloneDeep(localConfig);
    set(newConfig, path, value);
    setLocalConfig(newConfig);
    setIsDirty(true);
    onConfigChange(newConfig);
  };

  const getFieldLabel = (path: string): string => {
    return path.split('.').pop()?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || '';
  };

  const renderField = (path: string, meta: UIMetadata) => {
    const value = get(localConfig, path);
    const fieldId = `field-${path.replace(/\./g, '-')}`;
    const label = getFieldLabel(path);

    if (meta.visible === false) return null;

    const commonProps = {
      id: fieldId,
      title: meta.tooltip,
      disabled: !meta.editable
    };

    const renderInput = () => {
      if (!meta.editable) {
        return (
          <div className="flex items-center gap-2">
            <Input
              {...commonProps}
              value={Array.isArray(value) ? value.join(', ') : String(value || '')}
              readOnly
              className="bg-gray-50"
            />
            <Lock className="h-4 w-4 text-gray-400" />
          </div>
        );
      }

      switch (meta.type) {
        case 'number':
          return (
            <Input
              {...commonProps}
              type="number"
              value={value || ''}
              onChange={(e) => updateConfig(path, parseFloat(e.target.value) || 0)}
              min={meta.min}
              max={meta.max}
              step={meta.step || 0.01}
            />
          );

        case 'range':
          if (Array.isArray(value) && value.length === 2) {
            return (
              <div className="space-y-3">
                <Slider
                  value={value}
                  onValueChange={(newValue) => updateConfig(path, newValue)}
                  min={meta.min || 0}
                  max={meta.max || 100}
                  step={meta.step || 1}
                  className="w-full"
                />
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>{value[0]}</span>
                  <span>{value[1]}</span>
                </div>
              </div>
            );
          }
          return (
            <Input
              {...commonProps}
              type="range"
              value={value || 0}
              onChange={(e) => updateConfig(path, parseInt(e.target.value))}
              min={meta.min}
              max={meta.max}
              step={meta.step || 1}
            />
          );

        case 'boolean':
          return (
            <div className="flex items-center space-x-2">
              <Switch
                {...commonProps}
                checked={Boolean(value)}
                onCheckedChange={(checked) => updateConfig(path, checked)}
              />
              <Label htmlFor={fieldId} className="text-sm">
                {value ? 'Enabled' : 'Disabled'}
              </Label>
            </div>
          );

        case 'select':
          return (
            <select
              {...commonProps}
              value={Array.isArray(value) ? value[0] : value || ''}
              onChange={(e) => updateConfig(path, e.target.value)}
              className="w-full p-2 border border-input rounded-md bg-background"
            >
              {meta.options?.map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          );

        default:
          return (
            <Input
              {...commonProps}
              type="text"
              value={Array.isArray(value) ? value.join(', ') : String(value || '')}
              onChange={(e) => {
                const newValue = e.target.value;
                // Handle arrays by splitting on comma
                if (Array.isArray(value)) {
                  updateConfig(path, newValue.split(',').map(s => s.trim()).filter(s => s));
                } else {
                  updateConfig(path, newValue);
                }
              }}
            />
          );
      }
    };

    return (
      <div key={path} className="space-y-2">
        <div className="flex items-center gap-2">
          <Label htmlFor={fieldId} className="font-medium text-sm">
            {label}
          </Label>
          {meta.editable && <Edit3 className="h-3 w-3 text-blue-600" />}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <HelpCircle className="h-4 w-4 text-muted-foreground" />
              </TooltipTrigger>
              <TooltipContent>
                <p className="max-w-xs text-sm">{meta.tooltip}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
        {renderInput()}
        {meta.min !== undefined && meta.max !== undefined && (
          <p className="text-xs text-muted-foreground">
            Range: {meta.min} - {meta.max}
            {meta.step && ` (step: ${meta.step})`}
          </p>
        )}
      </div>
    );
  };

  // Group fields by section (first part of path)
  const groupedFields = Object.entries(uiMeta).reduce((groups, [path, meta]) => {
    const section = path.split('.')[0];
    if (!groups[section]) groups[section] = [];
    groups[section].push([path, meta]);
    return groups;
  }, {} as Record<string, Array<[string, UIMetadata]>>);

  const getSectionTitle = (sectionKey: string): string => {
    const titles: Record<string, string> = {
      'position_parameters': 'Position Parameters',
      'entry_signals': 'Entry Signals',
      'exit_rules': 'Exit Rules',
      'timing': 'Timing Parameters',
      'strike_selection': 'Strike Selection',
      'scoring': 'Scoring Parameters',
      'risk_management': 'Risk Management',
      'profit_zone_analysis': 'Profit Zone Analysis'
    };
    return titles[sectionKey] || sectionKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">{title}</h2>
          <p className="text-muted-foreground">{description}</p>
        </div>
        {isDirty && (
          <Badge variant="outline" className="bg-blue-50 text-blue-700">
            Modified
          </Badge>
        )}
      </div>

      {/* Dynamic Form Sections */}
      {Object.entries(groupedFields).map(([sectionKey, fields]) => (
        <Card key={sectionKey}>
          <CardHeader>
            <CardTitle className="text-lg">{getSectionTitle(sectionKey)}</CardTitle>
            <CardDescription>
              {fields.length} parameters • {fields.filter(([, meta]) => meta.editable).length} editable
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {fields.map(([path, meta]) => renderField(path, meta))}
            </div>
          </CardContent>
        </Card>
      ))}

      {/* Actions */}
      <div className="flex gap-3">
        <Button 
          onClick={() => console.log('Test configuration:', localConfig)}
          disabled={!isDirty}
        >
          Test Configuration
        </Button>
        <Button 
          variant="outline"
          onClick={() => console.log('Save configuration:', localConfig)}
          disabled={!isDirty}
        >
          Save Changes
        </Button>
        <Button 
          variant="outline"
          onClick={() => {
            setLocalConfig(config);
            setIsDirty(false);
          }}
          disabled={!isDirty}
        >
          Reset
        </Button>
      </div>

      {/* Debug Info */}
      <details className="mt-8">
        <summary className="cursor-pointer text-sm text-muted-foreground">
          Debug: Current Configuration
        </summary>
        <pre className="mt-2 p-4 bg-gray-100 rounded text-xs overflow-auto">
          {JSON.stringify(localConfig, null, 2)}
        </pre>
      </details>
    </div>
  );
};

export default JsonDrivenForm;