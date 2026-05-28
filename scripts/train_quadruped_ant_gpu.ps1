param(
  [int]$Timesteps = 1500000,
  [int]$BatchSize = 1024
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".conda\winros\python.exe"

Set-Location $root

& $python -m winros `
  --train-env Ant-v5 `
  --algo ppo `
  --timesteps $Timesteps `
  --device cuda `
  --batch-size $BatchSize

