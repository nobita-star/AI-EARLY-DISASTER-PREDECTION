"""
validation.py - Satellite Ground-Truth Spatial Validation Layer
SIH Problem Statement ID: 260001

Implements:
1. Spatial intersection metrics: Intersection over Union (IoU), Precision, Recall, Dice/F1.
2. Comparison between AI predicted inundation extent and observed Sentinel-1 SAR water masks.
3. Strict scientific boundaries: Satellite imagery represents post-hoc observation, NOT the prediction.
"""

from typing import Dict, Any, List, Optional, Union
import numpy as np


class SatelliteValidationEngine:
    """
    Validates model spatial footprints against observed satellite-derived flood masks.
    Supports either raster grids (2D binary matrices) or polygon area overlap inputs.
    """

    @staticmethod
    def calculate_raster_spatial_metrics(
        predicted_mask: np.ndarray,
        observed_satellite_mask: np.ndarray
    ) -> Dict[str, Any]:
        """
        Calculates spatial overlap metrics between predicted flood extent raster
        and ground-truth satellite water mask (e.g. Sentinel-1 SAR thresholded mask).

        Metrics:
        - IoU (Intersection over Union / Jaccard Index) = TP / (TP + FP + FN)
        - Precision = TP / (TP + FP)
        - Recall = TP / (TP + FN)
        - F1-Score (Dice Similarity Coefficient) = 2*TP / (2*TP + FP + FN)
        """
        if predicted_mask.shape != observed_satellite_mask.shape:
            raise ValueError(
                f"Shape mismatch: predicted shape {predicted_mask.shape} != "
                f"observed shape {observed_satellite_mask.shape}"
            )

        # Convert to boolean binary representations
        pred_bool = predicted_mask.astype(bool)
        obs_bool = observed_satellite_mask.astype(bool)

        tp = int(np.sum(pred_bool & obs_bool))
        fp = int(np.sum(pred_bool & ~obs_bool))
        fn = int(np.sum(~pred_bool & obs_bool))
        tn = int(np.sum(~pred_bool & ~obs_bool))

        total_pixels = int(predicted_mask.size)

        # Intersection over Union (Jaccard Index)
        union = tp + fp + fn
        iou = round(float(tp / union), 4) if union > 0 else 1.0

        # Spatial Precision
        precision = round(float(tp / (tp + fp)), 4) if (tp + fp) > 0 else 0.0

        # Spatial Recall (Sensitivity to true flooded terrain)
        recall = round(float(tp / (tp + fn)), 4) if (tp + fn) > 0 else 0.0

        # Dice Similarity Coefficient / F1
        dice_f1 = round(float((2.0 * tp) / (2.0 * tp + fp + fn)), 4) if (2 * tp + fp + fn) > 0 else 0.0

        accuracy = round(float((tp + tn) / total_pixels), 4) if total_pixels > 0 else 0.0

        return {
            "intersection_over_union_iou": iou,
            "precision": precision,
            "recall": recall,
            "dice_f1_score": dice_f1,
            "pixel_accuracy": accuracy,
            "contingency_counts": {
                "true_positive_pixels": tp,
                "false_positive_pixels": fp,
                "false_negative_pixels": fn,
                "true_negative_pixels": tn,
                "total_pixels_evaluated": total_pixels,
            },
            "satellite_sensor": "Copernicus Sentinel-1 SAR C-Band (Ground-Truth)",
            "validation_notice": (
                "Validation metrics quantify spatial agreement between model-projected "
                "inundation extent and verified satellite radar observations. "
                "Satellite imagery is treated strictly as an observational validator, NOT the prediction."
            ),
        }

    @staticmethod
    def calculate_vector_overlap_metrics(
        predicted_area_km2: float,
        observed_area_km2: float,
        intersection_area_km2: float
    ) -> Dict[str, Any]:
        """
        Computes spatial metrics when polygon geometric vectors have already been intersected.
        """
        union_area = (predicted_area_km2 + observed_area_km2) - intersection_area_km2
        iou = round(intersection_area_km2 / union_area, 4) if union_area > 0 else 0.0
        precision = round(intersection_area_km2 / predicted_area_km2, 4) if predicted_area_km2 > 0 else 0.0
        recall = round(intersection_area_km2 / observed_area_km2, 4) if observed_area_km2 > 0 else 0.0
        f1 = round((2.0 * precision * recall) / (precision + recall), 4) if (precision + recall) > 0 else 0.0

        return {
            "intersection_over_union_iou": iou,
            "precision": precision,
            "recall": recall,
            "dice_f1_score": f1,
            "predicted_area_km2": round(predicted_area_km2, 2),
            "observed_area_km2": round(observed_area_km2, 2),
            "intersection_area_km2": round(intersection_area_km2, 2),
            "union_area_km2": round(union_area, 2),
            "validation_notice": (
                "Vector spatial validation computed via geometric polygon intersection. "
                "Satellite-derived SAR flood polygons are treated as empirical ground truth."
            ),
        }
