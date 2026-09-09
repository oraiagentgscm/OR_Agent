import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
load_dotenv(ROOT / ".env")

from coal_agent import load_config, DailyPlanningAgent

if __name__ == "__main__":
    cfg = load_config(ROOT / "config" / "network.yaml")
    result = DailyPlanningAgent(cfg).run(ROOT / "outputs", run_type="manual")
    print(result["meta"]["status"])
    print(f"Weather live: {result['meta']['weather_live_locations']}/{result['meta']['weather_total_locations']}")
    print(f"News connector connected: {result['meta']['news_fetch_ok']} | articles: {result['meta']['news_article_count']}")
    print(f"News risk: {result['meta']['news_risk']:.2f}")
    print(f"Corridor factor: {result['meta']['corridor_factor_day0']:.2f}")
    print(f"Max route delay: {result['meta']['max_route_delay_hours_day0']:.1f} h")
    print("Run folder:", result["output_dir"])
    print("Report:", result["output_dir"] / "daily_brief.md")
    print("Audit:", result["output_dir"] / "audit_latest.md")
