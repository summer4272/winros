param(
  [switch]$Go2,
  [switch]$G1
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot

if (-not $Go2 -and -not $G1) {
  $Go2 = $true
  $G1 = $true
}

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

function Stop-JobFromCsv {
  param(
    [string]$Name,
    [string]$CsvPath
  )

  if (-not (Test-Path $CsvPath)) {
    Write-Host "${Name}: no PID file found: $CsvPath"
    return
  }

  $job = Import-Csv $CsvPath | Select-Object -Last 1
  if (-not $job -or -not $job.pid) {
    Write-Host "${Name}: no job entry found in $CsvPath"
    return
  }

  $pidValue = [int]$job.pid
  $proc = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
  if (-not $proc) {
    Write-Host "${Name}: already stopped or finished, pid=$pidValue"
    return
  }

  Write-Host "${Name}: stopping process tree from pid=$pidValue"
  Stop-ProcessTree -TargetPid $pidValue
}

if ($Go2) {
  Stop-JobFromCsv `
    -Name "Go2 stairs V3" `
    -CsvPath (Join-Path $root "runs\unitree_stairs_v3\unitree_stairs_v3_jobs.csv")
}

if ($G1) {
  Stop-JobFromCsv `
    -Name "G1 stairs V1" `
    -CsvPath (Join-Path $root "runs\g1_stairs_forward\g1_stairs_forward_jobs.csv")
}

Write-Host "Done. G1 fast-flat training is not touched by this script."

