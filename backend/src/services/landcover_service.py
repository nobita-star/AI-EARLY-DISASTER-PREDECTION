"""
landcover_service.py - Geospatial Land-Use / Land-Cover (LULC) Agricultural Risk Service
SIH Problem Statement ID: 260001

Calculates agricultural cropland and plantation area intersecting predicted disaster risk zones.
Provides pluggable hooks for high-resolution LULC rasters (Copernicus Global Land Cover,
ESA WorldCover 10m, Google Dynamic World) alongside a terrain- and NDVI-grounded
deterministic spatial LULC model.
"""

import math
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("disaster_platform.landcover")

# Regional Land-Cover Profiles (Calibrated agricultural fractions for characteristic ecotones)
REGIONAL_LULC_PROFILES = [
    # Fertile alluvial plains & agricultural heartlands
    {"name": "Majuli Island Brahmaputra Lowlands", "lat": 26.9500, "lon": 94.2000, "radius_km": 40.0, "agri_fraction": 0.68, "primary_crop": "Wetland Paddy, Mustard & Pulses"},
    {"name": "Assam Alluvial Floodplain", "lat": 26.5000, "lon": 92.5000, "radius_km": 150.0, "agri_fraction": 0.62, "primary_crop": "Paddy, Tea Estates & Jute"},
    {"name": "Krishna-Godavari Alluvial Delta", "lat": 16.7000, "lon": 81.2000, "radius_km": 80.0, "agri_fraction": 0.74, "primary_crop": "Irrigated Rice & Sugarcane"},
    {"name": "Northern Bihar River Lowlands", "lat": 26.0000, "lon": 86.0000, "radius_km": 100.0, "agri_fraction": 0.72, "primary_crop": "Wheat, Rice & Maize"},

    # Plantation & terrace escarpments
    {"name": "Wayanad Western Ghats Foothills", "lat": 11.6854, "lon": 76.1320, "radius_km": 40.0, "agri_fraction": 0.45, "primary_crop": "Coffee, Pepper, Rubber & Tea"},
    {"name": "Idukki High Ranges", "lat": 9.8500, "lon": 77.0000, "radius_km": 40.0, "agri_fraction": 0.38, "primary_crop": "Cardamom, Spice Groves & Tea"},
    {"name": "Munnar Escarpment & Tea Slopes", "lat": 10.0889, "lon": 77.0595, "radius_km": 25.0, "agri_fraction": 0.42, "primary_crop": "Highland Tea Plantations"},
    {"name": "Sohra / Cherrapunji Plateau", "lat": 25.2700, "lon": 91.7300, "radius_km": 30.0, "agri_fraction": 0.18, "primary_crop": "Terraced Areca Nut & Broomgrass"},

    # Highly built-up urban cores (minimal agricultural land)
    {"name": "Mumbai Metropolitan Core", "lat": 19.0760, "lon": 72.8777, "radius_km": 25.0, "agri_fraction": 0.03, "primary_crop": "Peri-urban Vegetable Patches"},
    {"name": "Delhi-NCR Urban Basin", "lat": 28.6139, "lon": 77.2090, "radius_km": 28.0, "agri_fraction": 0.06, "primary_crop": "Yamuna Floodplain Vegetables"},
    {"name": "Kolkata Urban Center", "lat": 22.5726, "lon": 88.3639, "radius_km": 22.0, "agri_fraction": 0.04, "primary_crop": "East Kolkata Peri-urban Aquaculture/Greens"},
    {"name": "Chennai Urban Coastal Core", "lat": 13.0827, "lon": 80.2707, "radius_km": 22.0, "agri_fraction": 0.03, "primary_crop": "Urban Margin Horticultures"},

    # Alpine & high-altitude sectors (zero/minimal crops)
    {"name": "Teesta River Valley / Mangan Sikkim", "lat": 27.5000, "lon": 88.5200, "radius_km": 45.0, "agri_fraction": 0.08, "primary_crop": "Highland Cardamom Terraces"},
    {"name": "Kinnaur Sutlej Mountain Gorge", "lat": 31.6500, "lon": 78.4700, "radius_km": 50.0, "agri_fraction": 0.06, "primary_crop": "Apple Orchards on River Terraces"},
    {"name": "Spiti Alpine Cold Desert", "lat": 32.2461, "lon": 78.0349, "radius_km": 60.0, "agri_fraction": 0.01, "primary_crop": "Glacial Snow Pea Micro-patches"},
    {"name": "Leh-Ladakh High Altitude Desert", "lat": 34.1526, "lon": 77.5771, "radius_km": 70.0, "agri_fraction": 0.02, "primary_crop": "Oasis Barley Terraces"},
]


def _haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return r * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


