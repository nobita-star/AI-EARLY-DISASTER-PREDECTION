"""
user_store.py - Registered User Store & Spatial Geofencing Engine
SIH Problem Statement ID: 260001 - Landscape Disaster Risk Detection

Provides:
1. In-memory / persistent registry of community residents, ward disaster managers, and response units.
2. Geofencing radius search using geodesic Haversine distance calculations.
3. Threshold-based alert filtering (notifying ONLY users inside or proximate to the active hazard zone).
"""

import math
from typing import Dict, Any, List, Optional
import uuid


class RegisteredUserStore:
    """
    Manages registered citizen and response team profiles.
    Executes geofenced proximity matching to ensure alerts are hyper-locally targeted.
    """

    def __init__(self):
        self.users: List[Dict[str, Any]] = [
            # --- 1. ASSAM (Brahmaputra Basin & Majuli) ---
            {
                "user_id": "USR-AS-001",
                "name": "Bipul Kalita",
                "role": "Community Disaster Warden",
                "phone": "+91 98640 12345",
                "latitude": 26.1850,
                "longitude": 91.7500,
                "alert_radius_km": 6.0,
                "preferred_channel": "SMS",
                "risk_threshold_pct": 55.0,
                "ward": "Guwahati North Ward 4",
                "state": "Assam",
            },
            {
                "user_id": "USR-AS-002",
                "name": "Ananya Hazarika",
                "role": "Resident & School Admin",
                "phone": "+91 98642 98765",
                "latitude": 26.1920,
                "longitude": 91.7610,
                "alert_radius_km": 4.0,
                "preferred_channel": "WHATSAPP",
                "risk_threshold_pct": 65.0,
                "ward": "Guwahati Riverside",
                "state": "Assam",
            },
            {
                "user_id": "USR-AS-003",
                "name": "Mridul Saikia",
                "role": "Majuli River Island Field Observer",
                "phone": "+91 98644 33221",
                "latitude": 26.9600,
                "longitude": 94.2200,
                "alert_radius_km": 8.0,
                "preferred_channel": "SMS",
                "risk_threshold_pct": 50.0,
                "ward": "Kamalabari Ghat Sub-Division",
                "state": "Assam",
            },

            # --- 2. ARUNACHAL PRADESH (Papum Pare & East Siang) ---
            {
                "user_id": "USR-AR-001",
                "name": "Tage Tado",
                "role": "District Disaster Management Officer (DDMO)",
                "phone": "+91 94360 11223",
                "latitude": 27.0970,
                "longitude": 93.6150,
                "alert_radius_km": 7.0,
                "preferred_channel": "SMS",
                "risk_threshold_pct": 50.0,
                "ward": "Itanagar Dikrong Sector 5",
                "state": "Arunachal Pradesh",
            },
            {
                "user_id": "USR-AR-002",
                "name": "Oyit Moyong",
                "role": "Community River Gauge Monitor",
                "phone": "+91 94362 44556",
                "latitude": 28.0660,
                "longitude": 95.3260,
                "alert_radius_km": 8.0,
                "preferred_channel": "SMS",
                "risk_threshold_pct": 55.0,
                "ward": "Pasighat Siang Bank Ward 2",
                "state": "Arunachal Pradesh",
            },

            # --- 3. MEGHALAYA (East Khasi Hills & Sohra) ---
            {
                "user_id": "USR-ML-001",
                "name": "Baphanglang Lyngdoh",
                "role": "Rainfall & Escarpment Safety Warden",
                "phone": "+91 94361 77889",
                "latitude": 25.2700,
                "longitude": 91.7300,
                "alert_radius_km": 6.0,
                "preferred_channel": "SMS",
                "risk_threshold_pct": 50.0,
                "ward": "Cherrapunji Sohra Rim Block",
                "state": "Meghalaya",
            },
            {
                "user_id": "USR-ML-002",
                "name": "Ibanylla Warjri",
                "role": "Community Health Volunteer",
                "phone": "+91 94363 88990",
                "latitude": 25.5788,
                "longitude": 91.8933,
                "alert_radius_km": 5.0,
                "preferred_channel": "WHATSAPP",
                "risk_threshold_pct": 60.0,
                "ward": "Shillong Polo Ground Lowlands",
                "state": "Meghalaya",
            },

            # --- 4. NAGALAND (Kohima & Dimapur) ---
            {
                "user_id": "USR-NL-001",
                "name": "Keviselie Angami",
                "role": "Village Council Disaster Coordinator",
                "phone": "+91 94360 55667",
                "latitude": 25.6701,
                "longitude": 94.1077,
                "alert_radius_km": 6.5,
                "preferred_channel": "SMS",
                "risk_threshold_pct": 55.0,
                "ward": "Kohima Doyang Ridge Ward 6",
                "state": "Nagaland",
            },
            {
                "user_id": "USR-NL-002",
                "name": "Temjen Jamir",
                "role": "Civil Defense Volunteer",
                "phone": "+91 94362 66778",
                "latitude": 25.9068,
                "longitude": 93.7274,
                "alert_radius_km": 5.0,
                "preferred_channel": "SMS",
                "risk_threshold_pct": 55.0,
                "ward": "Dimapur Dhansiri Riverbank",
                "state": "Nagaland",
            },

            # --- 5. MANIPUR (Imphal & Loktak) ---
            {
                "user_id": "USR-MN-001",
                "name": "Naobi Meitei",
                "role": "District Emergency Operations Warden",
                "phone": "+91 94361 22334",
                "latitude": 24.8170,
                "longitude": 93.9368,
                "alert_radius_km": 5.5,
                "preferred_channel": "SMS",
                "risk_threshold_pct": 50.0,
                "ward": "Imphal Nambul River Confluence",
                "state": "Manipur",
            },
            {
                "user_id": "USR-MN-002",
                "name": "Linthoingambi Devi",
                "role": "Wetland Ecology & Flood Monitor",
                "phone": "+91 94363 33445",
                "latitude": 24.5500,
                "longitude": 93.8000,
                "alert_radius_km": 7.0,
                "preferred_channel": "WHATSAPP",
                "risk_threshold_pct": 60.0,
                "ward": "Loktak Sendra Island Cluster",
                "state": "Manipur",
            },

            # --- 6. MIZORAM (Aizawl & Tlawng) ---
            {
                "user_id": "USR-MZ-001",
                "name": "Lalrinzuala Sailo",
                "role": "Disaster Response Team Lead (YMA)",
                "phone": "+91 94361 99887",
                "latitude": 23.7271,
                "longitude": 92.7176,
                "alert_radius_km": 6.0,
                "preferred_channel": "SMS",
                "risk_threshold_pct": 50.0,
                "ward": "Aizawl Tlawng River Escarpment",
                "state": "Mizoram",
            },

            # --- 7. TRIPURA (Agartala & Howrah) ---
            {
                "user_id": "USR-TR-001",
                "name": "Subir Debbarma",
                "role": "Municipal Flood Control Supervisor",
                "phone": "+91 94365 44332",
                "latitude": 23.8315,
                "longitude": 91.2868,
                "alert_radius_km": 5.0,
                "preferred_channel": "SMS",
                "risk_threshold_pct": 55.0,
                "ward": "Agartala Howrah Sluice Gate Ward 9",
                "state": "Tripura",
            },

            # --- 8. SIKKIM (Teesta & Mangan) ---
            {
                "user_id": "USR-SK-001",
                "name": "Karma Lepcha",
                "role": "Alpine River & Slope Safety Warden",
                "phone": "+91 94340 77665",
                "latitude": 27.5050,
                "longitude": 88.5330,
                "alert_radius_km": 8.0,
                "preferred_channel": "SMS",
                "risk_threshold_pct": 50.0,
                "ward": "Upper Teesta Mangan North Ward",
                "state": "Sikkim",
            },
            {
                "user_id": "USR-SK-002",
                "name": "Pema Bhutia",
                "role": "Civil Defense Volunteer",
                "phone": "+91 94341 88776",
                "latitude": 27.3389,
                "longitude": 88.6065,
                "alert_radius_km": 6.0,
                "preferred_channel": "WHATSAPP",
                "risk_threshold_pct": 60.0,
                "ward": "Gangtok Ranipool Catchment",
                "state": "Sikkim",
            },

            # --- 9. OTHER STRATEGIC INDIAN BASINS ---
            {
                "user_id": "USR-MH-001",
                "name": "Rajesh Sawant",
                "role": "Ward Officer (MCGM Disaster Cell)",
                "phone": "+91 98200 45678",
                "latitude": 19.0760,
                "longitude": 72.8777,
                "alert_radius_km": 4.5,
                "preferred_channel": "SMS",
                "risk_threshold_pct": 50.0,
                "ward": "Kurla West (Mithi River Bank)",
                "state": "Maharashtra",
            },
            {
                "user_id": "USR-MH-002",
                "name": "Priya Kulkarni",
                "role": "Resident",
                "phone": "+91 98211 88990",
                "latitude": 19.0820,
                "longitude": 72.8850,
                "alert_radius_km": 2.5,
                "preferred_channel": "WHATSAPP",
                "risk_threshold_pct": 60.0,
                "ward": "Bandra East Transit Camp",
                "state": "Maharashtra",
            },
            {
                "user_id": "USR-KL-001",
                "name": "Thomas Mathew",
                "role": "Plantation Safety Lead",
                "phone": "+91 94470 33445",
                "latitude": 10.1076,
                "longitude": 76.3516,
                "alert_radius_km": 6.0,
                "preferred_channel": "SMS",
                "risk_threshold_pct": 55.0,
                "ward": "Munnar Hill Highway NH-85",
                "state": "Kerala",
            },
            {
                "user_id": "USR-KL-002",
                "name": "Lekshmi Nair",
                "role": "Primary Health Centre Coordinator",
                "phone": "+91 94471 66778",
                "latitude": 10.1150,
                "longitude": 76.3620,
                "alert_radius_km": 3.0,
                "preferred_channel": "VOICE",
                "risk_threshold_pct": 70.0,
                "ward": "Devikulam Valley",
                "state": "Kerala",
            },
            {
                "user_id": "USR-DL-001",
                "name": "Suresh Sharma",
                "role": "Irrigation & Flood Control Inspector",
                "phone": "+91 98110 55667",
                "latitude": 28.6600,
                "longitude": 77.2300,
                "alert_radius_km": 4.0,
                "preferred_channel": "SMS",
                "risk_threshold_pct": 55.0,
                "ward": "Old Yamuna Bridge (Loha Pul)",
                "state": "Delhi",
            },
            {
                "user_id": "USR-UK-001",
                "name": "Devendra Rawat",
                "role": "SDRF First Responder",
                "phone": "+91 94120 77889",
                "latitude": 30.5500,
                "longitude": 79.5600,
                "alert_radius_km": 8.0,
                "preferred_channel": "SMS",
                "risk_threshold_pct": 60.0,
                "ward": "Alaknanda Slope Monitoring",
                "state": "Uttarakhand",
            },
        ]

    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculates great-circle distance between two points on Earth using Haversine formula."""
        R = 6371.0  # Earth's radius in kilometers
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2.0) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(R * c, 2)

    def find_users_in_risk_zone(
        self,
        lat: float,
        lon: float,
        risk_radius_km: float = 5.0,
        risk_percentage: float = 65.0,
    ) -> List[Dict[str, Any]]:
        """
        Geofence Filter:
        Matches registered users located inside or within their configured buffer distance
        of the hazard zone, and checks whether the predicted risk meets their configured threshold.
        """
        matched_users: List[Dict[str, Any]] = []

        for user in self.users:
            dist_km = self.haversine_distance_km(lat, lon, user["latitude"], user["longitude"])
            max_effective_radius = risk_radius_km + user.get("alert_radius_km", 2.0)

            # Check spatial containment and risk threshold
            if dist_km <= max_effective_radius and risk_percentage >= user.get("risk_threshold_pct", 50.0):
                matched = dict(user)
                matched["distance_to_epicenter_km"] = dist_km
                matched["in_core_zone"] = dist_km <= risk_radius_km
                matched_users.append(matched)

        # Sort by proximity to epicenter
        matched_users.sort(key=lambda u: u["distance_to_epicenter_km"])
        return matched_users

    def register_user(
        self,
        name: str,
        phone: str,
        latitude: float,
        longitude: float,
        role: str = "Resident",
        alert_radius_km: float = 3.0,
        preferred_channel: str = "SMS",
        risk_threshold_pct: float = 60.0,
        ward: str = "Unassigned Ward",
        state: str = "India",
    ) -> Dict[str, Any]:
        """Registers a new user in the emergency geofencing store."""
        new_user = {
            "user_id": f"USR-{uuid.uuid4().hex[:6].upper()}",
            "name": name.strip(),
            "role": role.strip(),
            "phone": phone.strip(),
            "latitude": float(latitude),
            "longitude": float(longitude),
            "alert_radius_km": float(alert_radius_km),
            "preferred_channel": preferred_channel.upper(),
            "risk_threshold_pct": float(risk_threshold_pct),
            "ward": ward.strip(),
            "state": state.strip(),
        }
        self.users.append(new_user)
        return new_user

    def get_all_users(self) -> List[Dict[str, Any]]:
        return self.users
