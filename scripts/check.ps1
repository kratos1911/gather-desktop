param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
$rootPath = Split-Path $PSScriptRoot
Push-Location $rootPath
try {
    foreach ($suite in @('tests/worker', 'tests/evaluation', 'tests/inference')) {
        & $Python -m unittest discover -s $suite -v
        if ($LASTEXITCODE -ne 0) { throw "Python checks failed: $suite" }
    }
    foreach ($action in @('lint', 'typecheck', 'format-check', 'test', 'build')) {
        & (Join-Path $PSScriptRoot 'desktop.ps1') $action
    }
} finally { Pop-Location }
