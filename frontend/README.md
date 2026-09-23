# Disaster Intelligence Control Center — Frontend Dashboard
**Smart India Hackathon (SIH) Problem Statement ID: 260001**

A modern, high-density NDRF-inspired Disaster Intelligence Control Center built with **React 18**, **Vite**, and **Tailwind CSS**. Engineered for deployment on [Vercel](https://vercel.com).

---

## 1. Features

- **Tactical Command Center Design**: Dark mode aesthetic with high information density, accessible contrast, and zero childish gradients.
- **Interactive 24-Hour Time-Travel Engine**: Real-time visualization of early warning alerts, sensor ground-truth synchronization, and automated AI self-auditing.
- **Directional SHAP Feature Attribution**: Explains tree ensemble model margins without falsely claiming causal proof.
- **What-If Hypothesis Simulator**: Side-by-side comparison of baseline parameters against modified hydrologic stresses.
- **Live Connection Bar**: Dynamic backend URL switching, health ping testing, and transparent real vs synthetic data tags.
- **Subsystem & Model Diagnostics**: Holdout cross-validation metrics with honest scientific evaluation disclaimers.

---

## 2. Local Development

### Prerequisites
- Node.js 18+
- npm or yarn

### Setup Commands

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Create local environment configuration (Optional)
echo "VITE_BACKEND_API_URL=http://localhost:8000" > .env.local

# 4. Start the local Vite development server
npm run dev

# 5. Build production bundle
npm run build

# 6. Preview production build locally
npm run preview
```

The application will be accessible at: `http://localhost:5173`

---

## 3. Vercel Deployment Guide

To deploy the frontend to [Vercel](https://vercel.com):

### Option A: Via Vercel Web Dashboard (Recommended)

1. **Import Git Repository**:
   - Push your project to GitHub or GitLab.
   - Go to [vercel.com/new](https://vercel.com/new) and select your repository.
2. **Project Configuration**:
   - **Root Directory**: Click *Edit* and select `frontend`.
   - **Framework Preset**: `Vite` (automatically detected).
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`
3. **Environment Variables**:
   Add the following variable in the Vercel dashboard:
   - **Key**: `VITE_BACKEND_API_URL`
   - **Value**: Your Render.com backend URL (e.g., `https://disaster-intelligence-backend.onrender.com`)
4. **Deploy**:
   - Click **Deploy**. Vercel will build and assign an edge-cached `*.vercel.app` domain.

### Option B: Via Vercel CLI

```bash
cd frontend
npm install -g vercel
vercel login
vercel --prod
```

---

## 4. Connecting to the Render Backend

1. Deploy the backend on Render.com as outlined in `backend/README.md`.
2. Obtain your live Render URL (e.g. `https://sih-disaster-backend.onrender.com`).
3. Set `VITE_BACKEND_API_URL=https://sih-disaster-backend.onrender.com` in Vercel environment variables, OR simply enter it into the top **API Endpoint** configuration bar on the deployed frontend dashboard and click **Connect**.
4. The frontend will ping `/health`, retrieve live subsystem statuses from `/api/v1/system/status`, and display the active connection latency in milliseconds.
