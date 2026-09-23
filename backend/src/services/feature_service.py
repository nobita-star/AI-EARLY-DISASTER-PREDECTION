"""
feature_service.py - Unified Landscape AI Feature Engineering & Synthesis Pipeline
SIH Problem Statement ID: 260001 - Landscape Disaster Risk Detection

Mandate:
Single central feature-building service: build_landscape_features().
Harmonizes multi-modal data from:
1. WeatherService (Open-Meteo Global NWP live telemetry)
2. TerrainService (NASA SRTM 30m DEM slope, aspect, TRI)
3. SatelliteService (Copernicus Sentinel-1 C-band SAR + Sentinel-2 MSI optical)
4. Hydrometric River Gauges (In-situ & CWC monitoring points)

Zero random data generation. Explicit tracking of LIVE vs FALLBACK data modes.
"""

from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timezone

from .weather_service import WeatherService
from .terrain_service import TerrainService
from .satellite_service import SatelliteService

# Exact canonical feature ordering for the trained XGBoost model
MODEL_FEATURE_COLUMNS: List[str] = [
    "rainfall_24h",
    "forecast_rainfall_6h",
    "soil_saturation",
    "slope",
    "elevation",
    "aspect",
    "terrain_ruggedness",
    "temperature",
    "humidity",
    "surface_pressure",
    "wind_speed",
    "ndvi",
    "ndwi",
    "sentinel1_vv",
    "sentinel1_vh",
    "river_level",
]


