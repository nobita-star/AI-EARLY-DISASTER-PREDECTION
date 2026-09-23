"""
synthetic_data.py - Geospatial Hydrological Synthetic Data Generator & XGBoost Trainer
Problem Statement ID: 260001

Generates 1,000 realistic historical observations reflecting physical hydrology
(Sentinel-1 SAR soil saturation, SRTM DEM slope, NWP rain forecasts, river stage levels).
Trains, validates, and serializes an XGBClassifier and initializes a SHAP TreeExplainer.
"""

import json
import os
from typing import Dict, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
import xgboost as xgb
import shap

FEATURE_COLUMNS = [
    "rainfall_last_24h",
    "forecasted_rainfall_next_6h",
    "soil_saturation_index",
    "dem_slope_degrees",
    "river_water_level_m",
]

TARGET_COLUMN = "actual_inundation_risk"

MODEL_FILE = "disaster_xgb_model.json"
METADATA_FILE = "model_metadata.json"
DATASET_FILE = "synthetic_disaster_dataset.csv"


def generate_synthetic_hydrology_data(n_samples: int = 1000, random_seed: int = 42) -> pd.DataFrame:
    """
    Generates realistic multi-modal geospatial & hydrological telemetry records.

    Physical hydrologic dynamics modeled:
    - Saturated soil (> 0.75 SAR proxy) loses infiltration capacity, amplifying runoff.
    - Low slope (< 8 deg) causes severe surface ponding and river backflow.
    - River water levels exceeding 6.5m (bankfull flood stage) heavily drive inundation.
    - Compound interaction: Heavy rainfall + high saturation + high river stage triggers flooding.
    """
    np.random.seed(random_seed)

    # 1. Antecedent rainfall over past 24 hours (Gamma distribution: heavy right tail)
    rainfall_24h = np.random.gamma(shape=1.8, scale=25.0, size=n_samples)
    rainfall_24h = np.clip(rainfall_24h, 0.0, 240.0)

    # 2. Forecasted precipitation next 6h (Correlated with 24h rain + convective storm spikes)
    storm_bias = (rainfall_24h / 200.0) * 35.0
    forecast_6h = np.random.gamma(shape=1.5, scale=18.0, size=n_samples) + storm_bias
    forecast_6h = np.clip(forecast_6h, 0.0, 140.0)

    # 3. Sentinel-1 SAR soil saturation proxy (0.0 to 1.0)
    # Driven by antecedent 24h rainfall with beta distribution noise
    base_saturation = 0.20 + 0.65 * (1.0 - np.exp(-rainfall_24h / 45.0))
    sar_noise = np.random.normal(loc=0.0, scale=0.06, size=n_samples)
    soil_saturation = np.clip(base_saturation + sar_noise, 0.02, 0.99)

    # 4. SRTM DEM topographic slope in degrees (0 to 60)
    # Uniform/Beta mixture: river valleys have 0-10 deg, mountain ridges have 30-55 deg
    slope = np.random.beta(a=1.5, b=2.5, size=n_samples) * 55.0
    slope = np.clip(slope, 0.5, 58.0)

    # 5. Hydrometric river water level in meters (Base flow 2.5m, flood stage 6.5m, max 12m)
    river_stage = 2.2 + 0.035 * rainfall_24h + 0.025 * forecast_6h + (1.0 - slope / 60.0) * 1.8
    river_noise = np.random.normal(loc=0.0, scale=0.45, size=n_samples)
    river_level = np.clip(river_stage + river_noise, 1.0, 11.8)

    # 6. Physical Latent Inundation Risk Index (Horton infiltration excess + hydraulic overflow)
    # High saturation + heavy rain + high river + flat slope = massive flood probability
    effective_rain = 0.35 * rainfall_24h + 0.65 * forecast_6h
    runoff_potential = soil_saturation * (effective_rain / 50.0)
    topography_factor = np.exp(-slope / 14.0)  # flat slope dramatically amplifies ponding
    hydraulic_factor = np.maximum(0.0, (river_level - 6.0) / 3.0)  # river above 6.0m spills banks

    latent_risk_score = (
        0.30 * (runoff_potential)
        + 0.35 * (hydraulic_factor ** 1.3)
        + 0.25 * (topography_factor * (effective_rain / 40.0))
        + 0.10 * (soil_saturation ** 2)
    )

    # Stochastic threshold via logistic sigmoid with noise
    prob = 1.0 / (1.0 + np.exp(-(latent_risk_score - 1.15) * 4.2))
    noise = np.random.uniform(-0.04, 0.04, size=n_samples)
    final_prob = np.clip(prob + noise, 0.0, 1.0)
    actual_inundation = (final_prob >= 0.50).astype(int)

    df = pd.DataFrame(
        {
            "rainfall_last_24h": np.round(rainfall_24h, 2),
            "forecasted_rainfall_next_6h": np.round(forecast_6h, 2),
            "soil_saturation_index": np.round(soil_saturation, 4),
            "dem_slope_degrees": np.round(slope, 2),
            "river_water_level_m": np.round(river_level, 2),
            "actual_inundation_risk": actual_inundation,
        }
    )
    return df


