param([ValidateSet('preview', 'desktop', 'build', 'test', 'install', 'lint', 'typecheck', 'format-check')][string]$Action = 'preview')
$ErrorActionPreference = 'Stop'
$appPath = Join-Path $PSScriptRoot '../apps/desktop'
$nodeCandidates = @(Get-Command node.exe -All -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
$nodePath = $nodeCandidates | Where-Object {
    $version = [version]((& $_ --version).TrimStart('v'))
    $version.Major -ge 24 -or ($version.Major -eq 22 -and $version.Minor -ge 12)
} | Select-Object -First 1
if (-not $nodePath) { throw 'Install Node.js 24 LTS, then run this script again.' }
$npmCandidates = @($nodeCandidates | ForEach-Object { Join-Path (Split-Path $_) 'node_modules/npm/bin/npm-cli.js' })
$npmCli = $npmCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
$previousPath = $env:PATH
try {
    $env:PATH = (Split-Path $nodePath) + ';' + (Join-Path $env:USERPROFILE '.cargo/bin') + ';' + $env:PATH
    Push-Location $appPath
    switch ($Action) {
        'install' { if (-not $npmCli) { throw 'npm is missing. Repair the Node.js installation.' }; & $nodePath $npmCli ci }
        'preview' { & $nodePath scripts/frontend.mjs dev }
        'desktop' { & $nodePath node_modules/@tauri-apps/cli/tauri.js dev }
        'build' { & $nodePath scripts/frontend.mjs build }
        'test' { & $nodePath node_modules/vitest/vitest.mjs run }
        'lint' { & $nodePath node_modules/eslint/bin/eslint.js . }
        'typecheck' { & $nodePath node_modules/typescript/bin/tsc --noEmit }
        'format-check' { & $nodePath node_modules/prettier/bin/prettier.cjs --check src scripts '*.ts' '*.json' '*.mjs' index.html }
    }
    if ($LASTEXITCODE -ne 0) { throw "Desktop task failed with exit code $LASTEXITCODE" }
} finally { Pop-Location; $env:PATH = $previousPath }
