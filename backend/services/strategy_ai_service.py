"""
Strategy AI Assistant Service using OpenAI
Cost-optimized with model switching capability
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

try:
    import openai
except ImportError:
    openai = None

logger = logging.getLogger(__name__)

@dataclass
class AIModelConfig:
    """Configuration for OpenAI models"""
    name: str
    cost_input: float  # per 1K tokens
    cost_output: float  # per 1K tokens
    description: str
    recommended_for: str

# Available models (cheapest first)
AVAILABLE_MODELS = {
    "gpt-4o-mini": AIModelConfig(
        name="gpt-4o-mini",
        cost_input=0.00015,
        cost_output=0.0006,
        description="Most cost-effective with great quality",
        recommended_for="Default - Best balance of cost/quality"
    ),
    "gpt-3.5-turbo": AIModelConfig(
        name="gpt-3.5-turbo", 
        cost_input=0.0005,
        cost_output=0.0015,
        description="Fast and cheap for simple analysis",
        recommended_for="Basic strategy questions"
    ),
    "gpt-4o": AIModelConfig(
        name="gpt-4o",
        cost_input=0.0025,
        cost_output=0.01,
        description="Premium model for complex analysis",
        recommended_for="Advanced strategy optimization"
    )
}

DEFAULT_MODEL = "gpt-4o-mini"  # Most cost-effective

class StrategyAIService:
    """Strategy-specific AI assistant using OpenAI"""
    
    def __init__(self, api_key: str = None):
        """Initialize with OpenAI API key"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OpenAI API key not found. AI features will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            if openai:
                openai.api_key = self.api_key
        
        self.current_model = DEFAULT_MODEL
        self.conversation_history: Dict[str, List[Dict]] = {}
    
    def set_model(self, model_name: str) -> bool:
        """Switch to a different OpenAI model"""
        if model_name in AVAILABLE_MODELS:
            old_model = self.current_model
            self.current_model = model_name
            logger.info(f"Switched AI model from {old_model} to {model_name}")
            return True
        else:
            logger.error(f"Unknown model: {model_name}")
            return False
    
    def get_available_models(self) -> Dict[str, AIModelConfig]:
        """Get list of available models with pricing"""
        return AVAILABLE_MODELS
    
    def get_current_model_info(self) -> AIModelConfig:
        """Get current model configuration"""
        return AVAILABLE_MODELS[self.current_model]
    
    def _create_strategy_prompt(self, strategy_name: str, strategy_config: Dict, 
                              performance_data: Optional[Dict] = None) -> str:
        """Create strategy-specific system prompt with guardrails"""
        
        # Convert strategy config to readable format
        config_text = self._format_strategy_config(strategy_config)
        
        # Add performance context if available
        performance_text = ""
        if performance_data:
            performance_text = f"\nRECENT PERFORMANCE:\n{self._format_performance_data(performance_data)}"
        
        system_prompt = f"""You are a specialized options trading strategy assistant for {strategy_name} ONLY.

CURRENT STRATEGY CONFIGURATION:
{config_text}
{performance_text}

STRICT INSTRUCTIONS:
- ONLY analyze and discuss this specific {strategy_name} strategy
- Focus on the provided parameters and their optimization
- Suggest improvements based on risk/reward analysis
- Explain how parameter changes affect strategy performance
- Keep responses concise and actionable (2-3 sentences max)

ABSOLUTELY FORBIDDEN:
- Discussing other trading strategies
- General investment advice or market predictions  
- Non-strategy related topics
- Financial advice or recommendations to buy/sell

RESPONSE STYLE:
- Direct and analytical
- Focus on parameter optimization
- Explain trade-offs clearly
- Use specific numbers from the configuration

You are an expert options strategy analyst focused solely on optimizing this {strategy_name} strategy."""

        return system_prompt
    
    def _format_strategy_config(self, config: Dict) -> str:
        """Format strategy configuration for LLM context"""
        formatted = []
        
        for section, params in config.items():
            if isinstance(params, dict):
                formatted.append(f"\n{section.upper()}:")
                for key, value in params.items():
                    formatted.append(f"  - {key}: {value}")
            else:
                formatted.append(f"- {section}: {params}")
        
        return "\n".join(formatted)
    
    def _format_performance_data(self, performance: Dict) -> str:
        """Format performance data for context"""
        if not performance:
            return "No recent performance data available"
        
        formatted = []
        for key, value in performance.items():
            if isinstance(value, float):
                if key.endswith('_rate') or key.endswith('_ratio'):
                    formatted.append(f"- {key}: {value:.1%}")
                else:
                    formatted.append(f"- {key}: {value:.2f}")
            else:
                formatted.append(f"- {key}: {value}")
        
        return "\n".join(formatted)
    
    async def chat_with_strategy(self, strategy_name: str, strategy_config: Dict,
                               user_message: str, conversation_id: str = None,
                               performance_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Chat with AI about a specific strategy
        
        Args:
            strategy_name: Name of the strategy (e.g., 'ThetaCrop Weekly')
            strategy_config: Current strategy configuration
            user_message: User's question/message
            conversation_id: Optional conversation ID for context
            performance_data: Optional recent performance metrics
            
        Returns:
            Dict with AI response, token usage, and cost
        """
        if not self.enabled:
            return {
                "response": "AI assistant is not available. Please configure OpenAI API key.",
                "error": "API key not configured",
                "model": None,
                "tokens_used": 0,
                "estimated_cost": 0
            }
        
        if not openai:
            return {
                "response": "OpenAI library not installed. Please install: pip install openai",
                "error": "Library missing",
                "model": None,
                "tokens_used": 0,
                "estimated_cost": 0
            }
        
        try:
            # Create system prompt with strategy context
            system_prompt = self._create_strategy_prompt(strategy_name, strategy_config, performance_data)
            
            # Build conversation history
            conversation_id = conversation_id or f"{strategy_name}_{datetime.now().isoformat()}"
            
            if conversation_id not in self.conversation_history:
                self.conversation_history[conversation_id] = []
            
            # Add user message to history
            self.conversation_history[conversation_id].append({
                "role": "user",
                "content": user_message
            })
            
            # Prepare messages for OpenAI
            messages = [
                {"role": "system", "content": system_prompt}
            ] + self.conversation_history[conversation_id]
            
            # Make OpenAI API call - this is the same regardless of model!
            response = await openai.ChatCompletion.acreate(
                model=self.current_model,  # Only this changes between models
                messages=messages,
                max_tokens=500,  # Keep responses concise
                temperature=0.3,  # Consistent, focused responses
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            # Extract response
            ai_response = response.choices[0].message.content.strip()
            
            # Add AI response to conversation history
            self.conversation_history[conversation_id].append({
                "role": "assistant", 
                "content": ai_response
            })
            
            # Calculate cost
            model_config = AVAILABLE_MODELS[self.current_model]
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            
            cost = (input_tokens * model_config.cost_input / 1000) + \
                   (output_tokens * model_config.cost_output / 1000)
            
            logger.info(f"Strategy AI chat - Model: {self.current_model}, "
                       f"Tokens: {total_tokens}, Cost: ${cost:.4f}")
            
            return {
                "response": ai_response,
                "model": self.current_model,
                "tokens_used": total_tokens,
                "estimated_cost": cost,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in strategy AI chat: {e}")
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "error": str(e),
                "model": self.current_model,
                "tokens_used": 0,
                "estimated_cost": 0
            }
    
    def clear_conversation(self, conversation_id: str):
        """Clear conversation history"""
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "active_conversations": len(self.conversation_history),
            "current_model": self.current_model,
            "model_info": self.get_current_model_info(),
            "total_conversations": len(self.conversation_history)
        }

# Global service instance
_strategy_ai_service = None

def get_strategy_ai_service() -> StrategyAIService:
    """Get global strategy AI service instance"""
    global _strategy_ai_service
    if _strategy_ai_service is None:
        _strategy_ai_service = StrategyAIService()
    return _strategy_ai_service

def initialize_strategy_ai_service(api_key: str = None) -> StrategyAIService:
    """Initialize strategy AI service with API key"""
    global _strategy_ai_service
    _strategy_ai_service = StrategyAIService(api_key)
    return _strategy_ai_service