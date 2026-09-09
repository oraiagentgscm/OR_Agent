from __future__ import annotations
import math
import pandas as pd
from .forecast import demand_stats


def _risk_decay(day: int) -> float:
    if day == 0:
        return 1.0
    if day <= 2:
        return 0.85
    if day <= 6:
        return 0.60
    if day <= 13:
        return 0.25
    return 0.0


def compute_inventory_targets(config, demand_df, route_delay_df, news_risk, horizon):
    z = float(config.get("service_level_z", 1.645))
    rows = []
    for p in config["plants"]:
        pid = p["id"]
        mu, sigma_d = demand_stats(demand_df, pid)
        policy_days = float(p.get("policy_days_cover", 0))

        for t in range(horizon):
            rdf = route_delay_df[(route_delay_df["plant"] == pid) & (route_delay_df["day"] == t)]
            avg_delay_days = float(rdf["delay_hours"].mean() / 24.0) if len(rdf) else 0.0
            base_lead = float(rdf["base_lead_days"].mean()) if len(rdf) else 1.0
            lead_days = max(1.0, base_lead + avg_delay_days)

            statistical_ss = z * sigma_d * math.sqrt(lead_days)
            safety_days = statistical_ss / max(mu, 1.0)
            risk_days = min(5.0, avg_delay_days + 5.0 * news_risk * _risk_decay(t))
            operational_target_days = lead_days + safety_days + risk_days
            target_days = max(policy_days, operational_target_days)

            rows.append({
                "plant": pid,
                "day": t,
                "target_days": target_days,
                "target_inventory": mu * target_days,
            })
    return pd.DataFrame(rows)
