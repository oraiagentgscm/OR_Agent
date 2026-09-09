from __future__ import annotations
import json
from pathlib import Path


def build_audit(config, weather, news, news_status, news_risk, corridor_factor, source_factors, route_delay):
    loc_names = {x["id"]: x["name"] for x in config["sources"] + config["plants"]}
    weather_rows = []
    for loc_id, w in weather.items():
        weather_rows.append({
            "id": loc_id,
            "name": loc_names.get(loc_id, loc_id),
            "connected": bool(w.fetch_ok),
            "source": w.source,
            "rain_24h_mm": w.rain_24h_mm,
            "rain_72h_mm": w.rain_72h_mm,
            "max_precip_probability_24h": w.max_precip_probability_24h,
            "severe_rain_flag": w.severe_rain_flag,
            "error": w.error,
        })

    live_weather = sum(1 for x in weather_rows if x["connected"])
    total_weather = len(weather_rows)
    day0 = route_delay[route_delay["day"] == 0] if "day" in route_delay.columns else route_delay
    max_delay = float(day0["delay_hours"].max()) if len(day0) else 0.0
    worst_routes = day0.sort_values("delay_hours", ascending=False).head(5).to_dict("records") if len(day0) else []

    return {
        "weather_connection": {
            "connected_locations": live_weather,
            "total_locations": total_weather,
            "all_live": live_weather == total_weather and total_weather > 0,
        },
        "news_connection": news_status.to_dict(),
        "weather": weather_rows,
        "news": [n.to_dict() for n in news[:15]],
        "interpretation": {
            "news_risk": round(float(news_risk), 3),
            "corridor_capacity_factor": round(float(corridor_factor), 3),
            "source_capacity_factors": {k: round(float(v), 3) for k, v in source_factors.items()},
            "max_route_delay_hours": round(max_delay, 1),
            "worst_routes": worst_routes,
        },
    }


def write_audit(outdir, audit):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "audit_latest.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")

    wc = audit["weather_connection"]
    ns = audit["news_connection"]
    it = audit["interpretation"]
    lines = [
        "# Agentic AI — Data Ingestion Audit",
        "",
        "## Connectivity",
        f"- Weather API: {'CONNECTED' if wc['all_live'] else 'PARTIAL / FALLBACK'} ({wc['connected_locations']}/{wc['total_locations']} locations live)",
        f"- News connector: {'CONNECTED' if ns['fetch_ok'] else 'FAILED'} ({ns['article_count']} articles)",
        f"- News source: {ns['source']}",
        f"- News fetch error: {ns['error'] or 'None'}",
        f"- News connector details: {ns.get('details', 'None') or 'None'}",
        "",
        "## Weather observations",
        "| Location | Live? | 24h rain mm | 72h rain mm | Max precip % | Severe flag |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for w in audit["weather"]:
        lines.append(
            f"| {w['name']} | {'YES' if w['connected'] else 'NO'} | {w['rain_24h_mm']:.1f} | "
            f"{w['rain_72h_mm']:.1f} | {w['max_precip_probability_24h']:.0f} | {w['severe_rain_flag']} |"
        )
    lines += [
        "",
        "## Agent interpretation",
        f"- News risk: {it['news_risk']:.2f}",
        f"- Effective corridor capacity factor: {it['corridor_capacity_factor']:.2f}",
        f"- Maximum predicted route delay: {it['max_route_delay_hours']:.1f} hours",
        "",
        "## Latest disruption news",
    ]
    if audit["news"]:
        for n in audit["news"][:10]:
            lines.append(f"- {n['title']} — {n['url']}")
    else:
        lines.append("- No matching live disruption articles were returned in this fetch.")

    (out / "audit_latest.md").write_text("\n".join(lines), encoding="utf-8")