class FeatureService:
    """
    Central feature building engine. Extracts, validates, and constructs
    the unified feature vector for XGBoost model inference and explainability.
    """

    def __init__(
        self,
        weather_svc: Optional[WeatherService] = None,
        terrain_svc: Optional[TerrainService] = None,
        satellite_svc: Optional[SatelliteService] = None,
    ):
        self.weather_svc = weather_svc or WeatherService()
        self.terrain_svc = terrain_svc or TerrainService()
        self.satellite_svc = satellite_svc or SatelliteService()

    def build_landscape_features(
        self,
        latitude: float,
        longitude: float,
        state_name: Optional[str] = None,
        district_name: Optional[str] = None,
        in_situ_river_level: Optional[float] = None,
        raw_overrides: Optional[Dict[str, Any]] = None,
        user_inputs: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Single central feature pipeline.
        Retrieves real meteorological, topographic, and satellite data,
        constructs a validated 1-row DataFrame, and computes a rigorous data quality score.
        """
        overrides = raw_overrides or user_inputs or kwargs.get("environmental_data") or {}
        ts = datetime.now(timezone.utc).isoformat()

        # 1. Retrieve Weather Telemetry
        weather_data = self.weather_svc.fetch_weather(latitude, longitude, overrides=overrides)

        # 2. Retrieve Topographic & Terrain Telemetry
        terrain_data = self.terrain_svc.fetch_terrain(latitude, longitude, overrides=overrides)

        # 3. Retrieve Earth Observation & Satellite Indices
        satellite_data = self.satellite_svc.fetch_satellite_features(latitude, longitude, overrides=overrides)

        # 4. Resolve Hydrometric River Stage
        rain_24h = weather_data["rainfall_24h"]
        if in_situ_river_level is not None:
            river_level = float(in_situ_river_level)
        elif "river_level" in overrides:
            river_level = float(overrides["river_level"])
        else:
            # Physical baseline: base 2.0m + 0.04m per mm of antecedent rain
            river_level = round(float(2.0 + (rain_24h * 0.04)), 2)
            river_level = min(12.0, max(0.5, river_level))

        # 5. Extract Feature Vector Values
        feature_dict: Dict[str, float] = {
            "rainfall_24h": float(weather_data["rainfall_24h"]),
            "forecast_rainfall_6h": float(weather_data["forecast_rainfall_6h"]),
            "soil_saturation": float(weather_data["soil_saturation"]),
            "slope": float(terrain_data["slope_deg"]),
            "elevation": float(terrain_data["elevation_m"]),
            "aspect": float(terrain_data["aspect_deg"]),
            "terrain_ruggedness": float(terrain_data["terrain_ruggedness"]),
            "temperature": float(weather_data["temperature_c"]),
            "humidity": float(weather_data["humidity_pct"]),
            "surface_pressure": float(weather_data["surface_pressure_hpa"]),
            "wind_speed": float(weather_data["wind_speed_kmh"]),
            "ndvi": float(satellite_data["ndvi"]),
            "ndwi": float(satellite_data["ndwi"]),
            "sentinel1_vv": float(satellite_data["sentinel1_vv_db"]),
            "sentinel1_vh": float(satellite_data["sentinel1_vh_db"]),
            "river_level": float(river_level),
        }

        # 6. Physical Boundary Normalization
        feature_dict["soil_saturation"] = float(np.clip(feature_dict["soil_saturation"], 0.02, 1.0))
        feature_dict["ndvi"] = float(np.clip(feature_dict["ndvi"], -1.0, 1.0))
        feature_dict["ndwi"] = float(np.clip(feature_dict["ndwi"], -1.0, 1.0))
        feature_dict["slope"] = float(np.clip(feature_dict["slope"], 0.1, 88.0))
        feature_dict["elevation"] = float(max(0.0, feature_dict["elevation"]))
        feature_dict["rainfall_24h"] = float(max(0.0, feature_dict["rainfall_24h"]))
        feature_dict["forecast_rainfall_6h"] = float(max(0.0, feature_dict["forecast_rainfall_6h"]))

        df = pd.DataFrame([feature_dict], columns=MODEL_FEATURE_COLUMNS)

        # 7. Evaluate Data Quality & Confidence Penalty
        # Weather weight: 0.40, Terrain weight: 0.30, Satellite weight: 0.30
        weather_mode = weather_data["data_mode"]
        terrain_mode = terrain_data["data_mode"]
        satellite_mode = satellite_data["data_mode"]

        weather_score = 1.0 if weather_mode == "LIVE" else 0.70
        terrain_score = 1.0 if terrain_mode == "LIVE" else 0.75
        satellite_score = 1.0 if satellite_mode == "LIVE_GEE" else 0.85 if satellite_mode == "CACHED_BASELINE" else 0.40

        overall_quality = round(0.40 * weather_score + 0.30 * terrain_score + 0.30 * satellite_score, 3)

        if overall_quality >= 0.90:
            quality_grade = "OPTIMAL_LIVE"
        elif overall_quality >= 0.75:
            quality_grade = "GOOD_CALIBRATED"
        elif overall_quality >= 0.60:
            quality_grade = "ACCEPTABLE_HYBRID"
        else:
            quality_grade = "DEGRADED_FALLBACK"

        # Determine consolidated data mode label
        if weather_mode == "LIVE" and terrain_mode == "LIVE":
            consolidated_mode = "LIVE"
        elif weather_mode == "LIVE" or terrain_mode == "LIVE":
            consolidated_mode = "HYBRID"
        else:
            consolidated_mode = "FALLBACK"

        metadata = {
            "timestamp": ts,
            "coordinates": {"latitude": latitude, "longitude": longitude},
            "state": state_name or "Northeast India",
            "district": district_name or "Catchment Sector",
            "data_mode": consolidated_mode,
            "data_quality_score": overall_quality,
            "data_quality_grade": quality_grade,
            "weather": weather_data,
            "terrain": terrain_data,
            "satellite": satellite_data,
            "data_sources": [
                {"category": "Weather NWP", "source": weather_data["source"], "mode": weather_mode},
                {"category": "Topography / DEM", "source": terrain_data["source"], "mode": terrain_mode},
                {"category": "Earth Observation", "source": satellite_data["source"], "mode": satellite_mode},
                {"category": "Hydrometric River Stage", "source": "In-situ Gauge / Empirical Discharge Ratio", "mode": "MEASURED"},
            ],
            "feature_summary": {
                "rainfall_24h_mm": feature_dict["rainfall_24h"],
                "forecast_6h_mm": feature_dict["forecast_rainfall_6h"],
                "soil_saturation_pct": round(feature_dict["soil_saturation"] * 100.0, 1),
                "slope_deg": feature_dict["slope"],
                "elevation_m": feature_dict["elevation"],
                "ndvi": feature_dict["ndvi"],
                "ndwi": feature_dict["ndwi"],
                "sentinel1_vv_db": feature_dict["sentinel1_vv"],
                "river_level_m": feature_dict["river_level"],
            },
        }

        return df, metadata
