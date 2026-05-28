param(
  [Parameter(Mandatory = $true)]
  [string]$Task,
  [string]$Experiment = "",
  [string]$Checkpoint = ""
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$repo = Join-Path $root "third_party\unitree_rl_mjlab"
$python = Join-Path $root ".conda\winros\python.exe"

Set-Location $repo

if ($Experiment -eq "") {
  if ($Task -like "Unitree-Go2-*") {
    $Experiment = "go2_velocity"
  } elseif ($Task -like "Unitree-G1-*") {
    $Experiment = "g1_velocity"
  } else {
    throw "Please pass -Experiment for task $Task"
  }
}

if ($Checkpoint -eq "") {
  $taskRunPatterns = @{
    "Unitree-Go2-FastFlat" = "_unitree_go2_fast_flat_\d"
    "Unitree-Go2-Stairs" = "_unitree_go2_stairs_\d"
    "Unitree-Go2-StairsV2" = "_unitree_go2_stairs_v2_"
    "Unitree-Go2-StairsForwardV3" = "_unitree_go2_stairs_forward_v3_"
    "Unitree-G1-FastFlat" = "_unitree_g1_fast_flat_\d"
    "Unitree-G1-FastFlatV2" = "_unitree_g1_fast_flat_v2_"
    "Unitree-G1-FastRunV1" = "_unitree_g1_fast_run_v1_"
    "Unitree-G1-HurdlesRunV1" = "_unitree_g1_hurdles_run_v1_"
    "Unitree-G1-StairsForwardV1" = "_unitree_g1_stairs_forward_v1_"
  }

  $models = Get-ChildItem -Path (Join-Path "logs\rsl_rl" $Experiment) -Recurse -Filter "model_*.pt"
  if ($taskRunPatterns.ContainsKey($Task)) {
    $pattern = $taskRunPatterns[$Task]
    $models = $models | Where-Object { (Split-Path $_.DirectoryName -Leaf) -match $pattern }
  }

  $latest = $models |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
  if (-not $latest) {
    throw "No matching checkpoint found for $Task under $repo\logs\rsl_rl\$Experiment. Pass -Checkpoint explicitly if needed."
  }
  $Checkpoint = $latest.FullName
}

Write-Host "Playing task: $Task"
Write-Host "Checkpoint: $Checkpoint"

& $python scripts\play.py $Task `
  --checkpoint-file=$Checkpoint `
  --num-envs=1 `
  --viewer=native `
  --device=cuda:0

