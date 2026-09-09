from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
load_dotenv(ROOT / ".env")

from coal_agent import load_config, DailyPlanningAgent
from coal_agent.scenario import (
    load_active_scenario, save_active_scenario, reset_active_scenario,
    default_demand_schedule, default_supply_schedule, default_route_cost_schedule,
    active_paths,
)

TZ = ZoneInfo("Asia/Kolkata")
OUTPUTS = ROOT / "outputs"
CFG = load_config(ROOT / "config" / "network.yaml")
H = int(CFG["planning_horizon_days"])

st.set_page_config(page_title="Coal Allocation Control Tower", layout="wide")

st.markdown("""
<style>
    .stApp { background: #F4F7FB; }
    h1, h2, h3 { color: #12304A; }
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #D8E2EC;
        border-radius: 14px;
        padding: 12px 14px;
        box-shadow: 0 3px 10px rgba(18,48,74,0.06);
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #0B7A75 0%, #16A085 100%);
        color: white;
        border: 0;
        border-radius: 10px;
        font-weight: 700;
        padding: 0.65rem 1.2rem;
    }
    div.stButton > button[kind="secondary"] {
        border-radius: 10px;
        border: 1px solid #98AFC3;
        font-weight: 600;
    }
    .allocation-banner {
        background: linear-gradient(110deg, #12304A 0%, #1B5E74 100%);
        color: white;
        padding: 18px 22px;
        border-radius: 16px;
        margin: 4px 0 16px 0;
    }
    .allocation-banner h2 { color: white; margin: 0; }
    .allocation-banner p { margin: 5px 0 0 0; opacity: 0.9; }
</style>
""", unsafe_allow_html=True)

st.markdown(
    """<div class="allocation-banner">
    <h2>Coal Network Optimizer</h2>
    <p>60-day rolling-horizon allocation, disruption monitoring, scenario editing and decision explainability.</p>
    </div>""",
    unsafe_allow_html=True,
)


