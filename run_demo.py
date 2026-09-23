"""
run_demo.py - Interactive CLI Demonstration for PS ID: 260001
Self-Auditing Disaster Management Prediction Engine
"""

import json
import time
from ml_engine import DisasterRiskPredictor
from schemas import DisasterTelemetryInput, GeospatialCoordinates
from spatial_store import SpatialStore


def print_banner(title: str):
    print("\n" + "=" * 78)
    print(f"  {title.upper()}")
    print("=" * 78)


def main():
    print_banner("Self-Auditing Disaster Management Prediction Engine (PS ID: 260001)")
    print("Initializing Spatial PostGIS Emulation Store & Training/Loading XGBoost Engine...")

    spatial_store = SpatialStore("disaster_engine.db")
    predictor = DisasterRiskPredictor(spatial_store=spatial_store)

    print(f"[OK] Model successfully loaded: {predictor.metadata.get('model_type')}")
    print(f"[OK] Training Metrics -> AUC: {predictor.metadata['metrics']['auc']} | F1: {predictor.metadata['metrics']['f1']}")
    print(f"[OK] SHAP Base Value: {predictor.base_value:.4f}")

    # STAGE 1: T-24h Initial Prediction
    print_banner("Stage 1: T-24h Pre-Disaster Prediction (Severe Storm Forecast)")
    telemetry_input = DisasterTelemetryInput(
        rainfall_last_24h=35.0,
        forecasted_rainfall_next_6h=82.0,  # Aggressive storm prediction
        soil_saturation_index=0.32,        # Relatively dry SAR soil moisture
        dem_slope_degrees=5.2,             # Low slope plain
        river_water_level_m=4.20,          # Gauge below flood threshold
        staleness_hours=1.2,
        sensor_variance=0.06,
        coordinates=GeospatialCoordinates(
            latitude=19.10,
            longitude=72.92,
            elevation_m=9.0,
            catchment_id="CATCHMENT_DELTA_01",
        ),
    )

    print("Input Telemetry Vector:")
    print(f"  - Rainfall (Last 24h): {telemetry_input.rainfall_last_24h} mm")
    print(f"  - NWP Forecast (Next 6h): {telemetry_input.forecasted_rainfall_next_6h} mm [HIGH STORM ALERT]")
    print(f"  - Sentinel-1 SAR Soil Saturation: {telemetry_input.soil_saturation_index:.2f} (Dry)")
    print(f"  - SRTM DEM Topographic Slope: {telemetry_input.dem_slope_degrees}°")
    print(f"  - Hydrometric River Stage: {telemetry_input.river_water_level_m} m")
    print(f"  - Sensor Staleness: {telemetry_input.staleness_hours}h | Variance: {telemetry_input.sensor_variance}")

    pred_res = predictor.predict(telemetry_input)

    print("\nInference Output:")
    print(f"  - Prediction ID: {pred_res.prediction_id}")
    print(f"  - Inundation Risk Score: {pred_res.risk_score:.4f} (Probability: {pred_res.risk_score * 100:.1f}%)")
    print(f"  - Risk Tier: {pred_res.risk_level.value}")
    print(f"  - AI Confidence Score: {pred_res.confidence_score * 100:.1f}%")
    print("  - SHAP TreeExplainer Attributions:")
    for feat in pred_res.top_shap_features:
        sign = "+" if feat.direction == "INCREASES_RISK" else "-"
        print(f"      * {feat.feature_name:<28}: {sign}{abs(feat.shap_value):.4f} (Rel. Impact: {feat.relative_importance_pct:5.1f}%) -> {feat.direction}")

    if pred_res.spatial_context and pred_res.spatial_context.get("catchment"):
        c = pred_res.spatial_context["catchment"]
        print(f"  - Spatial Catchment Identified: {c['name']} ({c['type']}, Vulnerability: {c['vulnerability_index']})")

    # STAGE 2: T-0h Ground Truth Arrival
    print_banner("Stage 2: T-0h Ground Truth Arrival (Event Realization)")
    print("Time advancement: 24 hours have elapsed.")
    print("Field Observation & Satellite Ground Truth telemetry arrived:")
    actual_rain_6h = 13.5  # Realized rain was far lower
    actual_river_stage = 4.30
    actual_flood = 0       # No flood occurred!

    print(f"  - Realized Rainfall in 6h: {actual_rain_6h} mm (Forecast was {telemetry_input.forecasted_rainfall_next_6h} mm -> Overestimated by 507%)")
    print(f"  - Realized River Stage: {actual_river_stage} m")
    print(f"  - Actual Disaster Inundation Ground Truth: {actual_flood} (NO FLOOD)")
    print(f"  - Anomaly Flagged: Prediction ({pred_res.risk_level.value}) vs Reality ({actual_flood}) -> MISMATCH DETECTED: FALSE ALARM (False Positive)!")

    # STAGE 3: T+1h Automated Post-Inference Self-Auditing Loop & RCA
    print_banner("Stage 3: T+1h Automated Self-Auditing Loop & SHAP Delta RCA")
    print("Triggering automated Root Cause Analysis (RCA)...")

    audit_res = predictor.audit_prediction(
        prediction_id=pred_res.prediction_id,
        actual_ground_truth=actual_flood,
        observed_rainfall_next_6h=actual_rain_6h,
        observed_river_water_level_m=actual_river_stage,
        notes="CLI Demonstration of Self-Auditing RCA Engine",
    )

    print(f"  - Audit ID: {audit_res.audit_id}")
    print(f"  - Discrepancy Classification: {audit_res.discrepancy_type.value}")
    print(f"  - Primary Culprit Feature Identified: '{audit_res.primary_culprit_feature}'")
    print("\n  - SHAP Delta Root Cause Breakdown:")
    for delta in audit_res.shap_deltas:
        print(f"      * {delta.feature_name:<28}: Predicted SHAP {delta.predicted_shap:+.3f} -> Counterfactual SHAP {delta.counterfactual_shap:+.3f} | Delta: {delta.shap_delta:+.4f}")

    print("\n" + "=" * 78)
    print("  HUMAN-READABLE ROOT CAUSE ANALYSIS (RCA) ONE-LINER:")
    print(f"  \"{audit_res.rca_explanation}\"")
    print("=" * 78)

    print("\nSelf-Audit completed and recorded into SQLite audit repository.")
    summary = spatial_store.get_audit_summary()
    print(f"Updated System Audit Metrics: Total Audits: {summary['total_audits']} | Accuracy: {summary['accuracy'] * 100:.1f}%")


if __name__ == "__main__":
    main()
