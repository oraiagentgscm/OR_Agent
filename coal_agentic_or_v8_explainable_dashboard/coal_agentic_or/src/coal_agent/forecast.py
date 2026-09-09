\
from __future__ import annotations
import math
import numpy as np
import pandas as pd

def build_demand_forecast(config, horizon: int) -> pd.DataFrame:
    rows = []
    # Simple baseline + weekday shape. Replace with actual demand/PLF forecaster.
    weekday_factor = [1.00, 1.01, 1.02, 1.02, 1.01, 0.98, 0.96]
    for p in config["plants"]:
        base = float(p["base_demand_tpd"])
        for t in range(horizon):
            seasonal = 1.0 + 0.03 * math.sin(2 * math.pi * t / 30.0)
            demand = base * weekday_factor[t % 7] * seasonal
            rows.append({"plant": p["id"], "day": t, "demand": demand})
    return pd.DataFrame(rows)

def demand_stats(demand_df: pd.DataFrame, plant_id: str):
    x = demand_df.loc[demand_df["plant"] == plant_id, "demand"].to_numpy()
    return float(np.mean(x)), float(np.std(x, ddof=1) if len(x) > 1 else 0.0)
