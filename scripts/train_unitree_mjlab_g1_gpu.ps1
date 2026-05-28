param(
  [int]$NumEnvs = 256,
  [int]$MaxIterations = 5000,
  [int]$SaveInterval = 100
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$repo = Join-Path $root "third_party\unitree_rl_mjlab"
$python = Join-Path $root ".conda\winros\python.exe"

Set-Location $repo

& $python scripts\train.py Unitree-G1-Flat `
  --env.scene.num-envs=$NumEnvs `
  --agent.max-iterations=$MaxIterations `
  --agent.save-interval=$SaveInterval `
  --agent.logger=tensorboard

