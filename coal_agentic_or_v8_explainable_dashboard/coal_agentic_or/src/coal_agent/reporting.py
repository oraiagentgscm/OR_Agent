from __future__ import annotations
from pathlib import Path
import json
import pandas as pd


def _window_summary(dispatch, days):
    d = dispatch[dispatch["day"] < days]
    return d.groupby("source", as_index=False)["value"].sum().rename(columns={"value": f"tonnes_{days}d"})


def _fmt(x):
    return f"{float(x):,.0f}"


def _allocation_matrix(dispatch, config, days):
    source_name = {s["id"]: s["name"] for s in config["sources"]}
    plant_name = {p["id"]: p["name"] for p in config["plants"]}
    d = dispatch[dispatch["day"] < days]
    matrix = d.pivot_table(index="source", columns="plant", values="value", aggfunc="sum", fill_value=0)
    matrix = matrix.reindex(
        index=[s["id"] for s in config["sources"]],
        columns=[p["id"] for p in config["plants"]],
        fill_value=0,
    )
    matrix.index = [source_name.get(x, x) for x in matrix.index]
    matrix.columns = [plant_name.get(x, x) for x in matrix.columns]
    matrix["Total supplied"] = matrix.sum(axis=1)
    total_row = matrix.sum(axis=0)
    total_row.name = "Total received"
    return pd.concat([matrix, total_row.to_frame().T])


def _node_status_tables(config, plan, demand_df, target_df, weather, meta, supply_capacity_df):
    dispatch = plan[plan["kind"] == "dispatch"].copy()
    today_dispatch = dispatch[dispatch["day"] == 0].copy()

    inv = plan[plan["kind"].isin(["inventory", "shortfall", "buffer_gap"])].pivot_table(
        index=["plant", "day"], columns="kind", values="value", aggfunc="sum"
    ).reset_index().fillna(0)
    inv = inv.merge(target_df[["plant", "day", "target_inventory", "target_days"]], on=["plant", "day"], how="left")
    day0_inv = inv[inv["day"] == 0].copy()
    today_demand = demand_df[demand_df["day"] == 0][["plant", "demand"]].copy()
    cap0 = supply_capacity_df[supply_capacity_df["day"] == 0].set_index("source")["capacity"].to_dict()

    source_rows = []
    for s in config["sources"]:
        sid = s["id"]
        factor = float(meta["source_capacity_factors_day0"].get(sid, 1.0))
        base_cap = float(cap0.get(sid, s["base_capacity_tpd"]))
        eff_cap = base_cap * factor
        allocated = float(today_dispatch.loc[today_dispatch["source"] == sid, "value"].sum())
        util = allocated / eff_cap if eff_cap > 0 else 0.0
        w = weather[sid]
        if not w.fetch_ok:
            status = "DATA ALERT"
        elif factor <= 0.70 or w.severe_rain_flag:
            status = "CRITICAL"
        elif factor < 0.90 or w.rain_24h_mm >= 30 or w.max_precip_probability_24h >= 75:
            status = "WATCH"
        else:
            status = "NORMAL"
        source_rows.append({
            "source": sid, "source_name": s["name"], "status": status,
            "weather_source": w.source, "rain_24h_mm": float(w.rain_24h_mm),
            "rain_72h_mm": float(w.rain_72h_mm),
            "precip_probability_24h_pct": float(w.max_precip_probability_24h),
            "planned_capacity_tpd": base_cap, "capacity_factor": factor,
            "effective_capacity_tpd": eff_cap, "today_allocated_tonnes": allocated,
            "utilization_pct": util * 100.0,
            "remaining_capacity_tonnes": max(0.0, eff_cap - allocated),
        })
    supply_status = pd.DataFrame(source_rows)

    plant_cfg = {p["id"]: p for p in config["plants"]}
    demand_status = today_demand.merge(day0_inv, on="plant", how="left").fillna(0)
    demand_rows = []
    for r in demand_status.itertuples():
        p = plant_cfg[r.plant]
        w = weather[r.plant]
        opening = float(p["current_inventory_tonnes"])
        closing = float(r.inventory)
        demand = float(r.demand)
        closing_days = closing / demand if demand > 0 else 0.0
        if float(r.shortfall) > 1e-3:
            status = "CRITICAL"
        elif float(r.buffer_gap) > 1e-3 or closing + 1e-3 < float(r.target_inventory):
            status = "WATCH"
        elif not w.fetch_ok:
            status = "DATA ALERT"
        else:
            status = "NORMAL"
        ordered_today = float(today_dispatch.loc[today_dispatch["plant"] == r.plant, "value"].sum())
        demand_rows.append({
            "plant": r.plant, "plant_name": p["name"], "status": status,
            "weather_source": w.source, "rain_24h_mm": float(w.rain_24h_mm),
            "today_demand_tonnes": demand, "opening_inventory_tonnes": opening,
            "target_inventory_tonnes": float(r.target_inventory), "target_days": float(r.target_days),
            "projected_closing_inventory_tonnes": closing,
            "projected_closing_days": closing_days,
            "today_dispatch_ordered_to_plant_tonnes": ordered_today,
            "shortfall_tonnes": float(r.shortfall), "buffer_gap_tonnes": float(r.buffer_gap),
        })
    return supply_status, pd.DataFrame(demand_rows), inv


