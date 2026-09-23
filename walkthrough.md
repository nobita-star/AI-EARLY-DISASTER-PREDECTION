# Walkthrough: Rainfall Risk Fix & Multi-Metric Verification (SIH PS ID 260001)

## Executive Summary
We surgically diagnosed and resolved the **Rainfall Risk** calculation and presentation issue in the SIH 2026 Landscape Disaster Risk Detection prototype (PS ID 260001). 

**Key Achievement**: The overall **Landscape Risk** calculation (XGBoost model, SHAP TreeExplainer attributions, and 4-tier spatial contour polygons) has been **100% preserved**, while a dedicated, scientifically grounded, strictly monotonic **Rainfall Risk** calculation and display was implemented and verified locally on `http://localhost:8000` (backend) and `http://localhost:5173` (frontend).

---

## 1. Root Cause Analysis
Prior to this fix, three key issues caused the Rainfall Risk discrepancies:
1. **Absence of Dedicated Metric**: The backend previously computed only the compound, multi-modal **Landscape Risk** ($0-100\%$) via XGBoost combining terrain slope, river stage, soil saturation, and precipitation. There was **no dedicated `rainfall_risk` metric calculated or returned in API responses**.
2. **Conflated Frontend Display**: In the UI, the Stage 1 Early Warning card presented the compound Landscape Risk percentage while displaying raw antecedent rainfall millimeters directly beneath it, misleading users/judges into interpreting the compound landscape score as pure rainfall risk.
3. **Mislabeled Fallback Telemetry**: In offline/timeout conditions, the telemetry fallback branch falsely flagged fallback data as `"is_real_telemetry": True` without clearly distinguishing demo data from live Open-Meteo NWP observations.

---

