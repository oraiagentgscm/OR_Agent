$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    . ".\.venv\Scripts\Activate.ps1"
}
streamlit run dashboard.py
