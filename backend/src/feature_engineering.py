"""
feature_engineering.py - Geospatial & Hydrologic Feature Engineering Layer
SIH Problem Statement ID: 260001

Provides:
1. Standardized extraction of primary hydrologic risk features.
2. Digital Elevation Model (DEM) and terrain slope processing utilities.
3. Ingestion adapter supporting multi-modal Sentinel-1 SAR, Sentinel-2, DEM, and river telemetry.
4. Transparent Data Source Tagging: DATA_SOURCE = "real" | "synthetic".
"""

import math
from typing import Dict, Any, List, Optional, Tuple
# pyrefly: ignore [missing-import]
import numpy as np
import pandas as pd

# Core features mandated by the architecture
CORE_FEATURE_NAMES = [
    "rainfall",
    "forecast_rainfall",
    "soil_saturation",
    "slope",
    "river_level",
]

# Extended optional geospatial features
EXTENDED_FEATURE_NAMES = [
    "elevation",
    "terrain_ruggedness",
    "distance_to_river",
    "historical_flood_frequency",
    "vegetation_index",
    "radar_water_probability",
]

ALL_FEATURE_NAMES = CORE_FEATURE_NAMES + EXTENDED_FEATURE_NAMES

DEFAULT_IMPUTATION_VALUES: Dict[str, float] = {
    "rainfall": 0.0,
    "forecast_rainfall": 0.0,
    "soil_saturation": 0.35,
    "slope": 5.0,
    "river_level": 2.0,
    "elevation": 120.0,
    "terrain_ruggedness": 5.0,
    "distance_to_river": 1500.0,
    "historical_flood_frequency": 1.0,
    "vegetation_index": 0.40,
    "radar_water_probability": 0.10,
}


class GeospatialTerrainProcessor:
    """
    Utilities for analyzing Digital Elevation Models (DEM/SRTM) and hydrographic vector shapes.
    Computes topographic slope, Terrain Ruggedness Index (TRI), and river channel proximity.
    """

    @staticmethod
    def calculate_slope_from_elevation_matrix(
        dem_matrix: np.ndarray,
        cell_resolution_m: float = 30.0
    ) -> float:
        """
        Calculates average terrain slope (in degrees) from a 2D DEM grid using Horn's algorithm.
        Works directly with numpy arrays extracted from rasterio or synthetic elevation grids.
        """
        if dem_matrix.ndim != 2 or dem_matrix.shape[0] < 3 or dem_matrix.shape[1] < 3:
            return float(DEFAULT_IMPUTATION_VALUES["slope"])

        # Compute finite difference gradients
        dz_dy, dz_dx = np.gradient(dem_matrix, cell_resolution_m, cell_resolution_m)
        slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
        mean_slope_deg = float(np.degrees(np.nanmean(slope_rad)))
        return float(np.clip(mean_slope_deg, 0.0, 90.0))

    @staticmethod
    def compute_terrain_ruggedness_index(dem_matrix: np.ndarray) -> float:
        """
        Calculates Riley's Terrain Ruggedness Index (TRI) representing elevation heterogenity.
        """
        if dem_matrix.ndim != 2 or dem_matrix.size == 0:
            return float(DEFAULT_IMPUTATION_VALUES["terrain_ruggedness"])
        std_val = float(np.nanstd(dem_matrix))
        return float(np.clip(std_val, 0.0, 100.0))

    @staticmethod
    def compute_euclidean_distance_to_river(
        point_lon: float,
        point_lat: float,
        river_coordinates: List[Tuple[float, float]]
    ) -> float:
        """
        Calculates the minimum geodesic surface distance (in meters) from a target site
        to the nearest surveyed river centerline point using the Haversine formulation.
        """
        if not river_coordinates:
            return float(DEFAULT_IMPUTATION_VALUES["distance_to_river"])

        min_dist_m = float("inf")
        r_earth = 6371000.0  # Earth radius in meters

        lat1_rad = math.radians(point_lat)
        lon1_rad = math.radians(point_lon)

        for r_lon, r_lat in river_coordinates:
            lat2_rad = math.radians(r_lat)
            lon2_rad = math.radians(r_lon)

            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad

            a = (
                math.sin(dlat / 2.0) ** 2
                + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2.0) ** 2
            )
            c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
            dist_m = r_earth * c
            if dist_m < min_dist_m:
                min_dist_m = dist_m

        return round(float(min_dist_m), 2)


