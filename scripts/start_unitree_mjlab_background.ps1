param(
  [int]$Go2NumEnvs = 512,
  [int]$Go2Iterations = 3000,
  [int]$G1NumEnvs = 256,
  [int]$G1Iterations = 5000
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $root "runs\unitree_mjlab"
$pidFile = Join-Path $logDir "unitree_mjlab_jobs.csv"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null
"name,pid,task,num_envs,iterations,out_log,err_log,started_at" | Set-Content -Encoding UTF8 $pidFile

$jobs = @(
  @{
    Name = "unitree_go2_flat"
    Task = "Unitree-Go2-Flat"
    Script = Join-Path $root "scripts\train_unitree_mjlab_go2_gpu.ps1"
    NumEnvs = $Go2NumEnvs
    Iterations = $Go2Iterations
  },
  @{
    Name = "unitree_g1_flat"
    Task = "Unitree-G1-Flat"
    Script = Join-Path $root "scripts\train_unitree_mjlab_g1_gpu.ps1"
    NumEnvs = $G1NumEnvs
    Iterations = $G1Iterations
  }
)

foreach ($job in $jobs) {
  $outLog = Join-Path $logDir "$($job.Name).out.log"
  $errLog = Join-Path $logDir "$($job.Name).err.log"
  $process = Start-Process `
    -FilePath "powershell.exe" `
    -ArgumentList @(
      "-NoProfile",
      "-ExecutionPolicy", "Bypass",
      "-File", $job.Script,
      "-NumEnvs", [string]$job.NumEnvs,
      "-MaxIterations", [string]$job.Iterations
    ) `
    -WorkingDirectory $root `
    -RedirectStandardOutput $outLog `
    -RedirectStandardError $errLog `
    -WindowStyle Hidden `
    -PassThru

  "$($job.Name),$($process.Id),$($job.Task),$($job.NumEnvs),$($job.Iterations),$outLog,$errLog,$(Get-Date -Format o)" |
    Add-Content -Encoding UTF8 $pidFile
}

Write-Host "Started Unitree MJLab jobs. PID file: $pidFile"
Get-Content $pidFile

