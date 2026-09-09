$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Daily = Join-Path $Root "daily_once.py"
$Hourly = Join-Path $Root "monitor_once.py"

if (-not (Test-Path $Python)) {
    throw "Virtual environment Python not found at $Python. Create/activate .venv and install requirements first."
}

$DailyAction = '"' + $Python + '" "' + $Daily + '"'
$HourlyAction = '"' + $Python + '" "' + $Hourly + '"'

schtasks /Create /TN "AgenticOR-Daily-8AM" /TR $DailyAction /SC DAILY /ST 08:00 /F
schtasks /Create /TN "AgenticOR-Hourly-Monitor" /TR $HourlyAction /SC HOURLY /MO 1 /ST 00:05 /F

Write-Host "Created Windows scheduled tasks:"
Write-Host "  AgenticOR-Daily-8AM       -> daily report + email at 08:00"
Write-Host "  AgenticOR-Hourly-Monitor  -> disruption check every hour at :05"
Write-Host "Your PC must be running and network-connected for local scheduled tasks to execute."
