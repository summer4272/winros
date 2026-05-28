param(
  [string]$Checkpoint = ""
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$repo = Join-Path $root "third_party\unitree_rl_mjlab"
$python = Join-Path $root ".conda\winros\python.exe"

Set-Location $repo

if ($Checkpoint -eq "") {
  $latest = Get-ChildItem -Path "logs\rsl_rl\g1_velocity" -Recurse -Filter "model_*.pt" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
  if (-not $latest) {
    throw "No G1 checkpoint found under $repo\logs\rsl_rl\g1_velocity"
  }
  $Checkpoint = $latest.FullName
}

& $python scripts\play.py Unitree-G1-Flat `
  --checkpoint-file=$Checkpoint `
  --num-envs=1 `
  --viewer=native `
  --device=cuda:0

