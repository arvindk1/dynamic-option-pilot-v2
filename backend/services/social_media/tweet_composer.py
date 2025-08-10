# backend/services/social/tweet_composer.py
from __future__ import annotations
import os, datetime as dt
from typing import List, Optional, Dict, Any

USE_LLM = os.getenv("SOCIAL_USE_LLM", "0") == "1"

def _fmt_pct(x: float) -> str:
    return f"{x:+.1f}%"

def _pick_top_opportunities(opps: List[Dict[str, Any]], n=3):
    # expects keys: symbol, strategy, prob_profit, expected_value, dte
    return sorted(opps, key=lambda o: (o.get("prob_profit",0), o.get("expected_value",0)), reverse=True)[:n]

def compose_premarket(snap: Dict[str, Any], todays_events: List[Dict[str,Any]],
                      todays_earnings: List[str], opportunities: List[Dict[str,Any]]) -> str:
    spx = snap.get("spx_pct", 0.0); ndx = snap.get("ndx_pct", 0.0); vix = snap.get("vix", None)
    top = _pick_top_opportunities(opportunities, 3)
    lines = [
        "📈 PRE-MARKET INTEL",
        f"• S&P fut {_fmt_pct(spx)} | NAS fut {_fmt_pct(ndx)}" + (f" | VIX {vix:.1f}" if vix is not None else ""),
    ]
    if todays_events:
        key = [f"{e['time']} {e['name']}" for e in todays_events[:2]]
        lines.append("• Today: " + " · ".join(key))
    if todays_earnings:
        lines.append("• Earnings: " + ", ".join(todays_earnings[:3]))
    if top:
        parts = [f"{o['symbol']} {int(o.get('dte',0))}D {o.get('strategy')} (PoP {int(100*o.get('prob_profit',0))}%, EV {o.get('expected_value'):.2f})"
                 for o in top]
        lines.append("• High-prob setups: " + " | ".join(parts))
    lines.append("#options #premarket #trading")
    msg = "\n".join(lines)
    return _polish(msg) if USE_LLM else msg

def compose_open(breadth: Dict[str, Any], leaders: List[str], idea: Optional[Dict[str,Any]]) -> str:
    lines = ["🟢 OPEN CHECK-IN"]
    if breadth:
        lines.append(f"• Breadth: {breadth.get('advancers',0)}/{breadth.get('decliners',0)} | 5-min vol× {breadth.get('vol_mult',1.0):.1f}")
    if leaders:
        lines.append("• Leadership: " + ", ".join(leaders[:4]))
    if idea:
        lines.append(f"• Idea: {idea['symbol']} {idea['dte']}D {idea['strategy']} "
                     f"credit ~{idea.get('credit','$?')} (PoP {int(idea.get('pop',0)*100)}%)")
    lines.append("#options #marketopen")
    return "\n".join(lines)

def compose_close(day: Dict[str, Any], best: Optional[Dict[str,Any]], stats: Dict[str,Any]) -> str:
    lines = ["📊 CLOSING WRAP"]
    lines.append(f"• SPY {day.get('spy')} | QQQ {day.get('qqq')} | VIX {day.get('vix')}")
    if day.get("leaders"): lines.append("• Leaders: " + ", ".join(day["leaders"][:3]))
    if day.get("laggards"): lines.append("• Laggards: " + ", ".join(day["laggards"][:3]))
    if best:
        lines.append(f"• Best opp: {best['symbol']} {best['strategy']} hit {best['result']} (flagged {best['time']})")
    lines.append(f"• Perf: {stats.get('wins',0)}/{stats.get('trades',0)} wins | avg EV {stats.get('avg_ev',0):+.2f}")
    lines.append("#options #marketclose")
    return "\n".join(lines)

def _polish(msg: str) -> str:
    # OPTIONAL: call your LLM service to refine copy, keep it < 280 chars
    # Example stub that just returns the same text
    return msg[:270]
