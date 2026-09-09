from __future__ import annotations
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
from pathlib import Path

from .weather import WeatherTool, WeatherSignal
from .news import NewsTool, NewsFetchStatus
from .risk import RiskEngine
from .forecast import build_demand_forecast
from .inventory import compute_inventory_targets
from .optimizer import solve_plan
from .scenario import load_active_scenario
from .reporting import write_reports
from .audit import build_audit, write_audit


def risk_decay(day: int) -> float:
    # Current event/weather signals are informative near-term, not for 60 days.
    if day == 0:
        return 1.0
    if day <= 2:
        return 0.85
    if day <= 6:
        return 0.60
    if day <= 13:
        return 0.25
    return 0.0


class DailyPlanningAgent:
    def __init__(self, config):
        self.cfg = config
        self.H = int(config["planning_horizon_days"])
        self.risk = RiskEngine()

    def run(
        self, outdir="outputs", weather=None, news=None, news_status=None,
        run_type="manual", versioned=True,
        demand_override=None, supply_capacity_override=None, route_cost_override=None,
    ):
        base_outdir = Path(outdir)
        base_outdir.mkdir(parents=True, exist_ok=True)
        if versioned:
            stamp = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y%m%d_%H%M%S")
            safe_type = run_type.replace(" ", "-").replace("/", "-")
            outdir = base_outdir / "runs" / f"{stamp}_{safe_type}"
            outdir.mkdir(parents=True, exist_ok=True)
            (base_outdir / "LATEST_RUN.txt").write_text(str(outdir), encoding="utf-8")
        else:
            outdir = base_outdir
        # PERCEIVE
        locs = self.cfg["sources"] + self.cfg["plants"]
        live = os.getenv("LIVE_WEB_ENABLED", "true").lower() == "true"
        if weather is None or news is None:
            if live:
                if weather is None:
                    weather = WeatherTool().fetch(locs)
                if news is None:
                    news, fetched_status = NewsTool().fetch_with_status()
                    if news_status is None:
                        news_status = fetched_status
            else:
                now = datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()
                if weather is None:
                    weather = {
                        x["id"]: WeatherSignal(
                            x["id"], source="fallback", fetch_ok=False,
                            fetched_at=now, error="LIVE_WEB_ENABLED=false"
                        )
                        for x in locs
                    }
                if news is None:
                    news = []
                    news_status = NewsFetchStatus(False, "Google News RSS + NewsAPI", now, 0, "LIVE_WEB_ENABLED=false", "Web connectors disabled")

        if news_status is None:
            now = datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()
            news_status = NewsFetchStatus(True, "provided-input", now, len(news or []), "")

        # ASSESS
        news_risk = self.risk.news_risk(news)
        source_factors = {}
        corridor_factors = {}
        now_source_factor = {
            s["id"]: self.risk.source_capacity_factor(weather[s["id"]], news_risk)
            for s in self.cfg["sources"]
        }
        now_corridor_factor = self.risk.corridor_capacity_factor(weather, news_risk)

        for t in range(self.H):
            decay = risk_decay(t)
            for s in self.cfg["sources"]:
                f0 = now_source_factor[s["id"]]
                source_factors[(s["id"], t)] = 1.0 - (1.0 - f0) * decay
            corridor_factors[t] = 1.0 - (1.0 - now_corridor_factor) * decay

        route_rows = []
        for r in self.cfg["routes"]:
            sw = weather[r["source"]]
            pw = weather[r["plant"]]
            raw_delay = self.risk.estimate_route_delay_hours(
                sw, pw, news_risk, float(r["base_lead_days"])
            )
            for t in range(self.H):
                decay = risk_decay(t)
                confidence = "high" if t <= 2 else "medium" if t <= 6 else "low"
                route_rows.append({
                    "source": r["source"],
                    "plant": r["plant"],
                    "day": t,
                    "delay_hours": raw_delay * decay,
                    "base_lead_days": float(r["base_lead_days"]),
                    "forecast_confidence": confidence,
                })
        route_delay = pd.DataFrame(route_rows)
        day0_delays = route_delay[route_delay["day"] == 0]
        max_route_delay_day0 = float(day0_delays["delay_hours"].max()) if len(day0_delays) else 0.0

        # Audit raw web connectivity and interpreted risk BEFORE optimization.
        audit = build_audit(
            self.cfg, weather, news, news_status, news_risk,
            now_corridor_factor, now_source_factor, route_delay
        )
        write_audit(outdir, audit)

        # PLAN — all horizons are generated from one 60-day global solve.
        # Active dashboard scenario inputs persist into scheduled and disruption-triggered runs.
        active_demand, active_supply, active_cost = load_active_scenario(self.cfg, self.H)
        demand = demand_override.copy() if demand_override is not None else active_demand.copy()
        supply_capacity = supply_capacity_override.copy() if supply_capacity_override is not None else active_supply.copy()
        route_cost = route_cost_override.copy() if route_cost_override is not None else active_cost.copy()

        # Optimizer operates on relative day 0..59; absolute dates remain in the exported scenario files.
        demand["day"] = demand["day"].astype(int)
        supply_capacity["day"] = supply_capacity["day"].astype(int)
        route_cost["day"] = route_cost["day"].astype(int)
        targets = compute_inventory_targets(self.cfg, demand, route_delay, news_risk, self.H)

        # OPTIMIZE — one 60-day LP, with hard demand satisfaction if configured.
        plan, objective = solve_plan(
            self.cfg, demand, targets, route_delay, source_factors, corridor_factors,
            supply_capacity_df=supply_capacity, route_cost_df=route_cost,
        )

        # VALIDATE
        shortfall = float(plan.loc[plan["kind"] == "shortfall", "value"].sum())
        buffer_gap = float(plan.loc[plan["kind"] == "buffer_gap", "value"].sum())
        if shortfall > 1e-3:
            status = "CRITICAL: projected demand shortfall"
        elif buffer_gap > 1e-3:
            status = "WARNING: inventory target cannot be fully maintained"
        else:
            status = "FEASIBLE: demand and inventory targets met"

        # REPORT
        now = datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()
        weather_live = sum(1 for w in weather.values() if w.fetch_ok)
        meta = {
            "run_time": now,
            "run_type": run_type,
            "status": status,
            "web_enabled": live,
            "weather_live_locations": weather_live,
            "weather_total_locations": len(weather),
            "news_fetch_ok": news_status.fetch_ok,
            "news_article_count": news_status.article_count,
            "news_fetch_error": news_status.error,
            "news_source": news_status.source,
            "news_details": getattr(news_status, "details", ""),
            "news_risk": news_risk,
            "corridor_factor_day0": now_corridor_factor,
            "source_capacity_factors_day0": now_source_factor,
            "max_route_delay_hours_day0": max_route_delay_day0,
            "total_shortfall_tonnes": shortfall,
            "total_buffer_gap_tonnes": buffer_gap,
            "horizon_note": "Today/7/30/60-day allocations are cumulative slices of one 60-day optimization that is solved against the full 60-day demand schedule. Current-event risk tapers after day 7 and is removed after day 14.",
            "full_horizon_demand_enforced": bool(self.cfg.get("enforce_full_horizon_demand", True)),
        }
        write_reports(
            outdir, self.cfg, plan, route_delay, targets, demand, weather, news, objective, meta,
            supply_capacity_df=supply_capacity, route_cost_df=route_cost,
        )
        return {
            "meta": meta,
            "plan": plan,
            "route_delay": route_delay,
            "weather": weather,
            "news": news,
            "news_status": news_status,
            "audit": audit,
            "output_dir": Path(outdir),
        }
