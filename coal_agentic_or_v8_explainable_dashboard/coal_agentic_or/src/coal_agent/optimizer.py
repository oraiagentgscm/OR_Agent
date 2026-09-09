from __future__ import annotations
import math
import numpy as np
import pandas as pd
from scipy.optimize import linprog


def solve_plan(
    config,
    demand_df,
    target_df,
    route_delay_df,
    source_factors,
    corridor_factor,
    supply_capacity_df=None,
    route_cost_df=None,
):
    H = int(config["planning_horizon_days"])
    sources = [s["id"] for s in config["sources"]]
    plants = [p["id"] for p in config["plants"]]
    routes = [(r["source"], r["plant"]) for r in config["routes"]]
    route_map = {(r["source"], r["plant"]): r for r in config["routes"]}

    idx, names, c = {}, [], []
    delay_cost = float(config.get("delay_cost_per_tonne_hour", 0.0))
    hold_cost = float(config.get("holding_cost_per_tonne_day", 0.0))
    short_pen = float(config.get("shortfall_penalty_per_tonne", 5000.0))
    buffer_pen = float(config.get("buffer_violation_penalty_per_tonne", 1000.0))
    enforce_full_demand = bool(config.get("enforce_full_horizon_demand", True))

    delay_lookup = {
        (r.source, r.plant, int(r.day)): (float(r.delay_hours), float(r.base_lead_days))
        for r in route_delay_df.itertuples()
    }

    if route_cost_df is not None and len(route_cost_df):
        cost_lookup = {
            (r.source, r.plant, int(r.day)): float(r.cost)
            for r in route_cost_df.itertuples()
        }
    else:
        cost_lookup = {
            (s, p, t): float(route_map[(s, p)]["cost"])
            for s, p in routes for t in range(H)
        }

    for s, p in routes:
        for t in range(H):
            delay_h, _ = delay_lookup[(s, p, t)]
            idx[("x", s, p, t)] = len(names)
            names.append(("x", s, p, t))
            c.append(cost_lookup[(s, p, t)] + delay_cost * delay_h)

    for p in plants:
        for t in range(H):
            idx[("I", p, t)] = len(names); names.append(("I", p, t)); c.append(hold_cost)
            idx[("u", p, t)] = len(names); names.append(("u", p, t)); c.append(short_pen)
            idx[("v", p, t)] = len(names); names.append(("v", p, t)); c.append(buffer_pen)

    n = len(names)
    A_ub, b_ub, A_eq, b_eq = [], [], [], []

    if supply_capacity_df is not None and len(supply_capacity_df):
        capacity_lookup = {
            (r.source, int(r.day)): float(r.capacity)
            for r in supply_capacity_df.itertuples()
        }
    else:
        base_cap = {s["id"]: float(s["base_capacity_tpd"]) for s in config["sources"]}
        capacity_lookup = {(s, t): base_cap[s] for s in sources for t in range(H)}

    # Daily source capacity. Dashboard edits set the pre-disruption capacity; live risk then scales it.
    for s in sources:
        for t in range(H):
            row = np.zeros(n)
            for ss, p in routes:
                if ss == s:
                    row[idx[("x", s, p, t)]] = 1.0
            A_ub.append(row)
            b_ub.append(capacity_lookup[(s, t)] * source_factors.get((s, t), 1.0))

    # Corridor capacity by departure day.
    base_corridor_cap = float(config["base_corridor_capacity_tpd"])
    for t in range(H):
        row = np.zeros(n)
        for s, p in routes:
            row[idx[("x", s, p, t)]] = 1.0
        A_ub.append(row)
        b_ub.append(base_corridor_cap * corridor_factor.get(t, 1.0))

    demand_lookup = {(r.plant, int(r.day)): float(r.demand) for r in demand_df.itertuples()}
    target_lookup = {(r.plant, int(r.day)): float(r.target_inventory) for r in target_df.itertuples()}
    inv0 = {p["id"]: float(p["current_inventory_tonnes"]) for p in config["plants"]}

    arrivals = {}
    for s, p in routes:
        for dep in range(H):
            delay_h, base_lead = delay_lookup[(s, p, dep)]
            lead = max(1, int(math.ceil(base_lead + delay_h / 24.0)))
            arr = dep + lead
            if arr < H:
                arrivals.setdefault((p, arr), []).append((s, p, dep))

    # Inventory balance guarantees each day's demand is covered from opening stock + arrived shipments.
    # When enforce_full_horizon_demand=true, shortfall variables are fixed at zero.
    for p in plants:
        for t in range(H):
            row = np.zeros(n)
            row[idx[("I", p, t)]] = 1.0
            if t > 0:
                row[idx[("I", p, t - 1)]] = -1.0
                rhs = -demand_lookup[(p, t)]
            else:
                rhs = inv0[p] - demand_lookup[(p, t)]
            for s, pp, dep in arrivals.get((p, t), []):
                row[idx[("x", s, pp, dep)]] -= 1.0
            row[idx[("u", p, t)]] -= 1.0
            A_eq.append(row)
            b_eq.append(rhs)

    # Soft inventory target; demand itself is hard when full-horizon enforcement is enabled.
    for p in plants:
        for t in range(H):
            row = np.zeros(n)
            row[idx[("I", p, t)]] = -1.0
            row[idx[("v", p, t)]] = -1.0
            A_ub.append(row)
            b_ub.append(-target_lookup[(p, t)])

    bounds = []
    for name in names:
        if name[0] == "u" and enforce_full_demand:
            bounds.append((0.0, 0.0))
        else:
            bounds.append((0.0, None))

    res = linprog(
        c=np.asarray(c),
        A_ub=np.vstack(A_ub), b_ub=np.asarray(b_ub),
        A_eq=np.vstack(A_eq), b_eq=np.asarray(b_eq),
        bounds=bounds, method="highs",
    )
    if not res.success:
        mode = "with hard 60-day demand satisfaction" if enforce_full_demand else "with soft shortfall"
        raise RuntimeError(
            f"Optimization failed {mode}: {res.message}. "
            "If you edited demand/supply, verify that opening inventory, corridor capacity and source capacity can support the full 60-day requirement."
        )

    vals, records = res.x, []
    for k, position in idx.items():
        if k[0] == "x":
            _, s, p, t = k
            records.append({"kind": "dispatch", "source": s, "plant": p, "day": t, "value": vals[position]})
        elif k[0] in ("I", "u", "v"):
            kind, p, t = k
            records.append({
                "kind": {"I": "inventory", "u": "shortfall", "v": "buffer_gap"}[kind],
                "source": "", "plant": p, "day": t, "value": vals[position],
            })
    return pd.DataFrame(records), float(res.fun)
