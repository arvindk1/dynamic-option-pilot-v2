# backend/services/social/tweet_composer_v2.py
"""
Enhanced tweet composer for v2 architecture
"""

from typing import Dict, Any, List, Optional
import os

def compose_premarket_v2(
    market_snapshot: Dict[str, Any],
    todays_events: List[Dict[str, Any]],
    todays_earnings: List[str],
    opportunities: List[Dict[str, Any]]
) -> str:
    """
    Compose a premarket tweet with enhanced v2 functionality
    
    Args:
        market_snapshot: Market data with SPX, NDX, VIX values
        todays_events: List of economic events
        todays_earnings: List of companies reporting earnings
        opportunities: List of trading opportunities
        
    Returns:
        Formatted tweet content
    """
    
    def _format_pct(value: float) -> str:
        """Format percentage with sign"""
        return f"{value:+.1f}%"
    
    def _pick_top_opportunities(opps: List[Dict[str, Any]], n: int = 3) -> List[Dict[str, Any]]:
        """Select top opportunities by probability and expected value"""
        if not opps:
            return []
        
        return sorted(
            opps,
            key=lambda o: (
                o.get("probability_profit", 0),
                o.get("expected_value", 0)
            ),
            reverse=True
        )[:n]
    
    # Extract market data
    spx_pct = market_snapshot.get("spx_pct", 0.0)
    ndx_pct = market_snapshot.get("ndx_pct", 0.0)
    vix = market_snapshot.get("vix")
    
    # Get top opportunities
    top_opps = _pick_top_opportunities(opportunities, 3)
    
    # Build tweet content
    lines = ["📈 PRE-MARKET INTEL"]
    
    # Market futures line
    market_line = f"• S&P fut {_format_pct(spx_pct)} | NAS fut {_format_pct(ndx_pct)}"
    if vix is not None:
        market_line += f" | VIX {vix:.1f}"
    lines.append(market_line)
    
    # Economic events
    if todays_events:
        event_names = [f"{event.get('time', '')} {event.get('name', '')}" for event in todays_events[:2]]
        lines.append("• Today: " + " · ".join(event_names))
    
    # Earnings
    if todays_earnings:
        lines.append("• Earnings: " + ", ".join(todays_earnings[:3]))
    
    # Top opportunities
    if top_opps:
        opp_parts = []
        for opp in top_opps:
            symbol = opp.get('symbol', 'UNK')
            dte = int(opp.get('days_to_expiration', 0))
            strategy = opp.get('strategy_type', 'Unknown')
            pop = int(100 * opp.get('probability_profit', 0))
            ev = opp.get('expected_value', 0)
            
            opp_parts.append(f"{symbol} {dte}D {strategy} (PoP {pop}%, EV {ev:.2f})")
        
        lines.append("• High-prob setups: " + " | ".join(opp_parts))
    
    # Hashtags
    lines.append("#options #premarket #trading")
    
    tweet_content = "\n".join(lines)
    
    # Ensure tweet length constraint (Twitter limit is 280 chars)
    if len(tweet_content) > 270:
        tweet_content = tweet_content[:270] + "..."
    
    return tweet_content


def compose_market_open_v2(
    breadth_data: Dict[str, Any],
    market_leaders: List[str],
    featured_idea: Optional[Dict[str, Any]] = None
) -> str:
    """
    Compose a market open tweet
    
    Args:
        breadth_data: Market breadth information
        market_leaders: List of leading stocks
        featured_idea: Featured trading opportunity
        
    Returns:
        Formatted tweet content
    """
    lines = ["🟢 MARKET OPEN"]
    
    # Breadth data
    if breadth_data:
        advancers = breadth_data.get('advancers', 0)
        decliners = breadth_data.get('decliners', 0)
        vol_mult = breadth_data.get('volume_multiplier', 1.0)
        lines.append(f"• Breadth: {advancers}/{decliners} | Vol×{vol_mult:.1f}")
    
    # Market leaders
    if market_leaders:
        lines.append("• Leaders: " + ", ".join(market_leaders[:4]))
    
    # Featured idea
    if featured_idea:
        symbol = featured_idea.get('symbol', '')
        dte = featured_idea.get('days_to_expiration', 0)
        strategy = featured_idea.get('strategy_type', '')
        premium = featured_idea.get('premium', 0)
        pop = int(featured_idea.get('probability_profit', 0) * 100)
        
        lines.append(f"• Setup: {symbol} {dte}D {strategy} ~${premium:.2f} credit (PoP {pop}%)")
    
    lines.append("#options #marketopen")
    
    return "\n".join(lines)


def compose_market_close_v2(
    daily_summary: Dict[str, Any],
    best_opportunity: Optional[Dict[str, Any]] = None,
    performance_stats: Optional[Dict[str, Any]] = None
) -> str:
    """
    Compose a market close tweet
    
    Args:
        daily_summary: Daily market performance data
        best_opportunity: Best performing opportunity of the day
        performance_stats: Trading performance statistics
        
    Returns:
        Formatted tweet content
    """
    lines = ["📊 MARKET CLOSE"]
    
    # Market performance
    spy = daily_summary.get('spy_change', 'N/A')
    qqq = daily_summary.get('qqq_change', 'N/A')
    vix = daily_summary.get('vix_close', 'N/A')
    lines.append(f"• SPY {spy} | QQQ {qqq} | VIX {vix}")
    
    # Leaders/laggards
    if daily_summary.get('leaders'):
        lines.append("• Leaders: " + ", ".join(daily_summary['leaders'][:3]))
    
    if daily_summary.get('laggards'):
        lines.append("• Laggards: " + ", ".join(daily_summary['laggards'][:3]))
    
    # Best opportunity
    if best_opportunity:
        symbol = best_opportunity.get('symbol', '')
        strategy = best_opportunity.get('strategy_type', '')
        result = best_opportunity.get('result', '')
        time_flagged = best_opportunity.get('time_flagged', '')
        lines.append(f"• Top play: {symbol} {strategy} → {result} (flagged {time_flagged})")
    
    # Performance stats
    if performance_stats:
        wins = performance_stats.get('wins', 0)
        total_trades = performance_stats.get('total_trades', 0)
        avg_ev = performance_stats.get('average_expected_value', 0)
        lines.append(f"• Stats: {wins}/{total_trades} wins | avg EV {avg_ev:+.2f}")
    
    lines.append("#options #marketclose #trading")
    
    return "\n".join(lines)