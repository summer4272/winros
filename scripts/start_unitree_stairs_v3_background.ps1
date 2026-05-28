param(
  [int]$NumEnvs = 320,
  [int]$Iterations = 14000,
  [int]$SaveInterval = 100,
  [switch]$NoResume
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $root "runs\unitree_stairs_v3"
$pidFile = Join-Path $logDir "unitree_stairs_v3_jobs.csv"
$trainScript = Join-Path $root "scripts\train_unitree_mjlab_velocity_task_gpu.ps1"
$go2LogRoot = Join-Path $root "third_party\unitree_rl_mjlab\logs\rsl_rl\go2_velocity"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null
"name,pid,task,num_envs,iterations,resume_from,out_log,err_log,started_at" | Set-Content -Encoding UTF8 $pidFile

$name = "unitree_go2_stairs_forward_v3"
$task = "Unitree-Go2-StairsForwardV3"
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

if (-not $NoResume -and (Test-Path $go2LogRoot)) {
  $sourceRun = Get-ChildItem -Path $go2LogRoot -Directory |
    Where-Object { $_.Name -match "_unitree_go2_stairs_forward_v3_" -or $_.Name -match "_seed_go2_forward_stairs_visible" } |
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

Write-Host "Started Go2 stairs-forward V3 job. PID file: $pidFile"
if ($resumeFrom -ne "") {
  Write-Host "Resuming from checkpoint: $resumeFrom"
} else {
  Write-Host "Starting without resume checkpoint."
}
Get-Content $pidFile

