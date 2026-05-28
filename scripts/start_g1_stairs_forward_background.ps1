param(
  [int]$NumEnvs = 128,
  [int]$Iterations = 12000,
  [int]$SaveInterval = 100,
  [switch]$NoResume
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $root "runs\g1_stairs_forward"
$pidFile = Join-Path $logDir "g1_stairs_forward_jobs.csv"
$trainScript = Join-Path $root "scripts\train_unitree_mjlab_velocity_task_gpu.ps1"
$g1LogRoot = Join-Path $root "third_party\unitree_rl_mjlab\logs\rsl_rl\g1_velocity"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null
"name,pid,task,num_envs,iterations,resume_from,out_log,err_log,started_at" | Set-Content -Encoding UTF8 $pidFile

$name = "unitree_g1_stairs_forward_v1"
$task = "Unitree-G1-StairsForwardV1"
$outLog = Join-Path $logDir "unitree_g1_stairs_forward_v1.out.log"
$errLog = Join-Path $logDir "unitree_g1_stairs_forward_v1.err.log"
$runName = "$name`_$(Get-Date -Format yyyyMMdd_HHmmss)"
$resumeFrom = ""

$taskArgs = @(
  "-Task", $task,
  "-NumEnvs", [string]$NumEnvs,
  "-MaxIterations", [string]$Iterations,
  "-SaveInterval", [string]$SaveInterval,
  "-RunName", $runName
)

if (-not $NoResume -and (Test-Path $g1LogRoot)) {
  $sourceRun = Get-ChildItem -Path $g1LogRoot -Directory |
    Where-Object {
      $_.Name -match "_unitree_g1_stairs_forward_v1_" -or
      $_.Name -match "transfer_g1_fast_flat_to_stairs_step_clearance_seed" -or
      $_.Name -match "_seed_g1_forward_stairs_medium"
    } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

  if ($sourceRun) {
    $sourceCheckpoint = Get-ChildItem -Path $sourceRun.FullName -Filter "model_*.pt" |
      Sort-Object LastWriteTime -Descending |
      Select-Object -First 1

    if ($sourceCheckpoint) {
      $resumeFrom = "$($sourceRun.Name)\$($sourceCheckpoint.Name)"
      $taskArgs += @(
        "-Resume",
        "-LoadRun", $sourceRun.Name,
        "-LoadCheckpoint", $sourceCheckpoint.Name
      )
    }
  }
}

$process = Start-Process `
  -FilePath "powershell.exe" `
  -ArgumentList (@(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $trainScript
  ) + $taskArgs) `
  -WorkingDirectory $root `
  -RedirectStandardOutput $outLog `
  -RedirectStandardError $errLog `
  -WindowStyle Hidden `
  -PassThru

"$name,$($process.Id),$task,$NumEnvs,$Iterations,$resumeFrom,$outLog,$errLog,$(Get-Date -Format o)" |
  Add-Content -Encoding UTF8 $pidFile

Write-Host "Started G1 stairs-forward job. PID file: $pidFile"
if ($resumeFrom -ne "") {
  Write-Host "Resuming from checkpoint: $resumeFrom"
} else {
  Write-Host "Starting without resume checkpoint."
}
Get-Content $pidFile

