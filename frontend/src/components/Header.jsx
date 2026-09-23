import React, { useState, useEffect } from 'react';
import { Shield, Radio, Activity, Clock, Cpu } from 'lucide-react';

export default function Header({ systemStatus, isConnected }) {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formattedUtc = time.toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
  const formattedIst = time.toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false }) + ' IST';

  return (
    <header className="border-b border-slate-800 bg-[#0a0f1d]/90 backdrop-blur sticky top-0 z-40 px-4 lg:px-8 py-3.5">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
        
        {/* Left: Branding & SIH PS Identifier */}
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-600 to-blue-700 p-0.5 shadow-lg shadow-cyan-950/60 flex items-center justify-center">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg md:text-xl font-bold tracking-wider text-slate-100 uppercase font-sans">
                AI-POWERED LANDSCAPE EARLY WARNING SYSTEM
              </h1>
              <span className="text-[10px] uppercase tracking-widest font-semibold px-2 py-0.5 rounded bg-blue-950/80 border border-blue-700/60 text-blue-300 font-mono">
                SIH PS ID 260001
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">
              Multi-Hazard Prediction, 8-Hour Sequential Forecasting & Geofenced Early Warning
            </p>
          </div>
        </div>

        {/* Right: Operational Status & Real-time Clocks */}
        <div className="flex items-center space-x-4 text-xs">
          
          {/* Status Badge */}
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-md bg-slate-900/90 border border-slate-800">
            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
            <span className="font-mono text-slate-300 uppercase tracking-wide">
              {isConnected ? 'LIVE ENGINE CONNECTED' : 'OFFLINE / DISCONNECTED'}
            </span>
          </div>

          {/* Dual Clock display (UTC & IST for Disaster Operations) */}
          <div className="hidden sm:flex items-center space-x-3 px-3 py-1.5 rounded-md bg-slate-900/70 border border-slate-800/80 font-mono text-slate-400">
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            <span>{formattedUtc}</span>
            <span className="text-slate-600">|</span>
            <span className="text-cyan-300 font-medium">{formattedIst}</span>
          </div>

        </div>

      </div>
    </header>
  );
}
