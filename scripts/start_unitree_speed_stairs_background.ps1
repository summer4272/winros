param(
  [int]$Go2FastNumEnvs = 512,
  [int]$Go2FastIterations = 8000,
  [int]$Go2StairsNumEnvs = 384,
  [int]$Go2StairsIterations = 10000,
  [int]$G1FastNumEnvs = 256,
  [int]$G1FastIterations = 12000,
  [int]$SaveInterval = 100
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $root "runs\unitree_speed_stairs"
$pidFile = Join-Path $logDir "unitree_speed_stairs_jobs.csv"
$trainScript = Join-Path $root "scripts\train_unitree_mjlab_velocity_task_gpu.ps1"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null
"name,pid,task,num_envs,iterations,out_log,err_log,started_at" | Set-Content -Encoding UTF8 $pidFile

$jobs = @(
  @{
    Name = "unitree_go2_fast_flat"
    Task = "Unitree-Go2-FastFlat"
    NumEnvs = $Go2FastNumEnvs
    Iterations = $Go2FastIterations
  },
  @{
    Name = "unitree_go2_stairs"
    Task = "Unitree-Go2-Stairs"
    NumEnvs = $Go2StairsNumEnvs
    Iterations = $Go2StairsIterations
  },
  @{
    Name = "unitree_g1_fast_flat"
    Task = "Unitree-G1-FastFlat"
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

Write-Host "Started Unitree speed/stairs jobs. PID file: $pidFile"
Get-Content $pidFile

