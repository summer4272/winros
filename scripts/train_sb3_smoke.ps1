param(
    [ValidateSet("WinROSArmGrasp-v0", "WinROSQuadrupedLocomotion-v0", "WinROSHumanoidLocomotion-v0")]
    [string]$Env = "WinROSArmGrasp-v0",
    [ValidateSet("ppo", "sac")]
    [string]$Algo = "sac",
    [int]$Timesteps = 128,
    [string]$Device = "cuda",
    [string]$EnvPath = (Join-Path (Split-Path -Parent $PSScriptRoot) '.conda\winros')
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $EnvPath "python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "WinROS Conda environment not found at $EnvPath. Run scripts\setup_conda_env.ps1 first."
}

Push-Location $projectRoot
try {
    & $python -m winros --train-env $Env --algo $Algo --timesteps $Timesteps --device $Device
} finally {
    Pop-Location
}

