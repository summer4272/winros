param(
  [string]$Model = (Join-Path (Split-Path -Parent $PSScriptRoot) "runs\sb3\Ant-v5_ppo_1500000_steps.zip")
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".conda\winros\python.exe"

Set-Location $root

& $python -m winros `
  --env Ant-v5 `
  --play-model $Model `
  --algo ppo `
  --device cuda `
  --episodes 5 `
  --steps 1000 `
  --render-env `
  --realtime

