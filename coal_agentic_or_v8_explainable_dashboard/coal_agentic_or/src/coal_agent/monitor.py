from __future__ import annotations
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
import yaml

from .weather import WeatherTool
from .news import NewsTool
from .risk import RiskEngine
from .agent import DailyPlanningAgent
from .emailer import send_email
from .audit import build_audit, write_audit


def load_monitoring_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class HourlyDisruptionMonitor:
    def __init__(self, network_config, monitoring_config, root):
        self.cfg = network_config
        self.mon = monitoring_config
        self.root = Path(root)
        self.outdir = self.root / "outputs"
        self.state_dir = self.root / "state"
        self.state_dir.mkdir(exist_ok=True)
        self.state_path = self.state_dir / "last_alert.json"
        self.risk = RiskEngine()

    def _quick_assessment(self, weather, news):
        news_risk = self.risk.news_risk(news)
        source_factors = {
            s["id"]: self.risk.source_capacity_factor(weather[s["id"]], news_risk)
            for s in self.cfg["sources"]
        }
        corridor_factor = self.risk.corridor_capacity_factor(weather, news_risk)
        rows = []
        for r in self.cfg["routes"]:
            delay = self.risk.estimate_route_delay_hours(
                weather[r["source"]], weather[r["plant"]], news_risk, float(r["base_lead_days"])
            )
            rows.append({
                "source": r["source"], "plant": r["plant"], "day": 0,
                "delay_hours": delay, "base_lead_days": float(r["base_lead_days"]),
                "forecast_confidence": "high",
            })
        return news_risk, source_factors, corridor_factor, pd.DataFrame(rows)

    def _evaluate(self, weather, news_status, news_risk, route_delay, corridor_factor):
        breaches = []
        wcfg = self.mon["weather"]
        rcfg = self.mon["risk"]
        names = {x["id"]: x["name"] for x in self.cfg["sources"] + self.cfg["plants"]}

        if self.mon["alerts"].get("alert_on_weather_api_failure", True):
            failed = [names.get(k, k) for k, w in weather.items() if not w.fetch_ok]
            if failed:
                breaches.append(f"Weather API failure/fallback at {len(failed)}/{len(weather)} locations")
        if self.mon["alerts"].get("alert_on_news_api_failure", True) and not news_status.fetch_ok:
            breaches.append("All configured news providers failed")

        for loc_id, w in weather.items():
            label = names.get(loc_id, loc_id)
            if w.rain_24h_mm >= float(wcfg["rain_24h_mm"]):
                breaches.append(f"{label}: 24h rain {w.rain_24h_mm:.1f} mm >= {wcfg['rain_24h_mm']} mm")
            if w.rain_72h_mm >= float(wcfg["rain_72h_mm"]):
                breaches.append(f"{label}: 72h rain {w.rain_72h_mm:.1f} mm >= {wcfg['rain_72h_mm']} mm")
            if w.max_precip_probability_24h >= float(wcfg["precip_probability_24h_pct"]):
                breaches.append(f"{label}: precip probability {w.max_precip_probability_24h:.0f}% >= {wcfg['precip_probability_24h_pct']}%")
            if bool(wcfg.get("require_severe_rain_flag", True)) and w.severe_rain_flag:
                breaches.append(f"{label}: severe-rain flag triggered")

        if news_risk >= float(rcfg["news_risk"]):
            breaches.append(f"News disruption risk {news_risk:.2f} >= {rcfg['news_risk']}")

        max_delay = float(route_delay["delay_hours"].max()) if len(route_delay) else 0.0
        if max_delay >= float(rcfg["max_route_delay_hours"]):
            breaches.append(f"Maximum predicted route delay {max_delay:.1f} h >= {rcfg['max_route_delay_hours']} h")

        if corridor_factor <= float(rcfg["min_corridor_capacity_factor"]):
            breaches.append(f"Effective corridor capacity {corridor_factor:.2f} <= {rcfg['min_corridor_capacity_factor']}")

        return sorted(set(breaches))

    def _signature(self, breaches):
        return hashlib.sha256("\n".join(sorted(breaches)).encode("utf-8")).hexdigest()[:16]

    def _should_send(self, signature):
        if not self.state_path.exists():
            return True
        try:
            state = json.loads(self.state_path.read_text(encoding="utf-8"))
            last = datetime.fromisoformat(state["sent_at"])
            cooldown = timedelta(hours=float(self.mon["alerts"].get("cooldown_hours", 6)))
            changed = state.get("signature") != signature
            if changed and self.mon["alerts"].get("resend_if_signature_changes", True):
                return True
            return datetime.now(ZoneInfo("Asia/Kolkata")) - last >= cooldown
        except Exception:
            return True

    def check(self):
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
        locs = self.cfg["sources"] + self.cfg["plants"]
        weather = WeatherTool().fetch(locs)
        news, news_status = NewsTool().fetch_with_status()
        news_risk, source_factors, corridor_factor, route_delay = self._quick_assessment(weather, news)
        breaches = self._evaluate(weather, news_status, news_risk, route_delay, corridor_factor)

        # Every hourly check gets an immutable audit folder, even when no alert is sent.
        snap = self.outdir / "hourly_snapshots" / now.strftime("%Y%m%d_%H%M%S")
        snap.mkdir(parents=True, exist_ok=True)
        audit = build_audit(
            self.cfg, weather, news, news_status, news_risk,
            corridor_factor, source_factors, route_delay
        )
        write_audit(snap, audit)

        monitor_record = {
            "checked_at": now.isoformat(),
            "breach_count": len(breaches),
            "breaches": breaches,
            "weather_live_locations": sum(1 for w in weather.values() if w.fetch_ok),
            "weather_total_locations": len(weather),
            "news_fetch_ok": news_status.fetch_ok,
            "news_article_count": news_status.article_count,
            "news_source": news_status.source,
            "news_details": getattr(news_status, "details", ""),
            "news_risk": news_risk,
            "corridor_capacity_factor": corridor_factor,
            "max_route_delay_hours": float(route_delay["delay_hours"].max()) if len(route_delay) else 0.0,
            "audit_folder": str(snap),
        }
        (snap / "hourly_monitor.json").write_text(json.dumps(monitor_record, indent=2), encoding="utf-8")
        (self.outdir / "LATEST_HOURLY_SNAPSHOT.txt").write_text(str(snap), encoding="utf-8")

        if not breaches:
            print(f"[{now:%Y-%m-%d %H:%M}] Hourly monitor: no threshold breach.")
            if self.mon["alerts"].get("send_hourly_no_disruption_email", True):
                names = {x["id"]: x["name"] for x in self.cfg["sources"] + self.cfg["plants"]}
                weather_live = sum(1 for w in weather.values() if w.fetch_ok)
                total_locations = len(weather)
                max_delay = float(route_delay["delay_hours"].max()) if len(route_delay) else 0.0
                body = "\n".join([
                    "NO DISRUPTION DETECTED",
                    "",
                    f"Hourly check completed at: {now:%Y-%m-%d %H:%M %Z}",
                    "All configured disruption thresholds are currently within limits.",
                    "",
                    f"Weather feeds live: {weather_live}/{total_locations}",
                    f"News feed connected: {'YES' if news_status.fetch_ok else 'NO'}",
                    f"News source(s): {news_status.source}",
                    f"Matching news articles: {news_status.article_count}",
                    f"News-risk score: {news_risk:.2f}",
                    f"Effective corridor capacity factor: {corridor_factor:.2f}",
                    f"Maximum predicted route delay: {max_delay:.1f} hours",
                    "",
                    "Status: No disruption. No emergency re-optimization was required for this hourly check.",
                ])
                mail = send_email(
                    subject=f"[OK] No disruption detected — {now:%Y-%m-%d %H:%M}",
                    body=body,
                    attachments=[snap / "audit_latest.md"],
                )
                monitor_record["email"] = mail
            else:
                monitor_record["email"] = {"sent": False, "reason": "hourly no-disruption email disabled"}
            return monitor_record

        signature = self._signature(breaches)
        send_every_hour = self.mon["alerts"].get("send_alert_every_hour_while_active", True)
        if not send_every_hour and not self._should_send(signature):
            print(f"[{now:%Y-%m-%d %H:%M}] Disruption detected, but alert suppressed by cooldown/deduplication.")
            monitor_record["email"] = {"sent": False, "reason": "cooldown/deduplication"}
            return monitor_record

        # Threshold crossed: re-optimize immediately using the exact same weather/news snapshot.
        result = DailyPlanningAgent(self.cfg).run(
            self.outdir,
            weather=weather,
            news=news,
            news_status=news_status,
            run_type="disruption-alert",
            versioned=True,
        )
        run_dir = result["output_dir"]

        body = [
            "AGENTIC OR — DISRUPTION ALERT",
            "",
            f"Detected at: {now:%Y-%m-%d %H:%M %Z}",
            "",
            "Threshold breaches:",
        ]
        body += [f"- {x}" for x in breaches]
        body += [
            "",
            f"Current news-risk score: {result['meta']['news_risk']:.2f}",
            f"Effective corridor capacity factor: {result['meta']['corridor_factor_day0']:.2f}",
            f"Max predicted route delay: {result['meta']['max_route_delay_hours_day0']:.1f} hours",
            "",
            "Latest matching disruption news:",
        ]
        if news:
            body += [f"- {item.title} — {item.url}" for item in news[:5]]
        else:
            body += ["- No matching disruption headlines returned in this fetch."]
        body += [
            "",
            "The OR model was re-solved immediately using this same live weather/news snapshot.",
            "",
            "FULL REVISED NODE STATUS AND ALLOCATION",
            "---------------------------------------",
            (run_dir / "daily_brief.md").read_text(encoding="utf-8"),
        ]
        attachments = [run_dir / "audit_latest.md", run_dir / "daily_brief.md"]
        if self.mon["alerts"].get("attach_csv_reports", True):
            attachments += [
                run_dir / "procurement_summary.csv",
                run_dir / "route_delay.csv",
                run_dir / "inventory_plan.csv",
                run_dir / "supply_node_status.csv",
                run_dir / "demand_node_status.csv",
                run_dir / "allocation_matrix_today.csv",
                run_dir / "allocation_matrix_7d.csv",
                run_dir / "allocation_matrix_30d.csv",
                run_dir / "allocation_matrix_60d.csv",
                run_dir / "horizon_demand_coverage.csv",
                run_dir / "input_demand_60d.csv",
                run_dir / "input_supply_60d.csv",
                run_dir / "input_route_cost_60d.csv",
                run_dir / "route_cost_matrix.csv",
                run_dir / "today_route_cost_breakdown.csv",
            ]

        mail = send_email(
            subject=f"[ALERT] Coal corridor disruption — {len(breaches)} threshold breach(es)",
            body="\n".join(body),
            attachments=attachments,
        )
        if mail.get("sent") and not self.mon["alerts"].get("send_alert_every_hour_while_active", True):
            self.state_path.write_text(json.dumps({"signature": signature, "sent_at": now.isoformat()}, indent=2), encoding="utf-8")
        monitor_record["email"] = mail
        monitor_record["optimization_run_folder"] = str(run_dir)
        return monitor_record
