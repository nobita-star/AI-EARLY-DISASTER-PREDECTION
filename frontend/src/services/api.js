/**
 * api.js - Production API Client for Disaster Intelligence Control Center
 * SIH Problem Statement ID: 260001
 * 
 * Supports dynamic backend URL configuration with localStorage persistence,
 * environment variable defaults, timeout handling, and structured error responses.
 */

const STORAGE_KEY = 'DISASTER_BACKEND_API_URL';

export const getDefaultBackendUrl = () => {
  // 1. Check user-configured override in localStorage (e.g. for demo or testing)
  const stored = typeof localStorage !== 'undefined' ? localStorage.getItem(STORAGE_KEY) : null;
  if (stored && stored.trim() !== '') {
    return stored.trim().replace(/\/+$/, '');
  }

  // 2. Check Vite build-time environment variables
  const envUrl = import.meta.env.VITE_BACKEND_API_URL || import.meta.env.VITE_API_URL;
  if (envUrl && envUrl.trim() !== '') {
    return envUrl.trim().replace(/\/+$/, '');
  }

  // 3. Check runtime window configuration if provided
  if (typeof window !== 'undefined' && window.__DISASTER_BACKEND_URL__) {
    return window.__DISASTER_BACKEND_URL__.replace(/\/+$/, '');
  }

  // 4. In cloud production (e.g. Vercel) if no env var is provided, fallback to relative origin or empty
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return '';
  }

  // 5. Local development default
  return 'http://localhost:8000';
};

export const saveBackendUrl = (url) => {
  const sanitized = (url || '').trim().replace(/\/+$/, '');
  localStorage.setItem(STORAGE_KEY, sanitized);
  return sanitized;
};

const fetchWithTimeout = async (url, options = {}, timeoutMs = 12000) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        ...(options.headers || {}),
      },
    });
    clearTimeout(timeoutId);
    return response;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error(`Connection timed out after ${timeoutMs / 1000}s. Check backend server.`);
    }
    throw new Error(`Network error: ${err.message || 'Unable to reach backend API.'}`);
  }
};

export const api = {
  async checkHealth(baseUrl = null) {
    const root = (baseUrl || getDefaultBackendUrl()).replace(/\/+$/, '');
    const res = await fetchWithTimeout(`${root}/health`, { method: 'GET' }, 8000);
    if (!res.ok) {
      throw new Error(`Health check returned HTTP ${res.status}`);
    }
    const contentType = res.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error('API returned HTML instead of JSON. Configure your Render backend URL in the ConfigBar above or set VITE_BACKEND_API_URL.');
    }
    return await res.json();
  },

  async getSystemStatus(baseUrl = null) {
    const root = (baseUrl || getDefaultBackendUrl()).replace(/\/+$/, '');
    const res = await fetchWithTimeout(`${root}/api/v1/system/status`, { method: 'GET' });
    if (!res.ok) {
      throw new Error(`Failed fetching status: HTTP ${res.status}`);
    }
    const contentType = res.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error('API returned non-JSON response. Please verify backend URL.');
    }
    return await res.json();
  },

  async predictRisk(payload, baseUrl = null) {
    const root = (baseUrl || getDefaultBackendUrl()).replace(/\/+$/, '');
    const res = await fetchWithTimeout(`${root}/api/v1/predict`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Prediction failed: HTTP ${res.status}`);
    }
    return await res.json();
  },

  async simulateTimeTravel(baseUrl = null) {
    const root = (baseUrl || getDefaultBackendUrl()).replace(/\/+$/, '');
    const res = await fetchWithTimeout(`${root}/api/v1/simulate/time-travel`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Time travel simulation failed: HTTP ${res.status}`);
    }
    return await res.json();
  },

  async getModelMetrics(baseUrl = null) {
    const root = (baseUrl || getDefaultBackendUrl()).replace(/\/+$/, '');
    const res = await fetchWithTimeout(`${root}/api/v1/model/metrics`, { method: 'GET' });
    if (!res.ok) {
      throw new Error(`Failed fetching metrics: HTTP ${res.status}`);
    }
    return await res.json();
  },

  async getModelFeatures(baseUrl = null) {
    const root = (baseUrl || getDefaultBackendUrl()).replace(/\/+$/, '');
    const res = await fetchWithTimeout(`${root}/api/v1/model/features`, { method: 'GET' });
    if (!res.ok) {
      throw new Error(`Failed fetching features: HTTP ${res.status}`);
    }
    return await res.json();
  },

  async runWhatIfScenario(payload, baseUrl = null) {
    const root = (baseUrl || getDefaultBackendUrl()).replace(/\/+$/, '');
    const res = await fetchWithTimeout(`${root}/api/v1/scenario/what-if`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Scenario evaluation failed: HTTP ${res.status}`);
    }
    return await res.json();
  },

  async compareValidation(payload, baseUrl = null) {
    const root = (baseUrl || getDefaultBackendUrl()).replace(/\/+$/, '');
    const res = await fetchWithTimeout(`${root}/api/v1/validation/compare`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Satellite validation failed: HTTP ${res.status}`);
    }
    return await res.json();
  },

  async auditPrediction(payload, baseUrl = null) {
    const root = (baseUrl || getDefaultBackendUrl()).replace(/\/+$/, '');
    const res = await fetchWithTimeout(`${root}/api/v1/audit`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Audit failed: HTTP ${res.status}`);
    }
    return await res.json();
  },

  async getAuditLogs(limit = 25, baseUrl = null) {
    const root = (baseUrl || getDefaultBackendUrl()).replace(/\/+$/, '');
    const res = await fetchWithTimeout(`${root}/api/v1/audit/logs?limit=${limit}`, { method: 'GET' });
    if (!res.ok) {
      throw new Error(`Failed fetching audit logs: HTTP ${res.status}`);
    }
    return await res.json();
  },

  async getSafeLocations(lat, lon, elev = 14, baseUrl = null) {
    const root = (baseUrl || getDefaultBackendUrl()).replace(/\/+$/, '');
    const res = await fetchWithTimeout(`${root}/api/v1/safety/safe-locations?lat=${lat}&lon=${lon}&user_elevation=${elev}`, { method: 'GET' });
    if (!res.ok) {
      throw new Error(`Failed fetching safe locations: HTTP ${res.status}`);
    }
    return await res.json();
  },

  async getHazardRelevance(lat, lon, riskPct = 50, baseUrl = null) {
    const root = (baseUrl || getDefaultBackendUrl()).replace(/\/+$/, '');
    const res = await fetchWithTimeout(`${root}/api/v1/safety/hazard-relevance?lat=${lat}&lon=${lon}&risk_pct=${riskPct}`, { method: 'GET' });
    if (!res.ok) {
      throw new Error(`Failed fetching hazard relevance: HTTP ${res.status}`);
    }
    return await res.json();
  },

  async getLiveTelemetry(lat, lon, catchmentId = null, baseUrl = null) {
    const root = (baseUrl || getDefaultBackendUrl()).replace(/\/+$/, '');
    let url = `${root}/api/v1/telemetry/live?lat=${lat}&lon=${lon}`;
    if (catchmentId) {
      url += `&catchment_id=${encodeURIComponent(catchmentId)}`;
    }
    const res = await fetchWithTimeout(url, { method: 'GET' }, 8000);
    if (!res.ok) {
      throw new Error(`Failed fetching telemetry: HTTP ${res.status}`);
    }
    return await res.json();
  }
};
