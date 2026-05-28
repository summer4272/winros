param(
    [int]$Episodes = 5,
    [int]$Seed = 2000,
    [string]$Model = (Join-Path (Split-Path -Parent $PSScriptRoot) "runs\arm_bc\arm_scripted_bc.pt"),
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
    "-m", "winros.play_arm_scripted_bc",
    "--model", "$Model",
    "--episodes", "$Episodes",
    "--seed", "$Seed",
    "--device", "$Device"
)

if ($Render) {
    $args += @("--render", "--realtime")
}

Push-Location $projectRoot
try {
    & $python @args
    if ($LASTEXITCODE -ne 0) {
        throw "BC policy playback failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}

