"""
synthetic_data.py - Synthetic Training Dataset & Model Artifact Serializer
SIH Problem Statement ID: 260001

Implements:
1. Generation of realistic 1,000-sample training dataset strictly matching prompt specification:
   - rainfall_last_24h (mm)
   - forecasted_rainfall_next_6h (mm)
   - soil_saturation_index (0.0 to 1.0, Sentinel-1 SAR proxy)
   - dem_slope_degrees (0 to 60 degrees, SRTM DEM proxy)
   - river_water_level_m (meters)
   - actual_inundation_risk (0 or 1 binary target)
2. Automated XGBClassifier training & serialization.
3. shap.TreeExplainer initialization.
"""

import os
from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd
import joblib
from xgboost import XGBClassifier
import shap

SPEC_FEATURE_NAMES = [
    "rainfall_last_24h",
    "forecasted_rainfall_next_6h",
    "soil_saturation_index",
    "dem_slope_degrees",
    "river_water_level_m"
]

DEFAULT_MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
DEFAULT_ARTIFACT_PATH = os.path.join(DEFAULT_MODEL_DIR, "xgboost_disaster_spec_model.joblib")


def generate_synthetic_disaster_dataset(
    n_samples: int = 1000,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Generates a physically constrained synthetic dataset of 1,000 historical records:
    - rainfall_last_24h: Gamma distribution [0 - 250mm]
    - forecasted_rainfall_next_6h: Gamma distribution [0 - 200mm]
    - soil_saturation_index: Beta distribution [0.0 - 1.0] (Sentinel-1 SAR proxy)
    - dem_slope_degrees: Uniform [0.5 - 60.0 degrees] (NASA SRTM DEM proxy)
    - river_water_level_m: Normal [0.5 - 12.0 meters]
    - actual_inundation_risk: Binary target (0 or 1) based on physical infiltration-excess runoff
    """
    rng = np.random.default_rng(random_seed)

    rainfall_24h = rng.gamma(shape=2.5, scale=20.0, size=n_samples)
    forecast_6h = rng.gamma(shape=2.0, scale=25.0, size=n_samples)
    soil_sat = rng.beta(a=2.0, b=2.0, size=n_samples)
    slope_deg = rng.uniform(0.5, 60.0, size=n_samples)
    river_m = np.clip(rng.normal(loc=3.2, scale=1.6, size=n_samples), 0.5, 12.0)

    # Physical runoff formulation
    effective_precipitation = rainfall_24h * 0.45 + forecast_6h * 0.55
    soil_impedance = np.power(soil_sat, 1.8)
    river_overtop = np.clip((river_m - 4.2) / 3.0, -1.0, 2.5)
    slope_retention = np.clip((15.0 - slope_deg) / 15.0, -0.5, 1.2)

    latent_risk = (
        0.35 * (effective_precipitation / 120.0)
        + 0.28 * soil_impedance
        + 0.25 * river_overtop
        + 0.12 * slope_retention
    )

    noise = rng.normal(loc=0.0, scale=0.06, size=n_samples)
    continuous_prob = 1.0 / (1.0 + np.exp(-5.5 * (latent_risk + noise - 0.22)))
    actual_inundation_risk = (continuous_prob >= 0.50).astype(int)

    df = pd.DataFrame({
        "rainfall_last_24h": np.round(rainfall_24h, 2),
        "forecasted_rainfall_next_6h": np.round(forecast_6h, 2),
        "soil_saturation_index": np.round(soil_sat, 3),
        "dem_slope_degrees": np.round(slope_deg, 2),
        "river_water_level_m": np.round(river_m, 2),
        "actual_inundation_risk": actual_inundation_risk,
    })

    return df


def train_and_serialize_spec_model(
    artifact_path: str = DEFAULT_ARTIFACT_PATH,
    n_samples: int = 1000,
    random_seed: int = 42
) -> Tuple[XGBClassifier, shap.TreeExplainer, Dict[str, Any]]:
    """
    Trains an XGBClassifier on the 1,000 synthetic rows, initializes a SHAP TreeExplainer,
    and serializes the artifact bundle.
    """
    os.makedirs(os.path.dirname(artifact_path), exist_ok=True)
    df = generate_synthetic_disaster_dataset(n_samples=n_samples, random_seed=random_seed)

    X = df[SPEC_FEATURE_NAMES]
    y = df["actual_inundation_risk"]

    clf = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        eval_metric="logloss",
        random_state=random_seed,
    )
    clf.fit(X, y)

    explainer = shap.TreeExplainer(clf)

    bundle = {
        "model": clf,
        "explainer": explainer,
        "feature_names": SPEC_FEATURE_NAMES,
        "sample_size": n_samples,
    }

    joblib.dump(bundle, artifact_path)
    return clf, explainer, bundle
