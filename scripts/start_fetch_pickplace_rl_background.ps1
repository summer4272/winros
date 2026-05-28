param(
    [int]$Timesteps = 300000,
    [int]$BatchSize = 256,
    [int]$GradientSteps = 1,
    [string]$EnvId = "FetchPickAndPlace-v4",
    [string]$Device = "cuda",
    [string]$EnvPath = (Join-Path (Split-Path -Parent $PSScriptRoot) '.conda\winros')
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $EnvPath "python.exe"
$logDir = Join-Path $projectRoot "runs\fetch_pickplace_rl"
$pidFile = Join-Path $logDir "fetch_pickplace_rl_job.csv"
$outLog = Join-Path $logDir "fetch_pickplace_rl.out.log"
$errLog = Join-Path $logDir "fetch_pickplace_rl.err.log"

if (-not (Test-Path -LiteralPath $python)) {
    throw "WinROS Conda environment not found at $EnvPath. Run scripts\setup_conda_env.ps1 first."
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$process = Start-Process `
    -FilePath $python `
    -ArgumentList @(
        "-m", "winros",
        "--train-env", "$EnvId",
        "--algo", "sac",
        "--timesteps", "$Timesteps",
        "--device", "$Device",
        "--batch-size", "$BatchSize",
        "--gradient-steps", "$GradientSteps"
    ) `
    -WorkingDirectory $projectRoot `
    -RedirectStandardOutput $outLog `
    -RedirectStandardError $errLog `
    -WindowStyle Hidden `
    -PassThru

"name,pid,env,algo,timesteps,batch_size,gradient_steps,device,out_log,err_log,started_at" |
    Set-Content -Encoding UTF8 $pidFile
"fetch_pickplace_rl,$($process.Id),$EnvId,sac,$Timesteps,$BatchSize,$GradientSteps,$Device,$outLog,$errLog,$(Get-Date -Format o)" |
    Add-Content -Encoding UTF8 $pidFile

Write-Host "Started Fetch pick-place RL job. PID file: $pidFile"
Get-Content $pidFile

