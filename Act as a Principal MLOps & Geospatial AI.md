Act as a Principal MLOps & Geospatial AI Architect. I want you to build a complete, production-ready, fully functional Python backend using FastAPI and XGBoost for a Self-Auditing Disaster Management Prediction Engine (PS ID: 260001).

### 1. SYSTEM OVERVIEW & ARCHITECTURE
Build an end-to-end working pipeline that:
1. Takes multi-modal geospatial/hydrological inputs (Satellite SAR soil saturation, DEM elevation/slope, precipitation forecasts, river discharge).
2. Predicts disaster risk (Flood/Inundation probability between 0.0 and 1.0) using XGBoost.
3. Computes feature attribution using SHAP (TreeExplainer).
4. Generates an AI Confidence Score based on sensor variance and input data staleness.
5. Implements a POST-INFERENCE SELF-AUDITING LOOP:
   - Compares past predictions with actual ground truth data (simulated ground truth).
   - Flags discrepancies (False Positives or False Negatives).
   - Runs automated Root Cause Analysis (RCA) via SHAP deltas to determine *why* the prediction failed.
   - Outputs a human-readable one-liner explanation of the error (e.g., "False Alarm caused by 45% overestimated rainfall forecast overriding dry soil moisture").

### 2. TECH STACK SPECIFICATIONS
- Language: Python 3.10+
- Web Framework: FastAPI + Pydantic (data validation)
- Core ML & Explainability: XGBoost, SHAP, Scikit-learn
- Data & Spatial Processing: Pandas, NumPy
- Database & Spatial Simulation: SQLite / Mock In-Memory Store mimicking PostGIS spatial operations (ST_Intersection/Bounding Box logic).

### 3. REQUIRED MODULES & WORKING CODE
You must generate modular, fully runnable Python code with no placeholders or broken imports:

1. `synthetic_data.py`:
   - Generate a realistic training dataset of 1,000 historical rows with features:
     - `rainfall_last_24h` (mm)
     - `forecasted_rainfall_next_6h` (mm)
     - `soil_saturation_index` (0.0 to 1.0, Sentinel-1 SAR proxy)
     - `dem_slope_degrees` (0 to 60 degrees, SRTM DEM proxy)
     - `river_water_level_m` (meters)
     - `actual_inundation_risk` (0 or 1 - binary target)
   - Automatically train and serialize an `XGBClassifier` and initialize a `shap.TreeExplainer`.

2. `ml_engine.py`:
   - Class `DisasterRiskPredictor`:
     - Method `predict(input_data)`: Returns `risk_score`, `risk_level` (Low, Medium, High), `confidence_score`, and `top_shap_features` (dict of feature names and directional contribution).
     - Method `audit_prediction(prediction_id, actual_ground_truth)`:
       - Checks if prediction was correct or a mismatch (FP/FN).
       - If mismatch, computes the primary culprit feature driving the error.
       - Generates the human-readable root-cause summary string.

3. `main.py` (FastAPI Service):
   - Expose the following REST endpoints:
     - `POST /api/v1/predict`: Accepts telemetry/geospatial JSON payload, returns prediction + confidence + SHAP summary.
     - `POST /api/v1/audit`: Accepts `prediction_id` and `actual_outcome`, runs the self-auditing logic, logs the audit record, and returns the RCA explanation.
     - `GET /api/v1/audit/logs`: Returns historical audits to feed an administrative monitoring dashboard.
     - `POST /api/v1/simulate/time-travel`: Pre-packaged demo endpoint returning a sequence of 3 stages (T-24h Prediction, T-0h Ground Truth Arrival, T+1h Automated RCA Audit) so judges can see the self-audit loop live in under 10 seconds.

### 4. CONSTRAINTS & OUTPUT QUALITY
- Do not use mock ellipses (`...`) or leave functions unfinished. Provide complete, fully executable code blocks.
- Ensure all Pydantic schemas are strictly typed.
- Include a quick startup script or instructions to run the server via `uvicorn main:app --reload`.Act as a Principal MLOps & Geospatial AI Architect. I want you to build a complete, production-ready, fully functional Python backend using FastAPI and XGBoost for a Self-Auditing Disaster Management Prediction Engine (PS ID: 260001).

