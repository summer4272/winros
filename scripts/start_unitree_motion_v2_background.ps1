param(
  [int]$Go2StairsNumEnvs = 320,
  [int]$Go2StairsIterations = 12000,
  [int]$G1FastNumEnvs = 256,
  [int]$G1FastIterations = 14000,
  [int]$SaveInterval = 100
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $root "runs\unitree_motion_v2"
$pidFile = Join-Path $logDir "unitree_motion_v2_jobs.csv"
$trainScript = Join-Path $root "scripts\train_unitree_mjlab_velocity_task_gpu.ps1"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null
"name,pid,task,num_envs,iterations,out_log,err_log,started_at" | Set-Content -Encoding UTF8 $pidFile

$jobs = @(
  @{
    Name = "unitree_go2_stairs_v2"
    Task = "Unitree-Go2-StairsV2"
    NumEnvs = $Go2StairsNumEnvs
    Iterations = $Go2StairsIterations
  },
  @{
    Name = "unitree_g1_fast_flat_v2"
    Task = "Unitree-G1-FastFlatV2"
    NumEnvs = $G1FastNumEnvs
    Iterations = $G1FastIterations
  }
)

foreach ($job in $jobs) {
  $outLog = Join-Path $logDir "$($job.Name).out.log"
  $errLog = Join-Path $logDir "$($job.Name).err.log"
  $runName = "$($job.Name)_$(Get-Date -Format yyyyMMdd_HHmmss)"

  $process = Start-Process `
    -FilePath "powershell.exe" `
    -ArgumentList @(
      "-NoProfile",
      "-ExecutionPolicy", "Bypass",
      "-File", $trainScript,
      "-Task", $job.Task,
      "-NumEnvs", [string]$job.NumEnvs,
      "-MaxIterations", [string]$job.Iterations,
      "-SaveInterval", [string]$SaveInterval,
      "-RunName", $runName
    ) `
    -WorkingDirectory $root `
    -RedirectStandardOutput $outLog `
    -RedirectStandardError $errLog `
    -WindowStyle Hidden `
    -PassThru

  "$($job.Name),$($process.Id),$($job.Task),$($job.NumEnvs),$($job.Iterations),$outLog,$errLog,$(Get-Date -Format o)" |
    Add-Content -Encoding UTF8 $pidFile
}

Write-Host "Started Unitree motion V2 jobs. PID file: $pidFile"
Get-Content $pidFile

