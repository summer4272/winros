param(
    [string]$Model = (Join-Path (Split-Path -Parent $PSScriptRoot) "runs\sb3\FetchPickAndPlace-v4_sac_300000_steps.zip"),
    [string]$EnvId = "FetchPickAndPlace-v4",
    [int]$Episodes = 5,
    [int]$Steps = 100,
    [string]$Device = "cuda",
    [string]$EnvPath = (Join-Path (Split-Path -Parent $PSScriptRoot) '.conda\winros'),
    [switch]$Render
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $EnvPath "python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "WinROS Conda environment not found at $EnvPath. Run scripts\setup_conda_env.ps1 first."
}

$args = @(
    "-m", "winros",
    "--env", "$EnvId",
    "--play-model", "$Model",
    "--algo", "sac",
    "--episodes", "$Episodes",
    "--steps", "$Steps",
    "--device", "$Device"
)

if ($Render) {
    $args += @("--render-env")
}

Push-Location $projectRoot
try {
    & $python @args
    if ($LASTEXITCODE -ne 0) {
        throw "Fetch pick-place playback failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}

