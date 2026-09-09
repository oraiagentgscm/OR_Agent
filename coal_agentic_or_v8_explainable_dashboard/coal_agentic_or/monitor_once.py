import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
load_dotenv(ROOT / ".env")

from coal_agent import load_config
from coal_agent.monitor import HourlyDisruptionMonitor, load_monitoring_config

if __name__ == "__main__":
    network = load_config(ROOT / "config" / "network.yaml")
    monitoring = load_monitoring_config(ROOT / "config" / "monitoring.yaml")
    result = HourlyDisruptionMonitor(network, monitoring, ROOT).check()
    print(result)
