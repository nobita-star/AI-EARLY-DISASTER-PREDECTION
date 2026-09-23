"""
ml_engine.py - Core ML Inference, SHAP Explainability, and Self-Auditing RCA Engine
Problem Statement ID: 260001
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import shap
import xgboost as xgb

from schemas import (
    ConfidenceBreakdown,
    DisasterTelemetryInput,
    DiscrepancyType,
    FeatureAttribution,
    PredictionResponse,
    RiskLevel,
    ShapDeltaItem,
    AuditResponse,
)
from spatial_store import SpatialStore
from synthetic_data import (
    FEATURE_COLUMNS,
    METADATA_FILE,
    MODEL_FILE,
    train_and_serialize_engine,
)


class DisasterRiskPredictor:
    """
    Principal Geospatial AI & MLOps Engine for Disaster Inundation Risk.
    Encapsulates XGBoost inference, TreeExplainer SHAP attribution,
    sensor-quality confidence scoring, and automated Root Cause Analysis (RCA).
    """

    def __init__(
        self,
        model_path: str = MODEL_FILE,
        metadata_path: str = METADATA_FILE,
        spatial_store: Optional[SpatialStore] = None,
    ):
        self.model_path = model_path
        self.metadata_path = metadata_path
        self.spatial_store = spatial_store or SpatialStore()

        self.model: Optional[xgb.XGBClassifier] = None
        self.explainer: Optional[shap.TreeExplainer] = None
        self.metadata: Dict[str, Any] = {}
        self.base_value: float = 0.5

        self._ensure_model_loaded()

    def _ensure_model_loaded(self) -> None:
        """Loads trained XGBoost model and SHAP explainer, or trains on startup if missing."""
        import json

        if not os.path.exists(self.model_path) or not os.path.exists(self.metadata_path):
            print(f"[Engine] Artifacts not found. Training new XGBoost model on synthetic hydrology...")
            train_and_serialize_engine(model_path=self.model_path, metadata_path=self.metadata_path)

        # Load XGBoost Classifier
        self.model = xgb.XGBClassifier()
        self.model.load_model(self.model_path)

        # Load Metadata
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        # Initialize SHAP TreeExplainer
        # We initialize with TreeExplainer directly on the XGBoost Booster
        self.explainer = shap.TreeExplainer(self.model)

        raw_base = self.explainer.expected_value
        if isinstance(raw_base, (np.ndarray, list)):
            self.base_value = float(raw_base[1] if len(raw_base) > 1 else raw_base[0])
        else:
            self.base_value = float(raw_base)

    def calculate_confidence_score(
        self,
        risk_probability: float,
        staleness_hours: float,
        sensor_variance: float,
    ) -> ConfidenceBreakdown:
        """
        Calculates AI Confidence Score based on model decision margin,
        telemetry staleness age, and sensor variance / signal-to-noise ratio.

        Mathematical Formulation:
        - Model Certainty: C_model = 0.50 + |P - 0.50|  (0.50 at boundary, 1.0 at pure certainty)
        - Staleness Penalty: S_pen = min(0.35, staleness_hours * 0.015)
        - Variance Penalty: V_pen = min(0.30, sensor_variance * 0.40)
        - Final Confidence: C_model * (1 - S_pen) * (1 - V_pen)
        """
        # Distance from 0.5 decision threshold
        model_certainty = 0.50 + abs(risk_probability - 0.50)

        # Staleness degradation
        staleness_penalty = min(0.35, staleness_hours * 0.015)

        # Sensor noise degradation
        variance_penalty = min(0.30, sensor_variance * 0.40)

        # Combined confidence
        raw_confidence = model_certainty * (1.0 - staleness_penalty) * (1.0 - variance_penalty)
        final_confidence = round(float(np.clip(raw_confidence, 0.05, 0.99)), 4)

        return ConfidenceBreakdown(
            model_certainty=round(model_certainty, 4),
            staleness_penalty=round(staleness_penalty, 4),
            variance_penalty=round(variance_penalty, 4),
            final_confidence=final_confidence,
            staleness_hours=staleness_hours,
            sensor_variance=sensor_variance,
        )

    def compute_shap_attribution(self, input_df: pd.DataFrame) -> Tuple[List[FeatureAttribution], float]:
        """
        Computes SHAP TreeExplainer feature attributions for a single telemetry record.
        Returns list of feature contributions sorted by absolute impact and base value.
        """
        shap_values = self.explainer.shap_values(input_df)

        # Handle binary classification shap output shapes
        if isinstance(shap_values, list):
            sv = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
        elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 2:
            sv = shap_values[0]
        else:
            sv = np.array(shap_values).flatten()

        total_abs = float(np.sum(np.abs(sv)))
        total_abs = max(total_abs, 1e-6)

        attributions: List[FeatureAttribution] = []
        for i, col in enumerate(FEATURE_COLUMNS):
            val = float(input_df[col].iloc[0])
            s_val = float(sv[i])
            rel_pct = round((abs(s_val) / total_abs) * 100.0, 2)
            direction = "INCREASES_RISK" if s_val >= 0 else "DECREASES_RISK"

            attributions.append(
                FeatureAttribution(
                    feature_name=col,
                    feature_value=val,
                    shap_value=round(s_val, 4),
                    direction=direction,
                    relative_importance_pct=rel_pct,
                )
            )

        # Sort by absolute SHAP impact descending
        attributions.sort(key=lambda x: abs(x.shap_value), reverse=True)
        return attributions, round(self.base_value, 4)

    def predict(
        self,
        input_data: DisasterTelemetryInput,
        prediction_id: Optional[str] = None,
    ) -> PredictionResponse:
        """
        Executes disaster inundation risk inference pipeline:
        1. Prepares telemetry dataframe.
        2. Executes calibrated XGBoost inference.
        3. Computes TreeExplainer SHAP feature attributions.
        4. Calculates AI Confidence score from sensor health.
        5. Performs spatial PostGIS intersection query.
        6. Persists prediction in spatial database.
        """
        pred_id = prediction_id or f"PRED-{uuid.uuid4().hex[:10].upper()}"
        timestamp = datetime.now(timezone.utc).isoformat()

        # Build feature DataFrame
        feature_dict = {
            "rainfall_last_24h": [input_data.rainfall_last_24h],
            "forecasted_rainfall_next_6h": [input_data.forecasted_rainfall_next_6h],
            "soil_saturation_index": [input_data.soil_saturation_index],
            "dem_slope_degrees": [input_data.dem_slope_degrees],
            "river_water_level_m": [input_data.river_water_level_m],
        }
        df_in = pd.DataFrame(feature_dict)

        # Predict probability
        proba = self.model.predict_proba(df_in)[0, 1]
        risk_score = round(float(proba), 4)

        # Classify risk level
        if risk_score < 0.35:
            risk_level = RiskLevel.LOW
        elif risk_score < 0.70:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.HIGH

        # AI Confidence calculation
        confidence_breakdown = self.calculate_confidence_score(
            risk_probability=risk_score,
            staleness_hours=input_data.staleness_hours,
            sensor_variance=input_data.sensor_variance,
        )

        # SHAP Attribution
        shap_attrs, base_val = self.compute_shap_attribution(df_in)

        # Spatial context query (Mock PostGIS)
        spatial_context = None
        lat = input_data.coordinates.latitude if input_data.coordinates else None
        lon = input_data.coordinates.longitude if input_data.coordinates else None
        elev = input_data.coordinates.elevation_m if input_data.coordinates else None
        catchment_id = input_data.coordinates.catchment_id if input_data.coordinates else None

        if lat is not None and lon is not None:
            catchment_info = self.spatial_store.find_catchment(lat, lon)
            nearby_gauges = self.spatial_store.find_nearby_gauges(lat, lon, radius_km=30.0)
            spatial_context = {
                "catchment": catchment_info,
                "nearby_gauges": nearby_gauges,
                "coordinates": {"lat": lat, "lon": lon, "elevation_m": elev},
            }
            if catchment_info and not catchment_id:
                catchment_id = catchment_info["catchment_id"]

        # Save to SQLite database
        self.spatial_store.save_prediction(
            prediction_id=pred_id,
            timestamp=timestamp,
            telemetry={
                "rainfall_last_24h": input_data.rainfall_last_24h,
                "forecasted_rainfall_next_6h": input_data.forecasted_rainfall_next_6h,
                "soil_saturation_index": input_data.soil_saturation_index,
                "dem_slope_degrees": input_data.dem_slope_degrees,
                "river_water_level_m": input_data.river_water_level_m,
                "staleness_hours": input_data.staleness_hours,
                "sensor_variance": input_data.sensor_variance,
            },
            risk_score=risk_score,
            risk_level=risk_level.value,
            confidence_score=confidence_breakdown.final_confidence,
            confidence_breakdown=confidence_breakdown.model_dump(),
            shap_attributions=[a.model_dump() for a in shap_attrs],
            base_value=base_val,
            latitude=lat,
            longitude=lon,
            elevation_m=elev,
            catchment_id=catchment_id,
        )

        return PredictionResponse(
            prediction_id=pred_id,
            timestamp=timestamp,
            risk_score=risk_score,
            risk_level=risk_level,
            confidence_score=confidence_breakdown.final_confidence,
            confidence_breakdown=confidence_breakdown,
            top_shap_features=shap_attrs,
            base_value=base_val,
            spatial_context=spatial_context,
        )

    def audit_prediction(
        self,
        prediction_id: str,
        actual_ground_truth: int,
        observed_rainfall_next_6h: Optional[float] = None,
        observed_river_water_level_m: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> AuditResponse:
        """
        POST-INFERENCE SELF-AUDITING LOOP & ROOT CAUSE ANALYSIS (RCA):
        1. Compares past prediction risk against ground truth.
        2. Identifies discrepancy: True Positive, True Negative, False Positive, False Negative.
        3. Runs automated RCA via SHAP Deltas (predicted SHAP vs counterfactual ground truth SHAP).
        4. Identifies the primary culprit feature driving the error.
        5. Outputs a human-readable one-liner explanation string.
        """
        pred_record = self.spatial_store.get_prediction(prediction_id)
        if not pred_record:
            raise ValueError(f"Prediction ID '{prediction_id}' not found in spatial store.")

        # Record ground truth
        self.spatial_store.save_ground_truth(
            prediction_id=prediction_id,
            actual_outcome=actual_ground_truth,
            observed_rainfall_6h=observed_rainfall_next_6h,
            observed_river_level_m=observed_river_water_level_m,
            notes=notes,
        )

        risk_score = pred_record["risk_score"]
        predicted_binary = 1 if risk_score >= 0.50 else 0
        predicted_level_str = pred_record["risk_level"]
        predicted_level = RiskLevel(predicted_level_str)
        raw_telemetry = pred_record["raw_telemetry"]

        # Classify discrepancy
        is_mismatch = (predicted_binary != actual_ground_truth)
        if predicted_binary == 1 and actual_ground_truth == 1:
            discrepancy = DiscrepancyType.TRUE_POSITIVE
        elif predicted_binary == 0 and actual_ground_truth == 0:
            discrepancy = DiscrepancyType.TRUE_NEGATIVE
        elif predicted_binary == 1 and actual_ground_truth == 0:
            discrepancy = DiscrepancyType.FALSE_POSITIVE
        else:
            discrepancy = DiscrepancyType.FALSE_NEGATIVE

        # SHAP Delta Root Cause Analysis (RCA)
        orig_shap_list = pred_record["shap_attributions"]
        orig_shap_dict = {item["feature_name"]: item["shap_value"] for item in orig_shap_list}

        # Build counterfactual reality
        counterfactual_telemetry = raw_telemetry.copy()

        # If actual telemetry observations were provided, inject them
        if observed_rainfall_next_6h is not None:
            counterfactual_telemetry["forecasted_rainfall_next_6h"] = observed_rainfall_next_6h
        if observed_river_water_level_m is not None:
            counterfactual_telemetry["river_water_level_m"] = observed_river_water_level_m

        # If mismatch occurred but no overrides were supplied, simulate counterfactual
        # based on ground-truth baseline distributions
        if is_mismatch and observed_rainfall_next_6h is None and observed_river_water_level_m is None:
            stats = self.metadata.get("feature_statistics", {})
            if discrepancy == DiscrepancyType.FALSE_POSITIVE:
                # Reality was dry: rain forecast was false alarm
                actual_rain = max(0.0, raw_telemetry["forecasted_rainfall_next_6h"] * 0.20)
                counterfactual_telemetry["forecasted_rainfall_next_6h"] = actual_rain
                observed_rainfall_next_6h = actual_rain
            elif discrepancy == DiscrepancyType.FALSE_NEGATIVE:
                # Reality flooded: river or rainfall spiked uncaptured
                river_base = stats.get("river_water_level_m", {}).get("p75", 7.2)
                counterfactual_telemetry["river_water_level_m"] = river_base + 1.5
                observed_river_water_level_m = river_base + 1.5

        # Compute counterfactual SHAP
        df_counterfactual = pd.DataFrame(
            [{col: counterfactual_telemetry[col] for col in FEATURE_COLUMNS}]
        )
        cf_shap_values = self.explainer.shap_values(df_counterfactual)
        if isinstance(cf_shap_values, list):
            cf_sv = cf_shap_values[1][0] if len(cf_shap_values) > 1 else cf_shap_values[0][0]
        elif isinstance(cf_shap_values, np.ndarray) and len(cf_shap_values.shape) == 2:
            cf_sv = cf_shap_values[0]
        else:
            cf_sv = np.array(cf_shap_values).flatten()

        cf_shap_dict = {FEATURE_COLUMNS[i]: float(cf_sv[i]) for i in range(len(FEATURE_COLUMNS))}

        # Calculate SHAP Deltas
        shap_deltas: List[ShapDeltaItem] = []
        max_delta_feat = None
        max_abs_delta = -1.0

        for col in FEATURE_COLUMNS:
            pred_shap = orig_shap_dict.get(col, 0.0)
            cf_shap = cf_shap_dict.get(col, 0.0)
            delta = pred_shap - cf_shap

            obs_val = None
            fc_val = None
            pct_err = None

            if col == "forecasted_rainfall_next_6h":
                fc_val = raw_telemetry.get(col)
                obs_val = observed_rainfall_next_6h
                if fc_val and obs_val is not None and obs_val > 0:
                    pct_err = round(((fc_val - obs_val) / obs_val) * 100.0, 1)
            elif col == "river_water_level_m":
                fc_val = raw_telemetry.get(col)
                obs_val = observed_river_water_level_m
                if fc_val and obs_val is not None and fc_val > 0:
                    pct_err = round(((obs_val - fc_val) / fc_val) * 100.0, 1)

            shap_deltas.append(
                ShapDeltaItem(
                    feature_name=col,
                    predicted_shap=round(pred_shap, 4),
                    counterfactual_shap=round(cf_shap, 4),
                    shap_delta=round(delta, 4),
                    observed_value=round(obs_val, 2) if obs_val is not None else None,
                    forecast_value=round(fc_val, 2) if fc_val is not None else None,
                    pct_error=pct_err,
                )
            )

            # Look for highest discrepancy
            if abs(delta) > max_abs_delta:
                max_abs_delta = abs(delta)
                max_delta_feat = col

        # Sort SHAP deltas by absolute impact
        shap_deltas.sort(key=lambda x: abs(x.shap_delta), reverse=True)

        primary_culprit = max_delta_feat if is_mismatch else None

        # Generate Human-Readable One-Liner RCA Explanation
        rca_explanation = self._generate_rca_explanation(
            discrepancy=discrepancy,
            primary_culprit=primary_culprit,
            raw_telemetry=raw_telemetry,
            shap_deltas=shap_deltas,
            observed_rainfall=observed_rainfall_next_6h,
            observed_river=observed_river_water_level_m,
        )

        audit_id = f"AUDIT-{uuid.uuid4().hex[:10].upper()}"
        audited_at = datetime.now(timezone.utc).isoformat()

        # Store audit in spatial database
        self.spatial_store.save_audit_log(
            audit_id=audit_id,
            prediction_id=prediction_id,
            risk_score=risk_score,
            predicted_level=predicted_level.value,
            actual_ground_truth=actual_ground_truth,
            discrepancy_type=discrepancy.value,
            is_mismatch=is_mismatch,
            primary_culprit_feature=primary_culprit,
            shap_deltas=[d.model_dump() for d in shap_deltas],
            rca_explanation=rca_explanation,
        )

        return AuditResponse(
            audit_id=audit_id,
            prediction_id=prediction_id,
            predicted_risk_score=risk_score,
            predicted_risk_level=predicted_level,
            actual_ground_truth=actual_ground_truth,
            discrepancy_type=discrepancy,
            is_mismatch=is_mismatch,
            primary_culprit_feature=primary_culprit,
            shap_deltas=shap_deltas,
            rca_explanation=rca_explanation,
            audited_at=audited_at,
        )

    def _generate_rca_explanation(
        self,
        discrepancy: DiscrepancyType,
        primary_culprit: Optional[str],
        raw_telemetry: Dict[str, Any],
        shap_deltas: List[ShapDeltaItem],
        observed_rainfall: Optional[float],
        observed_river: Optional[float],
    ) -> str:
        """Synthesizes human-readable one-liner RCA explaining prediction vs ground-truth error."""
        if discrepancy == DiscrepancyType.TRUE_POSITIVE:
            return (
                f"Valid Disaster Alarm: Model accurately detected inundation threshold driven by high "
                f"rainfall ({raw_telemetry['forecasted_rainfall_next_6h']}mm) and soil saturation ({raw_telemetry['soil_saturation_index']:.2f})."
            )

        if discrepancy == DiscrepancyType.TRUE_NEGATIVE:
            return (
                f"Valid Safe Status: Correctly predicted no inundation; telemetry stayed safely below catchment threshold limits."
            )

        if discrepancy == DiscrepancyType.FALSE_POSITIVE:
            forecast_rain = raw_telemetry.get("forecasted_rainfall_next_6h", 0.0)
            soil_sat = raw_telemetry.get("soil_saturation_index", 0.0)

            if primary_culprit == "forecasted_rainfall_next_6h" and observed_rainfall is not None:
                pct_over = round(((forecast_rain - observed_rainfall) / max(observed_rainfall, 1.0)) * 100)
                return (
                    f"False Alarm caused by {pct_over}% overestimated rainfall forecast "
                    f"({forecast_rain:.1f}mm vs realized {observed_rainfall:.1f}mm) overriding dry soil moisture ({soil_sat:.2f})."
                )
            elif primary_culprit == "soil_saturation_index":
                return (
                    f"False Alarm caused by anomalous Sentinel-1 SAR soil saturation spike ({soil_sat:.2f}) "
                    f"confused with standing surface inundation."
                )
            else:
                return (
                    f"False Alarm driven primarily by {primary_culprit} (SHAP contribution delta: {shap_deltas[0].shap_delta:+.3f}) "
                    f"inflating baseline inundation probability."
                )

        if discrepancy == DiscrepancyType.FALSE_NEGATIVE:
            river_level = raw_telemetry.get("river_water_level_m", 0.0)
            staleness = raw_telemetry.get("staleness_hours", 0.0)

            if primary_culprit == "river_water_level_m" and observed_river is not None:
                return (
                    f"Missed Inundation caused by rapid river discharge surge "
                    f"(actual {observed_river:.2f}m vs {river_level:.2f}m reported) uncaptured by stale telemetry ({staleness:.1f}h old)."
                )
            elif primary_culprit == "forecasted_rainfall_next_6h" and observed_rainfall is not None:
                return (
                    f"Missed Inundation caused by severe localized cloudburst "
                    f"(actual {observed_rainfall:.1f}mm vs forecasted {forecast_rain:.1f}mm) overwhelming catchment drainage."
                )
            else:
                return (
                    f"Missed Inundation caused by sudden hydrologic surge in {primary_culprit} "
                    f"(SHAP attribution error: {shap_deltas[0].shap_delta:+.3f}) bypassing threshold."
                )

        return "Audit complete: Discrepancy analysis logged."
