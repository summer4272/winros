param(
  [string]$Checkpoint = ""
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$repo = Join-Path $root "third_party\unitree_rl_mjlab"
$python = Join-Path $root ".conda\winros\python.exe"

Set-Location $repo

if ($Checkpoint -eq "") {
  $latest = Get-ChildItem -Path "logs\rsl_rl\go2_velocity" -Recurse -Filter "model_*.pt" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
  if (-not $latest) {
    throw "No Go2 checkpoint found under $repo\logs\rsl_rl\go2_velocity"
  }
  $Checkpoint = $latest.FullName
}

& $python scripts\play.py Unitree-Go2-Flat `
  --checkpoint-file=$Checkpoint `
  --num-envs=1 `
  --viewer=native `
  --device=cuda:0

