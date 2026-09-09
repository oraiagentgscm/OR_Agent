import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
load_dotenv(ROOT / ".env")

from coal_agent import load_config
from coal_agent.weather import WeatherTool
from coal_agent.news import NewsTool

if __name__ == "__main__":
    cfg = load_config(ROOT / "config" / "network.yaml")
    locs = cfg["sources"] + cfg["plants"]
    weather = WeatherTool().fetch(locs)
    live = [w for w in weather.values() if w.fetch_ok]
    print(f"WEATHER: {len(live)}/{len(weather)} locations connected")
    for loc_id, w in weather.items():
        print(
            f"  {loc_id}: source={w.source} live={w.fetch_ok} "
            f"rain24={w.rain_24h_mm:.1f}mm rain72={w.rain_72h_mm:.1f}mm "
            f"p24={w.max_precip_probability_24h:.0f}%"
        )
        if w.error:
            print("    error:", w.error)

    news, status = NewsTool().fetch_with_status()
    print(f"NEWS CONNECTOR: connected={status.fetch_ok} articles={status.article_count} source={status.source}")
    if status.error:
        print("  error:", status.error)
    if getattr(status, "details", ""):
        print("  details:", status.details)
    for item in news[:5]:
        print("  -", item.title)
        print("   ", item.url)
