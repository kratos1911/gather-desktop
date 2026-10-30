param([ValidateSet('preview', 'desktop', 'build', 'test', 'install', 'lint', 'typecheck', 'format-check', 'native-pilot', 'installer-pilot')][string]$Action = 'preview')
$ErrorActionPreference = 'Stop'
$appPath = Join-Path $PSScriptRoot '../apps/desktop'
$nodeCandidates = @()
if ($env:GATHER_NODE) {
    $nodeCandidates = @($env:GATHER_NODE)
} else {
    $nodeCandidates = @(Get-Command node.exe -All -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
    if ($env:USERPROFILE) {
        $nodeCandidates += Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
    }
}
$nodeCandidates = @($nodeCandidates | Select-Object -Unique | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf })
$nodePath = $nodeCandidates | Where-Object {
    try {
        $version = [version]((& $_ --version).TrimStart('v'))
        $LASTEXITCODE -eq 0 -and ($version.Major -ge 24 -or ($version.Major -eq 22 -and $version.Minor -ge 12))
    } catch { $false }
} | Select-Object -First 1
if (-not $nodePath) { throw 'No supported Node runtime found. Set GATHER_NODE to an existing Node 24 LTS (or Node 22.12+) node.exe path, then retry.' }
$npmCandidates = @($nodeCandidates | ForEach-Object { Join-Path (Split-Path $_) 'node_modules/npm/bin/npm-cli.js' })
$npmCli = $npmCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
$previousPath = $env:PATH
$previousTemp = $env:TEMP
$previousTmp = $env:TMP
try {
    $taskTemp = Join-Path $PSScriptRoot '../output/desktop-build-temp'
    New-Item -ItemType Directory -Force -Path $taskTemp | Out-Null
    $env:TEMP = [IO.Path]::GetFullPath($taskTemp)
    $env:TMP = $env:TEMP
    $env:PATH = (Split-Path $nodePath) + ';' + (Join-Path $env:USERPROFILE '.cargo/bin') + ';' + $env:PATH
    Push-Location $appPath
    switch ($Action) {
        'install' { if (-not $npmCli) { throw 'npm is missing. Repair the Node.js installation.' }; & $nodePath $npmCli ci }
        'preview' { & $nodePath scripts/frontend.mjs dev }
        'desktop' { & $nodePath node_modules/@tauri-apps/cli/tauri.js dev }
        'native-pilot' { & $nodePath node_modules/@tauri-apps/cli/tauri.js build --debug --no-bundle --config src-tauri/tauri.pilot.conf.json }
        'installer-pilot' { & $nodePath node_modules/@tauri-apps/cli/tauri.js bundle --debug --bundles nsis --config src-tauri/tauri.pilot.conf.json --config '{"bundle":{"useLocalToolsDir":true}}' }
        'build' { & $nodePath scripts/frontend.mjs build }
        'test' { & $nodePath node_modules/vitest/vitest.mjs run }
        'lint' { & $nodePath node_modules/eslint/bin/eslint.js . }
        'typecheck' { & $nodePath node_modules/typescript/bin/tsc --noEmit }
        'format-check' { & $nodePath node_modules/prettier/bin/prettier.cjs --check src scripts '*.ts' '*.json' '*.mjs' index.html }
    }
    if ($LASTEXITCODE -ne 0) { throw "Desktop task failed with exit code $LASTEXITCODE" }
} finally {
    Pop-Location
    $env:PATH = $previousPath
    $env:TEMP = $previousTemp
    $env:TMP = $previousTmp
}
