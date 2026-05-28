param(
    [int]$ReachSteps = 50000,
    [int]$LiftSteps = 100000,
    [int]$PlaceSteps = 150000,
    [string]$Device = "cuda",
    [int]$BatchSize = 512,
    [int]$GradientSteps = 2,
    [string]$Algo = "ppo",
    [int]$NumEnvs = 8,
    [string]$VecEnv = "dummy",
    [string]$EnvPath = (Join-Path (Split-Path -Parent $PSScriptRoot) '.conda\winros'),
    [switch]$RenderTrain,
    [int]$RenderEvery = 10000,
    [int]$RenderSteps = 300
    ,
    [int]$RenderEpisodes = 5
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $EnvPath "python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "WinROS Conda environment not found at $EnvPath. Run scripts\setup_conda_env.ps1 first."
}

function Invoke-TrainStage {
    param(
        [string]$Env,
        [int]$Steps,
        [string]$LoadModel = ""
    )

    $args = @(
        "-m", "winros",
        "--train-env", $Env,
        "--algo", $Algo,
        "--timesteps", "$Steps",
        "--device", $Device,
        "--batch-size", "$BatchSize",
        "--gradient-steps", "$GradientSteps",
        "--num-envs", "$NumEnvs",
        "--vec-env", "$VecEnv"
    )

    if ($LoadModel) {
        $args += @("--load-model", $LoadModel)
    }
    if ($RenderTrain) {
        $args += @(
            "--render-train",
            "--render-train-freq", "$RenderEvery",
            "--render-train-steps", "$RenderSteps",
            "--render-train-episodes", "$RenderEpisodes"
        )
    }

    & $python @args
    if ($LASTEXITCODE -ne 0) {
        throw "$Env training failed with exit code $LASTEXITCODE"
    }
}

Push-Location $projectRoot
try {
    $reachModel = Join-Path $projectRoot "runs\sb3\WinROSArmReach-v0_${Algo}_${ReachSteps}_steps.zip"
    $liftModel = Join-Path $projectRoot "runs\sb3\WinROSArmLift-v0_${Algo}_${LiftSteps}_steps.zip"

    Invoke-TrainStage -Env "WinROSArmReach-v0" -Steps $ReachSteps
    Invoke-TrainStage -Env "WinROSArmLift-v0" -Steps $LiftSteps -LoadModel $reachModel
    Invoke-TrainStage -Env "WinROSArmPlace-v0" -Steps $PlaceSteps -LoadModel $liftModel
} finally {
    Pop-Location
}

