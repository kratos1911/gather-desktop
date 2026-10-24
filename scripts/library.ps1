param(
    [ValidateSet('check','server','worker','frontend')][string]$Action = 'check',
    [string]$JobId
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot
$previousPython = $env:GATHER_PYTHON
$previousTemp = $env:TEMP
$previousTmp = $env:TMP
$previousKey = $env:VITE_GATHER_PILOT_PUBLIC_KEY
$locationPushed = $false
try {
    $taskTemp = Join-Path $root 'output/library-temp'
    New-Item -ItemType Directory -Force $taskTemp | Out-Null
    $env:TEMP = $taskTemp
    $env:TMP = $taskTemp
    Push-Location $root
    $locationPushed = $true
    if ($Action -eq 'frontend') {
        $config = Get-Content -LiteralPath 'output/supabase/pilot-public.json' -Raw | ConvertFrom-Json
        if ($config.project_ref -ne 'fatolholcjxpwocnpzws' -or $config.url -ne 'https://fatolholcjxpwocnpzws.supabase.co' -or $config.publishable_key -notlike 'sb_publishable_*') {
            throw 'Invalid pilot public configuration.'
        }
        $env:VITE_GATHER_PILOT_PUBLIC_KEY = $config.publishable_key
        & ./scripts/desktop.ps1 preview
    } else {
        $runtime = Join-Path $root 'output/asgi-checks/venv/Scripts/python.exe'
        if (-not (Test-Path -LiteralPath $runtime)) { throw 'Existing isolated HTTP runtime is missing. No installation or fallback attempted.' }
        $env:GATHER_PYTHON = $runtime
        $arguments = @('-m','scripts.operator_library')
        if ($Action -eq 'server') { $arguments += '--serve' }
        if ($Action -eq 'worker') {
            if (-not $JobId) { throw 'Worker requires the exact acknowledged pilot JobId.' }
            $arguments += @('--work','--job-id',$JobId)
        }
        & ./scripts/python.ps1 @arguments
    }
    if ($LASTEXITCODE -ne 0) { throw "Library task exited with code $LASTEXITCODE" }
} finally {
    if ($locationPushed) { Pop-Location }
    $env:GATHER_PYTHON = $previousPython
    $env:TEMP = $previousTemp
    $env:TMP = $previousTmp
    $env:VITE_GATHER_PILOT_PUBLIC_KEY = $previousKey
}
