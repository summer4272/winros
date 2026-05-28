param(
    [string]$Model = (Join-Path (Split-Path -Parent $PSScriptRoot) "runs\sb3\WinROSArmGrasp-v0_sac_20000_steps.zip"),
    [int]$Episodes = 3,
    [int]$Steps = 300,
    [string]$Device = "cuda",
    [string]$EnvPath = (Join-Path (Split-Path -Parent $PSScriptRoot) '.conda\winros'),
    [switch]$NoRender
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $EnvPath "python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "WinROS Conda environment not found at $EnvPath. Run scripts\setup_conda_env.ps1 first."
}

$args = @(
    "-m", "winros",
    "--env", "WinROSArmGrasp-v0",
    "--play-model", $Model,
    "--algo", "sac",
    "--episodes", "$Episodes",
    "--steps", "$Steps",
    "--device", $Device
)

if (-not $NoRender) {
    $args += "--render-env"
}

Push-Location $projectRoot
try {
    & $python @args
} finally {
    Pop-Location
}

