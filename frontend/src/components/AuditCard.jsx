import React from 'react';
import { AlertOctagon, HelpCircle, ArrowRight, CheckCircle2, XCircle, Wrench, ShieldCheck } from 'lucide-react';

export default function AuditCard({ data, isRunning }) {
  if (!data) {
    return (
      <div className="bg-[#0e1628] border border-amber-900/30 rounded-xl p-6 flex flex-col justify-center items-center text-center min-h-[360px] text-slate-500 font-mono text-xs">
        <AlertOctagon className="w-8 h-8 text-amber-500/40 mb-2" />
        <p>AWAITING T+1h SELF-AUDIT EVALUATION</p>
      </div>
    );
  }

  const isCorrect = data.prediction_was_correct;

  return (
    <div className="bg-[#0f172a] border-2 border-amber-500/80 rounded-xl p-5 shadow-xl shadow-amber-950/20 relative flex flex-col justify-between">
      
      {/* Tactical Top Tag */}
      <div>
        <div className="flex items-center justify-between border-b border-amber-900/40 pb-3 mb-4">
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse" />
            <h3 className="font-mono font-bold text-amber-400 text-sm tracking-wide">
              STAGE 3: T+1h AI SELF-AUDIT
            </h3>
          </div>
          <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold border bg-amber-950/80 border-amber-600 text-amber-200">
            {data.audit_verdict || 'EVALUATED'}
          </span>
        </div>

        {/* Audit Verification Result & Error Metric */}
        <div className="bg-[#0b101f] border border-slate-800 rounded-lg p-3.5 mb-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono text-slate-400 uppercase">MODEL FIDELITY AUDIT</span>
            <div className="flex items-center space-x-1.5 font-mono text-xs font-bold">
              {isCorrect ? (
                <span className="text-emerald-400 flex items-center space-x-1">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>PREDICTION ACCURATE</span>
                </span>
              ) : (
                <span className="text-rose-400 flex items-center space-x-1">
                  <XCircle className="w-4 h-4" />
                  <span>FALSE POSITIVE DETECTED</span>
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between text-xs font-mono bg-slate-900/80 p-2 rounded border border-slate-800">
            <span className="text-slate-400">ABSOLUTE PREDICTION ERROR:</span>
            <span className="font-bold text-rose-400">{data.prediction_error ?? '--'} (Scale 0-1)</span>
          </div>

          <div className="flex items-center justify-between text-xs font-mono bg-slate-900/80 p-2 rounded border border-slate-800 mt-1.5">
            <span className="text-slate-400">STRONGEST ATTRIBUTION FEATURE:</span>
            <span className="font-bold text-amber-300">
              {data.strongest_attribution_feature} ({data.strongest_shap_contribution > 0 ? '+' : ''}{data.strongest_shap_contribution})
            </span>
          </div>
        </div>

        {/* PROMINENT ROOT-CAUSE EXPLANATION */}
        <div className="bg-amber-950/30 border-l-4 border-amber-500 p-3 rounded-r-lg mb-3">
          <div className="text-[10px] font-mono uppercase tracking-wider text-amber-400 font-bold mb-1 flex items-center space-x-1">
            <AlertOctagon className="w-3.5 h-3.5" />
            <span>DYNAMIC ROOT-CAUSE ANALYSIS (RCA)</span>
          </div>
          <p className="text-xs text-slate-200 leading-relaxed font-sans">
            "{data.root_cause_sentence}"
          </p>
        </div>

        {/* RECOMMENDED CORRECTIVE ACTION */}
        <div className="bg-slate-900/90 border border-slate-800 p-3 rounded-lg text-xs font-mono mb-2">
          <div className="text-[10px] uppercase text-cyan-400 font-bold mb-1 flex items-center space-x-1">
            <Wrench className="w-3.5 h-3.5" />
            <span>RECOMMENDED CORRECTIVE ACTION</span>
          </div>
          <p className="text-slate-300 leading-relaxed text-[11px] font-sans">
            {data.recommended_action}
          </p>
        </div>
      </div>

      {/* Scientific Attribution Disclaimer */}
      <div className="border-t border-slate-800/80 pt-2 text-[10px] font-mono text-slate-500 leading-normal">
        {data.scientific_disclaimer}
      </div>

    </div>
  );
}
