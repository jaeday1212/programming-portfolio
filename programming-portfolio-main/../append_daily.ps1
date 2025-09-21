# PowerShell helper to append today's synthetic device data
# Usage: run manually or schedule with Windows Task Scheduler to run once per day after midnight
# Adjust path to python.exe if needed
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $projectRoot '.venv/ Scripts /python.exe'
if (-Not (Test-Path $python)) { $python = 'python' }
Write-Host "Appending today's device metrics..."
python device_simulator.py --append-today
