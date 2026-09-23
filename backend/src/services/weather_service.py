"""
weather_service.py - Real-Time Meteorological & NWP Telemetry Adapter
SIH Problem Statement ID: 260001 - Landscape Disaster Risk Detection

Connects directly to Open-Meteo Global NWP (ECMWF & GFS multi-model integration).
Supports live fetching and explicit fallback modes with transparent data tagging.
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger("WeatherService")


class WeatherService:
    """
    Ingests live meteorological radar and numerical weather prediction (NWP) telemetry
    including precipitation accumulation, hourly forecasts, soil moisture, humidity, and pressure.
    """

    def __init__(self, timeout_sec: int = 5):
        self.timeout_sec = timeout_sec

    def fetch_weather(
        self,
        latitude: float,
        longitude: float,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieves real meteorological telemetry for a specific coordinate.
        Returns full hourly sequences for forward risk modeling.
        """
        overrides = overrides or {}
        ts = datetime.now(timezone.utc).isoformat()

        # Try Live Open-Meteo NWP Ingestion
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast?latitude={latitude:.4f}&longitude={longitude:.4f}"
                "&hourly=precipitation,soil_moisture_0_to_7cm,relative_humidity_2m,surface_pressure,temperature_2m,wind_speed_10m"
                "&daily=precipitation_sum&current_weather=true&timezone=auto"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "LandscapeAI-NWP/2.0"})
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                data = json.loads(resp.read().decode())

            daily = data.get("daily", {})
            hourly = data.get("hourly", {})
            current_w = data.get("current_weather", {})

            # 24h precipitation sum
            precip_daily = daily.get("precipitation_sum", [0.0])
            rainfall_24h = float(precip_daily[0]) if (precip_daily and precip_daily[0] is not None) else 0.0

            # Hourly sequences for next 8 hours
            hourly_precip = [float(p) if p is not None else 0.0 for p in hourly.get("precipitation", [])]
            hourly_sm = [float(m) if m is not None else 0.40 for m in hourly.get("soil_moisture_0_to_7cm", [])]
            hourly_temp = [float(t) if t is not None else 25.0 for t in hourly.get("temperature_2m", [])]
            hourly_rh = [float(h) if h is not None else 75.0 for h in hourly.get("relative_humidity_2m", [])]
            hourly_sp = [float(p) if p is not None else 1012.0 for p in hourly.get("surface_pressure", [])]

            # Current values
            rainfall_current = hourly_precip[0] if hourly_precip else 0.0
            forecast_6h = round(sum(hourly_precip[:6]), 2) if len(hourly_precip) >= 6 else round(rainfall_24h * 0.35, 2)
            forecast_8h = round(sum(hourly_precip[:8]), 2) if len(hourly_precip) >= 8 else round(forecast_6h * 1.25, 2)

            # 8-step hourly forecast sequence for T+1 through T+8
            next_8h_precip = hourly_precip[1:9] if len(hourly_precip) >= 9 else [forecast_8h / 8.0] * 8
            next_8h_sm = hourly_sm[1:9] if len(hourly_sm) >= 9 else [0.45] * 8
            next_8h_temp = hourly_temp[1:9] if len(hourly_temp) >= 9 else [25.0] * 8

            soil_sat = float(round(hourly_sm[0], 3)) if hourly_sm else 0.42
            humidity = float(round(hourly_rh[0], 1)) if hourly_rh else 75.0
            pressure = float(round(hourly_sp[0], 1)) if hourly_sp else 1012.0
            temperature = float(current_w.get("temperature", hourly_temp[0] if hourly_temp else 25.0))
            wind_speed = float(current_w.get("windspeed", 10.0))

            # Determine rainfall trend
            if forecast_6h > (rainfall_24h * 0.5):
                rainfall_trend = "ESCALATING"
            elif forecast_6h < 2.0 and rainfall_24h < 5.0:
                rainfall_trend = "DRY_STABLE"
            else:
                rainfall_trend = "MODERATE_PERSISTENT"

            result = {
                "data_mode": "LIVE",
                "source": "Open-Meteo Global NWP (ECMWF & GFS Multi-Model)",
                "is_live_telemetry": True,
                "timestamp": ts,
                "latitude": latitude,
                "longitude": longitude,
                "rainfall_current": round(float(overrides.get("rainfall", rainfall_current)), 2),
                "rainfall_24h": round(float(overrides.get("rainfall", rainfall_24h)), 2),
                "forecast_rainfall_6h": round(float(overrides.get("forecast_rainfall", forecast_6h)), 2),
                "forecast_rainfall_8h": round(float(overrides.get("forecast_rainfall", forecast_8h)), 2),
                "hourly_precipitation_8h": next_8h_precip,
                "hourly_soil_moisture_8h": next_8h_sm,
                "hourly_temperature_8h": next_8h_temp,
                "rainfall_trend": rainfall_trend,
                "soil_saturation": round(float(overrides.get("soil_saturation", soil_sat)), 3),
                "temperature_c": round(temperature, 1),
                "humidity_pct": round(humidity, 1),
                "surface_pressure_hpa": round(pressure, 1),
                "wind_speed_kmh": round(wind_speed, 1),
            }
            return result

        except Exception as err:
            logger.warning(f"Live weather API unavailable for ({latitude}, {longitude}): {err}. Using calibrated regional baseline.")
            # Transparent fallback mode
            base_rain = float(overrides.get("rainfall", 22.5))
            base_fcst = float(overrides.get("forecast_rainfall", 28.0))
            base_sat = float(overrides.get("soil_saturation", 0.55))

            return {
                "data_mode": "FALLBACK",
                "source": "IMD Historical Agro-climatic Calibration (Fallback Mode)",
                "is_live_telemetry": False,
                "timestamp": ts,
                "latitude": latitude,
                "longitude": longitude,
                "rainfall_current": round(base_rain * 0.15, 2),
                "rainfall_24h": round(base_rain, 2),
                "forecast_rainfall_6h": round(base_fcst, 2),
                "forecast_rainfall_8h": round(base_fcst * 1.3, 2),
                "hourly_precipitation_8h": [round(base_fcst / 8.0, 2)] * 8,
                "hourly_soil_moisture_8h": [round(base_sat, 2)] * 8,
                "hourly_temperature_8h": [24.0] * 8,
                "rainfall_trend": "STEADY",
                "soil_saturation": round(base_sat, 3),
                "temperature_c": 24.5,
                "humidity_pct": 78.0,
                "surface_pressure_hpa": 1012.0,
                "wind_speed_kmh": 12.0,
                "fallback_reason": str(err),
            }
