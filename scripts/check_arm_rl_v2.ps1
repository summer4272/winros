$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $root "runs\arm_rl_v2\arm_rl_v2_job.csv"

if (-not (Test-Path $pidFile)) {
    throw "No ArmRL-v2 job file found: $pidFile"
}

$job = Import-Csv $pidFile | Select-Object -First 1
Write-Host "=== $($job.name) ==="
$process = Get-Process -Id ([int]$job.pid) -ErrorAction SilentlyContinue
if ($process) {
    Write-Host "status: running pid=$($job.pid)"
} else {
    Write-Host "status: finished or stopped pid=$($job.pid)"
}

if (Test-Path $job.out_log) {
    Write-Host "--- latest stdout ---"
    Get-Content $job.out_log -Tail 140
}
if ((Test-Path $job.err_log) -and ((Get-Item $job.err_log).Length -gt 0)) {
    Write-Host "--- latest stderr ---"
    Get-Content $job.err_log -Tail 120
}

Write-Host "--- latest ArmRL-v2 model/checkpoints ---"
Get-ChildItem -Path (Join-Path $root "runs\sb3") -Recurse -Include "*ArmRLV2*.zip" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 12 FullName,Length,LastWriteTime |
    Format-Table -AutoSize

