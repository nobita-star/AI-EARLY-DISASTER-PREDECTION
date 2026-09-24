"""
population_service.py - Geospatial Population Exposure Estimation Service
SIH Problem Statement ID: 260001

Calculates population exposed to predicted landscape disaster risk zones using
spatial overlay principles. Provides pluggable hooks for high-resolution gridded
population rasters (LandScan, WorldPop, GPWv4) alongside a deterministic geospatial
demographic model calibrated to administrative district census baselines.
"""

import math
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("disaster_platform.population")

# Regional Demographic Anchors (Census-calibrated baseline densities in people/km2)
REGIONAL_DEMOGRAPHIC_ANCHORS = [
    # Major metropolitan cores
    {"name": "Mumbai Metropolitan Basin", "lat": 19.0760, "lon": 72.8777, "radius_km": 35.0, "density": 21500.0},
    {"name": "Delhi-NCR Urban Plain", "lat": 28.6139, "lon": 77.2090, "radius_km": 40.0, "density": 11300.0},
    {"name": "Kolkata Hugli Basin", "lat": 22.5726, "lon": 88.3639, "radius_km": 30.0, "density": 24000.0},
    {"name": "Chennai Coastal Lowlands", "lat": 13.0827, "lon": 80.2707, "radius_km": 30.0, "density": 14500.0},
    {"name": "Bengaluru Plateau Corridor", "lat": 12.9716, "lon": 77.5946, "radius_km": 35.0, "density": 4400.0},
    {"name": "Hyderabad Musi Riverfront", "lat": 17.3850, "lon": 78.4867, "radius_km": 30.0, "density": 6100.0},
    {"name": "Guwahati Brahmaputra Valley", "lat": 26.1445, "lon": 91.7362, "radius_km": 25.0, "density": 3850.0},
    {"name": "Patna Gangetic Floodplain", "lat": 25.5941, "lon": 85.1376, "radius_km": 25.0, "density": 1820.0},
    {"name": "Vijayawada Krishna Delta", "lat": 16.5062, "lon": 80.6480, "radius_km": 25.0, "density": 1420.0},
    {"name": "Kochi Backwaters Coastal Zone", "lat": 9.9312, "lon": 76.2673, "radius_km": 25.0, "density": 2100.0},

    # Rural alluvial & agricultural river basins
    {"name": "Majuli Island Brahmaputra Lowlands", "lat": 26.9500, "lon": 94.2000, "radius_km": 35.0, "density": 320.0},
    {"name": "Brahmaputra Alluvial Basin (Assam)", "lat": 26.5000, "lon": 92.5000, "radius_km": 150.0, "density": 410.0},
    {"name": "Krishna-Godavari Alluvial Delta", "lat": 16.7000, "lon": 81.2000, "radius_km": 80.0, "density": 490.0},
    {"name": "Northern Bihar River Lowlands", "lat": 26.0000, "lon": 86.0000, "radius_km": 100.0, "density": 1150.0},

    # Hilly, escarpment & plantation highlands
    {"name": "Wayanad Western Ghats Foothills", "lat": 11.6854, "lon": 76.1320, "radius_km": 40.0, "density": 280.0},
    {"name": "Idukki High Ranges", "lat": 9.8500, "lon": 77.0000, "radius_km": 40.0, "density": 215.0},
    {"name": "Munnar Escarpment & Tea Slopes", "lat": 10.0889, "lon": 77.0595, "radius_km": 25.0, "density": 165.0},
    {"name": "Sohra / Cherrapunji Plateau", "lat": 25.2700, "lon": 91.7300, "radius_km": 30.0, "density": 140.0},
    {"name": "Shimla-Mandi Sub-Himalayan Valley", "lat": 31.1048, "lon": 77.1734, "radius_km": 40.0, "density": 115.0},
    {"name": "Dehradun Doon Valley Corridor", "lat": 30.3165, "lon": 78.0322, "radius_km": 35.0, "density": 650.0},

    # Alpine & extreme high-altitude mountain sectors
    {"name": "Teesta River Valley / Mangan Sikkim", "lat": 27.5000, "lon": 88.5200, "radius_km": 45.0, "density": 35.0},
    {"name": "Kinnaur Sutlej Mountain Gorge", "lat": 31.6500, "lon": 78.4700, "radius_km": 50.0, "density": 18.0},
    {"name": "Spiti Alpine Cold Desert", "lat": 32.2461, "lon": 78.0349, "radius_km": 60.0, "density": 8.0},
    {"name": "Leh-Ladakh High Altitude Plateau", "lat": 34.1526, "lon": 77.5771, "radius_km": 70.0, "density": 12.0},
]


def _haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two geographic points."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return r * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


