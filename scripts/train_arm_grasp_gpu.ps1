param(
    [int]$Timesteps = 20000,
    [string]$Device = "cuda",
    [string]$EnvPath = (Join-Path (Split-Path -Parent $PSScriptRoot) '.conda\winros'),
    [switch]$RenderTrain,
    [int]$RenderEvery = 5000,
    [int]$RenderSteps = 300,
    [int]$RenderEpisodes = 5,
    [int]$BatchSize = 512,
    [int]$GradientSteps = 2
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $EnvPath "python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "WinROS Conda environment not found at $EnvPath. Run scripts\setup_conda_env.ps1 first."
}

Push-Location $projectRoot
try {
    $args = @(
        "-m", "winros",
        "--train-env", "WinROSArmGrasp-v0",
        "--algo", "sac",
        "--timesteps", "$Timesteps",
        "--device", $Device,
        "--batch-size", "$BatchSize",
        "--gradient-steps", "$GradientSteps"
    )
    if ($RenderTrain) {
        $args += @(
            "--render-train",
            "--render-train-freq", "$RenderEvery",
            "--render-train-steps", "$RenderSteps",
            "--render-train-episodes", "$RenderEpisodes"
        )
    }
    & $python @args
} finally {
    Pop-Location
}

