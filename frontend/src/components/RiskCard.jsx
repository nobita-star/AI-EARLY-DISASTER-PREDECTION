import React from 'react';
import { AlertTriangle, CloudRain, Droplets, Waves, ShieldAlert, Gauge, Activity, Clock } from 'lucide-react';

export default function RiskCard({ data, isRunning }) {
  if (!data) {
    return (
      <div className="bg-[#0e1628] border border-rose-900/30 rounded-xl p-6 flex flex-col justify-center items-center text-center min-h-[360px] text-slate-500 font-mono text-xs">
        <AlertTriangle className="w-8 h-8 text-rose-500/40 mb-2" />
        <p>AWAITING T-24h SIMULATION TRIGGER</p>
      </div>
    );
  }

  // 1. Overall Landscape Multi-Hazard Risk (XGBoost AI Model) - PRESERVED UNCHANGED
  const landscapeRisk = data.predicted_risk ?? 0;
  const landscapeCategory = data.risk_category || 'UNKNOWN';
  const confidence = data.confidence_indicator ?? 0.85;
  const uncertainty = data.uncertainty_level || 'LOW';

  // 2. Dedicated Rainfall Risk (Meteorological Standard) - SEPARATE INDICATOR
  const rainRiskObj = data.rainfall_risk || {};
  const currentRainValue = rainRiskObj.current_rainfall_value ?? (data.rainfall ?? 0);
  const rainUnit = rainRiskObj.unit || 'mm/day';
  const rainRiskPct = typeof rainRiskObj.rainfall_risk_percentage === 'number'
    ? rainRiskObj.rainfall_risk_percentage
    : (currentRainValue <= 15.5 ? 20.0 : currentRainValue <= 64.4 ? 45.0 : currentRainValue <= 115.5 ? 72.0 : 88.0);
  const rainCategory = rainRiskObj.rainfall_risk_category || (
    rainRiskPct >= 80 ? 'CRITICAL' : rainRiskPct >= 60 ? 'HIGH' : rainRiskPct >= 30 ? 'MODERATE' : 'LOW'
  );
  const rainSource = rainRiskObj.source_status || (data.data_source === 'real' ? 'Open-Meteo Global NWP' : 'Calibrated Telemetry Buffer');
  const isFallback = rainRiskObj.is_fallback ?? false;

  // Badge styles
  const landscapeBadgeColor =
    landscapeCategory === 'SEVERE' || landscapeCategory === 'CRITICAL'
      ? 'bg-rose-900/60 border-rose-600 text-rose-200'
      : landscapeCategory === 'HIGH'
      ? 'bg-orange-900/60 border-orange-600 text-orange-200'
      : 'bg-amber-900/60 border-amber-600 text-amber-200';

  const rainBadgeColor =
    rainCategory === 'CRITICAL'
      ? 'bg-rose-950/80 border-rose-600 text-rose-300'
      : rainCategory === 'HIGH'
      ? 'bg-orange-950/80 border-orange-600 text-orange-300'
      : rainCategory === 'MODERATE'
      ? 'bg-amber-950/80 border-amber-600 text-amber-300'
      : 'bg-emerald-950/80 border-emerald-600 text-emerald-300';

  return (
    <div className="bg-[#0f172a] border-2 border-rose-600/70 rounded-xl p-5 shadow-xl shadow-rose-950/20 relative flex flex-col justify-between">
      
      {/* Tactical Top Tag */}
      <div>
        <div className="flex items-center justify-between border-b border-rose-900/40 pb-3 mb-4">
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping" />
            <h3 className="font-mono font-bold text-rose-400 text-sm tracking-wide">
              STAGE 1: T-24h EARLY WARNING
            </h3>
          </div>
          <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border ${landscapeBadgeColor}`}>
            {landscapeCategory} HAZARD
          </span>
        </div>

        {/* 1. Primary Metric: Landscape Risk Meter (XGBoost compound multi-hazard) */}
        <div className="bg-[#0b101f] border border-slate-800 rounded-lg p-3.5 mb-3">
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center space-x-1.5">
              <Gauge className="w-3.5 h-3.5 text-rose-400" />
              <span className="text-xs font-mono text-slate-300 uppercase font-semibold">PREDICTED LANDSCAPE RISK</span>
            </div>
            <span className="text-xl font-bold font-mono text-rose-400">{landscapeRisk}%</span>
          </div>

          {/* Progress Bar Meter */}
          <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden p-0.5">
            <div
              className="bg-gradient-to-r from-amber-500 via-orange-500 to-rose-600 h-full rounded-full transition-all duration-1000"
              style={{ width: `${Math.min(100, Math.max(5, landscapeRisk))}%` }}
            />
          </div>

          <div className="flex justify-between items-center text-[9px] font-mono text-slate-500 mt-1">
            <span>0% SAFE</span>
            <span>50% MODERATE</span>
            <span className="text-rose-400">100% SEVERE (XGBoost)</span>
          </div>
        </div>

        {/* 2. Dedicated Section: Meteorological Rainfall Risk (IMD Standards) */}
        <div className="bg-[#080e1e] border-2 border-cyan-800/70 rounded-lg p-3.5 mb-4 shadow-inner">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-2.5">
            <div className="flex items-center space-x-1.5">
              <CloudRain className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-mono text-cyan-300 font-bold uppercase tracking-wider">
                RAINFALL RISK INTELLIGENCE
              </span>
            </div>
            <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${rainBadgeColor}`}>
              {rainCategory}
            </span>
          </div>

          {/* Rainfall Key-Value Display conforming to prompt requirements */}
          <div className="grid grid-cols-2 gap-2 text-xs font-mono mb-2.5">
            <div className="bg-slate-900/90 border border-slate-800/80 p-2 rounded">
              <div className="text-[10px] text-slate-400">Current Rainfall</div>
              <div className="text-sm font-bold text-cyan-200 mt-0.5">
                {currentRainValue} <span className="text-xs font-normal text-slate-400">{rainUnit}</span>
              </div>
            </div>

            <div className="bg-slate-900/90 border border-slate-800/80 p-2 rounded">
              <div className="text-[10px] text-slate-400">Rainfall Risk %</div>
              <div className="text-sm font-bold text-cyan-300 mt-0.5">
                {rainRiskPct}%
              </div>
            </div>
          </div>

          {/* Dedicated Rainfall Risk Progress Bar */}
          <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden p-0.5 mb-2">
            <div
              className="bg-gradient-to-r from-emerald-400 via-cyan-400 via-amber-400 to-rose-500 h-full rounded-full transition-all duration-700"
              style={{ width: `${Math.min(100, Math.max(5, rainRiskPct))}%` }}
            />
          </div>

          {/* Source Status & Label */}
          <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-1 border-t border-slate-800/60">
            <span className="truncate max-w-[200px]" title={rainSource}>
              Source: <b className={isFallback ? 'text-amber-400' : 'text-emerald-400'}>{rainSource}</b>
            </span>
            <span className="text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">
              {isFallback ? 'FALLBACK/DEMO' : 'LIVE'}
            </span>
          </div>
        </div>

        {/* 8-Hour Early Warning Sequential Forecast Block */}
        {data.eight_hour_forecast && (
          <div className="bg-[#0c1427] border border-indigo-900/60 rounded-lg p-3 mb-3">
            <div className="flex items-center justify-between border-b border-indigo-950 pb-1.5 mb-2">
              <div className="flex items-center space-x-1.5">
                <Clock className="w-3.5 h-3.5 text-indigo-400" />
                <span className="text-[11px] font-mono text-indigo-300 font-bold uppercase">
                  8-HOUR SEQUENTIAL FORECAST (LSTM)
                </span>
              </div>
              <span className={`px-2 py-0.2 rounded text-[9px] font-mono font-bold ${
                data.warning_status === 'EARLY_WARNING' ? 'bg-rose-950 text-rose-300 border border-rose-700' :
                data.warning_status === 'ADVISORY' ? 'bg-amber-950 text-amber-300 border border-amber-700' :
                'bg-emerald-950 text-emerald-300 border border-emerald-700'
              }`}>
                {data.warning_status || 'NOMINAL'}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono">
              <div className="bg-slate-900/80 p-1.5 rounded border border-slate-800">
                <div className="text-[9px] text-slate-400">NOW</div>
                <div className="font-bold text-white mt-0.5">
                  {Number(data.eight_hour_forecast.current_risk || landscapeRisk).toFixed(1)}%
                </div>
              </div>
              <div className="bg-slate-900/80 p-1.5 rounded border border-slate-800">
                <div className="text-[9px] text-slate-400">+8 HOURS</div>
                <div className="font-bold text-rose-400 mt-0.5">
                  {Number(data.eight_hour_forecast.forecast_risk_8h || landscapeRisk).toFixed(1)}%
                </div>
              </div>
              <div className="bg-slate-900/80 p-1.5 rounded border border-slate-800">
                <div className="text-[9px] text-slate-400">LEAD TIME</div>
                <div className="font-bold text-cyan-300 mt-0.5">
                  {data.eight_hour_forecast.lead_time_to_critical_hours !== null && data.eight_hour_forecast.lead_time_to_critical_hours !== undefined
                    ? `~${Number(data.eight_hour_forecast.lead_time_to_critical_hours).toFixed(1)}h`
                    : '>8h'}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 3. Hydrological Environmental Telemetry Grid */}
        <div className="grid grid-cols-2 gap-2 text-xs font-mono mb-4">
          <div className="bg-slate-900/80 border border-slate-800 p-2 rounded flex items-center space-x-2">
            <CloudRain className="w-4 h-4 text-cyan-400" />
            <div>
              <div className="text-[10px] text-slate-500">ANTECEDENT RAIN</div>
              <div className="font-bold text-slate-200">{data.rainfall ?? '--'} mm</div>
            </div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 p-2 rounded flex items-center space-x-2">
            <CloudRain className="w-4 h-4 text-rose-400" />
            <div>
              <div className="text-[10px] text-slate-500">NWP FORECAST RAIN</div>
              <div className="font-bold text-rose-300">{data.forecast_rainfall ?? '--'} mm</div>
            </div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 p-2 rounded flex items-center space-x-2">
            <Droplets className="w-4 h-4 text-blue-400" />
            <div>
              <div className="text-[10px] text-slate-500">SOIL SATURATION</div>
              <div className="font-bold text-slate-200">
                {typeof data.soil_saturation === 'number' ? (data.soil_saturation * 100).toFixed(1) + '%' : '--'}
              </div>
            </div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 p-2 rounded flex items-center space-x-2">
            <Waves className="w-4 h-4 text-amber-400" />
            <div>
              <div className="text-[10px] text-slate-500">RIVER STAGE</div>
              <div className="font-bold text-slate-200">{data.river_level ?? '--'} m</div>
            </div>
          </div>
        </div>

        {/* 4. Dynamic Geospatial Impact Assessment Strip */}
        {data.impact_assessment && (
          <div className="bg-[#0b101f] border border-cyan-900/40 rounded-lg p-2.5 mb-3 font-mono">
            <div className="flex items-center justify-between text-[10px] text-cyan-400 font-bold mb-1.5 pb-1 border-b border-slate-800">
              <span className="uppercase tracking-wider">GEOSPATIAL IMPACT ASSESSMENT</span>
              <span className="text-[9px] text-slate-400">{data.impact_assessment.demographic_zone || 'GIS OVERLAY'}</span>
            </div>
            <div className="grid grid-cols-4 gap-1.5 text-center">
              <div className="bg-slate-900/90 p-1.5 rounded border border-slate-800">
                <div className="text-[8px] text-slate-400">AREA</div>
                <div className="font-extrabold text-cyan-300 text-xs mt-0.5">{data.impact_assessment.affected_land_area_km2} km²</div>
              </div>
              <div className="bg-slate-900/90 p-1.5 rounded border border-slate-800">
                <div className="text-[8px] text-slate-400">POPULATION</div>
                <div className="font-extrabold text-purple-300 text-xs mt-0.5">
                  {Number(data.impact_assessment.population_exposed).toLocaleString()}
                </div>
              </div>
              <div className="bg-slate-900/90 p-1.5 rounded border border-slate-800">
                <div className="text-[8px] text-slate-400">CROPLAND</div>
                <div className="font-extrabold text-amber-300 text-xs mt-0.5">{data.impact_assessment.agricultural_area_at_risk_hectares} Ha</div>
              </div>
              <div className="bg-slate-900/90 p-1.5 rounded border border-slate-800">
                <div className="text-[8px] text-slate-400">ROADS</div>
                <div className="font-extrabold text-rose-300 text-xs mt-0.5">{data.impact_assessment.roads_interrupted} {data.impact_assessment.roads_interrupted === 1 ? 'Corridor' : 'Corridors'}</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Model Attribution Footer */}
      <div className="border-t border-slate-800/80 pt-3 text-[11px] font-mono text-slate-400">
        <div className="flex justify-between items-center">
          <span className="text-slate-500">PRIMARY DRIVER:</span>
          <span className="text-amber-300 font-semibold">{data.top_contributing_feature}</span>
        </div>
        <div className="flex justify-between items-center mt-1">
          <span className="text-slate-500">CONFIDENCE INDEX:</span>
          <span className="text-cyan-300">{(confidence * 100).toFixed(1)}% ({uncertainty} UNCERTAINTY)</span>
        </div>
      </div>

    </div>
  );
}