class LandCoverService:
    """
    Geospatial Land-Cover and Agricultural Exposure Service.
    Determines cropland area at risk from predicted landscape disaster perimeter.
    """

    def __init__(self, external_lulc_path: Optional[str] = None):
        self.external_lulc_path = external_lulc_path
        self._has_real_raster = False

    def query_real_lulc_raster(
        self,
        polygon_coords: List[List[float]]
    ) -> Optional[float]:
        """
        Zonal statistics integration hook for ESA WorldCover 10m / Copernicus 100m.
        Returns agricultural hectares if real GeoTIFF is mounted.
        """
        # Pluggable hook for ESA WorldCover Class 40 (Cropland)
        return None

    def get_agricultural_fraction(
        self,
        lat: float,
        lon: float,
        elevation_m: float = 50.0,
        slope_deg: float = 2.0,
        ndvi: float = 0.52
    ) -> Tuple[float, str, str]:
        """
        Calculates deterministic agricultural land fraction [0.0, 1.0] for the location,
        grounded in regional LULC baselines, elevation, slope, and Sentinel-2 optical NDVI.
        """
        nearest_profile = None
        min_dist = float("inf")

        for prof in REGIONAL_LULC_PROFILES:
            dist = _haversine_distance_km(lat, lon, prof["lat"], prof["lon"])
            if dist < min_dist:
                min_dist = dist
                nearest_profile = prof

        if nearest_profile and min_dist <= nearest_profile["radius_km"]:
            base_agri = nearest_profile["agri_fraction"]
            zone_desc = nearest_profile["name"]
            crop_type = nearest_profile["primary_crop"]
        elif nearest_profile and min_dist <= nearest_profile["radius_km"] * 3.0:
            ratio = min_dist / (nearest_profile["radius_km"] * 3.0)
            base_agri = (nearest_profile["agri_fraction"] * (1.0 - ratio)) + (0.45 * ratio)
            zone_desc = f"Transition to {nearest_profile['name']}"
            crop_type = "Mixed Regional Cropland"
        else:
            # General rural Indian agrarian baseline
            base_agri = 0.48
            zone_desc = "Regional Agrarian LULC Grid"
            crop_type = "Seasonal Cereals & Pulses"

        # Optical NDVI Modulation (from Sentinel-2 / Landsat surface reflectance)
        # High NDVI (>0.40) indicates vigorous green vegetative cover (crops / plantations)
        # Low NDVI (<0.20) indicates built-up concrete, bare rock, or open water
        if ndvi < 0.20:
            ndvi_factor = max(0.05, ndvi / 0.20)
            base_agri *= ndvi_factor
        elif ndvi > 0.65:
            base_agri = min(0.85, base_agri * 1.15)

        # Topographic attenuation:
        # Steep slopes (>22 deg) cannot sustain conventional crops; rocky cliffs have 0 agriculture
        if slope_deg > 25.0:
            base_agri = 0.0
            crop_type = "No Agricultural Cropland (Steep Rock/Cliff)"
        elif slope_deg > 14.0:
            slope_factor = max(0.10, 1.0 - (slope_deg - 14.0) * 0.08)
            base_agri *= slope_factor

        # High elevation (>2500m) suppresses agriculture due to frost & sub-zero conditions
        if elevation_m > 2500.0:
            base_agri = 0.0
            crop_type = "No Agricultural Cropland (Alpine Frigid Zone)"
        elif elevation_m > 1600.0:
            elev_factor = max(0.10, 1.0 - (elevation_m - 1600.0) / 1000.0)
            base_agri *= elev_factor

        final_fraction = max(0.0, min(0.90, base_agri))
        return round(final_fraction, 3), zone_desc, crop_type

    def calculate_agricultural_impact(
        self,
        polygon_coords: List[List[float]],
        affected_area_km2: float,
        lat: float,
        lon: float,
        risk_pct: float,
        elevation_m: float = 50.0,
        slope_deg: float = 2.0,
        ndvi: float = 0.52
    ) -> Dict[str, Any]:
        """
        Calculates Agricultural Land at Risk (in hectares and km2).

        Safeguards:
        - If risk_pct < 20.0 or affected_area_km2 <= 0.02: hectares = 0.0.
        - If no agricultural land present: returns 0.0.
        - Never returns negative values.
        - 1 km2 = 100 Hectares.
        """
        # Low risk safeguard
        if risk_pct < 20.0 or affected_area_km2 <= 0.02:
            agri_frac, zone, crop = self.get_agricultural_fraction(lat, lon, elevation_m, slope_deg, ndvi)
            return {
                "agricultural_area_at_risk_hectares": 0.0,
                "agricultural_area_at_risk_km2": 0.0,
                "agricultural_fraction": agri_frac,
                "crop_classification": crop,
                "zone_name": zone,
                "data_source": "PROTOTYPE_DETERMINISTIC_LULC (Copernicus Land Cover / Sentinel-2 Ready)",
                "is_real_data": False,
            }

        # 1. Check real raster provider if configured
        real_ha = self.query_real_lulc_raster(polygon_coords)
        if real_ha is not None:
            ha = max(0.0, float(real_ha))
            return {
                "agricultural_area_at_risk_hectares": round(ha, 1),
                "agricultural_area_at_risk_km2": round(ha / 100.0, 3),
                "agricultural_fraction": round(min(1.0, (ha / 100.0) / max(0.01, affected_area_km2)), 3),
                "crop_classification": "Satellite-Observed Cropland (Class 40)",
                "zone_name": "High-Resolution LULC Raster",
                "data_source": "REAL_LULC_RASTER (Copernicus / ESA WorldCover 10m)",
                "is_real_data": True,
            }

        # 2. Deterministic LULC calculation
        agri_frac, zone, crop = self.get_agricultural_fraction(lat, lon, elevation_m, slope_deg, ndvi)

        # Risk zone intersection: higher risk leads to broader inundation across floodplain fields
        agri_km2 = affected_area_km2 * agri_frac
        agri_ha = agri_km2 * 100.0  # 1 km2 = 100 Hectares

        return {
            "agricultural_area_at_risk_hectares": round(max(0.0, agri_ha), 1),
            "agricultural_area_at_risk_km2": round(max(0.0, agri_km2), 3),
            "agricultural_fraction": agri_frac,
            "crop_classification": crop,
            "zone_name": zone,
            "data_source": "PROTOTYPE_DETERMINISTIC_LULC (Copernicus Land Cover / Sentinel-2 Ready)",
            "is_real_data": False,
        }
