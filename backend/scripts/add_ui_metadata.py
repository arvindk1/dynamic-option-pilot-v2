#!/usr/bin/env python3
"""
Automated UI Metadata Generator for Strategy Configurations
Analyzes existing strategy parameters and generates appropriate ui_metadata
"""

import json
import os
import glob
from typing import Dict, List, Any

def get_field_type_and_config(key: str, value: Any, parent_key: str = "") -> Dict[str, Any]:
    """Intelligently determine UI field type and configuration based on parameter name and value"""
    
    full_key = f"{parent_key}.{key}" if parent_key else key
    
    # Range/Array parameters
    if isinstance(value, list) and len(value) == 2 and all(isinstance(x, (int, float)) for x in value):
        return {
            "type": "range",
            "min": min(value) - 10,
            "max": max(value) + 20,
            "step": 1 if all(isinstance(x, int) for x in value) else 0.01,
            "default": value
        }
    
    # Boolean toggles
    if isinstance(value, bool):
        return {
            "type": "toggle",
            "default": value
        }
    
    # Number parameters with intelligent ranges
    if isinstance(value, (int, float)):
        config = {"type": "slider" if isinstance(value, float) else "number", "default": value}
        
        # DTE parameters
        if 'dte' in key.lower():
            config.update({"min": 1, "max": 120, "step": 1})
        
        # Delta parameters
        elif 'delta' in key.lower():
            config.update({"min": 0.05, "max": 0.95, "step": 0.01})
        
        # Percentage parameters
        elif any(x in key.lower() for x in ['pct', 'percent', 'ratio', 'level', 'target']):
            if value < 1:
                config.update({"min": 0.01, "max": 1.0, "step": 0.01, "format": "percentage"})
            else:
                config.update({"min": 1, "max": 100, "step": 1, "format": "percentage"})
        
        # Count/quantity parameters
        elif any(x in key.lower() for x in ['max', 'min', 'count', 'opportunities', 'positions']):
            config.update({"min": 1, "max": 20, "step": 1})
        
        # Volatility parameters
        elif 'volatility' in key.lower() or 'vol' in key.lower():
            config.update({"min": 0.1, "max": 2.0, "step": 0.05})
        
        # Default numeric range
        else:
            if isinstance(value, float):
                config.update({"min": value * 0.1, "max": value * 5, "step": 0.01})
            else:
                config.update({"min": max(1, value // 2), "max": value * 3, "step": 1})
        
        return config
    
    # String parameters
    if isinstance(value, str):
        return {
            "type": "select",
            "options": [value],  # Single option for now, can be expanded
            "default": value
        }
    
    # Array of strings
    if isinstance(value, list) and value and isinstance(value[0], str):
        return {
            "type": "multiselect", 
            "options": value,
            "default": value
        }
    
    # Fallback
    return {"type": "text", "default": str(value)}

def generate_section_metadata(section_key: str, section_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate UI metadata for a configuration section"""
    
    # Section titles and descriptions
    section_info = {
        "position_parameters": {
            "title": "Position Parameters",
            "description": "Core position sizing and timing parameters"
        },
        "entry_signals": {
            "title": "Entry Signals", 
            "description": "Conditions for entering new positions"
        },
        "exit_rules": {
            "title": "Exit Rules",
            "description": "Profit targets, stop losses, and exit conditions"
        },
        "risk_management": {
            "title": "Risk Management",
            "description": "Portfolio-level risk controls and limits"
        },
        "strike_selection": {
            "title": "Strike Selection",
            "description": "How to select optimal strike prices"
        },
        "adjustment_rules": {
            "title": "Adjustment Rules",
            "description": "Position adjustment and management rules"
        },
        "scoring": {
            "title": "Scoring Parameters",
            "description": "Opportunity scoring weights and criteria"
        },
        "universe": {
            "title": "Trading Universe",
            "description": "Symbol selection and filtering criteria"
        }
    }
    
    info = section_info.get(section_key, {
        "title": section_key.replace('_', ' ').title(),
        "description": f"{section_key.replace('_', ' ').title()} configuration parameters"
    })
    
    fields = []
    for key, value in section_data.items():
        if isinstance(value, dict):
            # Skip nested objects for now - could be expanded later
            continue
            
        field_config = get_field_type_and_config(key, value, section_key)
        field = {
            "key": f"{section_key}.{key}",
            "label": key.replace('_', ' ').title(),
            "description": generate_field_description(key, value),
            **field_config
        }
        fields.append(field)
    
    return {
        "id": section_key,
        "title": info["title"],
        "description": info["description"],
        "fields": fields
    }

def generate_field_description(key: str, value: Any) -> str:
    """Generate helpful description for a field based on its key and value"""
    
    descriptions = {
        'max_opportunities': 'Maximum number of opportunities to find',
        'target_dte': 'Target days to expiration',
        'min_dte': 'Minimum days to expiration', 
        'max_dte': 'Maximum days to expiration',
        'delta_target': 'Target delta for option selection',
        'profit_target': 'Profit target as percentage of premium',
        'max_allocation': 'Maximum portfolio allocation percentage',
        'volatility_threshold': 'Volatility threshold for entry signals',
        'max_positions': 'Maximum number of concurrent positions'
    }
    
    if key in descriptions:
        return descriptions[key]
    
    # Generate description based on key patterns
    if 'max' in key.lower():
        return f"Maximum {key.replace('max_', '').replace('_', ' ')}"
    elif 'min' in key.lower():
        return f"Minimum {key.replace('min_', '').replace('_', ' ')}"
    elif 'target' in key.lower():
        return f"Target {key.replace('_target', '').replace('_', ' ')}"
    elif 'threshold' in key.lower():
        return f"Threshold for {key.replace('_threshold', '').replace('_', ' ')}"
    else:
        return f"{key.replace('_', ' ').title()} parameter"

def add_ui_metadata_to_strategy(file_path: str):
    """Add comprehensive ui_metadata to a strategy configuration file"""
    
    with open(file_path, 'r') as f:
        strategy = json.load(f)
    
    # Skip if already has ui_metadata
    if 'ui_metadata' in strategy:
        print(f"Skipping {file_path} - already has ui_metadata")
        return
    
    sections = []
    
    # Key sections to include in UI
    ui_sections = [
        'position_parameters', 'entry_signals', 'exit_rules', 
        'risk_management', 'strike_selection', 'adjustment_rules', 
        'scoring', 'universe'
    ]
    
    for section_key in ui_sections:
        if section_key in strategy and isinstance(strategy[section_key], dict):
            section_metadata = generate_section_metadata(section_key, strategy[section_key])
            if section_metadata['fields']:  # Only add sections with fields
                sections.append(section_metadata)
    
    # Add ui_metadata to strategy
    strategy['ui_metadata'] = {
        "sections": sections
    }
    
    # Write back to file
    with open(file_path, 'w') as f:
        json.dump(strategy, f, indent=2)
    
    print(f"Added UI metadata to {os.path.basename(file_path)} - {len(sections)} sections, {sum(len(s['fields']) for s in sections)} fields")

def main():
    """Process all strategy files in the development directory"""
    
    strategy_dir = "/home/arvindk/devl/dynamic-option-pilot-v2/backend/config/strategies/development/"
    strategy_files = glob.glob(os.path.join(strategy_dir, "*.json"))
    
    print(f"Found {len(strategy_files)} strategy files")
    print("Adding UI metadata...")
    
    for file_path in strategy_files:
        try:
            add_ui_metadata_to_strategy(file_path)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    print("\nDone! All strategies now have UI metadata for JSON-driven forms.")

if __name__ == "__main__":
    main()