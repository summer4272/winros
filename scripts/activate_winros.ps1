param(
    [string]$EnvPath = (Join-Path (Split-Path -Parent $PSScriptRoot) '.conda\winros')
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath (Join-Path $EnvPath "python.exe"))) {
    throw "WinROS environment not found at $EnvPath. Run scripts\setup_conda_env.ps1 first."
}

$env:CONDA_PREFIX = $EnvPath
$env:PATH = "$EnvPath;$EnvPath\Scripts;$EnvPath\Library\bin;$env:PATH"

Write-Host "WinROS environment active in this PowerShell session."
python --version


