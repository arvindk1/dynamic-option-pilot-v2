import logging
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter

router = APIRouter()
logger = logging.getLogger(__name__)

# Sentiment API endpoints
@router.get("/pulse")
async def get_sentiment_pulse(force_refresh: bool = False):
    """Get comprehensive market sentiment pulse."""
    current_timestamp = datetime.utcnow().isoformat() + "Z"
    return {
        "timestamp": current_timestamp,
        "overall_sentiment": {
            "positive": 0.45,
            "negative": 0.25,
            "neutral": 0.30,
            "compound": 0.32,
            "confidence": 0.82,
        },
        "mag7_sentiment": {
            "AAPL": {
                "positive": 0.52,
                "negative": 0.18,
                "neutral": 0.30,
                "compound": 0.41,
                "confidence": 0.85,
            },
            "GOOGL": {
                "positive": 0.48,
                "negative": 0.22,
                "neutral": 0.30,
                "compound": 0.35,
                "confidence": 0.78,
            },
            "MSFT": {
                "positive": 0.55,
                "negative": 0.15,
                "neutral": 0.30,
                "compound": 0.48,
                "confidence": 0.88,
            },
            "AMZN": {
                "positive": 0.42,
                "negative": 0.28,
                "neutral": 0.30,
                "compound": 0.18,
                "confidence": 0.75,
            },
            "TSLA": {
                "positive": 0.38,
                "negative": 0.35,
                "neutral": 0.27,
                "compound": 0.05,
                "confidence": 0.72,
            },
            "META": {
                "positive": 0.46,
                "negative": 0.24,
                "neutral": 0.30,
                "compound": 0.28,
                "confidence": 0.80,
            },
            "NVDA": {
                "positive": 0.58,
                "negative": 0.12,
                "neutral": 0.30,
                "compound": 0.55,
                "confidence": 0.92,
            },
        },
        "top20_sentiment": {
            "AAPL": {
                "positive": 0.52,
                "negative": 0.18,
                "neutral": 0.30,
                "compound": 0.41,
                "price_change": 2.3,
            },
            "MSFT": {
                "positive": 0.55,
                "negative": 0.15,
                "neutral": 0.30,
                "compound": 0.48,
                "price_change": 1.8,
            },
            "GOOGL": {
                "positive": 0.48,
                "negative": 0.22,
                "neutral": 0.30,
                "compound": 0.35,
                "price_change": 0.9,
            },
            "AMZN": {
                "positive": 0.42,
                "negative": 0.28,
                "neutral": 0.30,
                "compound": 0.18,
                "price_change": -0.5,
            },
            "TSLA": {
                "positive": 0.38,
                "negative": 0.35,
                "neutral": 0.27,
                "compound": 0.05,
                "price_change": -1.2,
            },
            "META": {
                "positive": 0.46,
                "negative": 0.24,
                "neutral": 0.30,
                "compound": 0.28,
                "price_change": 1.1,
            },
            "NVDA": {
                "positive": 0.58,
                "negative": 0.12,
                "neutral": 0.30,
                "compound": 0.55,
                "price_change": 3.2,
            },
            "JPM": {
                "positive": 0.44,
                "negative": 0.26,
                "neutral": 0.30,
                "compound": 0.22,
                "price_change": 0.8,
            },
            "JNJ": {
                "positive": 0.41,
                "negative": 0.29,
                "neutral": 0.30,
                "compound": 0.15,
                "price_change": 0.3,
            },
            "V": {
                "positive": 0.49,
                "negative": 0.21,
                "neutral": 0.30,
                "compound": 0.32,
                "price_change": 1.4,
            },
            "PG": {
                "positive": 0.43,
                "negative": 0.27,
                "neutral": 0.30,
                "compound": 0.19,
                "price_change": 0.2,
            },
            "UNH": {
                "positive": 0.40,
                "negative": 0.30,
                "neutral": 0.30,
                "compound": 0.12,
                "price_change": -0.1,
            },
            "HD": {
                "positive": 0.45,
                "negative": 0.25,
                "neutral": 0.30,
                "compound": 0.24,
                "price_change": 0.7,
            },
            "MA": {
                "positive": 0.47,
                "negative": 0.23,
                "neutral": 0.30,
                "compound": 0.29,
                "price_change": 1.2,
            },
            "BAC": {
                "positive": 0.42,
                "negative": 0.28,
                "neutral": 0.30,
                "compound": 0.17,
                "price_change": 0.6,
            },
            "XOM": {
                "positive": 0.39,
                "negative": 0.31,
                "neutral": 0.30,
                "compound": 0.09,
                "price_change": -0.8,
            },
            "DIS": {
                "positive": 0.36,
                "negative": 0.34,
                "neutral": 0.30,
                "compound": 0.02,
                "price_change": -1.5,
            },
            "NFLX": {
                "positive": 0.44,
                "negative": 0.26,
                "neutral": 0.30,
                "compound": 0.22,
                "price_change": 0.9,
            },
            "CRM": {
                "positive": 0.46,
                "negative": 0.24,
                "neutral": 0.30,
                "compound": 0.27,
                "price_change": 1.3,
            },
            "ADBE": {
                "positive": 0.43,
                "negative": 0.27,
                "neutral": 0.30,
                "compound": 0.19,
                "price_change": 0.5,
            },
        },
        "spy_sentiment": {
            "positive": 0.48,
            "negative": 0.22,
            "neutral": 0.30,
            "compound": 0.35,
            "confidence": 0.85,
        },
        "key_themes": ["AI growth", "earnings optimism", "rate cut speculation"],
        "market_summary": "Overall bullish sentiment driven by tech strength and AI momentum",
        "news_count": 247,
        "data_sources": ["Reuters", "Bloomberg", "Financial Times"],
    }


