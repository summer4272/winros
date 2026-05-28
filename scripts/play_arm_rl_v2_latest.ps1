param(
    [ValidateSet("WinROSArmRLV2Reach-v0", "WinROSArmRLV2Lift-v0", "WinROSArmRLV2Place-v0")]
    [string]$Env = "WinROSArmRLV2Place-v0",
    [string]$Model = "",
    [int]$Episodes = 5,
    [int]$Steps = 340,
    [string]$Device = "cuda"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".conda\winros\python.exe"

if ($Model -eq "") {
    $latest = Get-ChildItem -Path (Join-Path $root "runs\sb3") -Recurse -Filter "$($Env)_ppo*.zip" |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if (-not $latest) {
        throw "No model found for $Env under $(Join-Path $root 'runs\sb3')"
    }
    $Model = $latest.FullName
}

Push-Location $root
try {
    & $python -m winros `
        --env $Env `
        --play-model $Model `
        --algo ppo `
        --episodes $Episodes `
        --steps $Steps `
        --render-env `
        --device $Device
} finally {
    Pop-Location
}

