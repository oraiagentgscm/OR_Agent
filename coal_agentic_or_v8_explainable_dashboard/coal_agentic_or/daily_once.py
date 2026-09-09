import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
load_dotenv(ROOT / ".env")

from coal_agent import load_config, DailyPlanningAgent
from coal_agent.emailer import send_email

if __name__ == "__main__":
    cfg = load_config(ROOT / "config" / "network.yaml")
    result = DailyPlanningAgent(cfg).run(ROOT / "outputs", run_type="daily-08am")
    run_dir = result["output_dir"]
    report = (run_dir / "daily_brief.md").read_text(encoding="utf-8")
    mail = send_email(
        subject=f"Daily Coal OR Plan — {datetime.now(ZoneInfo('Asia/Kolkata')):%Y-%m-%d}",
        body=report,
        attachments=[
            run_dir / "daily_brief.md",
            run_dir / "audit_latest.md",
            run_dir / "procurement_summary.csv",
            run_dir / "inventory_plan.csv",
            run_dir / "route_delay.csv",
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
        ],
    )
    print("Run folder:", run_dir)
    print("Daily email:", mail)
