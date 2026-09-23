import React, { useEffect, useRef, useState } from 'react';
import { Map, Crosshair, Navigation, Layers, ShieldCheck, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';

const CATCHMENTS = [
  // --- NORTHEAST INDIA (PS ID 260001) ---
  { id: 'BRAHMAPUTRA_GUWAHATI', name: 'Assam: Guwahati (Brahmaputra Floodplain)', lat: 26.1850, lon: 91.7500, slope: 2.8, elev: 54.0 },
  { id: 'BRAHMAPUTRA_MAJULI', name: 'Assam: Majuli Island (Alluvial Basin)', lat: 26.9600, lon: 94.2200, slope: 1.2, elev: 84.0 },
  { id: 'DIKRONG_ITANAGAR', name: 'Arunachal: Itanagar (Dikrong Basin)', lat: 27.0970, lon: 93.6150, slope: 14.5, elev: 320.0 },
  { id: 'SIANG_PASIGHAT', name: 'Arunachal: Pasighat (Siang Gorge)', lat: 28.0660, lon: 95.3260, slope: 12.0, elev: 155.0 },
  { id: 'CHERRAPUNJI_SOHRA', name: 'Meghalaya: Cherrapunji (Sohra Plateau)', lat: 25.2700, lon: 91.7300, slope: 18.2, elev: 1430.0 },
  { id: 'DOYANG_KOHIMA', name: 'Nagaland: Kohima (Doyang Ridge)', lat: 25.6701, lon: 94.1077, slope: 16.8, elev: 1444.0 },
  { id: 'DHANSIRI_DIMAPUR', name: 'Nagaland: Dimapur (Dhansiri Floodplain)', lat: 25.9068, lon: 93.7274, slope: 2.2, elev: 145.0 },
  { id: 'IMPHAL_LOKTAK', name: 'Manipur: Imphal & Loktak Catchment', lat: 24.8170, lon: 93.9368, slope: 1.4, elev: 780.0 },
  { id: 'TLAWNG_AIZAWL', name: 'Mizoram: Aizawl (Tlawng Escarpment)', lat: 23.7271, lon: 92.7176, slope: 21.5, elev: 1132.0 },
  { id: 'HOWRAH_AGARTALA', name: 'Tripura: Agartala (Howrah Basin)', lat: 23.8315, lon: 91.2868, slope: 1.6, elev: 15.0 },
  { id: 'TEESTA_MANGAN', name: 'Sikkim: Mangan (Upper Teesta Alpine Gorge)', lat: 27.5050, lon: 88.5330, slope: 24.0, elev: 1310.0 },
  // --- OTHER MONITORED BASINS ---
  { id: 'MITHI_MUMBAI', name: 'Mumbai (Mithi Coastal Basin)', lat: 19.0760, lon: 72.8777, slope: 1.5, elev: 8.0 },
  { id: 'YAMUNA_DELHI', name: 'Delhi NCR (Yamuna Barrage Zone)', lat: 28.6600, lon: 77.2300, slope: 1.2, elev: 204.0 },
  { id: 'PERIYAR_KOCHI', name: 'Kerala Ghats (Periyar Basin)', lat: 10.1076, lon: 76.3516, slope: 5.8, elev: 12.0 },
  { id: 'GODAVARI_RAJAHMUNDRY', name: 'Andhra Delta (Godavari Basin)', lat: 16.9891, lon: 81.7840, slope: 1.8, elev: 14.0 },
  { id: 'KOSI_BIHAR', name: 'North Bihar (Kosi Silt Plain)', lat: 26.5180, lon: 87.0140, slope: 0.8, elev: 72.0 },
];

export default function CommandMap({ backendUrl, onLocationSelect }) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const polygonLayerRef = useRef(null);
  const gpsMarkerRef = useRef(null);

  const [selectedCatchment, setSelectedCatchment] = useState('MITHI_MUMBAI');
  const [currentCoords, setCurrentCoords] = useState({ lat: 19.0760, lon: 72.8777 });
  const [mapRiskData, setMapRiskData] = useState({
    riskPercentage: 78.5,
    riskCategory: 'HIGH',
    elevation: 8.0,
    slope: 1.5,
    locationName: 'Mumbai (Mithi Coastal Basin)',
  });
  const [isLocating, setIsLocating] = useState(false);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current) return;
    if (mapInstanceRef.current) return;

    const L = window.L;
    if (!L) return;

    const map = L.map(mapContainerRef.current, {
      zoomControl: true,
      attributionControl: false,
    }).setView([currentCoords.lat, currentCoords.lon], 11);

    // Default White GIS Basemap (CartoDB Positron)
    const baseLight = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      subdomains: 'abcd',
    }).addTo(map);

    L.control
      .attribution({ prefix: false })
      .addAttribution('LandscapeAI GIS • Earth Observation & Topographic Risk Intelligence')
      .addTo(map);

    mapInstanceRef.current = map;

    // Render Initial 4-Tier Risk Zones
    renderRiskTiers(currentCoords.lat, currentCoords.lon, mapRiskData.riskPercentage, map);

    // Map Click Listener
    map.on('click', async (e) => {
      const { lat, lng } = e.latlng;
      setCurrentCoords({ lat, lon: lng });
      await handleLocationInspect(lat, lng, `Custom Coordinate (${lat.toFixed(3)}°N, ${lng.toFixed(3)}°E)`);
    });

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // 4-Tier Risk Zone Renderer
  const renderRiskTiers = (lat, lon, riskPct, map = mapInstanceRef.current) => {
    const L = window.L;
    if (!L || !map) return;

    if (polygonLayerRef.current) {
      map.removeLayer(polygonLayerRef.current);
    }

    const group = L.layerGroup();
    const baseRadiusKm = Math.max(0.6, (riskPct / 100.0) * 4.2);

    const tiers = [
      { mult: 2.8, color: '#10b981', fillOpacity: 0.12, name: 'Tier 4: Peripheral Monitored Buffer', badge: 'SAFE BUFFER' },
      { mult: 2.0, color: '#f59e0b', fillOpacity: 0.20, name: 'Tier 3: Advisory Alert Perimeter', badge: 'MODERATE WATCH' },
      { mult: 1.4, color: '#f97316', fillOpacity: 0.32, name: 'Tier 2: High Vulnerability Buffer', badge: 'WARNING ZONE' },
      { mult: 1.0, color: '#ef4444', fillOpacity: 0.45, name: 'Tier 1: Critical Runoff / Inundation Zone', badge: 'CRITICAL HAZARD' },
    ];

    tiers.forEach((t) => {
      const radiusKm = baseRadiusKm * t.mult;
      const latDeg = radiusKm / 111.0;
      const lonDeg = radiusKm / (111.0 * Math.cos((lat * Math.PI) / 180));
      const coords = [];
      const numPts = 28;
      for (let i = 0; i < numPts; i++) {
        const angle = (2 * Math.PI * i) / numPts;
        const r = 1.0 + 0.2 * Math.sin(3 * angle + t.mult);
        coords.push([lat + r * Math.sin(angle) * latDeg, lon + r * Math.cos(angle) * lonDeg]);
      }
      coords.push(coords[0]);

      const poly = L.polygon(coords, {
        color: t.color,
        fillColor: t.color,
        fillOpacity: t.fillOpacity,
        weight: 2,
        dashArray: t.mult > 2.0 ? '4, 4' : null,
      }).bindPopup(`
        <div style="font-family: monospace; font-size: 11px;">
          <strong style="color: #0f172a; display: block; margin-bottom: 2px;">${t.name}</strong>
          <div>Radius: ~${radiusKm.toFixed(1)} km</div>
          <div>Predicted Risk: <b>${riskPct.toFixed(1)}%</b></div>
          <div style="margin-top: 4px; color: ${t.color}; font-weight: bold;">Status: ${t.badge}</div>
        </div>
      `);
      group.addLayer(poly);
    });

    group.addTo(map);
    polygonLayerRef.current = group;
  };

  // Inspect Location with Live Environmental Telemetry & ML Inference
  const handleLocationInspect = async (lat, lon, locName) => {
    try {
      let tel = {
        rainfall: 48.0,
        forecast_rainfall: 55.0,
        soil_saturation: 0.65,
        slope: 2.5,
        river_level: 3.2,
      };
      let rainRiskData = null;
      let elev = 12.0;

      // 1. Fetch live meteorological & environmental telemetry
      try {
        const liveRes = await api.getLiveTelemetry(lat, lon, null, backendUrl);
        if (liveRes && liveRes.telemetry) {
          tel = {
            rainfall: Number(liveRes.telemetry.rainfall) || 0.0,
            forecast_rainfall: Number(liveRes.telemetry.forecast_rainfall) || 0.0,
            soil_saturation: Number(liveRes.telemetry.soil_saturation) || 0.45,
            slope: Number(liveRes.telemetry.slope) || 2.5,
            river_level: Number(liveRes.telemetry.river_level) || 2.0,
          };
          if (liveRes.location && typeof liveRes.location.elevation_m === 'number') {
            elev = liveRes.location.elevation_m;
          }
          if (liveRes.rainfall_risk) {
            rainRiskData = liveRes.rainfall_risk;
          }
        }
      } catch (telErr) {
        console.debug('Live telemetry notice:', telErr);
      }

      // 2. Multi-hazard XGBoost prediction for Landscape Risk (preserved)
      const payload = {
        rainfall: tel.rainfall,
        forecast_rainfall: tel.forecast_rainfall,
        soil_saturation: tel.soil_saturation,
        slope: tel.slope,
        river_level: tel.river_level,
        latitude: lat,
        longitude: lon,
      };

      let riskPct = 78.5;
      let category = 'HIGH';
      try {
        const pred = await api.predictRisk(payload, backendUrl);
        if (pred && typeof pred.risk_percentage === 'number') {
          riskPct = pred.risk_percentage;
          category = pred.risk_category;
          if (pred.rainfall_risk) {
            rainRiskData = pred.rainfall_risk;
          }
        }
      } catch (err) {
        console.debug('Predict call notice:', err);
      }

      setMapRiskData({
        riskPercentage: riskPct,
        riskCategory: category,
        elevation: elev,
        slope: tel.slope,
        rainfall: tel.rainfall,
        forecastRainfall: tel.forecast_rainfall,
        rainfallRisk: rainRiskData,
        locationName: locName,
      });

      renderRiskTiers(lat, lon, riskPct);
      if (onLocationSelect) {
        onLocationSelect({
          lat,
          lon,
          riskPercentage: riskPct,
          category,
          locationName: locName,
          rainfall: tel.rainfall,
          forecastRainfall: tel.forecast_rainfall,
          rainfallRisk: rainRiskData,
          elevation: elev,
        });
      }
    } catch (e) {
      console.warn('Inspect location error:', e);
    }
  };

  // Handle Preset Catchment Change
  const handleCatchmentSelect = (cId) => {
    setSelectedCatchment(cId);
    const target = CATCHMENTS.find((c) => c.id === cId);
    if (!target) return;

    setCurrentCoords({ lat: target.lat, lon: target.lon });
    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo([target.lat, target.lon], 11, { duration: 1.2 });
    }
    handleLocationInspect(target.lat, target.lon, target.name);
  };

  // Handle GPS Geolocation
  const handleGpsLocate = () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser.');
      return;
    }

    setIsLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setIsLocating(false);
        const { latitude: lat, longitude: lon } = pos.coords;
        setCurrentCoords({ lat, lon });

        const L = window.L;
        if (L && mapInstanceRef.current) {
          if (gpsMarkerRef.current) {
            mapInstanceRef.current.removeLayer(gpsMarkerRef.current);
          }
          const marker = L.circleMarker([lat, lon], {
            radius: 8,
            fillColor: '#0284c7',
            color: '#ffffff',
            weight: 3,
            opacity: 1,
            fillOpacity: 1,
          }).addTo(mapInstanceRef.current).bindPopup('<b>Your GPS Location</b>');

          gpsMarkerRef.current = marker;
          mapInstanceRef.current.flyTo([lat, lon], 12, { duration: 1.4 });
        }

        handleLocationInspect(lat, lon, 'Your Device GPS Coordinates');
      },
      (err) => {
        setIsLocating(false);
        alert(`GPS location error: ${err.message}`);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  };

  return (
    <div className="bg-[#0c1427] border border-slate-800 rounded-xl overflow-hidden shadow-xl mb-8">
      {/* Map Header Toolbar */}
      <div className="p-3.5 border-b border-slate-800 bg-[#0b101f] flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
        <div className="flex items-center space-x-2">
          <Map className="w-4 h-4 text-cyan-400" />
          <h3 className="font-bold text-white uppercase tracking-wider">
            Satellite Geospatial Risk Command Center
          </h3>
          <span className="text-[10px] text-slate-500 hidden sm:inline">
            • CartoDB Positron White GIS Basemap
          </span>
        </div>

        <div className="flex items-center space-x-2.5 flex-wrap">
          {/* Catchment Preset Dropdown */}
          <div className="flex items-center space-x-1.5 bg-slate-900 border border-slate-800 rounded px-2.5 py-1">
            <Navigation className="w-3.5 h-3.5 text-cyan-400" />
            <select
              value={selectedCatchment}
              onChange={(e) => handleCatchmentSelect(e.target.value)}
              className="bg-transparent text-slate-200 text-xs focus:outline-none cursor-pointer"
            >
              {CATCHMENTS.map((c) => (
                <option key={c.id} value={c.id} className="bg-slate-900">
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* GPS Button */}
          <button
            onClick={handleGpsLocate}
            disabled={isLocating}
            className="flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-cyan-300 transition text-xs font-bold"
          >
            <Crosshair className={`w-3.5 h-3.5 ${isLocating ? 'animate-spin' : ''}`} />
            <span>{isLocating ? 'LOCATING...' : 'GPS'}</span>
          </button>
        </div>
      </div>

      {/* Map Container */}
      <div className="relative">
        <div ref={mapContainerRef} className="w-full h-[460px] bg-white z-10" />

        {/* Floating Top-Left Terrain Profile HUD */}
        <div className="absolute top-3 left-3 z-[400] bg-slate-900/95 border border-slate-700/80 rounded-lg p-3 shadow-xl backdrop-blur max-w-xs text-xs font-mono pointer-events-auto">
          <div className="flex items-center justify-between border-b border-slate-800 pb-1.5 mb-2">
            <span className="font-bold text-white flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              TERRAIN PROFILE
            </span>
            <span
              className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                mapRiskData.riskPercentage >= 75
                  ? 'bg-rose-950 text-rose-300 border border-rose-700'
                  : 'bg-amber-950 text-amber-300 border border-amber-700'
              }`}
            >
              {mapRiskData.riskCategory}
            </span>
          </div>

          <div className="space-y-1 text-slate-300 text-[11px]">
            <div>
              Sector: <b className="text-white">{mapRiskData.locationName}</b>
            </div>
            <div className="grid grid-cols-2 gap-2 pt-1 border-t border-slate-800/80">
              <div>
                SRTM Elev: <b className="text-cyan-300">{mapRiskData.elevation} m</b>
              </div>
              <div>
                Slope: <b className="text-cyan-300">{mapRiskData.slope}°</b>
              </div>
            </div>
            {mapRiskData.rainfall !== undefined && (
              <div className="grid grid-cols-2 gap-2 pt-1 border-t border-slate-800/80 text-[10px]">
                <div>
                  Rainfall: <b className="text-cyan-300">{mapRiskData.rainfall} mm/day</b>
                </div>
                <div>
                  Rain Risk: <b className="text-amber-300">
                    {mapRiskData.rainfallRisk ? `${mapRiskData.rainfallRisk.rainfall_risk_percentage}%` : '--'}
                  </b>
                </div>
              </div>
            )}
            <div className="pt-1 text-rose-400 font-bold flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Landscape Risk: {mapRiskData.riskPercentage.toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* Floating Bottom-Left 4-Tier Risk Legend */}
        <div className="absolute bottom-3 left-3 z-[400] bg-slate-900/95 border border-slate-700/80 rounded-lg p-2.5 shadow-xl backdrop-blur text-[11px] font-mono pointer-events-auto flex items-center gap-3 flex-wrap">
          <span className="font-bold text-slate-300 uppercase tracking-wider text-[10px]">
            4-TIER RISK ZONES:
          </span>
          <span className="flex items-center gap-1 text-rose-400">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500" /> Critical (Tier 1)
          </span>
          <span className="flex items-center gap-1 text-orange-400">
            <span className="w-2.5 h-2.5 rounded-full bg-orange-500" /> Warning (Tier 2)
          </span>
          <span className="flex items-center gap-1 text-amber-400">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Watch (Tier 3)
          </span>
          <span className="flex items-center gap-1 text-emerald-400">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Safe Buffer (Tier 4)
          </span>
        </div>

        {/* Floating Bottom-Right Status */}
        <div className="absolute bottom-3 right-3 z-[400] bg-slate-900/90 border border-slate-700/80 rounded px-2.5 py-1 text-[10px] font-mono text-slate-400 pointer-events-none flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>WHITE GIS BASAL CARTOGRAPHY • READY</span>
        </div>
      </div>
    </div>
  );
}
