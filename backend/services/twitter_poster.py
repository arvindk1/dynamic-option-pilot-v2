"""
Twitter Posting Service - Actually post to Twitter API
"""
import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import json

# Twitter API v2 - Install with: pip install tweepy
try:
    import tweepy
    TWITTER_AVAILABLE = True
except ImportError:
    TWITTER_AVAILABLE = False
    logging.warning("Tweepy not installed - Twitter posting disabled")

from services.twitter_automation import get_twitter_service

logger = logging.getLogger(__name__)

class TwitterPosterService:
    """Service to actually post tweets to Twitter API."""
    
    def __init__(self):
        self.twitter_automation = get_twitter_service()
        self.api_client = None
        self.posting_enabled = False
        
        # Initialize Twitter API if credentials available
        self._initialize_twitter_api()
        
        # Posting log for tracking
        self.posting_log = []
        
    def _initialize_twitter_api(self):
        """Initialize Twitter API v2 client."""
        
        if not TWITTER_AVAILABLE:
            logger.warning("Twitter posting disabled - tweepy not installed")
            return
        
        try:
            # Get credentials from environment variables
            api_key = os.getenv('TWITTER_API_KEY')
            api_secret = os.getenv('TWITTER_API_SECRET') 
            access_token = os.getenv('TWITTER_ACCESS_TOKEN')
            access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
            
            if not all([api_key, api_secret, access_token, access_token_secret]):
                logger.warning("Twitter API credentials not found in environment variables")
                return
            
            # Initialize Twitter API v2 client
            self.api_client = tweepy.Client(
                bearer_token=bearer_token,
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
                wait_on_rate_limit=True
            )
            
            # Test authentication
            try:
                user = self.api_client.get_me()
                logger.info(f"Twitter API authenticated successfully as @{user.data.username}")
                self.posting_enabled = True
            except Exception as e:
                logger.error(f"Twitter API authentication failed: {e}")
                
        except Exception as e:
            logger.error(f"Error initializing Twitter API: {e}")
    
    async def post_tweet(self, content: str, tweet_type: str = "manual") -> Dict[str, Any]:
        """Post a tweet to Twitter."""
        
        if not self.posting_enabled:
            return {
                "success": False,
                "error": "Twitter posting not enabled - check credentials",
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            # Post tweet
            response = self.api_client.create_tweet(text=content)
            
            tweet_data = {
                "success": True,
                "tweet_id": response.data['id'],
                "tweet_url": f"https://twitter.com/user/status/{response.data['id']}",
                "content": content,
                "character_count": len(content),
                "tweet_type": tweet_type,
                "posted_at": datetime.utcnow().isoformat(),
                "api_response": response.data
            }
            
            # Log successful post
            self.posting_log.append(tweet_data)
            logger.info(f"Successfully posted {tweet_type} tweet: {response.data['id']}")
            
            return tweet_data
            
        except tweepy.TooManyRequests:
            error_msg = "Twitter API rate limit exceeded"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except tweepy.Forbidden:
            error_msg = "Twitter API access forbidden - check permissions"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error posting tweet: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def post_premarket_tweet(self) -> Dict[str, Any]:
        """Generate and post pre-market intelligence tweet."""
        
        try:
            # Generate tweet content
            tweet_content = await self.twitter_automation.generate_premarket_tweet()
            
            # Post to Twitter
            result = await self.post_tweet(tweet_content, "premarket")
            
            return result
            
        except Exception as e:
            logger.error(f"Error posting pre-market tweet: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def post_market_open_tweet(self) -> Dict[str, Any]:
        """Generate and post market open tweet."""
        
        try:
            tweet_content = await self.twitter_automation.generate_market_open_tweet()
            result = await self.post_tweet(tweet_content, "market_open")
            return result
            
        except Exception as e:
            logger.error(f"Error posting market open tweet: {e}")
            return {"success": False, "error": str(e)}
    
    async def post_market_close_tweet(self) -> Dict[str, Any]:
        """Generate and post market close tweet."""
        
        try:
            tweet_content = await self.twitter_automation.generate_market_close_tweet()
            result = await self.post_tweet(tweet_content, "market_close")
            return result
            
        except Exception as e:
            logger.error(f"Error posting market close tweet: {e}")
            return {"success": False, "error": str(e)}
    
    async def post_educational_tweet(self, topic: str = "volatility") -> Dict[str, Any]:
        """Generate and post educational tweet."""
        
        try:
            tweet_content = await self.twitter_automation.generate_educational_tweet(topic)
            result = await self.post_tweet(tweet_content, f"educational_{topic}")
            return result
            
        except Exception as e:
            logger.error(f"Error posting educational tweet: {e}")
            return {"success": False, "error": str(e)}
    
    async def execute_daily_posting_schedule(self) -> Dict[str, Any]:
        """Execute the full daily posting schedule."""
        
        results = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "posts": [],
            "total_posts": 0,
            "successful_posts": 0,
            "failed_posts": 0
        }
        
        try:
            # Define daily posting schedule
            posting_schedule = [
                {"time": "06:30", "type": "premarket", "function": self.post_premarket_tweet},
                {"time": "09:35", "type": "market_open", "function": self.post_market_open_tweet},
                {"time": "16:05", "type": "market_close", "function": self.post_market_close_tweet},
            ]
            
            # Add educational content based on day of week
            day_of_week = datetime.now().weekday()
            educational_topics = ["volatility", "earnings", "options", "technical", "risk"]
            topic = educational_topics[day_of_week % len(educational_topics)]
            
            posting_schedule.append({
                "time": "12:00", 
                "type": f"educational_{topic}", 
                "function": lambda: self.post_educational_tweet(topic)
            })
            
            # Execute posts
            for post_config in posting_schedule:
                try:
                    result = await post_config["function"]()
                    results["posts"].append({
                        "scheduled_time": post_config["time"],
                        "type": post_config["type"],
                        "result": result
                    })
                    
                    if result.get("success"):
                        results["successful_posts"] += 1
                    else:
                        results["failed_posts"] += 1
                        
                except Exception as e:
                    logger.error(f"Error executing {post_config['type']} post: {e}")
                    results["posts"].append({
                        "scheduled_time": post_config["time"],
                        "type": post_config["type"],
                        "result": {"success": False, "error": str(e)}
                    })
                    results["failed_posts"] += 1
            
            results["total_posts"] = len(results["posts"])
            
            return results
            
        except Exception as e:
            logger.error(f"Error executing daily posting schedule: {e}")
            results["error"] = str(e)
            return results
    
    def get_posting_analytics(self) -> Dict[str, Any]:
        """Get posting analytics and performance metrics."""
        
        if not self.posting_log:
            return {
                "total_posts": 0,
                "success_rate": 0,
                "avg_engagement": 0,
                "note": "No posts recorded yet"
            }
        
        successful_posts = [post for post in self.posting_log if post.get("success")]
        
        return {
            "total_posts": len(self.posting_log),
            "successful_posts": len(successful_posts),
            "failed_posts": len(self.posting_log) - len(successful_posts),
            "success_rate": len(successful_posts) / len(self.posting_log) if self.posting_log else 0,
            "posting_enabled": self.posting_enabled,
            "last_post": self.posting_log[-1] if self.posting_log else None,
            "posts_today": len([p for p in self.posting_log if p.get("posted_at", "").startswith(datetime.now().strftime("%Y-%m-%d"))]),
            "api_status": "connected" if self.posting_enabled else "not_configured"
        }
    
    def get_setup_instructions(self) -> Dict[str, Any]:
        """Get instructions for setting up Twitter API credentials."""
        
        return {
            "setup_required": not self.posting_enabled,
            "instructions": {
                "step_1": "Go to https://developer.twitter.com/en/portal/dashboard",
                "step_2": "Create a new app or use existing app",
                "step_3": "Generate API keys and tokens",
                "step_4": "Set environment variables:",
                "environment_variables": [
                    "TWITTER_API_KEY=your_api_key",
                    "TWITTER_API_SECRET=your_api_secret", 
                    "TWITTER_ACCESS_TOKEN=your_access_token",
                    "TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret",
                    "TWITTER_BEARER_TOKEN=your_bearer_token"
                ],
                "step_5": "Install tweepy: pip install tweepy",
                "step_6": "Restart the backend server"
            },
            "required_permissions": [
                "Read and Write tweets",
                "Read users",
                "Read follows"
            ],
            "testing": "Use /api/social/twitter/test-post to verify setup"
        }

# Singleton instance
_twitter_poster = None

def get_twitter_poster() -> TwitterPosterService:
    """Get or create Twitter poster service instance."""
    global _twitter_poster
    if _twitter_poster is None:
        _twitter_poster = TwitterPosterService()
    return _twitter_poster

def reset_twitter_poster() -> TwitterPosterService:
    """Reset and reinitialize Twitter poster service (for debugging/credential updates)."""
    global _twitter_poster
    _twitter_poster = None
    return get_twitter_poster()