from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd

from .forecast import build_demand_forecast

TZ = ZoneInfo("Asia/Kolkata")


def _start_date():
    return datetime.now(TZ).date()


def _dates(horizon: int, start_date=None):
    start_date = start_date or _start_date()
    return [start_date + timedelta(days=i) for i in range(horizon)]


def default_demand_schedule(config, horizon: int, start_date=None) -> pd.DataFrame:
    df = build_demand_forecast(config, horizon).copy()
    dates = _dates(horizon, start_date)
    df["date"] = df["day"].map(lambda d: dates[int(d)].isoformat())
    return df[["date", "plant", "day", "demand"]]


def default_supply_schedule(config, horizon: int, start_date=None) -> pd.DataFrame:
    dates = _dates(horizon, start_date)
    rows = []
    for t, dt in enumerate(dates):
        for s in config["sources"]:
            rows.append({
                "date": dt.isoformat(), "source": s["id"], "day": t,
                "capacity": float(s["base_capacity_tpd"]),
            })
    return pd.DataFrame(rows)


def default_route_cost_schedule(config, horizon: int, start_date=None) -> pd.DataFrame:
    dates = _dates(horizon, start_date)
    rows = []
    for t, dt in enumerate(dates):
        for r in config["routes"]:
            rows.append({
                "date": dt.isoformat(), "source": r["source"], "plant": r["plant"],
                "day": t, "cost": float(r["cost"]),
            })
    return pd.DataFrame(rows)


def scenario_dir(config) -> Path:
    root = Path(config.get("_project_root", ".")).resolve()
    d = root / "scenario_inputs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def active_paths(config):
    d = scenario_dir(config)
    return {
        "demand": d / "active_demand_60d.csv",
        "supply": d / "active_supply_60d.csv",
        "cost": d / "active_route_cost_60d.csv",
    }


def _overlay(base: pd.DataFrame, override_path: Path, keys: list[str], value_col: str, horizon: int) -> pd.DataFrame:
    out = base.copy()
    if not override_path.exists():
        return out
    try:
        ov = pd.read_csv(override_path)
    except Exception:
        return out
    needed = set(keys + [value_col])
    if not needed.issubset(ov.columns):
        return out
    ov = ov[keys + [value_col]].copy()
    ov[value_col] = pd.to_numeric(ov[value_col], errors="coerce")
    ov = ov.dropna(subset=[value_col])
    out = out.drop(columns=[value_col]).merge(ov, on=keys, how="left")
    # Reconstruct default values where the active scenario does not cover the newly rolled horizon.
    default_lookup = base.set_index(keys)[value_col]
    missing = out[value_col].isna()
    if missing.any():
        vals = []
        for row in out.loc[missing, keys].itertuples(index=False, name=None):
            vals.append(float(default_lookup.loc[row]))
        out.loc[missing, value_col] = vals
    out["day"] = (pd.to_datetime(out["date"]).dt.date - pd.Timestamp(_start_date()).date()).apply(lambda x: x.days)
    out = out[(out["day"] >= 0) & (out["day"] < horizon)].copy()
    return out


def load_active_scenario(config, horizon: int, start_date=None):
    start_date = start_date or _start_date()
    base_d = default_demand_schedule(config, horizon, start_date)
    base_s = default_supply_schedule(config, horizon, start_date)
    base_c = default_route_cost_schedule(config, horizon, start_date)
    paths = active_paths(config)

    # Overlay by absolute date and node/route, so tomorrow automatically rolls day 0 forward.
    demand = _overlay(base_d, paths["demand"], ["date", "plant"], "demand", horizon)
    supply = _overlay(base_s, paths["supply"], ["date", "source"], "capacity", horizon)
    costs = _overlay(base_c, paths["cost"], ["date", "source", "plant"], "cost", horizon)
    return demand, supply, costs


def save_active_scenario(config, demand_df: pd.DataFrame, supply_df: pd.DataFrame, cost_df: pd.DataFrame):
    paths = active_paths(config)
    demand_df[["date", "plant", "demand"]].to_csv(paths["demand"], index=False)
    supply_df[["date", "source", "capacity"]].to_csv(paths["supply"], index=False)
    cost_df[["date", "source", "plant", "cost"]].to_csv(paths["cost"], index=False)
    return paths


def reset_active_scenario(config):
    for p in active_paths(config).values():
        if p.exists():
            p.unlink()