def _demand_coverage(config, plan, demand_df, horizons=(1, 7, 30, 60)):
    inv = plan[plan["kind"] == "inventory"]
    short = plan[plan["kind"] == "shortfall"]
    dispatch = plan[plan["kind"] == "dispatch"]
    rows = []
    for h in horizons:
        h = min(h, int(demand_df["day"].max()) + 1)
        demand = float(demand_df[demand_df["day"] < h]["demand"].sum())
        planned_dispatch = float(dispatch[dispatch["day"] < h]["value"].sum())
        shortfall = float(short[short["day"] < h]["value"].sum())
        end_inv = float(inv[inv["day"] == h - 1]["value"].sum()) if h > 0 else 0.0
        rows.append({
            "horizon_days": h,
            "cumulative_demand_tonnes": demand,
            "cumulative_dispatch_tonnes": planned_dispatch,
            "cumulative_shortfall_tonnes": shortfall,
            "ending_inventory_tonnes": end_inv,
            "demand_satisfaction": "YES" if shortfall <= 1e-6 else "NO",
        })
    return pd.DataFrame(rows)



def _allocation_explanations_today(config, plan, demand_status, route_delay, route_cost_df):
    """Produce plant-level, evidence-based explanations for today's dispatch decision."""
    dispatch = plan[plan["kind"] == "dispatch"].copy()
    day0 = dispatch[dispatch["day"] == 0].copy()
    source_name = {s["id"]: s["name"] for s in config["sources"]}
    plant_name = {p["id"]: p["name"] for p in config["plants"]}
    delay_cost_rate = float(config.get("delay_cost_per_tonne_hour", 0.0))

    cost0 = route_cost_df[route_cost_df["day"] == 0][["source", "plant", "cost"]].copy()
    delay0 = route_delay[route_delay["day"] == 0][
        ["source", "plant", "delay_hours", "base_lead_days"]
    ].copy()
    route_eval = cost0.merge(delay0, on=["source", "plant"], how="left")
    route_eval["effective_cost"] = (
        route_eval["cost"] + delay_cost_rate * route_eval["delay_hours"].fillna(0)
    )

    status_lookup = {r.plant: r for r in demand_status.itertuples()}
    rows = []

    for p in config["plants"]:
        pid = p["id"]
        stat = status_lookup[pid]
        plant_dispatch = day0[(day0["plant"] == pid) & (day0["value"] > 1e-6)].copy()
        today_alloc = float(plant_dispatch["value"].sum())

        future = dispatch[
            (dispatch["plant"] == pid) & (dispatch["day"] > 0) & (dispatch["value"] > 1e-6)
        ]
        first_future_day = int(future["day"].min()) if not future.empty else None

        demand = float(stat.today_demand_tonnes)
        opening = float(stat.opening_inventory_tonnes)
        opening_days = opening / demand if demand > 1e-9 else float("inf")
        target_days = float(stat.target_days)

        selected_sources = []
        selected_route_details = []
        max_selected_delay = 0.0
        selected_effective_costs = []

        for rr in plant_dispatch.itertuples():
            lane = route_eval[
                (route_eval["source"] == rr.source) & (route_eval["plant"] == pid)
            ]
            if lane.empty:
                eff_cost = float("nan")
                delay_h = 0.0
                base_lead = 0.0
            else:
                lr = lane.iloc[0]
                eff_cost = float(lr["effective_cost"])
                delay_h = float(lr["delay_hours"])
                base_lead = float(lr["base_lead_days"])

            selected_sources.append(source_name.get(rr.source, rr.source))
            selected_effective_costs.append(eff_cost)
            max_selected_delay = max(max_selected_delay, delay_h)
            selected_route_details.append(
                f"{source_name.get(rr.source, rr.source)}: {float(rr.value):,.0f} t "
                f"(₹{eff_cost:,.0f}/t modeled, {delay_h:.1f} h delay, "
                f"{base_lead:.1f} d base lead)"
            )

        all_lanes = route_eval[route_eval["plant"] == pid]
        min_effective_cost = (
            float(all_lanes["effective_cost"].min()) if not all_lanes.empty else float("nan")
        )
        chosen_near_cheapest = (
            today_alloc > 1e-6
            and selected_effective_costs
            and all((x != x) or x <= min_effective_cost + 1e-6 for x in selected_effective_costs)
        )

        if today_alloc > 1e-6:
            if demand <= 1e-9:
                inventory_reason = (
                    "There is no demand today, but the 60-day solve is pre-positioning stock "
                    "for future demand after allowing for transit lead time."
                )
            elif opening_days + 1e-6 < target_days:
                inventory_reason = (
                    f"Opening inventory covers about {opening_days:.1f} days versus a "
                    f"{target_days:.1f}-day target, so replenishment is initiated today."
                )
            else:
                inventory_reason = (
                    f"Opening inventory covers about {opening_days:.1f} days versus a "
                    f"{target_days:.1f}-day target; the model still dispatches today because "
                    "lead time and the remaining 60-day demand make early replenishment preferable."
                )

            if chosen_near_cheapest:
                route_reason = (
                    "The selected lane(s) are at the lowest effective modeled route cost for this plant "
                    "after the current delay-risk adder."
                )
            else:
                route_reason = (
                    "The selected lane mix is a network-wide optimum rather than simply the cheapest "
                    "stand-alone lane; source capacity, corridor capacity, lead times, inventories, "
                    "and every plant's 60-day demand are solved together."
                )

            risk_reason = (
                f" Current selected-lane delay risk reaches {max_selected_delay:.1f} hours, "
                "which also influences dispatch timing."
                if max_selected_delay > 0.1 else ""
            )

            reason = f"{inventory_reason} {route_reason}{risk_reason}"
            decision = "ALLOCATED TODAY"
        else:
            if demand <= 1e-9:
                reason = (
                    "No dispatch is required today because today's demand is zero under the active scenario."
                )
            elif opening_days + 1e-6 >= target_days:
                when = (
                    f"The first later dispatch is planned on Day {first_future_day}."
                    if first_future_day is not None else
                    "No later dispatch is needed within the 60-day horizon under the current demand schedule."
                )
                reason = (
                    f"No dispatch today because opening inventory covers about {opening_days:.1f} days, "
                    f"at or above the {target_days:.1f}-day target. Sending coal earlier would increase "
                    f"holding cost without improving hard demand satisfaction. {when}"
                )
            elif float(stat.buffer_gap_tonnes) > 1e-3:
                when = (
                    f"The first later dispatch is planned on Day {first_future_day}."
                    if first_future_day is not None else
                    "No later dispatch is currently planned."
                )
                reason = (
                    f"No dispatch is scheduled today even though inventory is below the soft target "
                    f"(buffer gap {float(stat.buffer_gap_tonnes):,.0f} t). Day-0 dispatch cannot arrive "
                    f"immediately because routes have transit lead time; the model protects hard demand "
                    f"while allowing a soft buffer gap. {when}"
                )
            else:
                when = (
                    f"The first later dispatch is planned on Day {first_future_day}."
                    if first_future_day is not None else
                    "No dispatch is needed within the 60-day solution because existing inventory is sufficient."
                )
                reason = (
                    f"No dispatch today because existing inventory and the timing of future replenishment "
                    f"are sufficient for the integrated 60-day demand plan. {when}"
                )
            decision = "NO DISPATCH TODAY"

        rows.append({
            "plant": pid,
            "plant_name": plant_name.get(pid, pid),
            "decision_today": decision,
            "today_dispatch_tonnes": today_alloc,
            "today_demand_tonnes": demand,
            "opening_inventory_tonnes": opening,
            "opening_days_cover": None if opening_days == float("inf") else opening_days,
            "target_days": target_days,
            "first_future_dispatch_day": first_future_day,
            "selected_sources": ", ".join(selected_sources) if selected_sources else "—",
            "selected_route_details": " | ".join(selected_route_details) if selected_route_details else "—",
            "reason": reason,
        })

    return pd.DataFrame(rows)

