import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
load_dotenv(ROOT / ".env")

from coal_agent import load_config, DailyPlanningAgent
from coal_agent.monitor import HourlyDisruptionMonitor, load_monitoring_config
from coal_agent.emailer import send_email

NETWORK = load_config(ROOT / "config" / "network.yaml")
MONITORING = load_monitoring_config(ROOT / "config" / "monitoring.yaml")
TZ = MONITORING["schedule"].get("timezone", "Asia/Kolkata")


def daily_job():
    print("Starting 08:00 daily optimization...")
    result = DailyPlanningAgent(NETWORK).run(ROOT / "outputs", run_type="daily-08am")
    run_dir = result["output_dir"]
    report = (run_dir / "daily_brief.md").read_text(encoding="utf-8")
    attachments = [
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
    ]
    mail = send_email(
        subject=f"Daily Coal OR Plan — {datetime.now(ZoneInfo(TZ)):%Y-%m-%d}",
        body=report,
        attachments=attachments,
    )
    print(result["meta"])
    print("Daily email:", mail)


def hourly_job():
    print("Starting hourly disruption check...")
    monitor = HourlyDisruptionMonitor(NETWORK, MONITORING, ROOT)
    print(monitor.check())


if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone=TZ)
    scfg = MONITORING["schedule"]
    scheduler.add_job(
        daily_job,
        CronTrigger(
            hour=int(scfg.get("daily_report_hour", 8)),
            minute=int(scfg.get("daily_report_minute", 0)),
            timezone=TZ,
        ),
        id="daily_report",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        hourly_job,
        CronTrigger(minute=int(scfg.get("hourly_monitor_minute", 5)), timezone=TZ),
        id="hourly_monitor",
        max_instances=1,
        coalesce=True,
    )
    print(f"Scheduler active in {TZ}")
    print(f"- Daily report: {scfg.get('daily_report_hour', 8):02d}:{scfg.get('daily_report_minute', 0):02d}")
    print(f"- Hourly disruption check: minute {scfg.get('hourly_monitor_minute', 5):02d} of every hour")
    scheduler.start()
