"""
simulation.py - Hydrodynamic Physics Layer & What-If Scenario Engine
SIH Problem Statement ID: 260001

Implements:
1. Pluggable abstract interface for physics-based numerical solvers (HEC-RAS, Delft3D, SPH).
2. "Physics-Inspired MVP Simulation" fallback modeling open-channel Manning conveyance and hydrograph propagation.
3. Scenario Engine for interactive What-If evaluations (Baseline vs Altered Scenario).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd


class BaseHydrodynamicSolver(ABC):
    """
    Abstract interface for numerical hydrodynamic solvers.
    Enables future integration with HEC-RAS 2D, Delft3D-FM, or SPH (Smoothed Particle Hydrodynamics)
    solvers without modifying upstream API or frontend contracts.
    """

    @abstractmethod
    def solve_flood_wave_propagation(
        self,
        inflow_m3s: float,
        channel_slope_deg: float,
        manning_n: float,
        duration_hours: float
    ) -> Dict[str, Any]:
        """Calculates flood wave front velocity, peak depth, and inundated footprint."""
        pass


class PhysicsInspiredMVPSimulator(BaseHydrodynamicSolver):
    """
    Fallback 1D/2D kinematic physics simulator.
    Solves Manning's equation for open channel hydraulics and Darcy's infiltration balance.
    Clearly designated in all outputs as 'Physics-Inspired MVP Simulation'.
    """

    SOLVER_NAME = "Physics-Inspired MVP Simulation"
    STATUS = "READY"

    def __init__(self, default_manning_n: float = 0.035):
        # Manning's roughness coefficient for natural channels with vegetation/debris
        self.default_manning_n = default_manning_n

    def solve_flood_wave_propagation(
        self,
        inflow_m3s: float,
        channel_slope_deg: float,
        manning_n: Optional[float] = None,
        duration_hours: float = 24.0
    ) -> Dict[str, Any]:
        """
        Solves Manning's formula: V = (1/n) * R_h^(2/3) * S^(1/2)
        Calculates peak flood wave velocity and estimated inundation volume.
        """
        n = manning_n or self.default_manning_n
        slope_rad = np.radians(max(0.01, channel_slope_deg))
        energy_slope = np.sin(slope_rad)

        # Simplified trapezoidal channel geometry approximation
        bottom_width = 25.0  # meters
        estimated_depth = (inflow_m3s / (bottom_width * 2.0)) ** 0.6
        hydraulic_radius = (bottom_width * estimated_depth) / (bottom_width + 2.0 * estimated_depth)

        # Velocity via Manning equation
        velocity_ms = (1.0 / n) * (hydraulic_radius ** (2.0 / 3.0)) * (energy_slope ** 0.5)
        velocity_ms = float(np.clip(velocity_ms, 0.2, 8.5))

        # Wave propagation front distance
        front_distance_km = round((velocity_ms * duration_hours * 3600.0) / 1000.0, 2)

        # Inundation volume proxy (m3)
        total_volume_m3 = round(inflow_m3s * duration_hours * 3600.0, 1)

        return {
            "solver_engine": self.SOLVER_NAME,
            "hydraulic_head_velocity_ms": round(velocity_ms, 2),
            "estimated_propagation_distance_km": front_distance_km,
            "discharge_volume_m3": total_volume_m3,
            "stage_depth_m": round(float(estimated_depth), 2),
            "is_simplified_mvp": True,
            "notice": (
                "Simulation computed via kinematic Manning formulation. "
                "This serves as a physics-inspired fallback; full 2D Saint-Venant PDE solvers "
                "(e.g. HEC-RAS, Delft3D) can be docked through BaseHydrodynamicSolver."
            ),
        }

    def simulate_discharge_flux(
        self,
        rainfall_mm: float,
        soil_saturation: float,
        river_level: float,
        surcharge_factor: float = 0.0
    ) -> float:
        """
        Estimates total hydrograph peak inflow (m3/s) based on Rational Method Q = C * I * A
        plus extreme meteorological storm surge / channel surcharge factor.
        """
        basin_area_km2 = 150.0  # Normalized drainage basin
        # Infiltration runoff coefficient C modulated by soil saturation
        runoff_coeff = 0.15 + 0.75 * (soil_saturation ** 1.5)
        rainfall_intensity_mmh = rainfall_mm / 24.0

        # Runoff flow in m3/s
        q_runoff = (runoff_coeff * rainfall_intensity_mmh * basin_area_km2) / 3.6

        # River baseline baseflow
        baseflow = 12.0 * (river_level ** 1.8)

        # Extreme hydrologic channel surcharge pulse
        surcharge_discharge = surcharge_factor * 450.0  # m3/s additional flash flood volume

        total_inflow_m3s = q_runoff + baseflow + surcharge_discharge
        return float(round(total_inflow_m3s, 2))


class ScenarioEngine:
    """
    Evaluates sensitivity and what-if hypotheses:
    Compares Baseline conditions with user-manipulated parameter variations.
    """

    def __init__(self, model_engine, feature_engineer, physics_sim: PhysicsInspiredMVPSimulator):
        self.model_engine = model_engine
        self.feature_engineer = feature_engineer
        self.physics_sim = physics_sim

    def run_what_if_scenario(
        self,
        baseline_params: Dict[str, Any],
        what_if_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes parallel predictions for Baseline vs What-If parameter states.
        Quantifies risk difference, physics-inspired flow dynamics, and impact summary.
        """
        # 1. Evaluate baseline
        df_base, src_base = self.feature_engineer.process_input(baseline_params)
        b_risk, b_cat, b_conf, b_unc, _ = self.model_engine.predict_risk(df_base)

        # 2. Merge baseline with scenario modifications
        merged_params = dict(baseline_params)
        merged_params.update(what_if_params)

        df_scenario, src_scenario = self.feature_engineer.process_input(merged_params)
        s_risk, s_cat, s_conf, s_unc, s_diag = self.model_engine.predict_risk(df_scenario)

        # Calculate differential impacts
        risk_delta = round(s_risk - b_risk, 2)

        # Compute list of altered features
        changed_features: Dict[str, Dict[str, Any]] = {}
        for k, new_v in what_if_params.items():
            old_v = baseline_params.get(k)
            if old_v != new_v and new_v is not None:
                changed_features[k] = {
                    "baseline": old_v,
                    "what_if": new_v,
                    "delta": round(float(new_v) - float(old_v), 2) if isinstance(new_v, (int, float)) and isinstance(old_v, (int, float)) else "modified"
                }

        # Hydrodynamic flow projection for scenario
        rain_val = float(merged_params.get("rainfall", 0.0)) + float(merged_params.get("forecast_rainfall", 0.0)) * 0.4
        soil_sat = float(merged_params.get("soil_saturation", 0.5))
        riv_lvl = float(merged_params.get("river_level", 2.5))
        surcharge = float(merged_params.get("surcharge_factor", merged_params.get("breach_factor", 0.0)))
        slope = float(merged_params.get("slope", 5.0))

        simulated_inflow = self.physics_sim.simulate_discharge_flux(
            rainfall_mm=rain_val,
            soil_saturation=soil_sat,
            river_level=riv_lvl,
            surcharge_factor=surcharge
        )
        hydro_res = self.physics_sim.solve_flood_wave_propagation(
            inflow_m3s=simulated_inflow,
            channel_slope_deg=slope,
            duration_hours=24.0
        )

        # Formulate contextual impact summary
        if risk_delta > 15.0:
            impact_summary = (
                f"Elevated hazard scenario: Risk surges by +{risk_delta}% (to {s_risk}%, {s_cat}). "
                f"Physical discharge expands to {simulated_inflow} m³/s with flood wave reaching "
                f"{hydro_res['estimated_propagation_distance_km']} km within 24h."
            )
        elif risk_delta < -15.0:
            impact_summary = (
                f"Mitigated scenario: Disaster risk drops by {abs(risk_delta)}% (to {s_risk}%, {s_cat}). "
                f"Basin storage and lowered precipitation moderate peak hydraulic discharge to {simulated_inflow} m³/s."
            )
        else:
            impact_summary = (
                f"Moderate scenario shift: Net risk variation is {risk_delta:+0.2f}% (currently {s_risk}%, {s_cat}). "
                f"Peak discharge estimated at {simulated_inflow} m³/s."
            )

        return {
            "baseline": {
                "risk_percentage": b_risk,
                "risk_category": b_cat,
                "confidence_indicator": b_conf,
                "uncertainty_level": b_unc,
            },
            "what_if": {
                "risk_percentage": s_risk,
                "risk_category": s_cat,
                "confidence_indicator": s_conf,
                "uncertainty_level": s_unc,
            },
            "comparison": {
                "risk_delta_percentage": risk_delta,
                "changed_features": changed_features,
                "impact_summary": impact_summary,
                "hydrodynamic_simulation": hydro_res,
            }
        }
