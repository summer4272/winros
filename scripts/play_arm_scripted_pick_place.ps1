param(
    [int]$Episodes = 5,
    [int]$Seed = 1,
    [string]$EnvPath = (Join-Path (Split-Path -Parent $PSScriptRoot) '.conda\winros'),
    [switch]$Render,
    [switch]$NoAssistGrasp
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $EnvPath "python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "WinROS Conda environment not found at $EnvPath. Run scripts\setup_conda_env.ps1 first."
}

$args = @(
    "-m", "winros.scripted_arm_pick_place",
    "--episodes", "$Episodes",
    "--seed", "$Seed"
)

if ($Render) {
    $args += @("--render", "--realtime")
}

if ($NoAssistGrasp) {
    $args += @("--no-assist-grasp")
}

Push-Location $projectRoot
try {
    & $python @args
    if ($LASTEXITCODE -ne 0) {
        throw "Scripted arm pick-place failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}

