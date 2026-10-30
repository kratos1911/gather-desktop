param([ValidateSet('build','native','installer')][string]$Action='build')
$ErrorActionPreference='Stop'
$gatherRoot=Split-Path $PSScriptRoot
$previousConnected=$env:VITE_GATHER_CONNECTED_PILOT
$previousKey=$env:VITE_GATHER_PILOT_PUBLIC_KEY
$previousOffline=$env:CARGO_NET_OFFLINE
$previousTarget=$env:CARGO_TARGET_DIR
try {
    $public=Get-Content -LiteralPath (Join-Path $gatherRoot 'output/supabase/pilot-public.json') -Raw | ConvertFrom-Json
    if ($public.project_ref -ne 'fatolholcjxpwocnpzws' -or $public.url -ne 'https://fatolholcjxpwocnpzws.supabase.co' -or $public.publishable_key -notlike 'sb_publishable_*') { throw 'Invalid Gather public configuration.' }
    $env:VITE_GATHER_CONNECTED_PILOT='1'
    $env:VITE_GATHER_PILOT_PUBLIC_KEY=$public.publishable_key
    $env:CARGO_NET_OFFLINE='true'
    if($Action -eq 'installer') {
        $verified=Get-Content -LiteralPath (Join-Path $gatherRoot 'output/private-desktop/verification.json') -Raw | ConvertFrom-Json
        $binary=Join-Path $gatherRoot 'apps/desktop/src-tauri/target/debug/gather-desktop.exe'
        if((Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash -ne $verified.sha256) { throw 'Native executable differs from the verified candidate; do not package it.' }
        # Bundle an isolated copy so stamp updates never modify a running app.
        $installerTarget=Join-Path $gatherRoot 'output/private-desktop/installer-target'
        New-Item -ItemType Directory -Force (Join-Path $installerTarget 'debug') | Out-Null
        Copy-Item -LiteralPath $binary -Destination (Join-Path $installerTarget 'debug/gather-desktop.exe')
        $tools=Join-Path $gatherRoot 'apps/desktop/src-tauri/target/.tauri'
        if(Test-Path -LiteralPath $tools) { Copy-Item -LiteralPath $tools -Destination $installerTarget -Recurse -Force }
        $env:CARGO_TARGET_DIR=$installerTarget
    }
    $desktopAction=if($Action -eq 'native'){'native-pilot'}elseif($Action -eq 'installer'){'installer-pilot'}else{'build'}
    & (Join-Path $PSScriptRoot 'desktop.ps1') $desktopAction
    if($LASTEXITCODE -ne 0){throw 'Private desktop build failed.'}
} finally {
    $env:VITE_GATHER_CONNECTED_PILOT=$previousConnected
    $env:VITE_GATHER_PILOT_PUBLIC_KEY=$previousKey
    $env:CARGO_NET_OFFLINE=$previousOffline
    $env:CARGO_TARGET_DIR=$previousTarget
}