@router.get("/quick")
async def get_quick_sentiment():
    """Get quick sentiment overview for widgets."""
    current_timestamp = datetime.utcnow().isoformat() + "Z"
    return {
        "overall_score": 0.32,
        "overall_label": "Positive",
        "spy_score": 0.35,
        "spy_label": "Positive",
        "mag7_average": 0.33,
        "mag7_label": "Positive",
        "last_updated": current_timestamp,
        "market_summary": "Markets showing positive sentiment with tech leadership",
    }


@router.get("/history")
async def get_sentiment_history(days: int = 7):
    """Get sentiment history for trend analysis."""
    import random
    from datetime import timedelta

    history = []
    base_date = "2025-07-29"
    for i in range(days):
        date_obj = datetime.fromisoformat(base_date) - timedelta(days=i)
        history.append(
            {
                "date": date_obj.strftime("%Y-%m-%d"),
                "sentiment_score": round(random.uniform(-0.2, 0.6), 3),
                "news_count": random.randint(180, 320),
                "key_themes": ["earnings", "fed policy", "ai developments"],
            }
        )
    return history[::-1]  # Reverse to chronological order


@router.get("/symbols/{symbol}")
async def get_symbol_sentiment(symbol: str, hours: int = 24):
    """Get sentiment for a specific stock symbol."""
    current_timestamp = datetime.utcnow().isoformat() + "Z"
    return {
        "symbol": symbol,
        "sentiment": {
            "positive": 0.48,
            "negative": 0.22,
            "neutral": 0.30,
            "compound": 0.35,
            "confidence": 0.85,
            "label": "Positive",
        },
        "last_updated": current_timestamp,
        "news_count": 23,
        "market_context": f"Positive sentiment for {symbol} driven by strong fundamentals",
    }


@router.post("/refresh")
async def refresh_sentiment():
    """Manually trigger sentiment data refresh."""
    return {
        "status": "success",
        "message": "Demo mode: Sentiment data refresh simulated",
        "timestamp": "2025-07-29T18:30:00Z",
    }
