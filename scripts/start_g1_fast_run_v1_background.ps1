param(
  [int]$NumEnvs = 256,
  [int]$Iterations = 9000,
  [int]$SaveInterval = 100,
  [switch]$NoResume
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $root "runs\g1_fast_run_v1"
$pidFile = Join-Path $logDir "g1_fast_run_v1_jobs.csv"
$trainScript = Join-Path $root "scripts\train_unitree_mjlab_velocity_task_gpu.ps1"
$g1LogRoot = Join-Path $root "third_party\unitree_rl_mjlab\logs\rsl_rl\g1_velocity"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null
"name,pid,task,num_envs,iterations,resume_from,out_log,err_log,started_at" | Set-Content -Encoding UTF8 $pidFile

$name = "unitree_g1_fast_run_v1"
$task = "Unitree-G1-FastRunV1"
$outLog = Join-Path $logDir "$name.out.log"
$errLog = Join-Path $logDir "$name.err.log"
$runName = "$name`_$(Get-Date -Format yyyyMMdd_HHmmss)"
$resumeFrom = ""

$taskArgs = @(
  "-Task", $task,
  "-NumEnvs", [string]$NumEnvs,
  "-MaxIterations", [string]$Iterations,
  "-SaveInterval", [string]$SaveInterval,
  "-RunName", $runName
)

if (-not $NoResume) {
  $sourceRun = Get-ChildItem -Path $g1LogRoot -Directory |
    Where-Object { $_.Name -match "_unitree_g1_fast_flat_v2_" } |
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

Write-Host "Started G1 fast-run V1 job. PID file: $pidFile"
if ($resumeFrom -ne "") {
  Write-Host "Resuming from FastFlatV2 checkpoint: $resumeFrom"
} else {
  Write-Host "Starting without resume checkpoint."
}
Get-Content $pidFile

