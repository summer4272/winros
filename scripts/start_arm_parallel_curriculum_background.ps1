param(
  [int]$ReachSteps = 200000,
  [int]$LiftSteps = 400000,
  [int]$PlaceSteps = 600000,
  [int]$NumEnvs = 8,
  [int]$BatchSize = 1024,
  [string]$VecEnv = "dummy"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $root "runs\arm_parallel"
$pidFile = Join-Path $logDir "arm_parallel_curriculum_job.csv"
$script = Join-Path $root "scripts\train_arm_curriculum_gpu.ps1"
$outLog = Join-Path $logDir "arm_parallel_curriculum.out.log"
$errLog = Join-Path $logDir "arm_parallel_curriculum.err.log"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$process = Start-Process `
  -FilePath "powershell.exe" `
  -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $script,
    "-ReachSteps", [string]$ReachSteps,
    "-LiftSteps", [string]$LiftSteps,
    "-PlaceSteps", [string]$PlaceSteps,
    "-Algo", "ppo",
    "-NumEnvs", [string]$NumEnvs,
    "-VecEnv", $VecEnv,
    "-BatchSize", [string]$BatchSize,
    "-Device", "cpu"
  ) `
  -WorkingDirectory $root `
  -RedirectStandardOutput $outLog `
  -RedirectStandardError $errLog `
  -WindowStyle Hidden `
  -PassThru

"name,pid,algo,num_envs,vec_env,reach_steps,lift_steps,place_steps,out_log,err_log,started_at" |
  Set-Content -Encoding UTF8 $pidFile
"arm_parallel_curriculum,$($process.Id),ppo,$NumEnvs,$VecEnv,$ReachSteps,$LiftSteps,$PlaceSteps,$outLog,$errLog,$(Get-Date -Format o)" |
  Add-Content -Encoding UTF8 $pidFile

Write-Host "Started arm parallel curriculum job. PID file: $pidFile"
Get-Content $pidFile

