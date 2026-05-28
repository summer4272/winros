$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $root "runs\unitree_mjlab"
$pidFile = Join-Path $logDir "unitree_mjlab_jobs.csv"

if (-not (Test-Path $pidFile)) {
  throw "No Unitree MJLab job file found: $pidFile"
}

$jobs = Import-Csv $pidFile
foreach ($job in $jobs) {
  Write-Host ""
  Write-Host "=== $($job.name) / $($job.task) ==="
  $process = Get-Process -Id ([int]$job.pid) -ErrorAction SilentlyContinue
  if ($process) {
    Write-Host "status: running pid=$($job.pid)"
  } else {
    Write-Host "status: finished or stopped pid=$($job.pid)"
  }

  if (Test-Path $job.out_log) {
    Write-Host "--- latest stdout ---"
    Get-Content $job.out_log -Tail 80
  }
  if ((Test-Path $job.err_log) -and ((Get-Item $job.err_log).Length -gt 0)) {
    Write-Host "--- latest stderr ---"
    Get-Content $job.err_log -Tail 80
  }
}

