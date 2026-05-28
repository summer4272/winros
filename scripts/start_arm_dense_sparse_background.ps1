param(
  [int]$DenseTimesteps = 1000000,
  [int]$SparseTimesteps = 1000000,
  [int]$BatchSize = 1024,
  [int]$GradientSteps = 4
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $root "runs\overnight"
$pidFile = Join-Path $logDir "arm_dense_sparse_job.csv"
$script = Join-Path $root "scripts\train_external_panda_dense_then_sparse_gpu.ps1"
$outLog = Join-Path $logDir "arm_dense_sparse.out.log"
$errLog = Join-Path $logDir "arm_dense_sparse.err.log"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$process = Start-Process `
  -FilePath "powershell.exe" `
  -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $script,
    "-DenseTimesteps", [string]$DenseTimesteps,
    "-SparseTimesteps", [string]$SparseTimesteps,
    "-BatchSize", [string]$BatchSize,
    "-GradientSteps", [string]$GradientSteps
  ) `
  -WorkingDirectory $root `
  -RedirectStandardOutput $outLog `
  -RedirectStandardError $errLog `
  -WindowStyle Hidden `
  -PassThru

"name,pid,dense_timesteps,sparse_timesteps,out_log,err_log,started_at" |
  Set-Content -Encoding UTF8 $pidFile
"arm_dense_sparse,$($process.Id),$DenseTimesteps,$SparseTimesteps,$outLog,$errLog,$(Get-Date -Format o)" |
  Add-Content -Encoding UTF8 $pidFile

Write-Host "Started arm dense-to-sparse job. PID file: $pidFile"
Get-Content $pidFile

