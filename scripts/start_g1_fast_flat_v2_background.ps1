param(
  [int]$NumEnvs = 256,
  [int]$Iterations = 14000,
  [int]$SaveInterval = 100
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $root "runs\g1_fast_flat_v2"
$pidFile = Join-Path $logDir "g1_fast_flat_v2_jobs.csv"
$trainScript = Join-Path $root "scripts\train_unitree_mjlab_velocity_task_gpu.ps1"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null
"name,pid,task,num_envs,iterations,out_log,err_log,started_at" | Set-Content -Encoding UTF8 $pidFile

$name = "unitree_g1_fast_flat_v2"
$task = "Unitree-G1-FastFlatV2"
$outLog = Join-Path $logDir "$name.out.log"
$errLog = Join-Path $logDir "$name.err.log"
$runName = "$name`_$(Get-Date -Format yyyyMMdd_HHmmss)"

$process = Start-Process `
  -FilePath "powershell.exe" `
  -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $trainScript,
    "-Task", $task,
    "-NumEnvs", [string]$NumEnvs,
    "-MaxIterations", [string]$Iterations,
    "-SaveInterval", [string]$SaveInterval,
    "-RunName", $runName
  ) `
  -WorkingDirectory $root `
  -RedirectStandardOutput $outLog `
  -RedirectStandardError $errLog `
  -WindowStyle Hidden `
  -PassThru

"$name,$($process.Id),$task,$NumEnvs,$Iterations,$outLog,$errLog,$(Get-Date -Format o)" |
  Add-Content -Encoding UTF8 $pidFile

Write-Host "Started G1 fast-flat V2 job. PID file: $pidFile"
Get-Content $pidFile