def train_and_serialize_engine(
    dataset_path: str = DATASET_FILE,
    model_path: str = MODEL_FILE,
    metadata_path: str = METADATA_FILE,
) -> Tuple[xgb.XGBClassifier, shap.TreeExplainer, Dict]:
    """
    Trains XGBoost classifier on the synthetic geospatial hydrological dataset,
    initializes SHAP TreeExplainer, and serializes model weights and feature statistics.
    """
    df = generate_synthetic_hydrology_data(n_samples=1000, random_seed=42)
    df.to_csv(dataset_path, index=False)

    x = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.20, random_state=42, stratify=y
    )

    # Calibrated XGBoost for tabular geospatial hydrology
    clf = xgb.XGBClassifier(
        n_estimators=130,
        max_depth=4,
        learning_rate=0.06,
        subsample=0.85,
        colsample_bytree=0.85,
        scale_pos_weight=1.1,
        eval_metric="logloss",
        random_state=42,
    )
    clf.fit(x_train, y_train)

    y_pred_proba = clf.predict_proba(x_test)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)

    auc = float(roc_auc_score(y_test, y_pred_proba))
    f1 = float(f1_score(y_test, y_pred))
    acc = float(accuracy_score(y_test, y_pred))

    # Initialize SHAP TreeExplainer with background sample
    explainer = shap.TreeExplainer(clf, data=x_train.sample(n=100, random_state=42))

    # Extract feature statistical baselines for counterfactual RCA deltas
    stats = {}
    for col in FEATURE_COLUMNS:
        stats[col] = {
            "mean": float(df[col].mean()),
            "std": float(df[col].std()),
            "min": float(df[col].min()),
            "max": float(df[col].max()),
            "median": float(df[col].median()),
            "p25": float(df[col].quantile(0.25)),
            "p75": float(df[col].quantile(0.75)),
        }

    # Save model
    clf.save_model(model_path)

    # Save metadata
    base_val = explainer.expected_value
    if isinstance(base_val, (np.ndarray, list)):
        base_val = float(base_val[1] if len(base_val) > 1 else base_val[0])
    else:
        base_val = float(base_val)

    metadata = {
        "model_type": "XGBClassifier",
        "ps_id": "260001",
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "metrics": {"auc": round(auc, 4), "f1": round(f1, 4), "accuracy": round(acc, 4)},
        "feature_statistics": stats,
        "shap_expected_value": base_val,
        "training_samples": len(df),
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Model successfully trained and saved to {model_path}")
    print(f"Metrics -> ROC-AUC: {auc:.4f} | F1: {f1:.4f} | Accuracy: {acc:.4f}")
    print(f"Metadata saved to {metadata_path}")
    return clf, explainer, metadata


if __name__ == "__main__":
    train_and_serialize_engine()
