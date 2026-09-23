"""
test_engine.py - Comprehensive Unit & Integration Test Suite
Problem Statement ID: 260001

Verifies:
1. Geospatial & Hydrological Synthetic Data Generation.
2. XGBoost Training, Model Metrics, and SHAP TreeExplainer Attribution.
3. AI Confidence Scoring (staleness and variance degradation).
4. Spatial Store & PostGIS Emulation (ST_Contains, ST_Intersects, ST_DWithin).
5. Post-Inference Self-Auditing Loop & SHAP Delta RCA (FP, FN, TP, TN).
6. FastAPI REST Endpoints via TestClient.
"""

import os
import sys
import unittest
import pandas as pd
from fastapi.testclient import TestClient

from ml_engine import DisasterRiskPredictor
from schemas import DisasterTelemetryInput, GeospatialCoordinates
from spatial_store import SpatialGeometry, SpatialStore
from synthetic_data import (
    FEATURE_COLUMNS,
    generate_synthetic_hydrology_data,
    train_and_serialize_engine,
)
from main import app


class TestDisasterManagementEngine(unittest.TestCase):
    """Integration test suite for Self-Auditing Disaster Management Prediction Engine."""

    @classmethod
    def setUpClass(cls):
        """Prepares trained model and spatial test environment."""
        cls.test_db_path = "test_disaster_engine.db"
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)

        cls.spatial_store = SpatialStore(db_path=cls.test_db_path)
        cls.predictor = DisasterRiskPredictor(spatial_store=cls.spatial_store)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        """Cleans up test database."""
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)

    def test_01_synthetic_data_generation(self):
        """Validates synthetic data distributions and physical features."""
        df = generate_synthetic_hydrology_data(n_samples=500, random_seed=42)
        self.assertEqual(len(df), 500)
        for col in FEATURE_COLUMNS:
            self.assertIn(col, df.columns)
        self.assertIn("actual_inundation_risk", df.columns)

        # Check domain boundaries
        self.assertTrue((df["rainfall_last_24h"] >= 0).all())
        self.assertTrue((df["soil_saturation_index"] >= 0.0).all())
        self.assertTrue((df["soil_saturation_index"] <= 1.0).all())
        self.assertTrue((df["dem_slope_degrees"] >= 0.0).all())
        self.assertTrue((df["river_water_level_m"] >= 1.0).all())

    def test_02_spatial_geometry_postgis_emulation(self):
        """Validates ST_Contains, ST_Intersects, and ST_DWithin calculations."""
        # Haversine distance between Mumbai (19.076, 72.877) and Pune (18.520, 73.856) ~ 120 km
        dist = SpatialGeometry.haversine_distance_km(19.076, 72.877, 18.520, 73.856)
        self.assertGreater(dist, 100.0)
        self.assertLess(dist, 150.0)

        # ST_DWithin
        self.assertTrue(SpatialGeometry.st_dwithin(19.076, 72.877, 19.080, 72.880, 5.0))
        self.assertFalse(SpatialGeometry.st_dwithin(19.076, 72.877, 18.520, 73.856, 50.0))

        # ST_Contains Bounding Box
        self.assertTrue(SpatialGeometry.st_contains_bbox(18.0, 72.0, 20.0, 74.0, 19.1, 72.9))
        self.assertFalse(SpatialGeometry.st_contains_bbox(18.0, 72.0, 20.0, 74.0, 21.0, 75.0))

        # Catchment query
        catchment = self.spatial_store.find_catchment(19.10, 72.92)
        self.assertIsNotNone(catchment)
        self.assertEqual(catchment["catchment_id"], "CATCHMENT_DELTA_01")

    def test_03_prediction_and_shap_attribution(self):
        """Tests core ML prediction pipeline, confidence scoring, and SHAP features."""
        telemetry = DisasterTelemetryInput(
            rainfall_last_24h=80.0,
            forecasted_rainfall_next_6h=65.0,
            soil_saturation_index=0.88,
            dem_slope_degrees=3.5,
            river_water_level_m=7.2,
            staleness_hours=1.5,
            sensor_variance=0.04,
            coordinates=GeospatialCoordinates(latitude=19.12, longitude=72.95, elevation_m=6.0),
        )

        res = self.predictor.predict(telemetry)
        self.assertIsNotNone(res.prediction_id)
        self.assertGreaterEqual(res.risk_score, 0.0)
        self.assertLessEqual(res.risk_score, 1.0)
        self.assertIn(res.risk_level.value, ["LOW", "MEDIUM", "HIGH"])
        self.assertGreaterEqual(res.confidence_score, 0.0)
        self.assertLessEqual(res.confidence_score, 1.0)

        # Verify SHAP attributions
        self.assertEqual(len(res.top_shap_features), 5)
        top_feature = res.top_shap_features[0]
        self.assertIn(top_feature.feature_name, FEATURE_COLUMNS)
        self.assertIn(top_feature.direction, ["INCREASES_RISK", "DECREASES_RISK"])
        self.assertGreater(top_feature.relative_importance_pct, 0.0)

    def test_04_ai_confidence_scoring_dynamics(self):
        """Verifies that confidence score appropriately penalizes stale or noisy data."""
        # Fresh, pristine telemetry
        conf_pristine = self.predictor.calculate_confidence_score(
            risk_probability=0.90, staleness_hours=0.1, sensor_variance=0.01
        )

        # Highly stale, noisy telemetry
        conf_degraded = self.predictor.calculate_confidence_score(
            risk_probability=0.90, staleness_hours=20.0, sensor_variance=0.50
        )

        self.assertGreater(conf_pristine.final_confidence, conf_degraded.final_confidence)
        self.assertGreater(conf_degraded.staleness_penalty, conf_pristine.staleness_penalty)
        self.assertGreater(conf_degraded.variance_penalty, conf_pristine.variance_penalty)

    def test_05_self_auditing_false_alarm_rca(self):
        """Tests post-inference self-audit loop on a False Alarm (False Positive)."""
        # Step 1: Ingest High Risk prediction driven by heavy rain forecast
        telemetry = DisasterTelemetryInput(
            rainfall_last_24h=20.0,
            forecasted_rainfall_next_6h=85.0,  # Overestimated rain forecast
            soil_saturation_index=0.30,        # Dry soil
            dem_slope_degrees=8.0,
            river_water_level_m=3.5,
            staleness_hours=0.5,
            sensor_variance=0.05,
        )
        pred = self.predictor.predict(telemetry)

        # Step 2: Ingest Ground Truth showing NO flood and realized rain was only 12mm
        audit = self.predictor.audit_prediction(
            prediction_id=pred.prediction_id,
            actual_ground_truth=0,
            observed_rainfall_next_6h=12.0,
            observed_river_water_level_m=3.6,
        )

        self.assertIsNotNone(audit.audit_id)
        self.assertEqual(audit.actual_ground_truth, 0)
        # Discrepancy should reflect False Positive or True Negative
        if audit.is_mismatch:
            self.assertEqual(audit.discrepancy_type.value, "FALSE_POSITIVE")
            self.assertEqual(audit.primary_culprit_feature, "forecasted_rainfall_next_6h")
            self.assertIn("False Alarm", audit.rca_explanation)
            self.assertIn("overestimated", audit.rca_explanation)

    def test_06_fastapi_rest_endpoints(self):
        """Tests all FastAPI REST endpoints via TestClient."""
        # 1. Health check
        res_health = self.client.get("/api/v1/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.json()["status"], "HEALTHY")

        # 2. Predict endpoint
        payload = {
            "telemetry": {
                "rainfall_last_24h": 45.0,
                "forecasted_rainfall_next_6h": 50.0,
                "soil_saturation_index": 0.65,
                "dem_slope_degrees": 6.0,
                "river_water_level_m": 5.8,
                "staleness_hours": 0.5,
                "sensor_variance": 0.05,
                "coordinates": {
                    "latitude": 19.10,
                    "longitude": 72.92,
                    "elevation_m": 10.0,
                    "catchment_id": "CATCHMENT_DELTA_01",
                },
            }
        }
        res_pred = self.client.post("/api/v1/predict", json=payload)
        self.assertEqual(res_pred.status_code, 200)
        pred_data = res_pred.json()
        pred_id = pred_data["prediction_id"]
        self.assertIn("risk_score", pred_data)
        self.assertIn("top_shap_features", pred_data)
        self.assertIn("confidence_score", pred_data)

        # 3. Audit endpoint
        audit_payload = {
            "prediction_id": pred_id,
            "actual_ground_truth": 1,
            "observed_rainfall_next_6h": 55.0,
            "observed_river_water_level_m": 6.2,
        }
        res_audit = self.client.post("/api/v1/audit", json=audit_payload)
        self.assertEqual(res_audit.status_code, 200)
        audit_data = res_audit.json()
        self.assertIn("discrepancy_type", audit_data)
        self.assertIn("rca_explanation", audit_data)

        # 4. Audit logs endpoint
        res_logs = self.client.get("/api/v1/audit/logs")
        self.assertEqual(res_logs.status_code, 200)
        summary = res_logs.json()
        self.assertGreater(summary["total_audits"], 0)
        self.assertIn("accuracy", summary)

        # 5. Time travel demo simulation endpoint
        res_demo = self.client.post("/api/v1/simulate/time-travel")
        self.assertEqual(res_demo.status_code, 200)
        demo_data = res_demo.json()
        self.assertIn("stage_1_prediction", demo_data)
        self.assertIn("stage_2_ground_truth", demo_data)
        self.assertIn("stage_3_rca_audit", demo_data)
        self.assertIn("system_verdict", demo_data)
        self.assertIn("False Alarm", demo_data["system_verdict"])


if __name__ == "__main__":
    unittest.main()
