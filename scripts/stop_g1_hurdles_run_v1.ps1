param()

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $root "runs\g1_hurdles_run_v1\g1_hurdles_run_v1_jobs.csv"

function Stop-ProcessTree {
  param([int]$TargetPid)

  $children = Get-CimInstance Win32_Process |
    Where-Object { $_.ParentProcessId -eq $TargetPid }

  foreach ($child in $children) {
    Stop-ProcessTree -TargetPid ([int]$child.ProcessId)
  }

  $proc = Get-Process -Id $TargetPid -ErrorAction SilentlyContinue
  if ($proc) {
    Write-Host "Stopping PID $TargetPid ($($proc.ProcessName))"
    Stop-Process -Id $TargetPid -Force
  }
}

if (-not (Test-Path $pidFile)) {
  Write-Host "No G1 hurdles-run PID file found: $pidFile"
  return
}

$job = Import-Csv $pidFile | Select-Object -Last 1
if (-not $job -or -not $job.pid) {
  Write-Host "No job entry found in $pidFile"
  return
}

$pidValue = [int]$job.pid
$proc = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
if (-not $proc) {
  Write-Host "G1 hurdles-run is already stopped or finished, pid=$pidValue"
  return
}

Write-Host "Stopping G1 hurdles-run process tree from pid=$pidValue"
Stop-ProcessTree -TargetPid $pidValue
Write-Host "Done."

