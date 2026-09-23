import React, { useState } from 'react';
import { Server, RefreshCw, CheckCircle2, AlertTriangle, Database, Zap } from 'lucide-react';
import { saveBackendUrl } from '../services/api';

export default function ConfigBar({
  backendUrl,
  onUrlChange,
  onTestConnection,
  isTesting,
  connectionStatus,
  dataSource,
  pingMs
}) {
  const [inputUrl, setInputUrl] = useState(backendUrl);
  const [hasSaved, setHasSaved] = useState(false);

  const handleSaveAndTest = (e) => {
    e.preventDefault();
    const cleanUrl = saveBackendUrl(inputUrl);
    onUrlChange(cleanUrl);
    setHasSaved(true);
    setTimeout(() => setHasSaved(false), 2000);
    onTestConnection(cleanUrl);
  };

  return (
    <div className="bg-[#0b1222] border-b border-slate-800/80 px-4 lg:px-8 py-2.5">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3 text-xs">
        
        {/* URL Configuration Input Form */}
        <form onSubmit={handleSaveAndTest} className="flex items-center space-x-2 w-full md:w-auto">
          <div className="flex items-center space-x-1.5 text-slate-400 font-mono">
            <Server className="w-3.5 h-3.5 text-cyan-400" />
            <span className="font-semibold text-slate-300 uppercase tracking-wider text-[11px]">API ENDPOINT:</span>
          </div>

          <div className="relative flex-1 md:w-80">
            <input
              type="text"
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
              placeholder="https://your-api.onrender.com or /api"
              className="w-full bg-slate-900/90 border border-slate-700/80 rounded px-2.5 py-1 text-slate-200 font-mono text-xs focus:outline-none focus:border-cyan-500 transition-colors"
            />
          </div>

          <button
            type="submit"
            disabled={isTesting}
            className="flex items-center space-x-1 px-3 py-1 bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-800 text-white font-medium rounded transition-all shadow-sm"
          >
            <RefreshCw className={`w-3 h-3 ${isTesting ? 'animate-spin' : ''}`} />
            <span>{isTesting ? 'Testing...' : 'Connect'}</span>
          </button>

          {hasSaved && (
            <span className="text-emerald-400 text-[11px] font-mono flex items-center space-x-0.5">
              <CheckCircle2 className="w-3 h-3" />
              <span>Saved</span>
            </span>
          )}
        </form>

        {/* Status Indicators & Sourcing Tag */}
        <div className="flex items-center space-x-3 w-full md:w-auto justify-end">
          
          {/* Connection Latency / State */}
          <div className="flex items-center space-x-1.5 font-mono">
            {connectionStatus === 'connected' ? (
              <span className="flex items-center space-x-1 text-emerald-400 bg-emerald-950/40 border border-emerald-800/60 px-2 py-0.5 rounded">
                <Zap className="w-3 h-3 text-emerald-400" />
                <span>ONLINE {pingMs ? `(${pingMs}ms)` : ''}</span>
              </span>
            ) : connectionStatus === 'error' ? (
              <span className="flex items-center space-x-1 text-rose-400 bg-rose-950/40 border border-rose-800/60 px-2 py-0.5 rounded">
                <AlertTriangle className="w-3 h-3 text-rose-400" />
                <span>CONNECTION FAILED</span>
              </span>
            ) : (
              <span className="text-slate-400 font-mono text-[11px]">CHECKING...</span>
            )}
          </div>

          {/* Scientific Data Source Sourcing Badge */}
          <div className="flex items-center space-x-1.5 pl-2 border-l border-slate-800">
            <span className="text-slate-400 font-mono text-[11px] uppercase">SOURCE:</span>
            {dataSource === 'real' ? (
              <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-blue-900/60 text-blue-200 border border-blue-600/70 tracking-wider">
                REAL SATELLITE/GAUGE DATA
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-amber-950/50 text-amber-300 border border-amber-700/60 tracking-wider" title="Using calibrated synthetic fallback dataset">
                SYNTHETIC DEMO DATA
              </span>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
