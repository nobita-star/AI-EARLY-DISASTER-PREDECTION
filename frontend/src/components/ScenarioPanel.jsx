import React, { useState } from 'react';
import { Sliders, Play, TrendingUp, TrendingDown, Waves, ArrowRight, RotateCcw, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';

export default function ScenarioPanel({ backendUrl, onNotify }) {
  // Baseline initial parameters
  const defaultBaseline = {
    rainfall: 45.0,
    forecast_rainfall: 35.0,
    soil_saturation: 0.55,
    slope: 4.5,
    river_level: 2.8,
  };

  // What-If mutable parameters
  const [whatIfParams, setWhatIfParams] = useState({
    rainfall: 145.0,
    forecast_rainfall: 80.0,
    soil_saturation: 0.85,
    slope: 3.5,
    river_level: 5.4,
    surcharge_factor: 0.25,
  });

  const [isLoading, setIsLoading] = useState(false);
  const [scenarioResult, setScenarioResult] = useState(null);

  const handleSliderChange = (field, value) => {
    setWhatIfParams((prev) => ({
      ...prev,
      [field]: parseFloat(value),
    }));
  };

  const handleRunScenario = async () => {
    setIsLoading(true);
    try {
      const payload = {
        baseline: defaultBaseline,
        what_if: whatIfParams,
      };
      const data = await api.runWhatIfScenario(payload, backendUrl);
      setScenarioResult(data);
    } catch (err) {
      if (onNotify) onNotify(err.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-[#0c1427] border border-slate-800 rounded-xl p-6 shadow-xl mb-8">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800 pb-4 mb-6">
        <div>
          <div className="flex items-center space-x-2">
            <Sliders className="w-5 h-5 text-amber-400" />
            <h3 className="font-mono font-bold text-white text-base tracking-wider uppercase">
              Landscape Multi-Hazard Scenario Simulator
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Simulate hypothetical extreme weather events, slope destabilization, or severe drainage basin surges.
          </p>
        </div>

        <button
          onClick={handleRunScenario}
          disabled={isLoading}
          className="flex items-center justify-center space-x-2 px-5 py-2.5 rounded-lg bg-amber-600 hover:bg-amber-500 disabled:bg-slate-800 text-white font-mono font-bold text-xs tracking-wider transition-all shadow-md"
        >
          <Play className={`w-4 h-4 fill-current ${isLoading ? 'animate-spin' : ''}`} />
          <span>{isLoading ? 'CALCULATING HYPOTHESIS...' : 'EVALUATE WHAT-IF SCENARIO'}</span>
        </button>
      </div>

      {/* Grid: Sliders Controls + Output Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Controls Column (7 Cols) */}
        <div className="lg:col-span-7 space-y-4 font-mono text-xs">
          
          {/* Rainfall Slider */}
          <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-lg">
            <div className="flex justify-between items-center mb-1.5">
              <span className="text-slate-300 font-medium">Precipitation / Antecedent Rain</span>
              <span className="text-cyan-300 font-bold">{whatIfParams.rainfall} mm</span>
            </div>
            <input
              type="range"
              min="0"
              max="250"
              step="5"
              value={whatIfParams.rainfall}
              onChange={(e) => handleSliderChange('rainfall', e.target.value)}
              className="w-full accent-cyan-400 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 mt-1">
              <span>0 mm (Drought)</span>
              <span>Baseline: {defaultBaseline.rainfall} mm</span>
              <span>250 mm (Monsoon Deluge)</span>
            </div>
          </div>

          {/* Forecast Rainfall Slider */}
          <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-lg">
            <div className="flex justify-between items-center mb-1.5">
              <span className="text-slate-300 font-medium">NWP Forecast Precipitation (Next 24h)</span>
              <span className="text-rose-400 font-bold">{whatIfParams.forecast_rainfall} mm</span>
            </div>
            <input
              type="range"
              min="0"
              max="250"
              step="5"
              value={whatIfParams.forecast_rainfall}
              onChange={(e) => handleSliderChange('forecast_rainfall', e.target.value)}
              className="w-full accent-rose-500 cursor-pointer"
            />
          </div>

          {/* Soil Saturation Slider */}
          <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-lg">
            <div className="flex justify-between items-center mb-1.5">
              <span className="text-slate-300 font-medium">Soil Saturation / SAR Wetness Index</span>
              <span className="text-blue-400 font-bold">{(whatIfParams.soil_saturation * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={whatIfParams.soil_saturation}
              onChange={(e) => handleSliderChange('soil_saturation', e.target.value)}
              className="w-full accent-blue-400 cursor-pointer"
            />
          </div>

          {/* River Stage Height Slider */}
          <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-lg">
            <div className="flex justify-between items-center mb-1.5">
              <span className="text-slate-300 font-medium">River Gauge Water Level (Stage)</span>
              <span className="text-amber-400 font-bold">{whatIfParams.river_level} m</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="10.0"
              step="0.1"
              value={whatIfParams.river_level}
              onChange={(e) => handleSliderChange('river_level', e.target.value)}
              className="w-full accent-amber-400 cursor-pointer"
            />
          </div>

          {/* Catchment Runoff Surcharge Factor */}
          <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-lg">
            <div className="flex justify-between items-center mb-1.5">
              <span className="text-slate-300 font-medium">Catchment Runoff Surcharge Pulse</span>
              <span className="text-rose-300 font-bold">{(whatIfParams.surcharge_factor * 100).toFixed(0)}% Surcharge</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={whatIfParams.surcharge_factor}
              onChange={(e) => handleSliderChange('surcharge_factor', e.target.value)}
              className="w-full accent-rose-400 cursor-pointer"
            />
          </div>

        </div>

        {/* Results Column (5 Cols) */}
        <div className="lg:col-span-5 flex flex-col justify-between font-mono text-xs">
          {scenarioResult ? (
            <div className="bg-slate-900/90 border-2 border-amber-600/60 rounded-xl p-5 space-y-4">
              <div className="border-b border-slate-800 pb-2">
                <span className="text-[10px] text-amber-400 font-bold uppercase tracking-wider">
                  HYPOTHESIS IMPACT ASSESSMENT
                </span>
                <h4 className="text-base font-bold text-white mt-0.5">
                  BASELINE VS WHAT-IF DELTA
                </h4>
              </div>

              {/* Side-by-side comparison */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-[#0b101f] border border-slate-800 p-3 rounded-lg text-center">
                  <div className="text-[10px] text-slate-500 uppercase">BASELINE RISK</div>
                  <div className="text-xl font-bold text-slate-300 mt-1">
                    {scenarioResult.baseline.risk_percentage}%
                  </div>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                    {scenarioResult.baseline.risk_category}
                  </span>
                </div>

                <div className="bg-[#0b101f] border border-amber-800/80 p-3 rounded-lg text-center">
                  <div className="text-[10px] text-amber-400 uppercase">WHAT-IF RISK</div>
                  <div className="text-xl font-bold text-rose-400 mt-1">
                    {scenarioResult.what_if.risk_percentage}%
                  </div>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-950/80 border border-rose-700 text-rose-300">
                    {scenarioResult.what_if.risk_category}
                  </span>
                </div>
              </div>

              {/* Risk Delta Badge */}
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between">
                <span className="text-slate-400">NET RISK SHIFT:</span>
                <div className="flex items-center space-x-1.5 font-bold">
                  {scenarioResult.comparison.risk_delta_percentage >= 0 ? (
                    <span className="text-rose-400 flex items-center">
                      <TrendingUp className="w-4 h-4 mr-1" />
                      +{scenarioResult.comparison.risk_delta_percentage}%
                    </span>
                  ) : (
                    <span className="text-emerald-400 flex items-center">
                      <TrendingDown className="w-4 h-4 mr-1" />
                      {scenarioResult.comparison.risk_delta_percentage}%
                    </span>
                  )}
                </div>
              </div>

              {/* Dynamic Impact Summary */}
              <div className="bg-amber-950/30 border border-amber-800/50 p-3 rounded-lg">
                <div className="text-[10px] font-bold text-amber-300 mb-1">HYDRODYNAMIC IMPACT PROJECTION:</div>
                <p className="text-slate-200 text-xs font-sans leading-relaxed">
                  {scenarioResult.comparison.impact_summary}
                </p>
              </div>

              {/* Hydrodynamic Physics Kinematics */}
              {scenarioResult.comparison.hydrodynamic_simulation && (
                <div className="text-[11px] text-slate-400 bg-slate-950 p-2.5 rounded border border-slate-800 space-y-1">
                  <div className="text-[10px] text-cyan-400 font-bold">
                    SOLVER: {scenarioResult.comparison.hydrodynamic_simulation.solver_engine}
                  </div>
                  <div>
                    Wave Front Velocity: <strong>{scenarioResult.comparison.hydrodynamic_simulation.hydraulic_head_velocity_ms} m/s</strong>
                  </div>
                  <div>
                    Estimated 24h Propagation: <strong>{scenarioResult.comparison.hydrodynamic_simulation.estimated_propagation_distance_km} km</strong>
                  </div>
                </div>
              )}

            </div>
          ) : (
            <div className="h-full bg-slate-900/40 border border-dashed border-slate-800 rounded-xl p-8 flex flex-col justify-center items-center text-center text-slate-500">
              <Sliders className="w-8 h-8 text-slate-600 mb-2" />
              <p>Adjust the hydrologic parameter sliders and click 'EVALUATE WHAT-IF SCENARIO' to see differential risk shifts.</p>
            </div>
          )}
        </div>

      </div>

    </div>
  );
}
