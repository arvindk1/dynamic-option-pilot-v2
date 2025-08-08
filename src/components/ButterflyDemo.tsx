import React, { useState, useEffect } from 'react';
import JsonDrivenForm from './JsonDrivenForm';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Info, Play, Settings } from 'lucide-react';

// This simulates loading your enhanced Butterfly configuration
const butterflyConfig = {
  "strategy_id": "butterfly_spread",
  "strategy_name": "Butterfly Spread",
  "strategy_type": "BUTTERFLY",
  "description": "Long 1 ITM, short 2 ATM, long 1 OTM (or vice versa) - profit from low volatility and precise price targeting",
  
  "universe": {
    "symbol_types": ["STOCK", "ETF"],
    "min_market_cap": 10000000000,
    "min_avg_volume": 5000000,
    "min_avg_option_volume": 1500,
    "low_volatility_preferred": true,
    "stable_underlyings": true,
    "include_symbols": [],
    "exclude_symbols": []
  },
  
  "position_parameters": {
    "max_net_debit_dollars": 0.02,
    "max_opportunities": 3,
    "max_position_cost": 1000
  },
  
  "entry_signals": {
    "allowed_bias": ["NEUTRAL"],
    "volatility_max": 0.30,
    "implied_volatility_rank_max": 60,
    "price_consolidation_required": true
  },
  
  "timing": {
    "dte_range": [14, 45],
    "optimal_dte": [21, 35],
    "avoid_earnings": true,
    "avoid_high_volatility_events": true
  },
  
  "profit_zone_analysis": {
    "optimal_zone_width": 0.05,
    "current_price_proximity_bonus": true,
    "time_decay_acceleration_zone": 0.03
  },

  // UI Metadata - this drives the form generation
  "ui_metadata": {
    "position_parameters.max_net_debit_dollars": {
      "editable": true, 
      "tooltip": "Maximum premium you'll pay per butterfly spread. Lower values = more conservative entries.",
      "type": "number",
      "min": 0.01,
      "max": 0.10,
      "step": 0.01
    },
    "position_parameters.max_opportunities": {
      "editable": true, 
      "tooltip": "Maximum number of simultaneous butterfly spreads in your portfolio.",
      "type": "number",
      "min": 1,
      "max": 10
    },
    "position_parameters.max_position_cost": {
      "editable": true,
      "tooltip": "Maximum dollar amount to risk per individual butterfly spread.",
      "type": "number",
      "min": 100,
      "max": 5000,
      "step": 100
    },
    "timing.dte_range": {
      "editable": true, 
      "tooltip": "Days to expiration range - shorter DTE = higher theta decay, longer DTE = more time value.",
      "type": "range",
      "min": 7,
      "max": 90
    },
    "entry_signals.volatility_max": {
      "editable": true,
      "tooltip": "Maximum implied volatility for entry. Higher IV = higher premiums but more risk.",
      "type": "number",
      "min": 0.10,
      "max": 0.80,
      "step": 0.05
    },
    "entry_signals.implied_volatility_rank_max": {
      "editable": true,
      "tooltip": "Maximum IV rank (0-100). Lower values = relatively cheaper options.",
      "type": "number",
      "min": 10,
      "max": 100,
      "step": 5
    },
    "entry_signals.price_consolidation_required": {
      "editable": true,
      "tooltip": "Require price to be in consolidation pattern before entry.",
      "type": "boolean"
    },
    "profit_zone_analysis.optimal_zone_width": {
      "editable": true,
      "tooltip": "Target profit zone width as percentage of underlying price.",
      "type": "number",
      "min": 0.02,
      "max": 0.15,
      "step": 0.01
    },
    "profit_zone_analysis.current_price_proximity_bonus": {
      "editable": true,
      "tooltip": "Give bonus score when current price is near center strike.",
      "type": "boolean"
    },
    "profit_zone_analysis.time_decay_acceleration_zone": {
      "editable": true,
      "tooltip": "Zone where time decay accelerates (as % of profit zone).",
      "type": "number",
      "min": 0.01,
      "max": 0.10,
      "step": 0.01
    }
  },

  // Educational content
  "educational_content": {
    "best_for": "Precise price targeting with limited risk and defined profit zone",
    "when_to_use": "Neutral outlook with expectation of low volatility and range-bound movement",
    "profit_mechanism": "Maximum profit when underlying closes exactly at center strike",
    "risk_level": "LOW-MEDIUM",
    "typical_duration": "21–35 days",
    "max_profit": "Center strike minus wing strike minus net debit",
    "max_loss": "Net debit paid (limited risk)",
    "profit_zone": "Between wing strikes with peak at center strike"
  },

  "tags": {
    "risk_level": "LOW-MEDIUM",
    "profit_potential": "MODERATE",
    "ideal_dte": [21, 35],
    "market_outlook": "NEUTRAL",
    "volatility_preference": "LOW",
    "complexity": "INTERMEDIATE"
  }
};

