$ErrorActionPreference = "Stop"
$workspace = Split-Path -Parent $PSScriptRoot
& (Join-Path $workspace ".venv/Scripts/python.exe") (Join-Path $PSScriptRoot "start_e2e_api.py")
exit $LASTEXITCODE