## 2. Scientific Rainfall Risk Engine (IMD Standards)
In [`backend/src/feature_engineering.py`](file:///c:/Users/HP%20640%20G8/.antigravity-ide/backend/src/feature_engineering.py), we implemented `calculate_rainfall_risk()` following **India Meteorological Department (IMD)** 24-hour rainfall classification and **Central Water Commission (CWC)** hydrologic runoff guidance:

### Effective Precipitation
$$R_{\text{eff}} = R_{24\text{h}} + 0.5 \times F_{6\text{h}}$$
where $R_{24\text{h}}$ is the 24-hour accumulated rainfall ($mm/day$) and $F_{6\text{h}}$ is the 6-hour NWP precipitation forecast ($mm$).

### IMD Threshold Mapping (Strictly Continuous & Monotonic)
| IMD Classification | 24h Rainfall ($R_{\text{eff}}$) | Rainfall Risk % | Risk Category |
| :--- | :--- | :--- | :--- |
| **Trace / Very Light** | $< 2.5$ mm/day | $5.0\% - 14.9\%$ | `LOW` |
| **Light Rain** | $2.5 - 15.5$ mm/day | $15.0\% - 29.9\%$ | `LOW` |
| **Moderate Rain** | $15.6 - 64.4$ mm/day | $30.0\% - 59.9\%$ | `MODERATE` |
| **Heavy Rain** | $64.5 - 115.5$ mm/day | $60.0\% - 79.9\%$ | `HIGH` |
| **Very Heavy Rain** | $115.6 - 204.4$ mm/day | $80.0\% - 92.9\%$ | `CRITICAL` |
| **Extremely Heavy / Cloudburst** | $> 204.4$ mm/day | $93.0\% - 99.0\%$ | `CRITICAL` |

- **Deterministic**: 100% reproducible for the same input; zero random numbers (`Math.random()`) or spinning dummy numbers.
- **Independent**: Distinct from the multi-hazard Landscape Risk.

---

## 3. Implemented Changes

### Backend Pipeline
- [`backend/src/feature_engineering.py`](file:///c:/Users/HP%20640%20G8/.antigravity-ide/backend/src/feature_engineering.py):
  - Added `calculate_rainfall_risk(rainfall_24h, forecast_6h, source_label, is_fallback, timestamp)`.
- [`backend/main.py`](file:///c:/Users/HP%20640%20G8/.antigravity-ide/backend/main.py):
  - Updated `PredictionOutput` schema with `rainfall_risk: Optional[Dict[str, Any]] = None`.
  - Updated `GET /api/v1/telemetry/live`: attaches `rainfall_risk` object; explicitly flags offline fallback with `"is_real_telemetry": False`, `"is_fallback": True`, and `"status": "DEMO_FALLBACK_TELEMETRY"`.
  - Updated `POST /api/v1/predict`: returns both `risk_percentage` (XGBoost Landscape Risk) and `rainfall_risk` (Rainfall Risk).
  - Updated `POST /api/v1/simulate/time-travel`: attaches `rainfall_risk` to Stage 1 and Stage 2.
  - Updated `POST /api/v1/scenario/what-if`: computes `rainfall_risk` for baseline and what-if scenarios.

### Frontend Presentation
- [`frontend/src/services/api.js`](file:///c:/Users/HP%20640%20G8/.antigravity-ide/frontend/src/services/api.js):
  - Added `getLiveTelemetry(lat, lon, catchmentId, baseUrl)`.
- [`frontend/src/components/RiskCard.jsx`](file:///c:/Users/HP%20640%20G8/.antigravity-ide/frontend/src/components/RiskCard.jsx):
  - Clearly split into two dedicated sections:
    1. **Predicted Landscape Risk (XGBoost)**: Compound multi-hazard meter with amber-to-rose progress bar.
    2. **Rainfall Risk Intelligence**: Shows Current Rainfall ($mm/day$), NWP Forecast ($mm$), Rainfall Risk $\%$, Category badge (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`), Source status, and dedicated progress meter.
- [`frontend/src/components/CommandMap.jsx`](file:///c:/Users/HP%20640%20G8/.antigravity-ide/frontend/src/components/CommandMap.jsx):
  - Inspecting any sector now queries live Open-Meteo telemetry coordinates and renders both Landscape Risk and Rainfall Risk in the floating HUD.
- [`frontend/vite.config.js`](file:///c:/Users/HP%20640%20G8/.antigravity-ide/frontend/vite.config.js):
  - Added proxy for `/api` and `/health` forwarding to `http://localhost:8000`.
- [`backend/static/index.html`](file:///c:/Users/HP%20640%20G8/.antigravity-ide/backend/static/index.html):
  - Synchronized the KPI card and map HUD to reflect the separate Rainfall Risk metric and source status.

---

## 4. Verification & Validation Results

### 1. 3-Condition Rainfall Scaling & Separation Test
Executed via [`scratch/test_rainfall_risk.py`](file:///C:/Users/HP%20640%20G8/.gemini/antigravity-ide/brain/156eeeb6-6285-407b-9024-5ecbd475cd18/scratch/test_rainfall_risk.py):

| Test Condition | Rain Input | Forecast | Rainfall Risk | Category | Landscape Risk (XGBoost) | Top SHAP Driver | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Test A: Low Rain** | $8.0$ mm/day | $2.0$ mm | **22.4%** | `LOW` | **0.84%** (`LOW`) | `river_level` | **PASSED** |
| **Test B: Moderate Rain** | $45.0$ mm/day | $15.0$ mm | **52.6%** | `MODERATE` | **15.52%** (`LOW`) | `slope` | **PASSED** |
| **Test C: Heavy Rain** | $140.0$ mm/day | $60.0$ mm | **87.9%** | `CRITICAL` | **99.40%** (`SEVERE`) | `river_level` | **PASSED** |
| **Test D: Reproducibility** | $86.0$ mm/day | $15.0$ mm | **71.3%** | `HIGH` | $37.55\%$ | `river_level` | **5/5 identical (0.0% variance)** |
| **Test E: Separation** | $5.0$ mm/day | $1.0$ mm | **18.4%** | `LOW` | **95.78%** (`SEVERE`) | `river_level` | **PASSED** |

> [!NOTE]
> In **Test E**, with low rainfall ($5.0$ mm) but saturated ground and swollen river ($7.5$ m), the XGBoost Landscape Risk correctly reported **95.78% [SEVERE]** while the Rainfall Risk reported **18.4% [LOW]**, confirming that Landscape Risk and Rainfall Risk operate as distinct, uncorrelated indicators.

### 2. Full End-to-End Workflow Verification
Executed via [`scratch/verify_end_to_end.py`](file:///C:/Users/HP%20640%20G8/.gemini/antigravity-ide/brain/156eeeb6-6285-407b-9024-5ecbd475cd18/scratch/verify_end_to_end.py):
- **Step 1: Servers**: Backend on `http://localhost:8000/health` (HTTP 200) and Frontend on `http://localhost:5173/health` (HTTP 200).
- **Step 2: Live Ingestion**: Open-Meteo GFS/ECMWF returned live data ($7.1$ mm rain, $1.9$ mm forecast, $21.4\%$ Rainfall Risk).
- **Step 3: Prediction**: XGBoost evaluated $2.12\%$ Landscape Risk with SHAP top driver `river_level`.
- **Step 4: GIS Cartography**: Inundation contour polygon with 25 vertices generated.
- **Step 5: Civil Defense**: Multi-channel emergency alert dispatched across 3 channels (`ALT-20260918-2C94`, 2,784 recipients).
- **Step 6: Self-Audit Simulation**: 3-stage time-travel completed with automated RCA and $81.46\%$ IoU agreement.

---

## 5. Localhost Execution Instructions

### Backend (FastAPI)
```powershell
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Frontend Dev Server
```powershell
python frontend_dev_server.py
```
- Open in Browser: [http://localhost:5173](http://localhost:5173)
- Fully proxied to `http://localhost:8000` with active CORS handling.