### 1. SYSTEM OVERVIEW & ARCHITECTURE
Build an end-to-end working pipeline that:
1. Takes multi-modal geospatial/hydrological inputs (Satellite SAR soil saturation, DEM elevation/slope, precipitation forecasts, river discharge).
2. Predicts disaster risk (Flood/Inundation probability between 0.0 and 1.0) using XGBoost.
3. Computes feature attribution using SHAP (TreeExplainer).
4. Generates an AI Confidence Score based on sensor variance and input data staleness.
5. Implements a POST-INFERENCE SELF-AUDITING LOOP:
   - Compares past predictions with actual ground truth data (simulated ground truth).
   - Flags discrepancies (False Positives or False Negatives).
   - Runs automated Root Cause Analysis (RCA) via SHAP deltas to determine *why* the prediction failed.
   - Outputs a human-readable one-liner explanation of the error (e.g., "False Alarm caused by 45% overestimated rainfall forecast overriding dry soil moisture").

### 2. TECH STACK SPECIFICATIONS
- Language: Python 3.10+
- Web Framework: FastAPI + Pydantic (data validation)
- Core ML & Explainability: XGBoost, SHAP, Scikit-learn
- Data & Spatial Processing: Pandas, NumPy
- Database & Spatial Simulation: SQLite / Mock In-Memory Store mimicking PostGIS spatial operations (ST_Intersection/Bounding Box logic).

### 3. REQUIRED MODULES & WORKING CODE
You must generate modular, fully runnable Python code with no placeholders or broken imports:

1. `synthetic_data.py`:
   - Generate a realistic training dataset of 1,000 historical rows with features:
     - `rainfall_last_24h` (mm)
     - `forecasted_rainfall_next_6h` (mm)
     - `soil_saturation_index` (0.0 to 1.0, Sentinel-1 SAR proxy)
     - `dem_slope_degrees` (0 to 60 degrees, SRTM DEM proxy)
     - `river_water_level_m` (meters)
     - `actual_inundation_risk` (0 or 1 - binary target)
   - Automatically train and serialize an `XGBClassifier` and initialize a `shap.TreeExplainer`.

2. `ml_engine.py`:
   - Class `DisasterRiskPredictor`:
     - Method `predict(input_data)`: Returns `risk_score`, `risk_level` (Low, Medium, High), `confidence_score`, and `top_shap_features` (dict of feature names and directional contribution).
     - Method `audit_prediction(prediction_id, actual_ground_truth)`:
       - Checks if prediction was correct or a mismatch (FP/FN).
       - If mismatch, computes the primary culprit feature driving the error.
       - Generates the human-readable root-cause summary string.

3. `main.py` (FastAPI Service):
   - Expose the following REST endpoints:
     - `POST /api/v1/predict`: Accepts telemetry/geospatial JSON payload, returns prediction + confidence + SHAP summary.
     - `POST /api/v1/audit`: Accepts `prediction_id` and `actual_outcome`, runs the self-auditing logic, logs the audit record, and returns the RCA explanation.
     - `GET /api/v1/audit/logs`: Returns historical audits to feed an administrative monitoring dashboard.
     - `POST /api/v1/simulate/time-travel`: Pre-packaged demo endpoint returning a sequence of 3 stages (T-24h Prediction, T-0h Ground Truth Arrival, T+1h Automated RCA Audit) so judges can see the self-audit loop live in under 10 seconds.

### 4. CONSTRAINTS & OUTPUT QUALITY
- Do not use mock ellipses (`...`) or leave functions unfinished. Provide complete, fully executable code blocks.
- Ensure all Pydantic schemas are strictly typed.
- Include a quick startup script or instructions to run the server via `uvicorn main:app --reload`.