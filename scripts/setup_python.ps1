param(
    [ValidateSet("none", "cpu", "cu118", "cu126", "cu128")]
    [string]$Torch = "none",

    [ValidateSet("base", "dev", "rl", "vla")]
    [string]$Profile = "dev",

    [string]$Venv = ".venv"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python was not found on PATH. Install Python 3.10 or newer first."
}

if (-not (Test-Path -LiteralPath $Venv)) {
    python -m venv $Venv
}

$python = Join-Path $Venv "Scripts\python.exe"
& $python -m pip install --upgrade pip
& $python -m pip install -r "requirements\$Profile.txt"

switch ($Torch) {
    "none" { Write-Host "Skipping PyTorch install." }
    "cpu" { & $python -m pip install torch torchvision torchaudio }
    "cu118" { & $python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 }
    "cu126" { & $python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126 }
    "cu128" { & $python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128 }
}

Write-Host "Python environment ready: $Venv"

