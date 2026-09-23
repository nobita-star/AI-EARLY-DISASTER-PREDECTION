"""
spatial_store.py - SQLite & PostGIS Emulation Layer for Disaster Management Engine
Problem Statement ID: 260001

Provides spatial indexing, bounding box intersections (ST_Intersects, ST_Contains),
Haversine proximity queries (ST_DWithin), and SQLite persistence for predictions,
telemetry, ground truth observations, and automated audit logs.
"""

import json
import math
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


class SpatialGeometry:
    """PostGIS emulation geometry helper (WGS84 Lat/Lon coordinates)."""

    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculates Great-Circle distance between two points in km (Haversine formula)."""
        r = 6371.0  # Earth's mean radius in km
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c

    @staticmethod
    def st_dwithin(lat1: float, lon1: float, lat2: float, lon2: float, distance_km: float) -> bool:
        """PostGIS ST_DWithin emulation: Returns True if distance <= distance_km."""
        return SpatialGeometry.haversine_distance_km(lat1, lon1, lat2, lon2) <= distance_km

    @staticmethod
    def st_contains_bbox(
        min_lat: float, min_lon: float, max_lat: float, max_lon: float, lat: float, lon: float
    ) -> bool:
        """PostGIS ST_Contains emulation for bounding boxes."""
        return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon

    @staticmethod
    def st_intersects_bbox(
        bbox1: Tuple[float, float, float, float], bbox2: Tuple[float, float, float, float]
    ) -> bool:
        """PostGIS ST_Intersects emulation between two bounding boxes (min_lat, min_lon, max_lat, max_lon)."""
        min_lat1, min_lon1, max_lat1, max_lon1 = bbox1
        min_lat2, min_lon2, max_lat2, max_lon2 = bbox2
        return not (
            max_lat1 < min_lat2
            or min_lat1 > max_lat2
            or max_lon1 < min_lon2
            or min_lon1 > max_lon2
        )


# Reference Hydrological Catchments mimicking GIS Layer
MOCK_CATCHMENTS = [
    {
        "catchment_id": "CATCHMENT_DELTA_01",
        "name": "Coastal Delta Lowlands",
        "type": "Alluvial Delta",
        "vulnerability_index": 0.88,
        "bbox": (18.90, 72.75, 19.35, 73.15),  # (min_lat, min_lon, max_lat, max_lon)
        "critical_river_stage_m": 6.8,
    },
    {
        "catchment_id": "CATCHMENT_VALLEY_02",
        "name": "North Mountain Valley Basin",
        "type": "Steep Gorge / Flash Corridor",
        "vulnerability_index": 0.72,
        "bbox": (19.36, 72.80, 19.90, 73.40),
        "critical_river_stage_m": 8.5,
    },
    {
        "catchment_id": "CATCHMENT_URBAN_03",
        "name": "Metro Central Floodplain",
        "type": "Impervious Urban Drainage",
        "vulnerability_index": 0.94,
        "bbox": (18.80, 72.80, 19.15, 72.98),
        "critical_river_stage_m": 5.5,
    },
    {
        "catchment_id": "CATCHMENT_HIGHLAND_04",
        "name": "Eastern Highland Plateau",
        "type": "Elevated Escarpment",
        "vulnerability_index": 0.25,
        "bbox": (19.00, 73.41, 19.70, 74.20),
        "critical_river_stage_m": 12.0,
    },
]

MOCK_RIVER_GAUGES = [
    {"gauge_id": "GAUGE_D01", "name": "Delta Outflow Gauge", "lat": 19.05, "lon": 72.90, "flood_stage_m": 6.5},
    {"gauge_id": "GAUGE_V02", "name": "Valley Narrow Gauge", "lat": 19.55, "lon": 73.10, "flood_stage_m": 8.0},
    {"gauge_id": "GAUGE_U03", "name": "Urban Sluice Gauge", "lat": 18.95, "lon": 72.85, "flood_stage_m": 5.2},
]


class SpatialStore:
    """SQLite-backed spatial and audit repository."""

    def __init__(self, db_path: str = "disaster_engine.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initializes relational tables for spatial predictions and self-audit records."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS predictions (
                    prediction_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    elevation_m REAL,
                    catchment_id TEXT,
                    raw_telemetry TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    risk_level TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    confidence_breakdown TEXT NOT NULL,
                    shap_attributions TEXT NOT NULL,
                    base_value REAL NOT NULL
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS ground_truth (
                    prediction_id TEXT PRIMARY KEY,
                    actual_outcome INTEGER NOT NULL,
                    observed_rainfall_6h REAL,
                    observed_river_level_m REAL,
                    recorded_at TEXT NOT NULL,
                    notes TEXT
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    audit_id TEXT PRIMARY KEY,
                    prediction_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    predicted_level TEXT NOT NULL,
                    actual_ground_truth INTEGER NOT NULL,
                    discrepancy_type TEXT NOT NULL,
                    is_mismatch INTEGER NOT NULL,
                    primary_culprit_feature TEXT,
                    shap_deltas TEXT NOT NULL,
                    rca_explanation TEXT NOT NULL,
                    FOREIGN KEY (prediction_id) REFERENCES predictions (prediction_id)
                )
                """
            )
            conn.commit()

    def find_catchment(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Spatial query: Identifies the catchment basin containing the given coordinates."""
        for catchment in MOCK_CATCHMENTS:
            min_lat, min_lon, max_lat, max_lon = catchment["bbox"]
            if SpatialGeometry.st_contains_bbox(min_lat, min_lon, max_lat, max_lon, lat, lon):
                return {
                    "catchment_id": catchment["catchment_id"],
                    "name": catchment["name"],
                    "type": catchment["type"],
                    "vulnerability_index": catchment["vulnerability_index"],
                    "critical_river_stage_m": catchment["critical_river_stage_m"],
                }
        return None

    def find_nearby_gauges(self, lat: float, lon: float, radius_km: float = 35.0) -> List[Dict[str, Any]]:
        """Spatial query: Returns all hydrometric river gauges within radius_km."""
        results = []
        for gauge in MOCK_RIVER_GAUGES:
            dist = SpatialGeometry.haversine_distance_km(lat, lon, gauge["lat"], gauge["lon"])
            if dist <= radius_km:
                g = gauge.copy()
                g["distance_km"] = round(dist, 2)
                results.append(g)
        results.sort(key=lambda x: x["distance_km"])
        return results

    def save_prediction(
        self,
        prediction_id: str,
        timestamp: str,
        telemetry: Dict[str, Any],
        risk_score: float,
        risk_level: str,
        confidence_score: float,
        confidence_breakdown: Dict[str, Any],
        shap_attributions: List[Dict[str, Any]],
        base_value: float,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        elevation_m: Optional[float] = None,
        catchment_id: Optional[str] = None,
    ) -> None:
        """Stores prediction inference snapshot."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO predictions (
                    prediction_id, timestamp, latitude, longitude, elevation_m, catchment_id,
                    raw_telemetry, risk_score, risk_level, confidence_score,
                    confidence_breakdown, shap_attributions, base_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    prediction_id,
                    timestamp,
                    latitude,
                    longitude,
                    elevation_m,
                    catchment_id,
                    json.dumps(telemetry),
                    risk_score,
                    risk_level,
                    confidence_score,
                    json.dumps(confidence_breakdown),
                    json.dumps(shap_attributions),
                    base_value,
                ),
            )
            conn.commit()

    def get_prediction(self, prediction_id: str) -> Optional[Dict[str, Any]]:
        """Fetches stored prediction record by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM predictions WHERE prediction_id = ?", (prediction_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "prediction_id": row["prediction_id"],
                "timestamp": row["timestamp"],
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "elevation_m": row["elevation_m"],
                "catchment_id": row["catchment_id"],
                "raw_telemetry": json.loads(row["raw_telemetry"]),
                "risk_score": row["risk_score"],
                "risk_level": row["risk_level"],
                "confidence_score": row["confidence_score"],
                "confidence_breakdown": json.loads(row["confidence_breakdown"]),
                "shap_attributions": json.loads(row["shap_attributions"]),
                "base_value": row["base_value"],
            }

    def save_ground_truth(
        self,
        prediction_id: str,
        actual_outcome: int,
        observed_rainfall_6h: Optional[float] = None,
        observed_river_level_m: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> None:
        """Records ground truth verification for a past prediction."""
        now_str = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO ground_truth (
                    prediction_id, actual_outcome, observed_rainfall_6h, observed_river_level_m, recorded_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (prediction_id, actual_outcome, observed_rainfall_6h, observed_river_level_m, now_str, notes),
            )
            conn.commit()

    def save_audit_log(
        self,
        audit_id: str,
        prediction_id: str,
        risk_score: float,
        predicted_level: str,
        actual_ground_truth: int,
        discrepancy_type: str,
        is_mismatch: bool,
        primary_culprit_feature: Optional[str],
        shap_deltas: List[Dict[str, Any]],
        rca_explanation: str,
    ) -> None:
        """Stores audit log record with RCA conclusions."""
        now_str = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO audit_logs (
                    audit_id, prediction_id, timestamp, risk_score, predicted_level,
                    actual_ground_truth, discrepancy_type, is_mismatch,
                    primary_culprit_feature, shap_deltas, rca_explanation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id,
                    prediction_id,
                    now_str,
                    risk_score,
                    predicted_level,
                    actual_ground_truth,
                    discrepancy_type,
                    1 if is_mismatch else 0,
                    primary_culprit_feature,
                    json.dumps(shap_deltas),
                    rca_explanation,
                ),
            )
            conn.commit()

    def get_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves historical audit logs ordered by recent timestamp."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            logs = []
            for row in rows:
                logs.append(
                    {
                        "audit_id": row["audit_id"],
                        "prediction_id": row["prediction_id"],
                        "timestamp": row["timestamp"],
                        "risk_score": row["risk_score"],
                        "predicted_level": row["predicted_level"],
                        "actual_ground_truth": row["actual_ground_truth"],
                        "discrepancy_type": row["discrepancy_type"],
                        "is_mismatch": bool(row["is_mismatch"]),
                        "primary_culprit_feature": row["primary_culprit_feature"],
                        "shap_deltas": json.loads(row["shap_deltas"]),
                        "rca_explanation": row["rca_explanation"],
                    }
                )
            return logs

    def get_audit_summary(self) -> Dict[str, Any]:
        """Calculates executive audit metrics (accuracy, false alarm rate, missed disaster rate, culprit breakdown)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_logs")
            rows = cursor.fetchall()

            total = len(rows)
            if total == 0:
                return {
                    "total_audits": 0,
                    "correct_predictions": 0,
                    "false_positives": 0,
                    "false_negatives": 0,
                    "accuracy": 1.0,
                    "false_alarm_rate": 0.0,
                    "missed_disaster_rate": 0.0,
                    "culprit_feature_distribution": {},
                    "recent_logs": [],
                }

            tp = sum(1 for r in rows if r["discrepancy_type"] == "TRUE_POSITIVE")
            tn = sum(1 for r in rows if r["discrepancy_type"] == "TRUE_NEGATIVE")
            fp = sum(1 for r in rows if r["discrepancy_type"] == "FALSE_POSITIVE")
            fn = sum(1 for r in rows if r["discrepancy_type"] == "FALSE_NEGATIVE")

            accuracy = (tp + tn) / total
            false_alarm_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            missed_disaster_rate = fn / (fn + tp) if (fn + tp) > 0 else 0.0

            culprits: Dict[str, int] = {}
            for r in rows:
                culprit = r["primary_culprit_feature"]
                if culprit:
                    culprits[culprit] = culprits.get(culprit, 0) + 1

            recent_logs = [
                {
                    "audit_id": r["audit_id"],
                    "prediction_id": r["prediction_id"],
                    "timestamp": r["timestamp"],
                    "risk_score": r["risk_score"],
                    "predicted_level": r["predicted_level"],
                    "actual_ground_truth": r["actual_ground_truth"],
                    "discrepancy_type": r["discrepancy_type"],
                    "is_mismatch": bool(r["is_mismatch"]),
                    "primary_culprit_feature": r["primary_culprit_feature"],
                    "rca_explanation": r["rca_explanation"],
                }
                for r in rows[:15]
            ]

            return {
                "total_audits": total,
                "correct_predictions": tp + tn,
                "false_positives": fp,
                "false_negatives": fn,
                "accuracy": round(accuracy, 4),
                "false_alarm_rate": round(false_alarm_rate, 4),
                "missed_disaster_rate": round(missed_disaster_rate, 4),
                "culprit_feature_distribution": culprits,
                "recent_logs": recent_logs,
            }
