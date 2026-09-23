"""
schemas.py - Strictly Typed Pydantic Schemas for Disaster Management Engine
Problem Statement ID: 260001
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DiscrepancyType(str, Enum):
    TRUE_POSITIVE = "TRUE_POSITIVE"
    TRUE_NEGATIVE = "TRUE_NEGATIVE"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    FALSE_NEGATIVE = "FALSE_NEGATIVE"


class GeospatialCoordinates(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    elevation_m: float = Field(default=0.0, description="Elevation above sea level in meters")
    catchment_id: Optional[str] = Field(default=None, description="Hydrographic catchment/basin identifier")


class DisasterTelemetryInput(BaseModel):
    rainfall_last_24h: float = Field(
        ..., ge=0.0, le=1000.0, description="Accumulated rainfall over past 24 hours (mm)"
    )
    forecasted_rainfall_next_6h: float = Field(
        ..., ge=0.0, le=500.0, description="NWP precipitation forecast for next 6 hours (mm)"
    )
    soil_saturation_index: float = Field(
        ..., ge=0.0, le=1.0, description="Sentinel-1 SAR surface soil moisture proxy (0.0 = bone dry, 1.0 = fully saturated)"
    )
    dem_slope_degrees: float = Field(
        ..., ge=0.0, le=90.0, description="SRTM DEM topographic slope in degrees (0 = flat plain, 60 = steep cliff)"
    )
    river_water_level_m: float = Field(
        ..., ge=0.0, le=50.0, description="Hydrometric river gauge stage height in meters"
    )
    staleness_hours: float = Field(
        default=0.5, ge=0.0, le=72.0, description="Age of the most recent telemetry packet in hours"
    )
    sensor_variance: float = Field(
        default=0.05, ge=0.0, le=1.0, description="Normalized sensor noise/variance ratio (0.0 = pristine, 1.0 = erratic)"
    )
    coordinates: Optional[GeospatialCoordinates] = Field(
        default=None, description="Geographic location of telemetry sensor node"
    )


class FeatureAttribution(BaseModel):
    feature_name: str
    feature_value: float
    shap_value: float
    direction: str = Field(description="'INCREASES_RISK' or 'DECREASES_RISK'")
    relative_importance_pct: float


class ConfidenceBreakdown(BaseModel):
    model_certainty: float = Field(..., description="Epistemic model certainty based on distance from decision threshold")
    staleness_penalty: float = Field(..., description="Penalty applied due to aged sensor telemetry")
    variance_penalty: float = Field(..., description="Penalty applied due to sensor noise/uncertainty")
    final_confidence: float = Field(..., description="Combined AI confidence score (0.0 to 1.0)")
    staleness_hours: float
    sensor_variance: float


class PredictionRequest(BaseModel):
    telemetry: DisasterTelemetryInput
    prediction_id: Optional[str] = Field(default=None, description="Optional custom prediction ID")


class PredictionResponse(BaseModel):
    prediction_id: str
    timestamp: str
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Inundation/Flood risk probability")
    risk_level: RiskLevel
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI Confidence Score")
    confidence_breakdown: ConfidenceBreakdown
    top_shap_features: List[FeatureAttribution]
    base_value: float = Field(..., description="SHAP expected base value")
    spatial_context: Optional[dict] = Field(default=None, description="PostGIS mock spatial query result")


class AuditRequest(BaseModel):
    prediction_id: str
    actual_ground_truth: int = Field(..., ge=0, le=1, description="Actual ground truth inundation (1 = flooded, 0 = no flood)")
    observed_rainfall_next_6h: Optional[float] = Field(
        default=None, description="Actual realized rainfall in the 6h window for RCA delta calculation (mm)"
    )
    observed_river_water_level_m: Optional[float] = Field(
        default=None, description="Actual realized river stage level in meters"
    )
    notes: Optional[str] = Field(default=None, description="Field operator commentary")


class ShapDeltaItem(BaseModel):
    feature_name: str
    predicted_shap: float
    counterfactual_shap: float
    shap_delta: float
    observed_value: Optional[float] = None
    forecast_value: Optional[float] = None
    pct_error: Optional[float] = None


class AuditResponse(BaseModel):
    audit_id: str
    prediction_id: str
    predicted_risk_score: float
    predicted_risk_level: RiskLevel
    actual_ground_truth: int
    discrepancy_type: DiscrepancyType
    is_mismatch: bool
    primary_culprit_feature: Optional[str]
    shap_deltas: List[ShapDeltaItem]
    rca_explanation: str
    audited_at: str


class AuditLogRecord(BaseModel):
    audit_id: str
    prediction_id: str
    timestamp: str
    risk_score: float
    predicted_level: str
    actual_ground_truth: int
    discrepancy_type: str
    is_mismatch: bool
    primary_culprit_feature: Optional[str]
    rca_explanation: str


class AuditLogsSummaryResponse(BaseModel):
    total_audits: int
    correct_predictions: int
    false_positives: int
    false_negatives: int
    accuracy: float
    false_alarm_rate: float
    missed_disaster_rate: float
    culprit_feature_distribution: Dict[str, int]
    recent_logs: List[AuditLogRecord]


class TimeTravelStage1(BaseModel):
    stage: str = "T-24h: Pre-Disaster Prediction"
    simulated_time: str
    telemetry_summary: Dict[str, float]
    prediction: PredictionResponse


class TimeTravelStage2(BaseModel):
    stage: str = "T-0h: Ground Truth Arrival"
    simulated_time: str
    actual_inundation_occurred: bool
    actual_telemetry: Dict[str, float]
    discrepancy_observed: str
    telemetry_discrepancies: Dict[str, str]


class TimeTravelStage3(BaseModel):
    stage: str = "T+1h: Automated RCA Audit Loop"
    simulated_time: str
    audit_result: AuditResponse
    model_feedback: str


class TimeTravelSimulationResponse(BaseModel):
    simulation_id: str
    scenario_name: str
    narrative: str
    stage_1_prediction: TimeTravelStage1
    stage_2_ground_truth: TimeTravelStage2
    stage_3_rca_audit: TimeTravelStage3
    system_verdict: str
