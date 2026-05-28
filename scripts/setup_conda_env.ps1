param(
    [string]$EnvPath = (Join-Path (Split-Path -Parent $PSScriptRoot) '.conda\winros'),

    [ValidateSet("3.10", "3.11", "3.12")]
    [string]$PythonVersion = "3.11",

    [ValidateSet("none", "cpu", "cu126", "cu128")]
    [string]$Torch = "cu128"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    throw "conda was not found on PATH. Install Anaconda or Miniconda first."
}

if (-not (Test-Path -LiteralPath (Join-Path $EnvPath "python.exe"))) {
    conda create --prefix $EnvPath "python=$PythonVersion" pip -y
}

$python = Join-Path $EnvPath "python.exe"
& $python -m pip install --upgrade pip

switch ($Torch) {
    "none" {
        Write-Host "Skipping PyTorch install."
    }
    "cpu" {
        & $python -m pip install torch torchvision torchaudio
    }
    "cu126" {
        & $python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
    }
    "cu128" {
        & $python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
    }
}

Push-Location $projectRoot
try {
    & $python -m pip install -e ".[dev,sim,rl]"
    & $python -m pytest
    & $python -m winros --robot two_link_arm --steps 100
} finally {
    Pop-Location
}

Write-Host "WinROS Conda environment ready: $EnvPath"


