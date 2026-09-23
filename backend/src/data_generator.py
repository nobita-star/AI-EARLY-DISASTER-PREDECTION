"""
data_generator.py - Physically Plausible Synthetic & Telemetry Data Generator
SIH Problem Statement ID: 260001

Implements:
1. Deterministic synthetic flood risk dataset generation adhering to hydrologic principles.
2. Controlled stochastic noise to reflect real-world sensor variances.
3. Pre-configured multi-stage scenarios for time-travel simulation and self-audit demonstrations.
"""

from typing import Dict, Any, Tuple
# pyrefly: ignore [missing-import]
import numpy as np
import pandas as pd


def generate_physically_plausible_dataset(
    n_samples: int = 1500,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Generates synthetic flood risk data governed by physical hydrological relationships:
    - High rainfall + high forecast rainfall raises runoff volume.
    - High soil saturation reduces infiltration capacity (Horton overland flow).
    - Lower elevation near river systems increases hydraulic head exposure.
    - Low slope retards drainage, concentrating water; steep slopes induce rapid flash runoff.
    - Historical flood frequency acts as geomorphic baseline vulnerability.
    """
    rng = np.random.default_rng(random_seed)

    # 1. Primary meteorological & hydrologic features
    rainfall = rng.gamma(shape=2.5, scale=20.0, size=n_samples)  # mm, [0 - 250+]
    forecast_rainfall = rng.gamma(shape=2.0, scale=25.0, size=n_samples)  # mm [0 - 300+]
    soil_saturation = rng.beta(a=2.0, b=2.0, size=n_samples)  # [0.0 - 1.0] Sentinel-1 SAR proxy
    slope = rng.uniform(0.5, 45.0, size=n_samples)  # degrees (SRTM DEM)
    river_level = rng.normal(loc=3.0, scale=1.5, size=n_samples)  # meters
    river_level = np.clip(river_level, 0.5, 12.0)

    # 2. Extended geospatial & terrain features
    elevation = rng.uniform(10.0, 850.0, size=n_samples)  # meters above sea level
    distance_to_river = rng.exponential(scale=1200.0, size=n_samples)  # meters [0 - 8000m]
    terrain_ruggedness = rng.uniform(1.0, 25.0, size=n_samples)  # TRI (index)
    historical_flood_frequency = rng.poisson(lam=1.5, size=n_samples)  # events per decade
    historical_flood_frequency = np.clip(historical_flood_frequency, 0, 10)
    vegetation_index = rng.uniform(0.1, 0.85, size=n_samples)  # NDVI proxy
    radar_water_probability = np.clip(
        0.1 * (river_level / 4.0) + 0.3 * soil_saturation + rng.normal(0, 0.05, size=n_samples),
        0.0,
        1.0
    )

    # 3. Physically grounded latent risk score formulation:
    # Hydrologic Runoff Index ~ Precipitation * Infiltration Deficit + River Overflow Tendency
    effective_rainfall = rainfall * 0.45 + forecast_rainfall * 0.55
    infiltration_barrier = np.power(soil_saturation, 1.8)
    river_overtop_potential = np.clip((river_level - 4.5) / 3.0, -1.0, 2.5)

    # Distance decay factor: proximity to river channels amplifies inundation
    proximity_factor = np.exp(-distance_to_river / 1500.0)

    # Slope attenuation: flat terrain retains water; moderate slopes drain; very steep cause flash run
    flatness_retention = np.clip((15.0 - slope) / 15.0, -0.5, 1.2)

    latent_risk = (
        0.30 * (effective_rainfall / 120.0)
        + 0.25 * infiltration_barrier
        + 0.25 * river_overtop_potential
        + 0.15 * proximity_factor
        + 0.10 * flatness_retention
        + 0.08 * (historical_flood_frequency / 5.0)
        - 0.05 * (elevation / 600.0)
        - 0.04 * vegetation_index
    )

    # Add controlled Gaussian noise to simulate sensor noise, micro-topography, and weather forecast drift
    noise = rng.normal(loc=0.0, scale=0.08, size=n_samples)
    continuous_risk = 1.0 / (1.0 + np.exp(-5.0 * (latent_risk + noise - 0.20)))

    # Binary flood classification label based on physical threshold
    disaster_label = (continuous_risk >= 0.50).astype(int)

    df = pd.DataFrame({
        "rainfall": np.round(rainfall, 2),
        "forecast_rainfall": np.round(forecast_rainfall, 2),
        "soil_saturation": np.round(soil_saturation, 3),
        "slope": np.round(slope, 2),
        "river_level": np.round(river_level, 2),
        "elevation": np.round(elevation, 1),
        "terrain_ruggedness": np.round(terrain_ruggedness, 2),
        "distance_to_river": np.round(distance_to_river, 1),
        "historical_flood_frequency": historical_flood_frequency,
        "vegetation_index": np.round(vegetation_index, 3),
        "radar_water_probability": np.round(radar_water_probability, 3),
        "flood_risk_score": np.round(continuous_risk, 4),
        "disaster_occurred": disaster_label,
    })

    return df


def get_time_travel_demo_data() -> Dict[str, Any]:
    """
    Returns deterministic telemetry representing a realistic SIH disaster scenario:
    - T-24h: Model issues Severe Inundation Alert due to high NWP forecast rainfall (145mm)
      and saturated ground, river approaching warning level.
    - T-0h: Actual observed ground-truth sensor state reveals a meteorological diversion;
      actual rainfall was only 14.2mm, river stabilized at 2.15m, NO flood occurred.
    - Demonstrates self-auditing AI discovering that NWP Forecast Rainfall had the
      highest positive model attribution driving the false alarm.
    """
    stage_1_early_warning = {
        "timestamp": "2026-09-09T18:00:00Z",
        "rainfall": 68.5,  # mm (antecedent rainfall)
        "forecast_rainfall": 142.0,  # mm (predicted cyclonic surge)
        "soil_saturation": 0.82,  # Sentinel-1 SAR wetness proxy
        "slope": 4.5,  # Flat basin terrain
        "river_level": 5.8,  # Meters (approaching danger threshold 6.0m)
        "elevation": 42.0,
        "distance_to_river": 250.0,
        "terrain_ruggedness": 3.2,
        "historical_flood_frequency": 3,
        "vegetation_index": 0.35,
        "radar_water_probability": 0.65,
        "description": "T-24h Early Warning: High atmospheric moisture flux and severe precipitation forecast."
    }

    stage_2_ground_truth = {
        "timestamp": "2026-09-10T18:00:00Z",
        "actual_rainfall": 14.2,  # mm (Actual storm system tracked 120km eastward)
        "actual_forecast_realization": 0.10,  # Only 10% of forecast materialized
        "actual_river_level": 2.25,  # Meters (stabilized safely below 3.0m)
        "actual_soil_saturation": 0.44,  # Rapid surface drainage through sandy loam
        "sensor_health_index": 0.98,
        "actual_disaster_status": "NO_DISASTER",
        "observed_inundation_extent_km2": 0.0,
        "ground_truth_confirmed": True,
        "description": "T-0h Ground Truth: Hydrometric station network and Sentinel-1 SAR water mask confirm river basin remained within normal conveyance capacity."
    }

    return {
        "stage_1_input": stage_1_early_warning,
        "stage_2_observation": stage_2_ground_truth
    }
