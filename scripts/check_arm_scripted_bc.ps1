$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $root "runs\arm_bc"
$pidFile = Join-Path $logDir "arm_scripted_bc_job.csv"
$outLog = Join-Path $logDir "arm_scripted_bc.out.log"
$errLog = Join-Path $logDir "arm_scripted_bc.err.log"
$metrics = Join-Path $logDir "arm_scripted_bc_metrics.json"

if (-not (Test-Path -LiteralPath $pidFile)) {
    Write-Host "No arm scripted BC job file found at $pidFile"
    exit 0
}

$job = Import-Csv $pidFile | Select-Object -Last 1
$proc = Get-Process -Id ([int]$job.pid) -ErrorAction SilentlyContinue

Write-Host "=== arm_scripted_bc ==="
if ($proc) {
    Write-Host "status: running pid=$($job.pid)"
} else {
    Write-Host "status: finished or stopped pid=$($job.pid)"
}

if (Test-Path -LiteralPath $metrics) {
    Write-Host "--- metrics ---"
    Get-Content -Path $metrics
}

if (Test-Path -LiteralPath $outLog) {
    Write-Host "--- latest stdout ---"
    Get-Content -Path $outLog -Tail 80
}

if (Test-Path -LiteralPath $errLog) {
    $err = Get-Content -Path $errLog -Tail 40
    if ($err) {
        Write-Host "--- latest stderr ---"
        $err
    }
}

