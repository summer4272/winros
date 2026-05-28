param(
  [int]$Tail = 80
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot

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

$sources = @(
  @{
    PidFile = Join-Path $root "runs\unitree_stairs_v3\unitree_stairs_v3_jobs.csv"
    Names = @("unitree_go2_stairs_forward_v3")
  },
  @{
    PidFile = Join-Path $root "runs\unitree_motion_v2\unitree_motion_v2_jobs.csv"
    Names = @("unitree_g1_fast_flat_v2")
  },
  @{
    PidFile = Join-Path $root "runs\g1_fast_flat_v2\g1_fast_flat_v2_jobs.csv"
    Names = @("unitree_g1_fast_flat_v2")
  },
  @{
    PidFile = Join-Path $root "runs\g1_fast_run_v1\g1_fast_run_v1_jobs.csv"
    Names = @("unitree_g1_fast_run_v1")
  },
  @{
    PidFile = Join-Path $root "runs\g1_hurdles_run_v1\g1_hurdles_run_v1_jobs.csv"
    Names = @("unitree_g1_hurdles_run_v1")
  },
  @{
    PidFile = Join-Path $root "runs\g1_stairs_forward\g1_stairs_forward_jobs.csv"
    Names = @("unitree_g1_stairs_forward_v1")
  }
)

function Get-LatestCheckpoint {
  param(
    [string]$Task
  )

  if ($Task -like "Unitree-Go2-*") {
    $experiment = "go2_velocity"
  } elseif ($Task -like "Unitree-G1-*") {
    $experiment = "g1_velocity"
  } else {
    return $null
  }

  $checkpointRoot = Join-Path $root "third_party\unitree_rl_mjlab\logs\rsl_rl\$experiment"
  if (-not (Test-Path $checkpointRoot)) {
    return $null
  }

  $models = Get-ChildItem -Path $checkpointRoot -Recurse -Filter "model_*.pt" -ErrorAction SilentlyContinue
  if ($taskRunPatterns.ContainsKey($Task)) {
    $pattern = $taskRunPatterns[$Task]
    $models = $models | Where-Object { (Split-Path $_.DirectoryName -Leaf) -match $pattern }
  }

  return $models | Sort-Object LastWriteTime -Descending | Select-Object -First 1
}

foreach ($source in $sources) {
  if (-not (Test-Path $source.PidFile)) {
    continue
  }

  $jobs = Import-Csv $source.PidFile
  foreach ($job in $jobs) {
    if ($job.name -eq "name") { continue }
    if ($source.Names -notcontains $job.name) { continue }

    $proc = Get-Process -Id ([int]$job.pid) -ErrorAction SilentlyContinue
    $status = if ($proc) { "running pid=$($job.pid)" } else { "finished or stopped pid=$($job.pid)" }
    $latest = Get-LatestCheckpoint -Task $job.task

    Write-Host ""
    Write-Host "=== $($job.name) / $($job.task) ==="
    Write-Host "status: $status"
    Write-Host "num_envs: $($job.num_envs), target_iterations: $($job.iterations), started_at: $($job.started_at)"
    if ($latest) {
      Write-Host "latest checkpoint: $($latest.FullName)"
      Write-Host "checkpoint time: $($latest.LastWriteTime)"
    }

    if (Test-Path $job.out_log) {
      Write-Host "--- latest stdout ---"
      Get-Content $job.out_log -Tail $Tail
    }
    if ((Test-Path $job.err_log) -and ((Get-Item $job.err_log).Length -gt 0)) {
      Write-Host "--- latest stderr ---"
      Get-Content $job.err_log -Tail 60
    }
  }
}

