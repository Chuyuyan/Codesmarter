# PowerShell script to start the Flask server
# Usage: .\start_server.ps1

# Change to script directory
Set-Location $PSScriptRoot

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Start Flask server
Write-Host "Starting Flask server..." -ForegroundColor Green
Write-Host "Open your browser at: http://127.0.0.1:5050" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server`n" -ForegroundColor Yellow

python -m backend.app

