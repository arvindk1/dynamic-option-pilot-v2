"""
Strategy AI Assistant Service using OpenAI
Cost-optimized with model switching capability
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

try:
    from openai import AsyncOpenAI
    from openai import RateLimitError, APIError
    openai_available = True
except ImportError:
    AsyncOpenAI = None
    RateLimitError = None
    APIError = None
    openai_available = False

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
    """Strategy-specific AI assistant using OpenAI with rate limiting"""
    
    def __init__(self, api_key: str = None):
        """Initialize with OpenAI API key and rate limiting"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OpenAI API key not found. AI features will be disabled.")
            self.enabled = False
            self.client = None
        else:
            self.enabled = True
            if openai_available and AsyncOpenAI:
                self.client = AsyncOpenAI(api_key=self.api_key)
            else:
                self.client = None
                self.enabled = False
        
        self.current_model = DEFAULT_MODEL
        self.conversation_history: Dict[str, List[Dict]] = {}
        
        # Rate limiting configuration
        self.rate_limit_config = {
            "requests_per_minute": int(os.getenv("AI_COACH_RATE_LIMIT", "60")),
            "requests_per_day": 1000,
            "max_retries": 3,
            "base_delay": 1.0,  # seconds
            "max_delay": 60.0   # seconds
        }
        
        # Track API usage
        self.request_timestamps = []
        self.daily_request_count = 0
        self.last_reset_date = datetime.now().date()
    
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
    
    def _reset_daily_counter_if_needed(self):
        """Reset daily request counter if it's a new day"""
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.daily_request_count = 0
            self.last_reset_date = current_date
            logger.info(f"Daily AI request counter reset for {current_date}")
    
    def _check_rate_limits(self) -> bool:
        """Check if we're within rate limits"""
        self._reset_daily_counter_if_needed()
        
        now = datetime.now()
        
        # Remove timestamps older than 1 minute
        minute_ago = now - timedelta(minutes=1)
        self.request_timestamps = [ts for ts in self.request_timestamps if ts > minute_ago]
        
        # Check minute limit
        if len(self.request_timestamps) >= self.rate_limit_config["requests_per_minute"]:
            logger.warning(f"Rate limit exceeded: {len(self.request_timestamps)} requests in the last minute")
            return False
        
        # Check daily limit
        if self.daily_request_count >= self.rate_limit_config["requests_per_day"]:
            logger.warning(f"Daily rate limit exceeded: {self.daily_request_count} requests today")
            return False
        
        return True
    
    def _record_request(self):
        """Record a new API request"""
        now = datetime.now()
        self.request_timestamps.append(now)
        self.daily_request_count += 1
    
    async def _wait_for_rate_limit(self) -> bool:
        """Wait until we're within rate limits"""
        max_wait_seconds = 65  # Just over a minute
        waited = 0
        
        while not self._check_rate_limits() and waited < max_wait_seconds:
            wait_time = min(5, max_wait_seconds - waited)  # Wait 5 seconds at a time
            logger.info(f"Rate limit hit, waiting {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            waited += wait_time
        
        return self._check_rate_limits()
    
    async def _make_openai_request_with_retry(self, messages: List[Dict], attempt: int = 1) -> Dict[str, Any]:
        """Make OpenAI API request with exponential backoff retry"""
        
        if not await self._wait_for_rate_limit():
            raise Exception("Rate limit exceeded and timeout waiting for reset")
        
        try:
            self._record_request()
            
            # Make the API call
            response = await self.client.chat.completions.create(
                model=self.current_model,
                messages=messages,
                max_tokens=500,  # Keep responses concise
                temperature=0.3,  # Consistent, focused responses
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            return response
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Handle rate limit errors
            if "rate_limit" in error_str or "429" in error_str:
                if attempt <= self.rate_limit_config["max_retries"]:
                    # Exponential backoff: 2^attempt * base_delay
                    delay = min(
                        self.rate_limit_config["base_delay"] * (2 ** attempt),
                        self.rate_limit_config["max_delay"]
                    )
                    logger.warning(f"Rate limit hit (attempt {attempt}/{self.rate_limit_config['max_retries']}), "
                                 f"retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                    return await self._make_openai_request_with_retry(messages, attempt + 1)
                else:
                    # Try fallback to cheaper model
                    if self.current_model != "gpt-3.5-turbo":
                        logger.warning("Max retries exceeded, switching to gpt-3.5-turbo as fallback")
                        old_model = self.current_model
                        self.current_model = "gpt-3.5-turbo"
                        try:
                            result = await self._make_openai_request_with_retry(messages, 1)
                            self.current_model = old_model  # Switch back after success
                            return result
                        except:
                            self.current_model = old_model  # Restore original model
                            raise Exception(f"Rate limit exceeded. Please try again in a few minutes. "
                                          f"Error: {str(e)[:100]}...")
                    else:
                        raise Exception(f"Rate limit exceeded on all models. Please try again in a few minutes. "
                                      f"Error: {str(e)[:100]}...")
            
            # Handle other API errors
            elif "api" in error_str or "timeout" in error_str:
                if attempt <= self.rate_limit_config["max_retries"]:
                    delay = self.rate_limit_config["base_delay"] * attempt
                    logger.warning(f"API error (attempt {attempt}), retrying in {delay:.1f} seconds: {str(e)[:100]}")
                    await asyncio.sleep(delay)
                    return await self._make_openai_request_with_retry(messages, attempt + 1)
                else:
                    raise Exception(f"API error after {self.rate_limit_config['max_retries']} attempts: {str(e)[:100]}...")
            
            # Re-raise other exceptions
            else:
                raise e
    
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
        logger.info(f"AI Chat Request - Strategy: {strategy_name}, Message: {user_message[:50]}...")
        logger.info(f"AI Service State - Enabled: {self.enabled}, Client: {self.client is not None}")
        
        if not self.enabled:
            logger.warning("AI service not enabled - API key not configured")
            return {
                "response": "AI assistant is not available. Please configure OpenAI API key.",
                "error": "API key not configured",
                "model": "unknown",
                "tokens_used": 0,
                "estimated_cost": 0,
                "conversation_id": conversation_id or "unknown",
                "timestamp": datetime.now().isoformat()
            }
        
        if not self.client:
            logger.warning("OpenAI client not available")
            return {
                "response": "OpenAI client not available. Please check API key and library installation.",
                "error": "Client not available",
                "model": "unknown",
                "tokens_used": 0,
                "estimated_cost": 0,
                "conversation_id": conversation_id or "unknown",
                "timestamp": datetime.now().isoformat()
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
            
            # Make OpenAI API call with retry logic
            response = await self._make_openai_request_with_retry(messages)
            
            # Extract response with better error handling
            if not response.choices or not response.choices[0].message:
                raise Exception("No response choices returned from OpenAI")
            
            ai_response = response.choices[0].message.content
            if not ai_response:
                raise Exception("Empty response content from OpenAI")
            
            ai_response = ai_response.strip()
            
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
            # Log critical AI service error
            try:
                from services.error_logging_service import log_critical_error
                await log_critical_error(
                    error_type="ai_service_error",
                    message=f"AI Assistant failed to respond: {str(e)}",
                    details={
                        "strategy_name": strategy_name,
                        "user_message": user_message[:100],  # First 100 chars
                        "model": self.current_model,
                        "error": str(e)
                    },
                    service="strategy_ai_service",
                    severity="HIGH"
                )
            except:
                pass  # Don't let error logging fail the response
            
            logger.error(f"Error in strategy AI chat: {e}")
            return {
                "response": f"Sorry, I encountered an error. This has been logged for investigation: {str(e)[:50]}...",
                "error": str(e),
                "model": self.current_model,
                "tokens_used": 0,
                "estimated_cost": 0,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def clear_conversation(self, conversation_id: str):
        """Clear conversation history"""
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        self._reset_daily_counter_if_needed()
        
        # Count recent requests (last hour)
        hour_ago = datetime.now() - timedelta(hours=1)
        recent_requests = len([ts for ts in self.request_timestamps if ts > hour_ago])
        
        return {
            "active_conversations": len(self.conversation_history),
            "current_model": self.current_model,
            "model_info": self.get_current_model_info(),
            "total_conversations": len(self.conversation_history),
            "rate_limit_status": {
                "requests_last_minute": len(self.request_timestamps),
                "requests_last_hour": recent_requests,
                "requests_today": self.daily_request_count,
                "rate_limit_per_minute": self.rate_limit_config["requests_per_minute"],
                "rate_limit_per_day": self.rate_limit_config["requests_per_day"],
                "within_limits": self._check_rate_limits()
            }
        }
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get detailed rate limit status"""
        self._reset_daily_counter_if_needed()
        
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        # Clean old timestamps
        self.request_timestamps = [ts for ts in self.request_timestamps if ts > minute_ago]
        
        return {
            "current_model": self.current_model,
            "requests_last_minute": len(self.request_timestamps),
            "requests_today": self.daily_request_count,
            "limits": {
                "per_minute": self.rate_limit_config["requests_per_minute"],
                "per_day": self.rate_limit_config["requests_per_day"]
            },
            "within_limits": self._check_rate_limits(),
            "next_reset": {
                "minute": (minute_ago + timedelta(minutes=1)).isoformat(),
                "daily": (datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1)).isoformat()
            }
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