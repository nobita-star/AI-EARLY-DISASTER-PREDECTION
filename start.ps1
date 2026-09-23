# PowerShell startup script for PS ID: 260001
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "Starting Disaster Intelligence Control Center (PS ID: 260001)" -ForegroundColor Green
Write-Host "Dashboard: http://localhost:8000/" -ForegroundColor Yellow
Write-Host "Swagger API: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "==============================================================================" -ForegroundColor Cyan

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
