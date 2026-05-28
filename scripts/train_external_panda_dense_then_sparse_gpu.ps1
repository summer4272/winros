param(
  [int]$DenseTimesteps = 1000000,
  [int]$SparseTimesteps = 1000000,
  [int]$BatchSize = 1024,
  [int]$GradientSteps = 4,
  [switch]$RenderTrain
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".conda\winros\python.exe"
$denseModel = Join-Path $root "runs\sb3\FrankaPickAndPlaceDense-v0_sac_${DenseTimesteps}_steps.zip"

Set-Location $root

$denseArgs = @(
  "-m", "winros",
  "--train-env", "FrankaPickAndPlaceDense-v0",
  "--algo", "sac",
  "--timesteps", [string]$DenseTimesteps,
  "--device", "cuda",
  "--batch-size", [string]$BatchSize,
  "--gradient-steps", [string]$GradientSteps
)

if ($RenderTrain) {
  $denseArgs += @(
    "--render-train",
    "--render-train-freq", "50000",
    "--render-train-steps", "250",
    "--render-train-episodes", "5"
  )
}

& $python @denseArgs

$sparseArgs = @(
  "-m", "winros",
  "--train-env", "FrankaPickAndPlaceSparse-v0",
  "--algo", "sac",
  "--load-model", $denseModel,
  "--timesteps", [string]$SparseTimesteps,
  "--device", "cuda",
  "--batch-size", [string]$BatchSize,
  "--gradient-steps", [string]$GradientSteps
)

if ($RenderTrain) {
  $sparseArgs += @(
    "--render-train",
    "--render-train-freq", "50000",
    "--render-train-steps", "250",
    "--render-train-episodes", "5"
  )
}

& $python @sparseArgs

