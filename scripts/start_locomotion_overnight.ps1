param(
  [int]$AntTimesteps = 1500000,
  [int]$HumanoidTimesteps = 3000000,
  [int]$BatchSize = 1024
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $root "runs\overnight"
$pidFile = Join-Path $logDir "locomotion_jobs.csv"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null
"name,pid,timesteps,out_log,err_log,started_at" | Set-Content -Encoding UTF8 $pidFile

$jobs = @(
  @{
    Name = "quadruped_ant"
    Script = Join-Path $root "scripts\train_quadruped_ant_gpu.ps1"
    Timesteps = $AntTimesteps
  },
  @{
    Name = "humanoid_mujoco"
    Script = Join-Path $root "scripts\train_humanoid_mujoco_gpu.ps1"
    Timesteps = $HumanoidTimesteps
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
      "-Timesteps", [string]$job.Timesteps,
      "-BatchSize", [string]$BatchSize
    ) `
    -WorkingDirectory $root `
    -RedirectStandardOutput $outLog `
    -RedirectStandardError $errLog `
    -WindowStyle Hidden `
    -PassThru

  "$($job.Name),$($process.Id),$($job.Timesteps),$outLog,$errLog,$(Get-Date -Format o)" |
    Add-Content -Encoding UTF8 $pidFile
}

Write-Host "Started locomotion overnight jobs. PID file: $pidFile"
Get-Content $pidFile

