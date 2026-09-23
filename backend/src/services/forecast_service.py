"""
forecast_service.py - True 8-Hour Sequential Forward Risk Forecasting Engine
SIH Problem Statement ID: 260001 - Landscape Disaster Risk Detection

Mandate:
Build a proper short-term forecasting path using the genuine 8-hour hourly forecast sequence
from Open-Meteo NWP (hourly precipitation, hourly soil moisture, temperature evolution)
combined with terrain elevation, slope, and satellite indices.

Evaluates the trained model across each hourly state to compute:
- Hourly risk trajectory (+1h to +8h)
- Peak risk hour and intensity
- Actionable lead time to hazard threshold
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timezone

from .feature_service import MODEL_FEATURE_COLUMNS


class ForecastService:
    """
    Evaluates multi-hour forward environmental risk by sequentially propagating
    hourly meteorological forecasts through the calibrated XGBoost model.
    """

    def __init__(self, model_engine: Any):
        self.model_engine = model_engine

    def generate_8h_forecast(
        self,
        base_features_df: pd.DataFrame,
        weather_telemetry: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Computes 8 hourly risk evaluations for T+1 through T+8.
        """
        hourly_precip = weather_telemetry.get("hourly_precipitation_8h", [1.0] * 8)
        hourly_sm = weather_telemetry.get("hourly_soil_moisture_8h", [0.45] * 8)
        hourly_temp = weather_telemetry.get("hourly_temperature_8h", [25.0] * 8)

        # Pad to at least 8 elements if necessary
        while len(hourly_precip) < 8:
            hourly_precip.append(0.0)
        while len(hourly_sm) < 8:
            hourly_sm.append(0.40)
        while len(hourly_temp) < 8:
            hourly_temp.append(25.0)

        base_row = base_features_df.iloc[0].to_dict()
        current_rain = float(base_row.get("rainfall_24h", 0.0))
        current_river = float(base_row.get("river_level", 2.0))

        hourly_trajectory: List[Dict[str, Any]] = []
        cum_rain = 0.0

        for h in range(1, 9):
            idx = h - 1
            rain_h = float(hourly_precip[idx])
            cum_rain += rain_h
            sm_h = float(hourly_sm[idx])
            temp_h = float(hourly_temp[idx])

            # Forward window rainfall (next 6h from this step)
            fwd_precip_slice = hourly_precip[idx: idx + 6]
            fwd_rain_6h = float(sum(fwd_precip_slice)) if fwd_precip_slice else 0.0

            # Fluvial river level response: hydrograph accumulation delay
            evolved_river = current_river + (cum_rain * 0.035)
            evolved_river = float(np.clip(evolved_river, 0.8, 12.5))

            # Construct hour h feature vector
            h_features = dict(base_row)
            h_features["rainfall_24h"] = round(current_rain + cum_rain, 2)
            h_features["forecast_rainfall_6h"] = round(fwd_rain_6h, 2)
            h_features["soil_saturation"] = round(float(np.clip(sm_h, 0.05, 0.98)), 3)
            h_features["temperature"] = round(temp_h, 1)
            h_features["river_level"] = round(evolved_river, 2)

            h_df = pd.DataFrame([h_features], columns=MODEL_FEATURE_COLUMNS)

            # Evaluate probability from calibrated model
            prob_h = self.model_engine.predict_calibrated_probability(h_df)
            risk_pct_h = round(prob_h * 100.0, 1)

            if risk_pct_h < 30.0:
                cat_h = "LOW"
            elif risk_pct_h < 60.0:
                cat_h = "MODERATE"
            elif risk_pct_h < 85.0:
                cat_h = "HIGH"
            else:
                cat_h = "CRITICAL"

            hourly_trajectory.append({
                "forecast_hour": h,
                "label": f"+{h}h",
                "risk_percentage": risk_pct_h,
                "risk_category": cat_h,
                "hourly_rainfall_mm": round(rain_h, 2),
                "cumulative_rainfall_mm": round(cum_rain, 2),
                "soil_saturation": round(sm_h, 3),
                "estimated_river_level_m": round(evolved_river, 2),
            })

        # Calculate peak risk hour and lead time
        risks = [step["risk_percentage"] for step in hourly_trajectory]
        peak_idx = int(np.argmax(risks))
        peak_hour = peak_idx + 1
        peak_risk = risks[peak_idx]

        # Lead time: first hour crossing into HIGH risk (>=60.0%)
        lead_time = None
        for step in hourly_trajectory:
            if step["risk_percentage"] >= 60.0:
                lead_time = float(step["forecast_hour"])
                break

        current_risk = float(risks[0])
        forecast_8h_risk = float(risks[-1])

        if forecast_8h_risk >= current_risk + 8.0:
            trend = "SURGING_ESCALATION"
        elif forecast_8h_risk <= current_risk - 8.0:
            trend = "SUBSIDING_DRAINAGE"
        else:
            trend = "STEADY_EQUILIBRIUM"

        forecast_seq = [
            {
                "hour_offset": step["forecast_hour"],
                "predicted_risk_pct": step["risk_percentage"],
                "risk_category": step["risk_category"],
                "hourly_precipitation_mm": step["hourly_rainfall_mm"],
                "soil_saturation": step["soil_saturation"],
            }
            for step in hourly_trajectory
        ]

        return {
            "forecast_window_hours": 8,
            "current_risk": current_risk,
            "current_risk_percentage": current_risk,
            "forecast_risk_8h": forecast_8h_risk,
            "forecast_8h_risk_percentage": forecast_8h_risk,
            "peak_risk": peak_risk,
            "peak_risk_percentage": peak_risk,
            "peak_hour": peak_hour,
            "peak_risk_hour": peak_hour,
            "lead_time_hours": lead_time or 4.0,
            "lead_time_to_critical_hours": lead_time,
            "risk_trend": trend,
            "trend": trend,
            "early_warning_active": lead_time is not None or peak_risk >= 60.0,
            "hourly_trajectory": hourly_trajectory,
            "forecast_sequence": forecast_seq,
            "meteorological_driver": (
                f"Driven by {round(cum_rain, 1)} mm cumulative precipitation forecast "
                f"over 8 hours across local terrain gradient."
            ),
        }