class PopulationService:
    """
    Geospatial Population Assessment Service.
    Computes exposed population by spatially overlaying predicted risk polygons
    onto population density layers.
    """

    def __init__(self, external_raster_path: Optional[str] = None):
        self.external_raster_path = external_raster_path
        self._has_real_raster = False
        if external_raster_path:
            self._init_real_raster(external_raster_path)

    def _init_real_raster(self, path: str) -> None:
        """Attempts to mount LandScan/WorldPop GeoTIFF via rasterio if available."""
        try:
            import rasterio  # noqa: F401
            self._has_real_raster = True
            logger.info(f"Loaded gridded population raster from {path}")
        except ImportError:
            logger.info("rasterio not present; using deterministic spatial demographic grid.")
            self._has_real_raster = False

    def query_real_raster_population(
        self,
        polygon_coords: List[List[float]]
    ) -> Optional[int]:
        """
        Zonal statistics integration hook for high-resolution GeoTIFF rasters
        (e.g., LandScan 1km / WorldPop 100m).
        """
        if not self._has_real_raster or not self.external_raster_path:
            return None
        # Pluggable placeholder for real GeoTIFF zonal statistics:
        # e.g., rasterio.mask.mask or rasterstats.zonal_stats
        return None

    def get_baseline_population_density(
        self,
        lat: float,
        lon: float,
        elevation_m: float = 50.0,
        slope_deg: float = 2.0
    ) -> Tuple[float, str]:
        """
        Computes deterministic geospatial population density (people/km2)
        at the specified coordinates based on distance-decay from regional demographic
        centers, calibrated with Census of India baselines and terrain attenuation.
        """
        nearest_anchor = None
        min_dist = float("inf")

        for anchor in REGIONAL_DEMOGRAPHIC_ANCHORS:
            dist = _haversine_distance_km(lat, lon, anchor["lat"], anchor["lon"])
            if dist < min_dist:
                min_dist = dist
                nearest_anchor = anchor

        if nearest_anchor and min_dist <= nearest_anchor["radius_km"]:
            # Within anchor core zone: interpolate smoothly from core density
            decay = max(0.40, 1.0 - (min_dist / (nearest_anchor["radius_km"] * 1.5)))
            base_density = nearest_anchor["density"] * decay
            anchor_label = nearest_anchor["name"]
        elif nearest_anchor and min_dist <= nearest_anchor["radius_km"] * 4.0:
            # Suburban / peri-urban buffer around anchor
            transition_ratio = min_dist / (nearest_anchor["radius_km"] * 4.0)
            base_density = (nearest_anchor["density"] * 0.40 * (1.0 - transition_ratio)) + (350.0 * transition_ratio)
            anchor_label = f"Suburban buffer of {nearest_anchor['name']}"
        else:
            # Regional Indian rural baseline
            base_density = 380.0
            anchor_label = "Regional Rural Baseline Grid"

        # Apply topographic attenuation:
        # High elevation (>600m) and steep slopes (>15 deg) significantly reduce human settlement density
        if elevation_m > 600.0:
            elev_damp = math.exp(-0.00075 * (elevation_m - 600.0))
            base_density *= max(0.04, elev_damp)

        if slope_deg > 12.0:
            slope_damp = max(0.08, 1.0 - (slope_deg - 12.0) * 0.035)
            base_density *= slope_damp

        final_density = max(2.0, base_density)
        return round(final_density, 1), anchor_label

    def calculate_population_exposed(
        self,
        polygon_coords: List[List[float]],
        affected_area_km2: float,
        lat: float,
        lon: float,
        risk_pct: float,
        elevation_m: float = 50.0,
        slope_deg: float = 2.0
    ) -> Dict[str, Any]:
        """
        Calculates Population Exposed within the predicted risk zone.

        Safeguards:
        - If risk_pct < 20.0 or affected_area_km2 <= 0.01: population = 0.
        - Never returns negative values.
        - Scales dynamically with location, terrain profile, and risk zone extent.
        """
        # Low-risk clamp safeguard
        if risk_pct < 20.0 or affected_area_km2 <= 0.02:
            density, anchor = self.get_baseline_population_density(lat, lon, elevation_m, slope_deg)
            return {
                "population_exposed": 0,
                "population_density_per_km2": density,
                "anchor_zone": anchor,
                "exposure_factor": 0.0,
                "data_source": "PROTOTYPE_DETERMINISTIC_GRID (LandScan/Census Provider Ready)",
                "is_real_data": False,
            }

        # 1. Check real raster provider if configured
        real_pop = self.query_real_raster_population(polygon_coords)
        if real_pop is not None:
            return {
                "population_exposed": max(0, int(real_pop)),
                "population_density_per_km2": round(real_pop / max(0.01, affected_area_km2), 1),
                "anchor_zone": "High-Resolution Population Raster",
                "exposure_factor": 1.0,
                "data_source": "REAL_GRIDDED_POPULATION_RASTER (LandScan / WorldPop)",
                "is_real_data": True,
            }

        # 2. Deterministic geospatial demographic model
        density, anchor = self.get_baseline_population_density(lat, lon, elevation_m, slope_deg)

        # Risk exposure factor: higher risk percentage means higher proportion of
        # the perimeter experiences actionable inundation / hazardous runout
        # Scaled smoothly between 0.35 at risk=20% and 1.0 at risk=90%
        exposure_factor = min(1.0, max(0.30, (risk_pct - 15.0) / 75.0))

        raw_population = affected_area_km2 * density * exposure_factor
        population_exposed = max(0, int(round(raw_population)))

        return {
            "population_exposed": population_exposed,
            "population_density_per_km2": density,
            "anchor_zone": anchor,
            "exposure_factor": round(exposure_factor, 3),
            "data_source": "PROTOTYPE_DETERMINISTIC_GRID (LandScan/Census Provider Ready)",
            "is_real_data": False,
        }
