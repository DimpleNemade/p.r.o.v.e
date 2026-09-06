[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$workspace = Split-Path -Parent $PSScriptRoot
$python = Join-Path $workspace ".venv\Scripts\python.exe"
$api = Join-Path $workspace "apps\api"

if (-not (Test-Path -LiteralPath $python)) { throw "Workspace Python environment not found at $python" }
Push-Location $api
try {
    & $python manage.py migrate --noinput
    & $python manage.py seed_demo
    & $python manage.py runserver 127.0.0.1:8000 --noreload
} finally {
    Pop-Location
}
