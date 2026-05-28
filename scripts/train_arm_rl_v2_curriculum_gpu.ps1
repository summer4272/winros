param(
    [int]$ReachSteps = 300000,
    [int]$LiftSteps = 900000,
    [int]$PlaceSteps = 1500000,
    [string]$Device = "cuda",
    [int]$BatchSize = 2048,
    [string]$Algo = "ppo",
    [int]$NumEnvs = 12,
    [string]$VecEnv = "dummy",
    [string]$EnvPath = (Join-Path (Split-Path -Parent $PSScriptRoot) '.conda\winros'),
    [switch]$RenderTrain,
    [int]$RenderEvery = 50000,
    [int]$RenderSteps = 340,
    [int]$RenderEpisodes = 3
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $EnvPath "python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "WinROS Conda environment not found at $EnvPath."
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
        "--num-envs", "$NumEnvs",
        "--vec-env", $VecEnv
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
    $reachModel = Join-Path $projectRoot "runs\sb3\WinROSArmRLV2Reach-v0_${Algo}_${ReachSteps}_steps.zip"
    $liftModel = Join-Path $projectRoot "runs\sb3\WinROSArmRLV2Lift-v0_${Algo}_${LiftSteps}_steps.zip"

    Invoke-TrainStage -Env "WinROSArmRLV2Reach-v0" -Steps $ReachSteps
    Invoke-TrainStage -Env "WinROSArmRLV2Lift-v0" -Steps $LiftSteps -LoadModel $reachModel
    Invoke-TrainStage -Env "WinROSArmRLV2Place-v0" -Steps $PlaceSteps -LoadModel $liftModel
} finally {
    Pop-Location
}

