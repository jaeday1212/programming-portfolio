# PowerShell helper to append today's synthetic device data
# Usage: run manually or schedule with Windows Task Scheduler to run once per day after midnight
# Adjust path to python.exe if needed
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $projectRoot '.venv' | Join-Path -ChildPath 'Scripts' | Join-Path -ChildPath 'python.exe'
if (-Not (Test-Path $venvPython)) { $venvPython = 'python' }
Write-Host "Appending today's device metrics using $venvPython"
& $venvPython device_simulator.py --append-today
