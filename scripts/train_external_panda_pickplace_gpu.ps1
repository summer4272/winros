$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".conda\winros\python.exe"

Set-Location $root

& $python -m winros `
  --train-env FrankaPickAndPlaceSparse-v0 `
  --algo sac `
  --timesteps 300000 `
  --device cuda `
  --batch-size 1024 `
  --gradient-steps 4 `
  --render-train `
  --render-train-freq 20000 `
  --render-train-steps 250 `
  --render-train-episodes 5

