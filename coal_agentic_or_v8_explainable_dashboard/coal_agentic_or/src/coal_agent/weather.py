from __future__ import annotations
import requests
from dataclasses import dataclass, asdict
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, List


@dataclass
class WeatherSignal:
    location_id: str
    rain_24h_mm: float = 0.0
    rain_72h_mm: float = 0.0
    max_precip_probability_24h: float = 0.0
    severe_rain_flag: int = 0
    source: str = "fallback"
    fetch_ok: bool = False
    fetched_at: str = ""
    error: str = ""

    def to_dict(self):
        return asdict(self)


class WeatherTool:
    URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, timeout=15):
        self.timeout = timeout

    def fetch(self, locations: List[dict]) -> Dict[str, WeatherSignal]:
        out = {}
        now = datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()
        for loc in locations:
            try:
                params = {
                    "latitude": loc["lat"],
                    "longitude": loc["lon"],
                    "hourly": "precipitation,precipitation_probability",
                    "forecast_days": 7,
                    "timezone": "Asia/Kolkata",
                }
                r = requests.get(self.URL, params=params, timeout=self.timeout)
                r.raise_for_status()
                data = r.json()["hourly"]
                rain = [float(x or 0) for x in data.get("precipitation", [])]
                prob = [float(x or 0) for x in data.get("precipitation_probability", [])]
                r24 = sum(rain[:24])
                r72 = sum(rain[:72])
                p24 = max(prob[:24] or [0.0])
                severe = int(r24 >= 64.5 or r72 >= 150 or p24 >= 90)
                out[loc["id"]] = WeatherSignal(
                    location_id=loc["id"],
                    rain_24h_mm=round(r24, 2),
                    rain_72h_mm=round(r72, 2),
                    max_precip_probability_24h=round(p24, 1),
                    severe_rain_flag=severe,
                    source="open-meteo",
                    fetch_ok=True,
                    fetched_at=now,
                )
            except Exception as exc:
                out[loc["id"]] = WeatherSignal(
                    location_id=loc["id"],
                    source="fallback",
                    fetch_ok=False,
                    fetched_at=now,
                    error=f"{type(exc).__name__}: {exc}",
                )
        return out
