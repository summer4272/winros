$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $root "runs\fetch_pickplace_rl"
$pidFile = Join-Path $logDir "fetch_pickplace_rl_job.csv"
$outLog = Join-Path $logDir "fetch_pickplace_rl.out.log"
$errLog = Join-Path $logDir "fetch_pickplace_rl.err.log"

if (-not (Test-Path -LiteralPath $pidFile)) {
    Write-Host "No Fetch pick-place RL job file found at $pidFile"
    exit 0
}

$job = Import-Csv $pidFile | Select-Object -Last 1
$proc = Get-Process -Id ([int]$job.pid) -ErrorAction SilentlyContinue

Write-Host "=== fetch_pickplace_rl ==="
if ($proc) {
    Write-Host "status: running pid=$($job.pid)"
} else {
    Write-Host "status: finished or stopped pid=$($job.pid)"
}

if (Test-Path -LiteralPath $outLog) {
    Write-Host "--- latest stdout ---"
    Get-Content -Path $outLog -Tail 100
}

if (Test-Path -LiteralPath $errLog) {
    $err = Get-Content -Path $errLog -Tail 40
    if ($err) {
        Write-Host "--- latest stderr ---"
        $err
    }
}

