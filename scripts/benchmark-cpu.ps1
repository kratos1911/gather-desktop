param(
    [ValidateSet('install', 'download', 'run')][string]$Action = 'run',
    [ValidateSet(2, 4, 8)][int]$Threads = 2,
    [ValidateSet('text-v1', 'text-v2')][string]$Corpus = 'text-v1',
    [string]$Python = 'python'
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot
$benchRoot = [IO.Path]::GetFullPath((Join-Path $repoRoot 'output/model-benchmark'))
if ([IO.Path]::GetPathRoot($benchRoot) -ne 'D:\') { throw 'Benchmark artifacts must be on D:.' }
$directories = @{
    TEMP = 'tmp'; TMP = 'tmp'; PIP_CACHE_DIR = 'pip-cache'; HF_HOME = 'hf'
    HF_HUB_CACHE = 'hf/hub'; HF_XET_CACHE = 'hf/xet'; TORCH_HOME = 'torch'; XDG_CACHE_HOME = 'cache'
}
foreach ($key in $directories.Keys) {
    $path = Join-Path $benchRoot $directories[$key]
    New-Item -ItemType Directory -Force -Path $path | Out-Null
    [Environment]::SetEnvironmentVariable($key, $path, 'Process')
}
$env:PYTHONNOUSERSITE = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:HF_HUB_DISABLE_TELEMETRY = '1'
$env:HF_HUB_DISABLE_IMPLICIT_TOKEN = '1'
$env:HF_HUB_DISABLE_XET = '1'
$benchPython = Join-Path $benchRoot 'venv/Scripts/python.exe'
$constraints = Join-Path $PSScriptRoot 'benchmark-cpu-constraints.txt'
Push-Location $repoRoot
try {
    if ($Action -eq 'install') {
        if (-not (Test-Path $benchPython)) {
            & $Python -m venv (Join-Path $benchRoot 'venv')
            if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed' }
        }
        & $benchPython -m pip install --only-binary=:all: --disable-pip-version-check -c $constraints 'torch==2.8.0+cpu' --index-url https://download.pytorch.org/whl/cpu
        if ($LASTEXITCODE -ne 0) { throw 'CPU PyTorch installation failed' }
        & $benchPython -m pip install --only-binary=:all: --disable-pip-version-check -c $constraints 'transformers==4.57.6' 'psutil==7.2.0' --index-url https://pypi.org/simple
        if ($LASTEXITCODE -ne 0) { throw 'Benchmark dependency installation failed' }
    } elseif ($Action -eq 'download') {
        & $benchPython -m scripts.benchmark_cpu --download
        if ($LASTEXITCODE -ne 0) { throw 'Model download failed' }
    } else {
        $runRoot = $benchRoot
        if ($Corpus -ne 'text-v1') { $runRoot = Join-Path $benchRoot $Corpus }
        & $benchPython -m scripts.prepare_text_evaluation --corpus $Corpus --output (Join-Path $runRoot 'inputs')
        if ($LASTEXITCODE -ne 0) { throw 'Corpus preparation failed' }
        & $benchPython -m scripts.benchmark_cpu --threads $Threads --corpus $Corpus
        if ($LASTEXITCODE -ne 0) { throw 'Model benchmark failed' }
        foreach ($dimension in @(256, 512, 1024)) {
            $runPath = Join-Path $runRoot "qwen-${Threads}threads"
            & $benchPython -m scripts.evaluate_vectors --corpus $Corpus --vectors "$runPath/vectors-$dimension.json" --output "$runPath/scores-$dimension"
            if ($LASTEXITCODE -ne 0) { throw 'Model scoring failed' }
        }
    }
    & $benchPython -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'Dependency consistency check failed' }
    & $benchPython -m pip freeze | Set-Content -Encoding utf8 (Join-Path $benchRoot 'environment.txt')
} finally { Pop-Location }
