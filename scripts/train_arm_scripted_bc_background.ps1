param(
    [int]$Demos = 80,
    [int]$Epochs = 60,
    [int]$BatchSize = 1024,
    [int]$EvalEpisodes = 10,
    [string]$Device = "cuda",
    [string]$EnvPath = (Join-Path (Split-Path -Parent $PSScriptRoot) '.conda\winros')
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $EnvPath "python.exe"
$logDir = Join-Path $projectRoot "runs\arm_bc"
$pidFile = Join-Path $logDir "arm_scripted_bc_job.csv"
$outLog = Join-Path $logDir "arm_scripted_bc.out.log"
$errLog = Join-Path $logDir "arm_scripted_bc.err.log"

if (-not (Test-Path -LiteralPath $python)) {
    throw "WinROS Conda environment not found at $EnvPath. Run scripts\setup_conda_env.ps1 first."
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$process = Start-Process `
    -FilePath $python `
    -ArgumentList @(
        "-m", "winros.train_arm_scripted_bc",
        "--demos", "$Demos",
        "--epochs", "$Epochs",
        "--batch-size", "$BatchSize",
        "--eval-episodes", "$EvalEpisodes",
        "--device", "$Device",
        "--output-dir", "$logDir"
    ) `
    -WorkingDirectory $projectRoot `
    -RedirectStandardOutput $outLog `
    -RedirectStandardError $errLog `
    -WindowStyle Hidden `
    -PassThru

"name,pid,demos,epochs,batch_size,eval_episodes,device,out_log,err_log,started_at" |
    Set-Content -Encoding UTF8 $pidFile
"arm_scripted_bc,$($process.Id),$Demos,$Epochs,$BatchSize,$EvalEpisodes,$Device,$outLog,$errLog,$(Get-Date -Format o)" |
    Add-Content -Encoding UTF8 $pidFile

Write-Host "Started arm scripted BC training. PID file: $pidFile"
Get-Content $pidFile