def write_reports(
    outdir, config, plan, route_delay, target_df, demand_df, weather, news_items,
    objective, meta, supply_capacity_df=None, route_cost_df=None,
):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    H = int(config["planning_horizon_days"])
    dispatch = plan[plan["kind"] == "dispatch"].copy()
    plant_name = {p["id"]: p["name"] for p in config["plants"]}
    source_name = {s["id"]: s["name"] for s in config["sources"]}

    # Persist the exact scenario inputs used by this solve.
    if supply_capacity_df is not None:
        supply_capacity_df.to_csv(out / "input_supply_60d.csv", index=False)
    if route_cost_df is not None:
        route_cost_df.to_csv(out / "input_route_cost_60d.csv", index=False)
    demand_df.to_csv(out / "input_demand_60d.csv", index=False)

    # All horizon summaries are cumulative slices of the SAME 60-day optimization.
    summaries = [_window_summary(dispatch, d) for d in (1, 7, 30, H)]
    summary = summaries[0]
    for s in summaries[1:]:
        summary = summary.merge(s, on="source", how="outer")
    summary = summary.fillna(0)
    summary.to_csv(out / "procurement_summary.csv", index=False)

    supply_status, demand_status, inv = _node_status_tables(
        config, plan, demand_df, target_df, weather, meta, supply_capacity_df
    )
    supply_status.to_csv(out / "supply_node_status.csv", index=False)
    demand_status.to_csv(out / "demand_node_status.csv", index=False)

    allocation_explanations = _allocation_explanations_today(
        config, plan, demand_status, route_delay, route_cost_df
    )
    allocation_explanations.to_csv(out / "allocation_explanations_today.csv", index=False)

    horizon_map = {1: "today", 7: "7d", 30: "30d", H: "60d"}
    matrices = {}
    for days, label in horizon_map.items():
        m = _allocation_matrix(dispatch, config, days)
        matrices[label] = m
        m.to_csv(out / f"allocation_matrix_{label}.csv", index=True)

    coverage = _demand_coverage(config, plan, demand_df, horizons=(1, 7, 30, H))
    coverage.to_csv(out / "horizon_demand_coverage.csv", index=False)

    # Route cost inputs: today's matrix plus complete editable 60-day schedule.
    if route_cost_df is None:
        rows = []
        for t in range(H):
            for r in config["routes"]:
                rows.append({"day": t, "source": r["source"], "plant": r["plant"], "cost": float(r["cost"])})
        route_cost_df = pd.DataFrame(rows)
    day0_cost_df = route_cost_df[route_cost_df["day"] == 0][["source", "plant", "cost"]]
    route_cost_matrix = day0_cost_df.pivot(index="source", columns="plant", values="cost").reindex(
        index=[s["id"] for s in config["sources"]], columns=[p["id"] for p in config["plants"]]
    )
    route_cost_matrix.index = [source_name.get(x, x) for x in route_cost_matrix.index]
    route_cost_matrix.columns = [plant_name.get(x, x) for x in route_cost_matrix.columns]
    route_cost_matrix.to_csv(out / "route_cost_matrix.csv", index=True)

    delay_cost_rate = float(config.get("delay_cost_per_tonne_hour", 0.0))
    day0_dispatch = dispatch[dispatch["day"] == 0][["source", "plant", "value"]].rename(columns={"value": "allocated_tonnes"})
    day0_delay = route_delay[route_delay["day"] == 0][["source", "plant", "delay_hours", "base_lead_days"]]
    today_route_cost = day0_dispatch.merge(day0_cost_df, on=["source", "plant"], how="left").merge(day0_delay, on=["source", "plant"], how="left")
    today_route_cost["effective_modeled_cost_per_tonne"] = today_route_cost["cost"] + delay_cost_rate * today_route_cost["delay_hours"]
    today_route_cost["base_transport_cost"] = today_route_cost["allocated_tonnes"] * today_route_cost["cost"]
    today_route_cost["modeled_transport_cost"] = today_route_cost["allocated_tonnes"] * today_route_cost["effective_modeled_cost_per_tonne"]
    today_route_cost = today_route_cost[today_route_cost["allocated_tonnes"] > 1e-6].copy()
    today_route_cost.to_csv(out / "today_route_cost_breakdown.csv", index=False)

    inv.to_csv(out / "inventory_plan.csv", index=False)
    route_delay.to_csv(out / "route_delay.csv", index=False)
    plan.to_csv(out / "full_plan.csv", index=False)

    lines = [
        "# Agentic OR Planning Brief", "",
        f"Run type: {meta['run_type']}", f"Run time: {meta['run_time']}",
        f"Optimization status: {meta['status']}", f"Optimization objective value: {objective:,.2f}", "",
        "## 60-day planning logic",
        "- The optimizer solves one integrated 60-day LP using the complete 60-day demand, supply-capacity and route-cost schedules.",
        "- Today, 7-day, 30-day and 60-day allocations are cumulative slices of that same solution; they are not separate forecasts solved independently.",
        f"- Full-horizon demand satisfaction is {'ENFORCED' if meta.get('full_horizon_demand_enforced') else 'SOFT'} in the LP.",
        "- Only today's dispatch is executed; later-day allocations are re-optimized as new information arrives.", "",
        "## Executive status",
        f"- Weather API live locations: {meta['weather_live_locations']}/{meta['weather_total_locations']}",
        f"- News connector connected: {'YES' if meta['news_fetch_ok'] else 'NO'}",
        f"- News source(s): {meta.get('news_source', 'unknown')}",
        f"- Live news items detected: {len(news_items)}",
        f"- Global disruption-news risk score: {meta['news_risk']:.2f}",
        f"- Effective corridor capacity factor today: {meta['corridor_factor_day0']:.2f}",
        f"- Maximum route delay today: {meta['max_route_delay_hours_day0']:.1f} hours", "",
        "## Horizon demand coverage", "",
        "| Horizon | Cumulative demand | Planned dispatch | Shortfall | Ending inventory | Demand satisfied? |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for r in coverage.itertuples():
        lines.append(f"| {r.horizon_days}d | {_fmt(r.cumulative_demand_tonnes)} | {_fmt(r.cumulative_dispatch_tonnes)} | {_fmt(r.cumulative_shortfall_tonnes)} | {_fmt(r.ending_inventory_tonnes)} | {r.demand_satisfaction} |")

    lines += ["", "## Supply-node status", "", "| Supply node | Status | Planned cap. t/day | Effective cap. t/day | Today allocated | Utilization |", "|---|---|---:|---:|---:|---:|"]
    for r in supply_status.itertuples():
        lines.append(f"| {r.source_name} | {r.status} | {_fmt(r.planned_capacity_tpd)} | {_fmt(r.effective_capacity_tpd)} | {_fmt(r.today_allocated_tonnes)} | {r.utilization_pct:.1f}% |")

    lines += ["", "## Demand-node status", "", "| Demand node | Status | Today demand | Opening inventory | Target inventory | Projected closing | Today dispatch |", "|---|---|---:|---:|---:|---:|---:|"]
    for r in demand_status.itertuples():
        lines.append(f"| {r.plant_name} | {r.status} | {_fmt(r.today_demand_tonnes)} | {_fmt(r.opening_inventory_tonnes)} | {_fmt(r.target_inventory_tonnes)} | {_fmt(r.projected_closing_inventory_tonnes)} | {_fmt(r.today_dispatch_ordered_to_plant_tonnes)} |")

    for label, title in [("today", "Today's"), ("7d", "Next 7 days cumulative"), ("30d", "Next 30 days cumulative"), ("60d", "Full 60 days cumulative")]:
        lines += ["", f"## {title} source → demand allocation (tonnes)", ""]
        m = matrices[label]
        cols = list(m.columns)
        lines.append("| Supply node | " + " | ".join(cols) + " |")
        lines.append("|---|" + "|".join(["---:" for _ in cols]) + "|")
        for idx, row in m.iterrows():
            lines.append(f"| {idx} | " + " | ".join(_fmt(row[c]) for c in cols) + " |")

    lines += ["", "## Procurement / dispatch recommendation by horizon", "", "| Source | Today | Next 7d | Next 30d | Next 60d |", "|---|---:|---:|---:|---:|"]
    for r in summary.itertuples():
        lines.append(f"| {source_name.get(r.source, r.source)} | {r.tonnes_1d:,.0f} | {r.tonnes_7d:,.0f} | {r.tonnes_30d:,.0f} | {getattr(r, f'tonnes_{H}d'):,.0f} |")

    lines += ["", "## Today's route transportation cost matrix — ₹/tonne", ""]
    rc_cols = list(route_cost_matrix.columns)
    lines.append("| Supply node | " + " | ".join(rc_cols) + " |")
    lines.append("|---|" + "|".join(["---:" for _ in rc_cols]) + "|")
    for idx, row in route_cost_matrix.iterrows():
        lines.append(f"| {idx} | " + " | ".join(f"₹{float(row[c]):,.0f}" for c in rc_cols) + " |")

    lines += ["", "## Today's selected-route cost review", "", "| Route | Allocated | Base cost ₹/t | Delay | Effective modeled cost ₹/t | Cost contribution |", "|---|---:|---:|---:|---:|---:|"]
    for r in today_route_cost.sort_values("modeled_transport_cost", ascending=False).itertuples():
        lines.append(f"| {source_name.get(r.source, r.source)} → {plant_name.get(r.plant, r.plant)} | {_fmt(r.allocated_tonnes)} | ₹{r.cost:,.0f} | {r.delay_hours:.1f} h | ₹{r.effective_modeled_cost_per_tonne:,.2f} | ₹{r.modeled_transport_cost:,.0f} |")
    lines.append(f"**Today's modeled transportation cost:** ₹{today_route_cost['modeled_transport_cost'].sum():,.0f}")

    if news_items:
        lines += ["", "## News triggers"] + [f"- {item.title} — {item.url}" for item in news_items[:8]]
    else:
        lines += ["", "## News triggers", "- No matching disruption articles were retrieved in this run."]

    lines += [
        "", "## Decision rule",
        "The 1/7/30/60-day tables come from one 60-day demand-fulfillment optimization. Execute only today's dispatch, then re-solve the remaining horizon with refreshed weather, news and edited scenario inputs.",
        "", "## Attached operational files",
        "- allocation_matrix_today.csv / allocation_matrix_7d.csv / allocation_matrix_30d.csv / allocation_matrix_60d.csv",
        "- horizon_demand_coverage.csv", "- input_demand_60d.csv", "- input_supply_60d.csv", "- input_route_cost_60d.csv",
        "- supply_node_status.csv", "- demand_node_status.csv", "- allocation_explanations_today.csv", "- procurement_summary.csv", "- inventory_plan.csv", "- route_delay.csv", "- today_route_cost_breakdown.csv", "- audit_latest.md",
        "", "## Model caveat",
        "Bundled network values are illustrative. Dashboard edits become the active planning assumptions until reset or replaced.",
    ]

    (out / "daily_brief.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
