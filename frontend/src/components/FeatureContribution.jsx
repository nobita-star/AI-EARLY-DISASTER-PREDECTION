import React from 'react';
import { BarChart3, HelpCircle, Info } from 'lucide-react';

export default function FeatureContribution({ contributions, topFeature, humanExplanation }) {
  if (!contributions || Object.keys(contributions).length === 0) {
    return (
      <div className="bg-[#0c1427] border border-slate-800 rounded-xl p-6 text-center text-slate-500 font-mono text-xs">
        <BarChart3 className="w-8 h-8 text-slate-600 mx-auto mb-2" />
        <p>AWAITING INFERENCE RUN TO EXTRACT SHAP FEATURE ATTRIBUTION VECTORS</p>
      </div>
    );
  }

  // Sort by absolute value
  const sortedFeatures = Object.entries(contributions).sort(
    (a, b) => Math.abs(b[1]) - Math.abs(a[1])
  );

  const maxMagnitude = Math.max(...sortedFeatures.map(([_, val]) => Math.abs(val)), 0.1);

  return (
    <div className="bg-[#0c1427] border border-slate-800 rounded-xl p-6 shadow-xl">
      
      {/* Header & Scientific Disclaimer Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-slate-800 pb-4 mb-5">
        <div>
          <div className="flex items-center space-x-2">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            <h3 className="font-mono font-bold text-white text-sm tracking-wider uppercase">
              SHAP Additive Feature Attribution
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Local directional contribution of telemetry inputs to model decision margin.
          </p>
        </div>

        {/* Mandatory Scientific Notice */}
        <div className="flex items-center space-x-1.5 px-3 py-1 rounded bg-amber-950/40 border border-amber-800/60 text-amber-300 text-xs font-mono">
          <Info className="w-3.5 h-3.5 flex-shrink-0" />
          <span className="font-semibold uppercase tracking-wider text-[10px]">
            Model Attribution — Not Causal Proof
          </span>
        </div>
      </div>

      {/* Dynamic AI Causal Explanation Card */}
      {humanExplanation && (
        <div className="bg-indigo-950/40 border border-indigo-800/60 rounded-lg p-3.5 mb-5 text-xs">
          <div className="text-[10px] font-mono text-indigo-300 font-bold uppercase tracking-wider mb-1">
            AI DECISION RATIONALE & RECOMMENDATIONS
          </div>
          <p className="text-slate-200 leading-relaxed font-sans">
            {humanExplanation.summary}
          </p>
          {humanExplanation.recommended_action && (
            <div className="mt-2 text-cyan-300 font-mono text-[11px] bg-slate-900/60 p-2 rounded border border-slate-800">
              <span className="text-amber-400 font-bold">PRECAUTIONARY ACTION:</span> {humanExplanation.recommended_action}
            </div>
          )}
        </div>
      )}

      {/* Feature Attribution Horizontal Bars */}
      <div className="space-y-3.5">
        {sortedFeatures.map(([featureName, value]) => {
          const isPositive = value >= 0;
          const percentageWidth = Math.min(100, Math.round((Math.abs(value) / maxMagnitude) * 100));
          const isTop = featureName === topFeature;

          return (
            <div key={featureName} className="group">
              <div className="flex justify-between items-center text-xs font-mono mb-1">
                <span className={`flex items-center space-x-1.5 ${isTop ? 'text-amber-300 font-bold' : 'text-slate-300'}`}>
                  {isTop && <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />}
                  <span>{featureName}</span>
                </span>
                <span className={`font-mono text-xs font-semibold ${isPositive ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {isPositive ? `+${value.toFixed(4)} (Elevates Risk)` : `${value.toFixed(4)} (Mitigates)`}
                </span>
              </div>

              {/* Centered / Directional Bar */}
              <div className="grid grid-cols-2 gap-1 h-3 bg-slate-900/90 rounded border border-slate-800/80 overflow-hidden">
                {/* Left (Negative / Mitigating side) */}
                <div className="flex justify-end items-center h-full">
                  {!isPositive && (
                    <div
                      className="h-full bg-gradient-to-l from-emerald-500 to-cyan-500 rounded-l transition-all duration-500"
                      style={{ width: `${percentageWidth}%` }}
                    />
                  )}
                </div>

                {/* Right (Positive / Risk Driver side) */}
                <div className="flex justify-start items-center h-full">
                  {isPositive && (
                    <div
                      className="h-full bg-gradient-to-r from-amber-500 to-rose-500 rounded-r transition-all duration-500"
                      style={{ width: `${percentageWidth}%` }}
                    />
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-5 pt-3 border-t border-slate-800/80 flex flex-col sm:flex-row justify-between text-[11px] font-mono text-slate-500">
        <span>Negative SHAP (← Mitigating Factors)</span>
        <span>Positive SHAP (Risk Surge Drivers →)</span>
      </div>

    </div>
  );
}
