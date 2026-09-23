@echo off
echo ==============================================================================
echo Starting Disaster Intelligence Control Center (PS ID: 260001)
echo Dashboard: http://localhost:8000/
echo Swagger API: http://localhost:8000/docs
echo ==============================================================================

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