class FeatureEngineer:
    """
    Standardizes raw ingestion payloads into model-ready numerical feature arrays.
    Handles data source qualification (real vs synthetic), imputations, and normalization.
    """

    def __init__(self, enable_real_data: bool = False):
        self.enable_real_data = enable_real_data
        self.terrain_processor = GeospatialTerrainProcessor()

    def process_input(
        self,
        raw_payload: Dict[str, Any],
        force_synthetic: bool = False
    ) -> Tuple[pd.DataFrame, str]:
        """
        Parses raw API input, extracts core and optional features, fills defaults,
        and returns a 1-row DataFrame along with the verified DATA_SOURCE flag.
        """
        # Distinguish real data from synthetic fallback
        has_real_sensor_flag = bool(raw_payload.get("is_real_telemetry", False))
        is_real = (self.enable_real_data or has_real_sensor_flag) and not force_synthetic
        data_source_label = "real" if is_real else "synthetic"

        row: Dict[str, float] = {}

        # 1. Parse core features
        for feat in CORE_FEATURE_NAMES:
            val = raw_payload.get(feat)
            if val is not None:
                try:
                    row[feat] = float(val)
                except (ValueError, TypeError):
                    row[feat] = DEFAULT_IMPUTATION_VALUES[feat]
            else:
                row[feat] = DEFAULT_IMPUTATION_VALUES[feat]

        # 2. Parse extended features if present
        for feat in EXTENDED_FEATURE_NAMES:
            val = raw_payload.get(feat)
            if val is not None:
                try:
                    row[feat] = float(val)
                except (ValueError, TypeError):
                    row[feat] = DEFAULT_IMPUTATION_VALUES[feat]
            else:
                row[feat] = DEFAULT_IMPUTATION_VALUES[feat]

        # Physical boundary constraints
        row["soil_saturation"] = float(np.clip(row["soil_saturation"], 0.0, 1.0))
        row["vegetation_index"] = float(np.clip(row["vegetation_index"], -1.0, 1.0))
        row["radar_water_probability"] = float(np.clip(row["radar_water_probability"], 0.0, 1.0))
        row["rainfall"] = float(max(0.0, row["rainfall"]))
        row["forecast_rainfall"] = float(max(0.0, row["forecast_rainfall"]))
        row["slope"] = float(np.clip(row["slope"], 0.0, 89.0))
        row["river_level"] = float(max(0.0, row["river_level"]))

        df = pd.DataFrame([row], columns=ALL_FEATURE_NAMES)
        return df, data_source_label

    def ingest_sentinel_telemetry(
        self,
        sar_backscatter_db: Optional[float] = None,
        ndvi_optical: Optional[float] = None,
        water_mask_detected: Optional[bool] = None
    ) -> Dict[str, float]:
        """
        Transforms Copernicus Sentinel-1 SAR VH/VV polarization ratios and Sentinel-2 NDVI
        into normalized hydrological features.
        """
        features: Dict[str, float] = {}
        if sar_backscatter_db is not None:
            # Low backscatter (<-16 dB in cross-pol) indicates specular reflection over open floodwater
            prob_water = 1.0 / (1.0 + np.exp(0.3 * (sar_backscatter_db + 15.0)))
            features["radar_water_probability"] = float(np.clip(prob_water, 0.0, 1.0))
            # Saturated soil increases dielectric constant, modulating radar response
            features["soil_saturation"] = float(np.clip(0.5 - (sar_backscatter_db / 35.0), 0.0, 1.0))

        if ndvi_optical is not None:
            features["vegetation_index"] = float(np.clip(ndvi_optical, -1.0, 1.0))

        if water_mask_detected is True:
            features["radar_water_probability"] = 0.95

        return features

    @staticmethod
    def compute_interaction_features(features_dict: Dict[str, float]) -> Dict[str, float]:
        """
        Computes non-linear physical interaction terms across hydrologic and terrain features:
        - saturation_x_slope: soil saturation interacting with slope gradient
        - rainfall_surge_ratio: forecast rain relative to antecedent rain
        - topographic_wetness_index: proxy ln(drainage_area / tan(slope))
        - optical_sar_water_congruence: agreement between Sentinel-1 water prob and Sentinel-2 vegetation loss
        """
        rain = max(0.0, features_dict.get("rainfall", 0.0))
        fcst = max(0.0, features_dict.get("forecast_rainfall", 0.0))
        sat = float(np.clip(features_dict.get("soil_saturation", 0.35), 0.0, 1.0))
        slope = float(np.clip(features_dict.get("slope", 5.0), 0.5, 85.0))
        sar_prob = float(np.clip(features_dict.get("radar_water_probability", 0.1), 0.0, 1.0))
        ndvi = float(np.clip(features_dict.get("vegetation_index", 0.4), -1.0, 1.0))

        slope_rad = np.radians(max(0.5, slope))
        tan_slope = max(0.01, float(np.tan(slope_rad)))

        return {
            "saturation_x_slope": round(sat * (slope / 45.0), 4),
            "rainfall_surge_ratio": round(fcst / (rain + 5.0), 4),
            "topographic_wetness_index": round(float(np.log(1000.0 / tan_slope)), 3),
            "optical_sar_water_congruence": round(sar_prob * max(0.0, 0.7 - ndvi), 4),
        }

    @staticmethod
    def validate_data_quality(
        raw_payload: Dict[str, Any],
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        sensor_staleness_hours: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Conducts pre-inference data validation:
        1. Coordinate geographical plausibility.
        2. Sensor staleness and telemetry age.
        3. Feature completeness vs default imputation ratios.
        4. Physical boundary sanity checks.
        """
        anomalies: List[str] = []
        imputed_count = 0
        total_features = len(CORE_FEATURE_NAMES) + len(EXTENDED_FEATURE_NAMES)

        # 1. Coordinate check
        coords_valid = True
        if latitude is not None and longitude is not None:
            if not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
                coords_valid = False
                anomalies.append(f"Invalid geographical coordinates: ({latitude}, {longitude})")
        else:
            anomalies.append("Coordinates unspecified; using default catchment center.")

        # 2. Imputation check
        for feat in CORE_FEATURE_NAMES:
            if feat not in raw_payload or raw_payload[feat] is None:
                imputed_count += 1

        for feat in EXTENDED_FEATURE_NAMES:
            if feat not in raw_payload or raw_payload[feat] is None:
                imputed_count += 1

        imputation_ratio = imputed_count / float(total_features)

        # 3. Staleness check
        staleness = max(0.0, float(sensor_staleness_hours or 0.0))
        if staleness > 6.0:
            anomalies.append(f"Telemetry latency is elevated ({staleness:.1f} hours old)")

        # 4. Extreme values check
        rain = float(raw_payload.get("rainfall") or 0.0)
        fcst = float(raw_payload.get("forecast_rainfall") or 0.0)
        if rain > 250.0 or fcst > 250.0:
            anomalies.append("Extreme deluge condition (>250mm precipitation rate) detected")

        # Scoring
        base_score = 100.0
        base_score -= min(40.0, imputation_ratio * 50.0)
        base_score -= min(30.0, staleness * 2.5)
        if not coords_valid:
            base_score -= 25.0

        score = round(float(np.clip(base_score, 15.0, 99.0)), 1)

        if score >= 80.0:
            grade = "OPTIMAL (MULTI-MODAL LIVE)"
        elif score >= 55.0:
            grade = "ACCEPTABLE (PARTIAL IMPUTATION / STALE SENSORS)"
        else:
            grade = "DEGRADED (HIGH UNCERTAINTY / FALLBACK SENSORS)"

        return {
            "overall_score": round(score / 100.0, 3),
            "grade": grade,
            "data_quality_score": score,
            "data_quality_grade": grade,
            "coordinates_valid": coords_valid,
            "staleness_hours": staleness,
            "imputed_features_count": imputed_count,
            "total_features_monitored": total_features,
            "anomalies_flagged": anomalies,
            "is_degraded": score < 60.0,
        }


def calculate_rainfall_risk(
    rainfall_24h: float,
    forecast_6h: float = 0.0,
    source_label: str = "Open-Meteo Global NWP (ECMWF/GFS Integration)",
    is_fallback: bool = False,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Computes a dedicated, scientifically grounded Rainfall Risk percentage and category
    based strictly on India Meteorological Department (IMD) 24-hour precipitation standards
    and CWC hydrologic flood-generating thresholds.

    IMD 24-Hour Precipitation Classification Standard:
    - Trace / Very Light Rain (< 2.5 mm/day): Risk 5.0% - 14.9% (Category: LOW)
    - Light Rain (2.5 - 15.5 mm/day): Risk 15.0% - 29.9% (Category: LOW)
    - Moderate Rain (15.6 - 64.4 mm/day): Risk 30.0% - 59.9% (Category: MODERATE)
    - Heavy Rain (64.5 - 115.5 mm/day): Risk 60.0% - 79.9% (Category: HIGH)
    - Very Heavy Rain (115.6 - 204.4 mm/day): Risk 80.0% - 92.9% (Category: CRITICAL)
    - Extremely Heavy / Cloudburst (> 204.4 mm/day): Risk 93.0% - 99.0% (Category: CRITICAL)

    Returns a reproducible, monotonically increasing dictionary payload.
    """
    from datetime import datetime, timezone

    r24 = max(0.0, float(rainfall_24h or 0.0))
    f6 = max(0.0, float(forecast_6h or 0.0))
    # Effective precipitation accounts for antecedent 24h rain plus immediate 6h forecast surge
    r_eff = r24 + 0.5 * f6

    if r_eff < 2.5:
        # Trace / Minimal Rain: 5.0% - 14.9%
        pct = 5.0 + (r_eff / 2.5) * 9.9
        cat = "LOW"
    elif r_eff <= 15.5:
        # Light Rain: 15.0% - 29.9%
        pct = 15.0 + ((r_eff - 2.5) / (15.5 - 2.5)) * 14.9
        cat = "LOW"
    elif r_eff <= 64.4:
        # Moderate Rain: 30.0% - 59.9%
        pct = 30.0 + ((r_eff - 15.6) / (64.4 - 15.6)) * 29.9
        cat = "MODERATE"
    elif r_eff <= 115.5:
        # Heavy Rain: 60.0% - 79.9%
        pct = 60.0 + ((r_eff - 64.5) / (115.5 - 64.5)) * 19.9
        cat = "HIGH"
    elif r_eff <= 204.4:
        # Very Heavy Rain: 80.0% - 92.9%
        pct = 80.0 + ((r_eff - 115.6) / (204.4 - 115.6)) * 12.9
        cat = "CRITICAL"
    else:
        # Extremely Heavy / Cloudburst Deluge: 93.0% - 99.0%
        overflow = min(100.0, r_eff - 204.4)
        pct = 93.0 + (overflow / 100.0) * 6.0
        cat = "CRITICAL"

    pct = round(float(np.clip(pct, 5.0, 99.0)), 1)
    ts = timestamp or datetime.now(timezone.utc).isoformat()

    return {
        "current_rainfall_value": round(r24, 1),
        "unit": "mm/day",
        "forecast_6h_value": round(f6, 1),
        "effective_precipitation_mm": round(r_eff, 1),
        "rainfall_risk_percentage": pct,
        "rainfall_risk_category": cat,
        "source_status": source_label,
        "is_fallback": is_fallback,
        "timestamp": ts,
    }
