import React from 'react';
import { Play, RotateCcw, FastForward, CheckCircle, Clock, AlertCircle } from 'lucide-react';

export default function Timeline({
  onRunSimulation,
  isLoading,
  currentStage,
  hasRun
}) {
  return (
    <div className="bg-[#0c1427] border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden mb-8">
      {/* Decorative tactical scanline grid in background */}
      <div className="absolute inset-0 bg-command-grid opacity-20 pointer-events-none" />

      <div className="relative z-10 flex flex-col lg:flex-row items-center justify-between gap-6">
        
        {/* Left: Hero Headline & Scientific Description */}
        <div className="max-w-2xl">
          <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded bg-cyan-950/60 border border-cyan-700/50 text-cyan-300 font-mono text-xs mb-2.5">
            <Clock className="w-3.5 h-3.5" />
            <span>SIH CORE INNOVATION — TIME-TRAVEL DECISION AUDITING</span>
          </div>
          <h2 className="text-xl md:text-2xl font-bold tracking-tight text-white font-mono">
            Autonomous Post-Inference Self-Auditing Engine
          </h2>
          <p className="text-sm text-slate-400 mt-1 leading-relaxed">
            Witness how the AI model issues an early disaster warning at T-24h, compares the forecast against
            actual hydrometric ground-truth at T-0h, and initiates a SHAP-powered self-audit at T+1h to explain
            discrepancies and correct operational biases.
          </p>
        </div>

        {/* Right: Primary Call to Action Button */}
        <div className="flex-shrink-0 w-full lg:w-auto">
          <button
            onClick={onRunSimulation}
            disabled={isLoading}
            className="w-full lg:w-auto flex items-center justify-center space-x-3 px-6 py-3.5 rounded-lg bg-gradient-to-r from-rose-600 via-amber-600 to-cyan-600 hover:from-rose-500 hover:to-cyan-500 text-white font-mono font-bold tracking-wider text-sm transition-all duration-200 shadow-lg shadow-cyan-950/80 disabled:opacity-50 disabled:cursor-not-allowed group"
          >
            {isLoading ? (
              <>
                <RotateCcw className="w-5 h-5 animate-spin" />
                <span>EXECUTING 24H TIME-TRAVEL...</span>
              </>
            ) : (
              <>
                <Play className="w-5 h-5 fill-current group-hover:scale-110 transition-transform" />
                <span>RUN 24-HOUR TIME-TRAVEL SIMULATION</span>
              </>
            )}
          </button>
        </div>

      </div>

      {/* Timeline 3-Stage Visual Pipeline */}
      <div className="relative z-10 mt-8 pt-6 border-t border-slate-800/80">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
          
          {/* Stage 1 Indicator */}
          <div className={`p-3 rounded-lg border transition-all ${hasRun ? 'bg-rose-950/20 border-rose-800/60 text-rose-300' : 'bg-slate-900/60 border-slate-800 text-slate-400'}`}>
            <div className="flex items-center justify-between">
              <span className="font-bold text-rose-400">STAGE 1 — T-24h</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-900/40 text-rose-300 border border-rose-800">EARLY WARNING</span>
            </div>
            <p className="mt-1 text-[11px] text-slate-400">NWP weather surge forecast triggers severe risk alert.</p>
          </div>

          {/* Stage 2 Indicator */}
          <div className={`p-3 rounded-lg border transition-all ${hasRun ? 'bg-blue-950/20 border-blue-800/60 text-blue-300' : 'bg-slate-900/60 border-slate-800 text-slate-400'}`}>
            <div className="flex items-center justify-between">
              <span className="font-bold text-blue-400">STAGE 2 — T-0h</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-900/40 text-blue-300 border border-blue-800">GROUND TRUTH</span>
            </div>
            <p className="mt-1 text-[11px] text-slate-400">Sensors confirm storm tracked away; actual inundation: 0 km².</p>
          </div>

          {/* Stage 3 Indicator */}
          <div className={`p-3 rounded-lg border transition-all ${hasRun ? 'bg-amber-950/20 border-amber-800/60 text-amber-300' : 'bg-slate-900/60 border-slate-800 text-slate-400'}`}>
            <div className="flex items-center justify-between">
              <span className="font-bold text-amber-400">STAGE 3 — T+1h</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-900/40 text-amber-300 border border-amber-800">SELF-AUDIT RCA</span>
            </div>
            <p className="mt-1 text-[11px] text-slate-400">SHAP attribution isolates error driver & generates corrective action.</p>
          </div>

        </div>
      </div>
    </div>
  );
}
