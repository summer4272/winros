$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $root "runs\g1_stairs_forward"
$pidFile = Join-Path $logDir "g1_stairs_forward_jobs.csv"

if (-not (Test-Path $pidFile)) {
  Write-Host "No G1 stairs-forward PID file found at $pidFile"
  exit 0
}

$jobs = Import-Csv $pidFile
foreach ($job in $jobs) {
  if ($job.name -eq "name") { continue }
  $proc = Get-Process -Id ([int]$job.pid) -ErrorAction SilentlyContinue
  $status = if ($proc) { "running pid=$($job.pid)" } else { "finished or stopped pid=$($job.pid)" }
  Write-Host ""
  Write-Host "=== $($job.name) / $($job.task) ==="
  Write-Host "status: $status"
  if (Test-Path $job.out_log) {
    Write-Host "--- latest stdout ---"
    Get-Content $job.out_log -Tail 120
  }
  if (Test-Path $job.err_log) {
    $err = Get-Content $job.err_log -Tail 40
    if ($err) {
      Write-Host "--- latest stderr ---"
      $err
    }
  }
}

