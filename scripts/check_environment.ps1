[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"
$workspace = Split-Path -Parent $PSScriptRoot
$localPython = Join-Path $workspace ".venv\Scripts\python.exe"
$requiredFailures = 0

function Report-Check {
    param(
        [string]$Name,
        [bool]$Required,
        [scriptblock]$Probe
    )
    try {
        $value = (& $Probe 2>&1 | Out-String).Trim()
        if ($LASTEXITCODE -ne 0 -or -not $value) { throw "probe returned no usable version" }
        Write-Output ("{0}: {1} - {2}" -f ($(if ($Required) { "REQUIRED" } else { "OPTIONAL" }), $Name, ($value -split "`r?`n")[0]))
    } catch {
        Write-Output ("{0}: {1} - MISSING ({2})" -f ($(if ($Required) { "REQUIRED" } else { "OPTIONAL" }), $Name, $_.Exception.Message))
        if ($Required) { $script:requiredFailures++ }
    }
}

Write-Output "Workspace: $workspace"
$os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
if ($os) { Write-Output "Windows: $($os.Caption) ($($os.Version), build $($os.BuildNumber))" }
else { Write-Output "Windows: unavailable" }

Report-Check "Python" $true { if (Test-Path -LiteralPath $localPython) { & $localPython --version } else { & python --version } }
if (Test-Path -LiteralPath (Join-Path $workspace ".venv")) { Write-Output "Virtual environment: REQUIRED - present (.venv)" }
else { Write-Output "Virtual environment: REQUIRED - MISSING (.venv)"; $requiredFailures++ }
Report-Check "Django" $true { & $localPython -c "import django; print(django.get_version())" }
Report-Check "Pytest" $true { & $localPython -m pytest --version }
Report-Check "Node.js" $true { & node --version }
Report-Check "npm" $true { & npm.cmd --version }
Report-Check "Rust" $false { & rustc --version }
Report-Check "Cargo" $false { & cargo --version }

$tauri = Join-Path $workspace "apps\desktop\node_modules\.bin\tauri.cmd"
Report-Check "Tauri CLI" $false { if (Test-Path -LiteralPath $tauri) { & $tauri --version } else { throw "desktop dependency directory is not installed" } }
Report-Check "Docker" $false { & docker --version }
Report-Check "Docker Compose" $false { & docker compose version }
Report-Check "PostgreSQL client" $false { & psql --version }
Report-Check "Redis client" $false { & redis-cli --version }

if (Test-Path -LiteralPath (Join-Path $workspace "apps\web\node_modules")) { Write-Output "Frontend dependency directory: REQUIRED - present" }
else { Write-Output "Frontend dependency directory: REQUIRED - MISSING"; $requiredFailures++ }
if (Test-Path -LiteralPath $localPython) {
    & $localPython -c "import django, rest_framework, pytest; print('Django REST/Pytest imports available')" 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Output "Backend dependency status: REQUIRED - imports available" }
    else { Write-Output "Backend dependency status: REQUIRED - incomplete"; $requiredFailures++ }
}
else { Write-Output "Backend dependency status: REQUIRED - cannot inspect without local Python"; $requiredFailures++ }

if ($requiredFailures -gt 0) {
    Write-Output "Environment result: FAILED ($requiredFailures required check(s) missing)"
    exit 1
}
Write-Output "Environment result: REQUIRED TOOLCHAIN AVAILABLE (optional integrations may be unavailable)"
exit 0