def newest_daily_run() -> Path | None:
    runs = OUTPUTS / "runs"
    if not runs.exists():
        return None
    candidates = sorted(
        [p for p in runs.iterdir() if p.is_dir() and p.name.endswith("_daily-08am")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def read_csv(path: Path):
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _wide(df, row_cols, col_col, value_col, ordered_cols):
    x = df.pivot_table(index=row_cols, columns=col_col, values=value_col, aggfunc="first").reset_index()
    for c in ordered_cols:
        if c not in x.columns:
            x[c] = 0.0
    return x[row_cols + ordered_cols]


def demand_to_wide(df):
    cols = [p["id"] for p in CFG["plants"]]
    return _wide(df, ["date"], "plant", "demand", cols)


def supply_to_wide(df):
    cols = [s["id"] for s in CFG["sources"]]
    return _wide(df, ["date"], "source", "capacity", cols)


def cost_to_wide(df):
    x = df.copy()
    x["route"] = x["source"] + "→" + x["plant"]
    cols = [f"{s['id']}→{p['id']}" for s in CFG["sources"] for p in CFG["plants"]]
    return _wide(x, ["date"], "route", "cost", cols)


def demand_from_wide(wide):
    ids = [p["id"] for p in CFG["plants"]]
    out = wide.melt(id_vars=["date"], value_vars=ids, var_name="plant", value_name="demand")
    out["demand"] = pd.to_numeric(out["demand"], errors="coerce").fillna(0).clip(lower=0)
    return out


def supply_from_wide(wide):
    ids = [s["id"] for s in CFG["sources"]]
    out = wide.melt(id_vars=["date"], value_vars=ids, var_name="source", value_name="capacity")
    out["capacity"] = pd.to_numeric(out["capacity"], errors="coerce").fillna(0).clip(lower=0)
    return out


def cost_from_wide(wide):
    routes = [f"{s['id']}→{p['id']}" for s in CFG["sources"] for p in CFG["plants"]]
    out = wide.melt(id_vars=["date"], value_vars=routes, var_name="route", value_name="cost")
    split = out["route"].str.split("→", expand=True)
    out["source"], out["plant"] = split[0], split[1]
    out["cost"] = pd.to_numeric(out["cost"], errors="coerce").fillna(0).clip(lower=0)
    return out[["date", "source", "plant", "cost"]]



def _style_allocation_table(df: pd.DataFrame):
    if df.empty:
        return df
    x = df.copy()
    if x.columns[0].startswith("Unnamed"):
        x = x.rename(columns={x.columns[0]: "Supply node"})
    numeric_cols = [c for c in x.columns if c != "Supply node"]
    for c in numeric_cols:
        x[c] = pd.to_numeric(x[c], errors="coerce").fillna(0.0)

    def cell_style(v):
        try:
            val = float(v)
        except Exception:
            return ""
        if val > 1e-6:
            return "background-color:#DDF5EC;color:#0B4F46;font-weight:700;"
        return "background-color:#F7F9FC;color:#7A8A99;"

    styler = x.style.format({c: "{:,.0f}" for c in numeric_cols})
    styler = styler.map(cell_style, subset=numeric_cols)
    return styler


def _show_explanation_cards(explain: pd.DataFrame):
    if explain.empty:
        st.info("No allocation-explanation file is available for this run.")
        return

    st.subheader("Why each plant is or is not allocated today")
    st.caption(
        "These explanations use the actual LP result, inventory cover, target stock, future dispatch timing, "
        "route cost/delay and the integrated 60-day network constraints."
    )

    rows = list(explain.to_dict("records"))
    for start in range(0, len(rows), 3):
        cols = st.columns(3)
        for col, item in zip(cols, rows[start:start + 3]):
            with col:
                with st.container(border=True):
                    allocated = float(item.get("today_dispatch_tonnes", 0) or 0)
                    decision = item.get("decision_today", "")
                    icon = "✅" if allocated > 1e-6 else "⏸️"
                    st.markdown(f"### {icon} {item.get('plant_name', item.get('plant', 'Plant'))}")
                    st.markdown(f"**{decision}**")
                    st.metric("Today's dispatch", f"{allocated:,.0f} t")
                    cover = item.get("opening_days_cover")
                    target = item.get("target_days")
                    if pd.notna(cover):
                        st.caption(f"Opening cover: {float(cover):.1f} d | Target: {float(target):.1f} d")
                    if item.get("selected_sources") not in (None, "", "—"):
                        st.caption(f"Selected source(s): {item.get('selected_sources')}")
                    st.write(item.get("reason", ""))


def show_run(run_dir: Path):
    meta = read_json(run_dir / "run_meta.json", {})
    audit = read_json(run_dir / "audit_latest.json", {})
    interp = audit.get("interpretation", {})
    news_conn = audit.get("news_connection", {})
    weather_conn = audit.get("weather_connection", {})

    # ---------- Allocation is intentionally the first and dominant view ----------
    st.markdown("## Allocation decision — primary view")
    st.caption(
        "The selected horizon is a cumulative slice of the same integrated 60-day solve. "
        "Today is the executable dispatch decision; later horizons show the forward plan."
    )
    horizon = st.segmented_control(
        "Allocation horizon",
        options=["Today", "7 days", "30 days", "60 days"],
        default="Today",
        key=f"alloc_{run_dir.name}",
    )
    file_map = {
        "Today": "allocation_matrix_today.csv",
        "7 days": "allocation_matrix_7d.csv",
        "30 days": "allocation_matrix_30d.csv",
        "60 days": "allocation_matrix_60d.csv",
    }
    alloc_df = read_csv(run_dir / file_map[horizon])
    st.dataframe(
        _style_allocation_table(alloc_df),
        use_container_width=True,
        hide_index=True,
        height=390,
    )
    st.caption(
        "Green cells are routes used by the optimizer; grey cells are zero-dispatch lanes for the selected horizon."
    )

    if horizon == "Today":
        _show_explanation_cards(read_csv(run_dir / "allocation_explanations_today.csv"))
    else:
        st.info("Plant-level decision explanations are shown for Today's executable allocation. Select Today to view them.")

    st.divider()

    # ---------- Secondary operational status placed below allocation ----------
    st.subheader("Network health and operating context")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Weather live", f"{weather_conn.get('connected_locations', 0)}/{weather_conn.get('total_locations', 0)}")
    c2.metric("News connector", "YES" if news_conn.get("fetch_ok") else "NO")
    c3.metric("News items", news_conn.get("article_count", 0))
    c4.metric("News risk", f"{float(interp.get('news_risk', 0)):.2f}")
    c5.metric("Corridor capacity", f"{100*float(interp.get('corridor_capacity_factor', 0)):.0f}%")
    c6.metric("Max route delay", f"{float(interp.get('max_route_delay_hours', 0)):.1f} h")

    st.info(
        f"Decision snapshot: {run_dir.name} | Status: {meta.get('status', 'See outputs')} | "
        f"60-day demand enforcement: {'ON' if meta.get('full_horizon_demand_enforced', False) else 'OFF'}"
    )

    coverage = read_csv(run_dir / "horizon_demand_coverage.csv")
    if not coverage.empty:
        st.markdown("**Demand-coverage check**")
        st.dataframe(coverage, use_container_width=True, hide_index=True)

    tabs = st.tabs([
        "Supply nodes", "Demand nodes", "Procurement", "Inventory",
        "Route delays", "Route costs", "Weather & news", "Inputs used",
    ])

    with tabs[0]:
        st.dataframe(read_csv(run_dir / "supply_node_status.csv"), use_container_width=True, hide_index=True)

    with tabs[1]:
        st.dataframe(read_csv(run_dir / "demand_node_status.csv"), use_container_width=True, hide_index=True)

    with tabs[2]:
        st.dataframe(read_csv(run_dir / "procurement_summary.csv"), use_container_width=True, hide_index=True)

    with tabs[3]:
        st.dataframe(read_csv(run_dir / "inventory_plan.csv"), use_container_width=True, hide_index=True)

    with tabs[4]:
        df = read_csv(run_dir / "route_delay.csv")
        if not df.empty:
            selected_day = st.slider("Route-delay day", 0, H - 1, 0, key=f"delay_{run_dir.name}")
            st.dataframe(
                df[df["day"] == selected_day].sort_values("delay_hours", ascending=False),
                use_container_width=True,
                hide_index=True,
            )

    with tabs[5]:
        st.markdown("**Today's route-cost matrix**")
        st.dataframe(read_csv(run_dir / "route_cost_matrix.csv"), use_container_width=True, hide_index=True)
        st.markdown("**Today's selected-route cost contribution**")
        st.dataframe(read_csv(run_dir / "today_route_cost_breakdown.csv"), use_container_width=True, hide_index=True)
        st.markdown("**Complete 60-day route-cost schedule used by the optimizer**")
        st.dataframe(read_csv(run_dir / "input_route_cost_60d.csv"), use_container_width=True, hide_index=True)

    with tabs[6]:
        weather = pd.DataFrame(audit.get("weather", []))
        if not weather.empty:
            st.markdown("**Weather observations**")
            st.dataframe(weather, use_container_width=True, hide_index=True)
        st.markdown("**Latest disruption news**")
        news = audit.get("news", [])
        if news:
            for item in news[:15]:
                provider = item.get("provider", "")
                title = item.get("title", "Untitled")
                url = item.get("url", "")
                source = item.get("domain", "")
                if url:
                    st.markdown(f"- [{title}]({url}) — {source} {f'({provider})' if provider else ''}")
                else:
                    st.write(f"- {title} — {source}")
        else:
            st.write("No matching disruption articles were returned in this run.")

    with tabs[7]:
        st.markdown("These are the exact 60-day assumptions used for this optimization run.")
        st.markdown("**Demand**")
        st.dataframe(read_csv(run_dir / "input_demand_60d.csv"), use_container_width=True, hide_index=True)
        st.markdown("**Supply capacity**")
        st.dataframe(read_csv(run_dir / "input_supply_60d.csv"), use_container_width=True, hide_index=True)
        st.markdown("**Route cost**")
        st.dataframe(read_csv(run_dir / "input_route_cost_60d.csv"), use_container_width=True, hide_index=True)


# ----------------------- Editable 60-day planning assumptions -----------------------
st.header("60-day planning input editor")
st.write(
    "Edit daily demand at all 6 demand nodes, daily available supply at all 4 supply nodes, "
    "and transportation cost on all 24 routes for each of the next 60 days. Saved values become the active scenario for dashboard, 08:00 and disruption-triggered runs."
)

active_d, active_s, active_c = load_active_scenario(CFG, H)
paths = active_paths(CFG)
active_exists = any(p.exists() for p in paths.values())
st.caption(f"Active scenario: {'CUSTOM SAVED INPUTS' if active_exists else 'BASELINE GENERATED INPUTS'}")

editor_tabs = st.tabs(["Demand — 60 days", "Supply — 60 days", "Transport cost — 60 days"])
with editor_tabs[0]:
    st.caption("Rows are dates; P1–P6 are tonnes/day demanded at each plant.")
    demand_wide = st.data_editor(
        demand_to_wide(active_d), use_container_width=True, hide_index=True,
        disabled=["date"], num_rows="fixed", key="demand_editor",
    )
with editor_tabs[1]:
    st.caption("Rows are dates; S1–S4 are pre-disruption source capacities in tonnes/day. Live risk factors are applied on top of these values.")
    supply_wide = st.data_editor(
        supply_to_wide(active_s), use_container_width=True, hide_index=True,
        disabled=["date"], num_rows="fixed", key="supply_editor",
    )
with editor_tabs[2]:
    st.caption("Rows are dates; each Sx→Py column is the transportation cost in ₹/tonne for that route on that day.")
    cost_wide = st.data_editor(
        cost_to_wide(active_c), use_container_width=True, hide_index=True,
        disabled=["date"], num_rows="fixed", key="cost_editor",
    )

b1, b2, b3 = st.columns([1, 1.4, 1])
with b1:
    save_only = st.button("Save active scenario")
with b2:
    save_run = st.button("Save + Run Live Network Reassessment", type="primary")
with b3:
    reset = st.button("Reset to baseline")

if reset:
    reset_active_scenario(CFG)
    st.success("Active custom scenario removed. Future runs will use baseline generated inputs until you save new edits.")
    st.rerun()

if save_only or save_run:
    d_long = demand_from_wide(demand_wide)
    s_long = supply_from_wide(supply_wide)
    c_long = cost_from_wide(cost_wide)
    save_active_scenario(CFG, d_long, s_long, c_long)
    st.success("Active 60-day demand, supply and transportation-cost scenario saved.")
    if save_run:
        with st.spinner("Refreshing disruption signals, rebuilding network constraints, and recalculating the 60-day allocation plan..."):
            result = DailyPlanningAgent(CFG).run(OUTPUTS, run_type="dashboard-scenario-live")
        st.session_state["dashboard_live_run"] = str(result["output_dir"])
        st.session_state["dashboard_live_time"] = datetime.now(TZ).isoformat()
        st.success(f"Scenario optimized: {result['output_dir'].name}")

st.divider()
st.header("Planning results")
mode = st.radio("Data mode", ["Latest 08:00 daily snapshot", "Refresh live now"], horizontal=True)

if mode == "Latest 08:00 daily snapshot":
    run = newest_daily_run()
    if run is None:
        st.warning("No saved 08:00 run exists yet. Run `python daily_once.py` or use Refresh live now.")
    else:
        st.success(f"Loaded saved daily snapshot: {run.name}")
        show_run(run)
else:
    st.info("Run an on-demand network reassessment using the latest disruption signals and your saved 60-day scenario. Each check is preserved as a separate decision snapshot.")
    if st.button("Run Live Disruption Check & Recalculate Plan", type="primary", key="live_refresh_bottom"):
        with st.spinner("Checking current risk signals, updating capacities and lead times, and rebuilding the 60-day allocation decision..."):
            result = DailyPlanningAgent(CFG).run(OUTPUTS, run_type="dashboard-live")
        st.session_state["dashboard_live_run"] = str(result["output_dir"])
        st.session_state["dashboard_live_time"] = datetime.now(TZ).isoformat()

    live_path = st.session_state.get("dashboard_live_run")
    if live_path and Path(live_path).exists():
        st.success(f"Displaying latest on-demand decision snapshot: {Path(live_path).name}")
        show_run(Path(live_path))
    else:
        st.info("Run the live disruption check above to create an on-demand decision snapshot.")
