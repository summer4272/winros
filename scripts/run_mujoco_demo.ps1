param(
    [string]$Robot = "two_link_arm",
    [int]$Steps = 1000,
    [string]$EnvPath = (Join-Path (Split-Path -Parent $PSScriptRoot) '.conda\winros'),
    [switch]$Viewer
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonCandidates = @(
    (Join-Path $EnvPath "python.exe"),
    (Join-Path $projectRoot ".venv\Scripts\python.exe")
)

foreach ($candidate in $pythonCandidates) {
    if (Test-Path -LiteralPath $candidate) {
        $python = $candidate
        break
    }
}

if (-not $python) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $python = $pythonCommand.Source
    }
}

if (-not $python) {
    throw "No Python environment found. Run scripts\setup_conda_env.ps1 or scripts\setup_python.ps1 first."
}

$args = @("-m", "winros", "--robot", $Robot, "--steps", "$Steps")
if ($Viewer) {
    $args += "--viewer"
}

Push-Location $projectRoot
try {
    & $python @args
} finally {
    Pop-Location
}

