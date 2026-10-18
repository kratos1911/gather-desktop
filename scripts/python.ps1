# Lightweight repository checks only; model workloads keep their dedicated runtime.
# All arguments are passed as separate values, including paths containing spaces.
$ErrorActionPreference = 'Stop'
$pythonArguments = @($args)
$candidates = @()
if ($env:GATHER_PYTHON) {
    $candidates = @($env:GATHER_PYTHON)
} else {
    if ($env:VIRTUAL_ENV) {
        $candidates += Join-Path $env:VIRTUAL_ENV 'Scripts/python.exe'
    }
    $candidates += @(Get-Command python.exe -CommandType Application -All -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty Source)
    $installRoots = @()
    if ($env:LOCALAPPDATA) { $installRoots += Join-Path $env:LOCALAPPDATA 'Programs/Python' }
    # Sandboxed shells can redirect LOCALAPPDATA away from the actual install.
    if ($env:USERPROFILE) { $installRoots += Join-Path $env:USERPROFILE 'AppData/Local/Programs/Python' }
    foreach ($installRoot in ($installRoots | Select-Object -Unique)) {
        if (Test-Path -LiteralPath $installRoot) {
            $candidates += @(Get-ChildItem -LiteralPath $installRoot -Directory -Filter 'Python*' |
                Sort-Object Name -Descending | ForEach-Object { Join-Path $_.FullName 'python.exe' })
        }
    }
}
$selectedPython = $null
foreach ($candidate in ($candidates | Select-Object -Unique)) {
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }
    if (-not $env:GATHER_PYTHON -and $candidate -like '*\Microsoft\WindowsApps\*') { continue }
    try {
        & $candidate -I -S -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>$null
        if ($LASTEXITCODE -eq 0) { $selectedPython = $candidate; break }
    } catch { continue }
}
if (-not $selectedPython) {
    throw 'No working Python 3.10+ found. Set GATHER_PYTHON to an existing python.exe path. Do not repeatedly retry or scan whole drives.'
}
& $selectedPython @pythonArguments
exit $LASTEXITCODE
