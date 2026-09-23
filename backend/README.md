# Disaster Intelligence Control Center — Backend API
**Smart India Hackathon (SIH) Problem Statement ID: 260001**

A production-oriented, explainable, and self-auditing Disaster Management Platform backend engineered with **FastAPI**, **XGBoost**, **SHAP TreeExplainer**, kinematic hydrodynamic physics modeling, and spatial ground-truth validation.

---

## 1. System Architecture

```
                    MULTI-MODAL DATA INGESTION
                                │
    ┌───────────────────────────┼───────────────────────────┐
    ↓                           ↓                           ↓
Sentinel-1 SAR / Optical    SRTM / DEM Raster       Hydrometric Gauges & NWP
(Backscatter / Water Mask)  (Slope, Elevation, TRI)  (Rainfall, River Levels)
    │                           │                           │
    └───────────────────────────┼───────────────────────────┘
                                ↓
                     Feature Engineering Layer
                    (Data Source Flag: Real/Synthetic)
                                │
    ┌───────────────────────────┴───────────────────────────┐
    ↓                                                       ↓
Physics-Inspired Layer                         XGBoost Risk Classifier
(Manning's Flow / Hydro Dynamics)              (Probability & Uncertainty)
    │                                                       │
    └───────────────────────────┬───────────────────────────┘
                                ↓
                 Decision & Uncertainty Estimator
                  (Calibrated Heuristic + Bound)
                                │
    ┌───────────────────────────┴───────────────────────────┐
    ↓                                                       ↓
SHAP TreeExplainer                              Automated Self-Audit Engine
(Attribution Vectors)                           (T-24h vs T-0h Ground Truth RCA)
                                │
                                ↓
                 Scenario Engine (What-If Analysis)
                                │
                                ↓
                     FastAPI REST Service
```

---

## 2. Key Scientific Innovations

1. **Self-Auditing AI Loop**:
   - Computes prediction discrepancies after ground truth arrives at T-0h.
   - Traces the error to individual feature attribution vectors via SHAP.
   - Dynamically constructs a human-readable Root Cause Analysis (RCA) sentence.
   - Recommends actionable operational corrections for emergency disaster managers.
2. **Scientific Attribution Integrity**:
   - SHAP is explicitly labeled as **Model Attribution**, not physical causality.
   - Uncertainty is quantified via input perturbation variance and training distribution Mahalanobis/Z-score distances.
3. **Modular Hydrodynamic Physics**:
   - Does not present machine learning as a replacement for physics.
   - Provides a modular `BaseHydrodynamicSolver` interface with a *"Physics-Inspired MVP Simulation"* implementing Manning's kinematic equation, ready for plug-and-play integration with HEC-RAS or Delft3D.
4. **Transparent Data Sourcing**:
   - Formally tags every response as `data_source: "real"` or `data_source: "synthetic"`.

---

## 3. Local Development Setup

### Prerequisites
- Python 3.10+
- pip

### Step-by-Step Installation

```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create and activate a virtual environment
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux / macOS:
source venv/bin/activate

# 3. Install pinned dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env

# 5. Start the development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Once running, interactive API documentation is available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 4. Render.com Deployment Guide

To deploy this backend as a Web Service on [Render](https://render.com):

1. **Create New Web Service**:
   - Connect your GitHub / GitLab repository.
   - Set **Root Directory** to: `backend`
   - Select **Runtime**: `Python 3`
2. **Build & Start Commands**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. **Environment Variables**:
   Configure the following in the Render Dashboard under **Environment**:
   - `ENVIRONMENT` = `production`
   - `MODEL_PATH` = `models/xgboost_flood_model.joblib`
   - `ENABLE_REAL_DATA` = `false` (set `true` if connected to live API feeds)
   - `ENABLE_PHYSICS_SIMULATION` = `true`
   - `LOG_LEVEL` = `INFO`
4. **Health Check Endpoint**:
   - Path: `/health`

---

## 5. API Reference & Testing Examples

### A. Health Check
```bash
curl -X GET "http://localhost:8000/health"
```
**Response**:
```json
{
  "status": "ok"
}
```

### B. Risk Prediction
```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "rainfall": 85.0,
    "forecast_rainfall": 120.0,
    "soil_saturation": 0.78,
    "slope": 3.2,
    "river_level": 5.4
  }'
```

### C. 24-Hour Time-Travel Simulation
```bash
curl -X POST "http://localhost:8000/api/v1/simulate/time-travel"
```

### D. What-If Scenario Analysis
```bash
curl -X POST "http://localhost:8000/api/v1/scenario/what-if" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline": {
      "rainfall": 45.0,
      "forecast_rainfall": 30.0,
      "soil_saturation": 0.50,
      "slope": 6.0,
      "river_level": 2.8
    },
    "what_if": {
      "rainfall": 160.0,
      "river_level": 6.2,
      "breach_factor": 0.35
    }
  }'
```

### E. Model Diagnostics
```bash
curl -X GET "http://localhost:8000/api/v1/model/metrics"
```

### F. Satellite Validation Comparison
```bash
curl -X POST "http://localhost:8000/api/v1/validation/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "predicted_area_km2": 45.2,
    "observed_area_km2": 42.0,
    "intersection_area_km2": 37.8
  }'
```
