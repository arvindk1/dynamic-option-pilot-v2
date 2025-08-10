# backend/api/routes/social_twitter.py
from fastapi import APIRouter, Depends, Query, Request
from datetime import datetime
import os, tweepy, pytz

router = APIRouter(prefix="/api/social/twitter", tags=["social-twitter"])

# ---- deps you already have; adapt imports as needed
from services.social.tweet_composer_v2 import compose_premarket_v2
from services.market_commentary import MarketCommentary
from services.opportunity_cache import OpportunityCache

EXPECTED_USER_ID = os.getenv("TWITTER_EXPECTED_USER_ID", "").strip()

def _is_trading_day_nyse(dt_utc=None) -> bool:
    tz = pytz.timezone("America/New_York")
    now = datetime.now(tz) if dt_utc is None else dt_utc.astimezone(tz)
    return now.weekday() < 5  # Mon-Fri

def _client_oauth1() -> tweepy.Client:
    return tweepy.Client(
        consumer_key=os.getenv("TWITTER_API_KEY"),
        consumer_secret=os.getenv("TWITTER_API_SECRET"),
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
        wait_on_rate_limit=True,
    )

def _is_true(val: str) -> bool:
    return str(val).lower() in {"1","true","t","yes","y"}

@router.post("/post-premarket")
def post_premarket(
    request: Request,
    dry_run: bool = Query(False, description="If true, preview only (no post)."),
    mc: MarketCommentary = Depends(),
    cache: OpportunityCache = Depends(),
):
    # robust dry_run parsing (covers ?dry_run=1/true/yes)
    if _is_true(request.query_params.get("dry_run", dry_run)):
        really_dry = True
    else:
        really_dry = os.getenv("TWITTER_DRY_RUN") == "1"

    # weekend/holiday guard
    if not _is_trading_day_nyse():
        text = "🛑 Market closed (weekend/holiday). No pre-market post."
        return {"version":"premarket-v2","action":"preview_only",
                "result":{"posted":False,"content":text,"character_count":len(text)},
                "timestamp": datetime.utcnow().isoformat()+"Z"}

    # pull data (map your shapes)
    snap = mc.overnight_snapshot()              # {spx_pct, ndx_pct, vix}
    events = mc.todays_macro_events()           # [{"time","name"}, ...]
    earnings = mc.todays_earnings_tickers()     # ["AAPL","MSFT", ...]
    raw = cache.get_recent(lookback_minutes=720)[:10]

    opps = []
    for r in raw:
        opps.append({
            "symbol": r.get("symbol") or r.get("ticker"),
            "strategy": r.get("strategy") or r.get("strategy_name"),
            "prob_profit": r.get("pop") or r.get("prob_profit", 0.0),
            "expected_value": r.get("expected_value", 0.0),
            "credit": r.get("credit") or r.get("premium"),
            "dte": r.get("dte") or r.get("days_to_expiry") or 0
        })

    text = compose_premarket_v2(snap, events, earnings, opps)
    if len(text) > 280:
        text = text[:277] + "…"

    if really_dry:
        return {"version":"premarket-v2","action":"preview_only",
                "result":{"posted":False,"content":text,"character_count":len(text),"tweet_type":"premarket"},
                "timestamp": datetime.utcnow().isoformat()+"Z"}

    # real post using OAuth1 (same tokens that worked in your CLI)
    client = _client_oauth1()
    me = client.get_me(user_auth=True).data
    if EXPECTED_USER_ID and str(me.id) != EXPECTED_USER_ID:
        return {"version":"premarket-v2","action":"post_to_twitter",
                "result":{"success":False,"posted":False,
                          "error":f"Refusing to post as @{me.username} ({me.id}); expected {EXPECTED_USER_ID}."},
                "timestamp": datetime.utcnow().isoformat()+"Z"}

    resp = client.create_tweet(text=text, user_auth=True)
    tid = resp.data["id"]
    url = f"https://x.com/{me.username}/status/{tid}"
    return {"version":"premarket-v2","action":"post_to_twitter",
            "result":{"success":True,"posted":True,"tweet_id":tid,"tweet_url":url,
                      "content":text,"character_count":len(text),"tweet_type":"premarket"},
            "timestamp": datetime.utcnow().isoformat()+"Z"}

# GET-only preview endpoint (nice for cURL)
@router.get("/preview/premarket")
def preview_premarket(mc: MarketCommentary = Depends(), cache: OpportunityCache = Depends()):
    snap = mc.overnight_snapshot()
    events = mc.todays_macro_events()
    earnings = mc.todays_earnings_tickers()
    raw = cache.get_recent(lookback_minutes=720)[:10]
    opps = [{
        "symbol": r.get("symbol") or r.get("ticker"),
        "strategy": r.get("strategy") or r.get("strategy_name"),
        "prob_profit": r.get("pop") or r.get("prob_profit", 0.0),
        "expected_value": r.get("expected_value", 0.0),
        "credit": r.get("credit") or r.get("premium"),
        "dte": r.get("dte") or r.get("days_to_expiry") or 0
    } for r in raw]
    text = compose_premarket_v2(snap, events, earnings, opps)
    if len(text) > 280: text = text[:277] + "…"
    return {"version":"premarket-v2","action":"preview_only",
            "result":{"posted":False,"content":text,"character_count":len(text)}}
