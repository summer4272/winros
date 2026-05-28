param(
    [int]$ReachSteps = 300000,
    [int]$LiftSteps = 900000,
    [int]$PlaceSteps = 1500000,
    [int]$NumEnvs = 12,
    [int]$BatchSize = 2048,
    [string]$Device = "cuda",
    [string]$VecEnv = "dummy"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $root "runs\arm_rl_v2"
$pidFile = Join-Path $logDir "arm_rl_v2_job.csv"
$script = Join-Path $root "scripts\train_arm_rl_v2_curriculum_gpu.ps1"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$outLog = Join-Path $logDir "arm_rl_v2.out.log"
$errLog = Join-Path $logDir "arm_rl_v2.err.log"

$process = Start-Process `
    -FilePath "powershell.exe" `
    -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $script,
        "-ReachSteps", [string]$ReachSteps,
        "-LiftSteps", [string]$LiftSteps,
        "-PlaceSteps", [string]$PlaceSteps,
        "-NumEnvs", [string]$NumEnvs,
        "-BatchSize", [string]$BatchSize,
        "-Device", $Device,
        "-VecEnv", $VecEnv
    ) `
    -WorkingDirectory $root `
    -RedirectStandardOutput $outLog `
    -RedirectStandardError $errLog `
    -WindowStyle Hidden `
    -PassThru

"name,pid,algo,num_envs,vec_env,reach_steps,lift_steps,place_steps,device,out_log,err_log,started_at" |
    Set-Content -Encoding UTF8 $pidFile
"arm_rl_v2,$($process.Id),ppo,$NumEnvs,$VecEnv,$ReachSteps,$LiftSteps,$PlaceSteps,$Device,$outLog,$errLog,$(Get-Date -Format o)" |
    Add-Content -Encoding UTF8 $pidFile

Write-Host "Started ArmRL-v2 curriculum job. PID file: $pidFile"
Get-Content $pidFile

