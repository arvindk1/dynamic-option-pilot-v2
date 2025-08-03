"""
Unified Strategy Parameter Template System
Creates dynamic parameter forms based on strategy JSON configurations
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ParameterField:
    """Individual parameter field definition"""
    name: str
    label: str
    type: str  # 'number', 'text', 'select', 'boolean', 'range', 'array'
    value: Any
    options: Optional[List[Any]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    description: str = ""
    enabled: bool = True
    category: str = "general"


@dataclass
class ParameterSection:
    """Section grouping related parameters"""
    name: str
    label: str
    fields: List[ParameterField]
    enabled: bool = True
    description: str = ""


class StrategyParameterTemplate:
    """Creates unified parameter templates for all strategies"""
    
    # Common parameter mappings with UI-friendly configurations
    PARAMETER_DEFINITIONS = {
        # Position Parameters
        'target_dte_range': {
            'type': 'range', 'label': 'Target DTE Range', 'min_value': 1, 'max_value': 365,
            'description': 'Days to expiration range for positions'
        },
        'delta_target': {
            'type': 'number', 'label': 'Delta Target', 'min_value': 0.01, 'max_value': 1.0, 'step': 0.01,
            'description': 'Target delta for option positions'
        },
        'delta_targets': {
            'type': 'array', 'label': 'Delta Targets', 
            'description': 'Multiple delta targets for different scenarios'
        },
        'max_opportunities': {
            'type': 'number', 'label': 'Max Opportunities', 'min_value': 1, 'max_value': 50,
            'description': 'Maximum number of opportunities to generate'
        },
        'position_size_per_3k': {
            'type': 'number', 'label': 'Position Size (per $3K)', 'min_value': 1, 'max_value': 10,
            'description': 'Number of contracts per $3,000 of capital'
        },
        'max_positions': {
            'type': 'number', 'label': 'Max Positions', 'min_value': 1, 'max_value': 20,
            'description': 'Maximum concurrent positions'
        },
        'wing_widths': {
            'type': 'array', 'label': 'Wing Widths', 
            'description': 'Strike width options for spreads'
        },
        'min_credit_ratio': {
            'type': 'number', 'label': 'Min Credit Ratio', 'min_value': 0.01, 'max_value': 1.0, 'step': 0.01,
            'description': 'Minimum credit as ratio of wing width'
        },
        'preferred_delta_range': {
            'type': 'range', 'label': 'Preferred Delta Range', 'min_value': 0.01, 'max_value': 1.0,
            'description': 'Preferred delta range for option selection'
        },
        'min_dte': {
            'type': 'number', 'label': 'Min DTE', 'min_value': 1, 'max_value': 365,
            'description': 'Minimum days to expiration'
        },
        'max_dte': {
            'type': 'number', 'label': 'Max DTE', 'min_value': 1, 'max_value': 365,
            'description': 'Maximum days to expiration'
        },
        
        # Entry Signals
        'allow_bias': {
            'type': 'select', 'label': 'Allowed Bias', 
            'options': ['BULLISH', 'BEARISH', 'NEUTRAL', 'SLIGHTLY_BULLISH', 'SLIGHTLY_BEARISH'],
            'description': 'Market bias conditions for entry'
        },
        'allowed_bias': {
            'type': 'select', 'label': 'Allowed Bias', 
            'options': ['BULLISH', 'BEARISH', 'NEUTRAL', 'SLIGHTLY_BULLISH', 'SLIGHTLY_BEARISH'],
            'description': 'Market bias conditions for entry'
        },
        'min_probability_profit': {
            'type': 'number', 'label': 'Min Profit Probability', 'min_value': 0.01, 'max_value': 1.0, 'step': 0.01,
            'description': 'Minimum probability of profit'
        },
        'min_credit_amount': {
            'type': 'number', 'label': 'Min Credit Amount', 'min_value': 0.01, 'max_value': 10.0, 'step': 0.01,
            'description': 'Minimum credit amount collected'
        },
        'volatility_min': {
            'type': 'number', 'label': 'Min Volatility', 'min_value': 0.01, 'max_value': 2.0, 'step': 0.01,
            'description': 'Minimum implied volatility'
        },
        'volatility_max': {
            'type': 'number', 'label': 'Max Volatility', 'min_value': 0.01, 'max_value': 2.0, 'step': 0.01,
            'description': 'Maximum implied volatility'
        },
        'rsi_below': {
            'type': 'number', 'label': 'RSI Below', 'min_value': 1, 'max_value': 100,
            'description': 'RSI threshold for oversold condition'
        },
        'required_oversold_confirmation': {
            'type': 'boolean', 'label': 'Require Oversold Confirmation',
            'description': 'Additional confirmation of oversold condition'
        },
        
        # Scoring Parameters
        'base_probability_weight': {
            'type': 'number', 'label': 'Base Probability Weight', 'min_value': 0.1, 'max_value': 10.0, 'step': 0.1,
            'description': 'Weight given to probability of profit in scoring'
        },
        'score_ceiling': {
            'type': 'number', 'label': 'Score Ceiling', 'min_value': 1.0, 'max_value': 100.0,
            'description': 'Maximum possible opportunity score'
        },
        'score_floor': {
            'type': 'number', 'label': 'Score Floor', 'min_value': 0.1, 'max_value': 10.0,
            'description': 'Minimum possible opportunity score'
        },
        
        # Universe Parameters
        'min_market_cap': {
            'type': 'number', 'label': 'Min Market Cap ($B)', 'min_value': 0.1, 'max_value': 5000.0,
            'description': 'Minimum market capitalization in billions'
        },
        'min_avg_volume': {
            'type': 'number', 'label': 'Min Avg Volume', 'min_value': 10000, 'max_value': 100000000,
            'description': 'Minimum average daily volume'
        },
        'symbol_types': {
            'type': 'select', 'label': 'Symbol Types',
            'options': ['STOCK', 'ETF', 'INDEX'],
            'description': 'Types of symbols to include'
        },
        'universe_name': {
            'type': 'select', 'label': 'Universe',
            'options': ['thetacrop', 'mag7', 'etfs', 'top20', 'sector_leaders'],
            'description': 'Predefined universe to use'
        },
        
        # Exit Rules
        'profit_target_level': {
            'type': 'number', 'label': 'Profit Target %', 'min_value': 0.1, 'max_value': 2.0, 'step': 0.05,
            'description': 'Profit target as percentage of max profit'
        },
        'stop_loss_level': {
            'type': 'number', 'label': 'Stop Loss %', 'min_value': 0.1, 'max_value': 2.0, 'step': 0.05,
            'description': 'Stop loss as percentage of max loss'
        }
    }
    
    def __init__(self):
        self.strategy_configs = {}
        self.load_strategy_configs()
    
    def load_strategy_configs(self):
        """Load all strategy JSON configurations"""
        strategy_dir = Path('/home/arvindk/devl/dynamic-option-pilot-v2/backend/config/strategies/production')
        
        for json_file in strategy_dir.glob('*.json'):
            try:
                with open(json_file, 'r') as f:
                    config = json.load(f)
                
                strategy_id = config.get('strategy_type', json_file.stem)
                strategy_name = config.get('strategy_name', json_file.stem)
                
                self.strategy_configs[strategy_id] = {
                    'name': strategy_name,
                    'config': config,
                    'file_path': str(json_file)
                }
                
            except Exception as e:
                logger.error(f"Error loading strategy config {json_file}: {e}")
    
    def create_template_for_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """Create a parameter template for a specific strategy"""
        if strategy_id not in self.strategy_configs:
            raise ValueError(f"Strategy {strategy_id} not found")
        
        strategy_info = self.strategy_configs[strategy_id]
        config = strategy_info['config']
        
        template = {
            'strategy_id': strategy_id,
            'strategy_name': strategy_info['name'],
            'sections': []
        }
        
        # Create sections based on strategy configuration
        sections = [
            ('position_parameters', 'Position Parameters', 'Configure position sizing and targets'),
            ('entry_signals', 'Entry Signals', 'Define when to enter positions'),
            ('scoring', 'Scoring', 'Opportunity ranking and selection'),
            ('universe', 'Universe', 'Symbol selection criteria'),
            ('exit_rules', 'Exit Rules', 'Position exit conditions')
        ]
        
        for section_key, section_label, section_desc in sections:
            if section_key in config:
                section = self.create_parameter_section(
                    section_key, section_label, section_desc, config[section_key]
                )
                if section.fields:  # Only add sections with fields
                    template['sections'].append(section)
        
        return template
    
    def create_parameter_section(self, section_key: str, section_label: str, 
                               section_desc: str, section_config: Dict[str, Any]) -> ParameterSection:
        """Create a parameter section with fields"""
        fields = []
        
        for param_name, param_value in section_config.items():
            field = self.create_parameter_field(param_name, param_value, section_key)
            if field:
                fields.append(field)
        
        return ParameterSection(
            name=section_key,
            label=section_label,
            description=section_desc,
            fields=fields
        )
    
    def create_parameter_field(self, param_name: str, param_value: Any, 
                             category: str) -> Optional[ParameterField]:
        """Create a parameter field with appropriate UI controls"""
        
        # Get parameter definition or create default
        param_def = self.PARAMETER_DEFINITIONS.get(param_name, {})
        
        # Determine field type based on value and definition
        field_type = param_def.get('type', self.infer_field_type(param_value))
        
        # Handle complex parameters
        if param_name in ['profit_targets', 'stop_loss_rules', 'time_exits']:
            # These are complex nested structures - simplify for UI
            if isinstance(param_value, list) and param_value:
                first_rule = param_value[0]
                if 'level' in first_rule:
                    return ParameterField(
                        name=f"{param_name}_level",
                        label=param_def.get('label', self.format_label(param_name)),
                        type='number',
                        value=first_rule['level'],
                        min_value=0.01,
                        max_value=2.0,
                        step=0.05,
                        description=first_rule.get('description', ''),
                        category=category
                    )
                elif 'trigger' in first_rule:
                    return ParameterField(
                        name=f"{param_name}_trigger",
                        label=param_def.get('label', self.format_label(param_name)),
                        type='number',
                        value=abs(first_rule['trigger']),
                        min_value=0.01,
                        max_value=2.0,
                        step=0.05,
                        description=first_rule.get('description', ''),
                        category=category
                    )
            return None  # Skip complex rules for now
        
        # Create the field
        return ParameterField(
            name=param_name,
            label=param_def.get('label', self.format_label(param_name)),
            type=field_type,
            value=param_value,
            options=param_def.get('options'),
            min_value=param_def.get('min_value'),
            max_value=param_def.get('max_value'),
            step=param_def.get('step'),
            description=param_def.get('description', ''),
            category=category
        )
    
    def infer_field_type(self, value: Any) -> str:
        """Infer UI field type from parameter value"""
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, (int, float)):
            return 'number'
        elif isinstance(value, list):
            if len(value) == 2 and all(isinstance(x, (int, float)) for x in value):
                return 'range'  # Likely a min/max range
            return 'array'
        elif isinstance(value, str):
            return 'text'
        else:
            return 'text'
    
    def format_label(self, param_name: str) -> str:
        """Convert parameter name to user-friendly label"""
        return param_name.replace('_', ' ').title()
    
    def get_all_strategy_templates(self) -> Dict[str, Any]:
        """Get templates for all loaded strategies"""
        templates = {}
        
        for strategy_id in self.strategy_configs:
            try:
                templates[strategy_id] = self.create_template_for_strategy(strategy_id)
            except Exception as e:
                logger.error(f"Error creating template for {strategy_id}: {e}")
        
        return templates
    
    def get_strategy_list(self) -> List[Dict[str, str]]:
        """Get list of available strategies"""
        return [
            {
                'id': strategy_id,
                'name': info['name'],
                'description': info['config'].get('description', '')
            }
            for strategy_id, info in self.strategy_configs.items()
        ]


# Global instance
_strategy_template = None

def get_strategy_parameter_template() -> StrategyParameterTemplate:
    """Get global strategy parameter template instance"""
    global _strategy_template
    if _strategy_template is None:
        _strategy_template = StrategyParameterTemplate()
    return _strategy_template