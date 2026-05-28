param(
    [ValidateSet("WinROSArmGrasp-v0", "WinROSQuadrupedLocomotion-v0", "WinROSHumanoidLocomotion-v0")]
    [string]$Env = "WinROSArmGrasp-v0",
    [int]$Episodes = 1,
    [int]$Steps = 300,
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
    "--env", $Env,
    "--episodes", "$Episodes",
    "--steps", "$Steps"
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

