import React from 'react';
import { CheckCircle2, Waves, Droplets, CloudRain, Satellite, Radio, AlertCircle } from 'lucide-react';

export default function GroundTruthCard({ data, isRunning }) {
  if (!data) {
    return (
      <div className="bg-[#0e1628] border border-blue-900/30 rounded-xl p-6 flex flex-col justify-center items-center text-center min-h-[360px] text-slate-500 font-mono text-xs">
        <Satellite className="w-8 h-8 text-blue-500/40 mb-2" />
        <p>AWAITING T-0h TELEMETRY SYNC</p>
      </div>
    );
  }

  const isSafe = data.actual_disaster_status === 'NO_DISASTER';

  return (
    <div className="bg-[#0f172a] border-2 border-blue-500/70 rounded-xl p-5 shadow-xl shadow-blue-950/20 relative flex flex-col justify-between">
      
      {/* Tactical Top Tag */}
      <div>
        <div className="flex items-center justify-between border-b border-blue-900/40 pb-3 mb-4">
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-400" />
            <h3 className="font-mono font-bold text-blue-400 text-sm tracking-wide">
              STAGE 2: T-0h GROUND TRUTH
            </h3>
          </div>
          <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold border bg-blue-950/80 border-blue-600 text-blue-200">
            OBSERVED REALITY
          </span>
        </div>

        {/* Observed Status Outcome Banner */}
        <div className="bg-[#0b101f] border border-slate-800 rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-mono text-slate-400 uppercase">FIELD OBSERVATION OUTCOME</span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-600 text-emerald-300 font-bold">
              {data.actual_disaster_status}
            </span>
          </div>

          <div className="mt-2 text-sm font-mono text-slate-200 flex items-center space-x-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
            <span>Inundation Extent: <strong>{data.observed_inundation_extent_km2 ?? 0.0} km²</strong> (Basin normal)</span>
          </div>

          <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
            {data.description}
          </p>
        </div>

        {/* Ground-Truth Sensor Array Telemetry */}
        <div className="grid grid-cols-2 gap-2 text-xs font-mono mb-4">
          <div className="bg-slate-900/80 border border-slate-800 p-2 rounded flex items-center space-x-2">
            <CloudRain className="w-4 h-4 text-cyan-400" />
            <div>
              <div className="text-[10px] text-slate-500">ACTUAL RAINFALL</div>
              <div className="font-bold text-slate-200">{data.actual_rainfall ?? '--'} mm</div>
            </div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 p-2 rounded flex items-center space-x-2">
            <Waves className="w-4 h-4 text-blue-400" />
            <div>
              <div className="text-[10px] text-slate-500">ACTUAL RIVER GAUGE</div>
              <div className="font-bold text-emerald-400">{data.actual_river_level ?? '--'} m (Safe)</div>
            </div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 p-2 rounded flex items-center space-x-2">
            <Droplets className="w-4 h-4 text-blue-400" />
            <div>
              <div className="text-[10px] text-slate-500">ACTUAL SATURATION</div>
              <div className="font-bold text-slate-200">
                {typeof data.actual_soil_saturation === 'number' ? (data.actual_soil_saturation * 100).toFixed(1) + '%' : '--'}
              </div>
            </div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 p-2 rounded flex items-center space-x-2">
            <Radio className="w-4 h-4 text-emerald-400" />
            <div>
              <div className="text-[10px] text-slate-500">SENSOR INTEGRITY</div>
              <div className="font-bold text-emerald-400">{data.actual_sensor_state}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Discrepancy Note Footer */}
      <div className="border-t border-slate-800/80 pt-3 text-[11px] font-mono text-slate-400">
        <div className="flex justify-between items-center text-amber-300">
          <span className="text-slate-500">PREDICTION VS REALITY:</span>
          <span className="font-semibold">DISCREPANCY DETECTED</span>
        </div>
        <div className="text-[10px] text-slate-500 mt-0.5">
          T-24h Warning predicted severe flood; T-0h confirms no inundation occurred.
        </div>
      </div>

    </div>
  );
}
