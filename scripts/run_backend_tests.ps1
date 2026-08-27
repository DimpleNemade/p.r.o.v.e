[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"
$workspace = Split-Path -Parent $PSScriptRoot
$python = Join-Path $workspace ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    $python = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $python) {
    Write-Error "Python was not found. Run scripts/check_environment.ps1 first."
    exit 1
}

$api = Join-Path $workspace "apps\api"
Push-Location $api
try {
    & $python manage.py test
    $djangoExit = $LASTEXITCODE
} finally {
    Pop-Location
}

if ($djangoExit -ne 0) {
    exit $djangoExit
}

& $python -m pytest (Join-Path $workspace "services\forensic-worker\tests") -q
exit $LASTEXITCODE
