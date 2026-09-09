\
from __future__ import annotations
from typing import Dict, List
from .weather import WeatherSignal
from .news import NewsItem

class RiskEngine:
    HIGH = {
        "washout": 1.0, "derailment": 1.0, "mine accident": 1.0,
        "track breach": 1.0, "landslide": 0.9, "flood": 0.9,
        "waterlogging": 0.8, "rake shortage": 0.8,
    }
    MED = {
        "heavy rain": 0.6, "very heavy rain": 0.7, "monsoon": 0.35,
        "congestion": 0.5, "strike": 0.7, "loading delay": 0.55,
        "unloading": 0.4, "wagon": 0.25, "rake": 0.25,
    }

    def news_risk(self, items: List[NewsItem]) -> float:
        if not items:
            return 0.0
        scores = []
        for item in items:
            text = item.title.lower()
            score = 0.0
            for k, v in self.HIGH.items():
                if k in text:
                    score = max(score, v)
            for k, v in self.MED.items():
                if k in text:
                    score = max(score, v)
            scores.append(score)
        # Multiple independent disruption headlines raise confidence, but cap at 1.
        return min(1.0, max(scores or [0.0]) + 0.05 * sum(s > 0 for s in scores))

    def weather_risk(self, w: WeatherSignal) -> float:
        # Transparent prototype scaling, not a trained probability.
        r = min(1.0, 0.004 * w.rain_24h_mm + 0.0015 * w.rain_72h_mm)
        r += 0.20 if w.max_precip_probability_24h >= 80 else 0.0
        r += 0.25 if w.severe_rain_flag else 0.0
        return min(1.0, r)

    def estimate_route_delay_hours(
        self,
        source_weather: WeatherSignal,
        plant_weather: WeatherSignal,
        news_risk: float,
        base_lead_days: float,
    ) -> float:
        wr = max(self.weather_risk(source_weather), self.weather_risk(plant_weather))
        # Heuristic: no disruption signal -> zero incremental delay.
        # Longer routes are somewhat more exposed when risk is present.
        exposure = 1.0 + 0.15 * max(0.0, base_lead_days - 1)
        delay = (24.0 * wr + 36.0 * news_risk) * exposure
        return round(min(72.0, delay), 1)

    def source_capacity_factor(self, w: WeatherSignal, news_risk: float) -> float:
        risk = max(self.weather_risk(w), news_risk * 0.6)
        return max(0.55, 1.0 - 0.35 * risk)

    def corridor_capacity_factor(self, all_weather: Dict[str, WeatherSignal], news_risk: float) -> float:
        weather = max((self.weather_risk(w) for w in all_weather.values()), default=0.0)
        risk = max(weather, news_risk)
        return max(0.50, 1.0 - 0.40 * risk)
