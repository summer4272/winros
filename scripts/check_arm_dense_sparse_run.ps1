$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $root "runs\overnight\arm_dense_sparse_job.csv"

if (-not (Test-Path $pidFile)) {
  throw "No arm dense-to-sparse job file found: $pidFile"
}

$job = Import-Csv $pidFile | Select-Object -First 1
$process = Get-Process -Id ([int]$job.pid) -ErrorAction SilentlyContinue

Write-Host "=== $($job.name) ==="
if ($process) {
  Write-Host "status: running pid=$($job.pid)"
} else {
  Write-Host "status: finished or stopped pid=$($job.pid)"
}

if (Test-Path $job.out_log) {
  Write-Host "--- latest stdout ---"
  Get-Content $job.out_log -Tail 60
}
if ((Test-Path $job.err_log) -and ((Get-Item $job.err_log).Length -gt 0)) {
  Write-Host "--- latest stderr ---"
  Get-Content $job.err_log -Tail 60
}

