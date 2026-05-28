$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".conda\winros\python.exe"
$model = Join-Path $root "runs\sb3\FrankaPickAndPlaceSparse-v0_sac_300000_steps.zip"

Set-Location $root

& $python -m winros `
  --env FrankaPickAndPlaceSparse-v0 `
  --play-model $model `
  --algo sac `
  --device cuda `
  --episodes 5 `
  --steps 250 `
  --render-env `
  --realtime

