import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import ConfigBar from './components/ConfigBar';
import Timeline from './components/Timeline';
import RiskCard from './components/RiskCard';
import GroundTruthCard from './components/GroundTruthCard';
import AuditCard from './components/AuditCard';
import FeatureContribution from './components/FeatureContribution';
import ScenarioPanel from './components/ScenarioPanel';
import SystemStatus from './components/SystemStatus';
import CommandMap from './components/CommandMap';
import { api, getDefaultBackendUrl } from './services/api';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function App() {
  const [backendUrl, setBackendUrl] = useState(getDefaultBackendUrl());
  const [connectionStatus, setConnectionStatus] = useState('checking'); // 'connected' | 'error' | 'checking'
  const [isTesting, setIsTesting] = useState(false);
  const [pingMs, setPingMs] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);
  const [dataSource, setDataSource] = useState('synthetic');
  const [errorMessage, setErrorMessage] = useState('');

  // Time-travel simulation state
  const [simulationData, setSimulationData] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [hasRunSimulation, setHasRunSimulation] = useState(false);

  // Test backend connection
  const checkBackend = useCallback(async (urlToTest = backendUrl) => {
    setIsTesting(true);
    const start = performance.now();
    try {
      await api.checkHealth(urlToTest);
      const latency = Math.round(performance.now() - start);
      setPingMs(latency);
      setConnectionStatus('connected');
      setErrorMessage('');

      // Fetch system status
      const statusData = await api.getSystemStatus(urlToTest);
      setSystemStatus(statusData);
      setDataSource(statusData.data_source || 'synthetic');

      // Auto-load initial live simulation so cards immediately show genuine ML data (never 0%)
      try {
        const initialSim = await api.simulateTimeTravel(urlToTest);
        setSimulationData(initialSim);
        setHasRunSimulation(true);
      } catch (simErr) {
        console.debug('Initial auto-simulation notice:', simErr);
      }
    } catch (err) {
      setConnectionStatus('error');
      setErrorMessage(err.message || 'Unable to reach backend API.');
    } finally {
      setIsTesting(false);
    }
  }, [backendUrl]);

  // Initial connection check on mount
  useEffect(() => {
    checkBackend();
  }, [checkBackend]);

  // Run Time-Travel Simulation
  const handleRunTimeTravel = async () => {
    setIsSimulating(true);
    setErrorMessage('');
    try {
      const data = await api.simulateTimeTravel(backendUrl);
      setSimulationData(data);
      setHasRunSimulation(true);
    } catch (err) {
      setErrorMessage(`Time travel execution failed: ${err.message}`);
    } finally {
      setIsSimulating(false);
    }
  };

  const stage1 = simulationData?.stage_1_early_warning;
  const stage2 = simulationData?.stage_2_ground_truth;
  const stage3 = simulationData?.stage_3_self_audit;

  return (
    <div className="min-h-screen bg-[#080c14] text-slate-100 flex flex-col selection:bg-cyan-500/30 selection:text-cyan-200">
      
      {/* 1. Masthead Header */}
      <Header
        systemStatus={systemStatus}
        isConnected={connectionStatus === 'connected'}
      />

      {/* 2. Top Tactical Configuration Bar */}
      <ConfigBar
        backendUrl={backendUrl}
        onUrlChange={(url) => {
          setBackendUrl(url);
          checkBackend(url);
        }}
        onTestConnection={checkBackend}
        isTesting={isTesting}
        connectionStatus={connectionStatus}
        dataSource={dataSource}
        pingMs={pingMs}
      />

      {/* Main Command Center Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 lg:px-8 py-6">
        
        {/* Backend Connection Error Alert Banner */}
        {connectionStatus === 'error' && (
          <div className="bg-rose-950/70 border-2 border-rose-600/80 rounded-xl p-4 mb-6 shadow-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs font-mono">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="text-rose-200 font-bold uppercase tracking-wider">
                  BACKEND SERVICE UNAVAILABLE
                </strong>
                <p className="text-rose-300/90 mt-0.5 font-sans">
                  Backend unavailable. Check BACKEND_API_URL ({backendUrl}) and Render service status.
                </p>
              </div>
            </div>

            <button
              onClick={() => checkBackend()}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-rose-700 hover:bg-rose-600 text-white font-mono font-bold text-xs tracking-wider transition-all"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>RETRY CONNECTION</span>
            </button>
          </div>
        )}

        {/* 3. Hero Time-Travel Timeline Orchestrator */}
        <Timeline
          onRunSimulation={handleRunTimeTravel}
          isLoading={isSimulating}
          hasRun={hasRunSimulation}
        />

        {/* 4. Geospatial White GIS Command Map */}
        <CommandMap
          backendUrl={backendUrl}
        />

        {/* 5. Three-Card Timeline Sequence */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          
          {/* Card 1: T-24h Early Warning */}
          <RiskCard
            data={stage1}
            isRunning={isSimulating}
          />

          {/* Card 2: T-0h Ground Truth */}
          <GroundTruthCard
            data={stage2}
            isRunning={isSimulating}
          />

          {/* Card 3: T+1h AI Self-Audit */}
          <AuditCard
            data={stage3}
            isRunning={isSimulating}
          />

        </div>

        {/* 5. SHAP Additive Feature Contribution Chart */}
        <div className="mb-8">
          <FeatureContribution
            contributions={stage1?.top_features || {}}
            topFeature={stage1?.top_contributing_feature}
            humanExplanation={stage1?.human_explanation}
          />
        </div>

        {/* 6. Interactive What-If Scenario Panel */}
        <ScenarioPanel
          backendUrl={backendUrl}
          onNotify={(msg) => setErrorMessage(msg)}
        />

        {/* 7. Subsystem Status & Model Performance Diagnostics */}
        <SystemStatus
          backendUrl={backendUrl}
          systemStatus={systemStatus}
        />

      </main>

      {/* Tactical Footer */}
      <footer className="border-t border-slate-800/80 bg-[#070b12] py-4 text-center text-xs font-mono text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>LANDSCAPE RISK INTELLIGENCE SYSTEM • SIH PROBLEM STATEMENT ID: 260001</span>
          <span>AI-POWERED MULTI-HAZARD RISK ASSESSMENT & EARLY WARNING PLATFORM</span>
        </div>
      </footer>

    </div>
  );
}