const ButterflyDemo: React.FC = () => {
  const [config, setConfig] = useState(butterflyConfig);
  const [isTestRunning, setIsTestRunning] = useState(false);
  const [testResults, setTestResults] = useState<any>(null);

  const handleConfigChange = (newConfig: any) => {
    setConfig(newConfig);
    console.log('Config changed:', newConfig);
  };

  const runTest = async () => {
    setIsTestRunning(true);
    
    // Simulate API call
    setTimeout(() => {
      setTestResults({
        opportunities_found: Math.floor(Math.random() * 15) + 5,
        avg_probability: 0.65 + Math.random() * 0.20,
        avg_expected_value: 35 + Math.random() * 30,
        avg_premium: 1.25 + Math.random() * 2.50,
        risk_reward_ratio: 1.8 + Math.random() * 1.2
      });
      setIsTestRunning(false);
    }, 2000);
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold">JSON-Driven UI Demo</h1>
        <p className="text-muted-foreground max-w-2xl mx-auto">
          This demonstrates how the enhanced Butterfly JSON configuration automatically 
          generates a complete UI form. Every input is driven by the ui_metadata in the JSON.
        </p>
        
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            <strong>What you're seeing:</strong> The form below is 100% generated from the JSON configuration.
            Change any parameter and see how it updates the underlying strategy config in real-time.
          </AlertDescription>
        </Alert>
      </div>

      {/* Strategy Overview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                {config.strategy_name}
                <Badge variant="outline">{config.tags.risk_level}</Badge>
                <Badge variant="secondary">{config.tags.complexity}</Badge>
              </CardTitle>
              <CardDescription>{config.description}</CardDescription>
            </div>
            <div className="flex gap-2">
              <Button 
                onClick={runTest}
                disabled={isTestRunning}
                className="flex items-center gap-2"
              >
                {isTestRunning ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Testing...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    Test Strategy
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardHeader>
        
        {testResults && (
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-700">
                  {testResults.opportunities_found}
                </div>
                <div className="text-xs text-green-600">Opportunities</div>
              </div>
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-700">
                  {(testResults.avg_probability * 100).toFixed(0)}%
                </div>
                <div className="text-xs text-blue-600">Win Rate</div>
              </div>
              <div className="text-center p-3 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-700">
                  ${testResults.avg_expected_value.toFixed(0)}
                </div>
                <div className="text-xs text-purple-600">Expected Value</div>
              </div>
              <div className="text-center p-3 bg-amber-50 rounded-lg">
                <div className="text-2xl font-bold text-amber-700">
                  {testResults.risk_reward_ratio.toFixed(1)}
                </div>
                <div className="text-xs text-amber-600">Risk/Reward</div>
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* The Magic: JSON-Driven Form */}
      <JsonDrivenForm
        config={config}
        uiMeta={config.ui_metadata}
        onConfigChange={handleConfigChange}
        title="Dynamic Strategy Configuration"
        description="Every field below is automatically generated from the JSON ui_metadata"
      />

      {/* Educational Content */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Strategy Education
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold mb-2">Best For</h4>
              <p className="text-sm text-muted-foreground mb-4">{config.educational_content.best_for}</p>
              
              <h4 className="font-semibold mb-2">When to Use</h4>
              <p className="text-sm text-muted-foreground">{config.educational_content.when_to_use}</p>
            </div>
            <div>
              <h4 className="font-semibold mb-2 text-green-600">Max Profit</h4>
              <p className="text-sm text-green-700 mb-4">{config.educational_content.max_profit}</p>
              
              <h4 className="font-semibold mb-2 text-red-600">Max Loss</h4>
              <p className="text-sm text-red-700">{config.educational_content.max_loss}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Implementation Note */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          <strong>Implementation:</strong> This exact approach can replace your current manual parameter forms. 
          Just load the enhanced JSON configurations and pass them to the JsonDrivenForm component.
          Zero hardcoding, infinite flexibility!
        </AlertDescription>
      </Alert>
    </div>
  );
};

export default ButterflyDemo;