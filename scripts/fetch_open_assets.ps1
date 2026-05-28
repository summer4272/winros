param(
    [string]$Root = "",
    [switch]$IncludeReferences
)

$ErrorActionPreference = "Stop"

if (-not $Root) {
    $Root = Split-Path -Parent $PSScriptRoot
}

$thirdParty = Join-Path $Root "third_party"
New-Item -ItemType Directory -Force -Path $thirdParty | Out-Null

function Invoke-Git {
    param([string[]]$GitArgs)

    & git @GitArgs
    if ($LASTEXITCODE -ne 0) {
        throw "git $($GitArgs -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Ensure-Repo {
    param(
        [string]$Name,
        [string]$Url,
        [string[]]$SparsePaths = @()
    )

    $destination = Join-Path $thirdParty $Name
    if (Test-Path -LiteralPath (Join-Path $destination ".git")) {
        Write-Host "Updating $Name..."
        Invoke-Git -GitArgs @("-C", $destination, "pull", "--ff-only")
        if ($SparsePaths.Count -gt 0) {
            Invoke-Git -GitArgs (@("-C", $destination, "sparse-checkout", "set") + $SparsePaths)
        }
        return
    }

    Write-Host "Cloning $Name..."
    if ($SparsePaths.Count -gt 0) {
        Invoke-Git -GitArgs @(
            "clone",
            "--filter=blob:none",
            "--sparse",
            $Url,
            $destination
        )
        Invoke-Git -GitArgs (@("-C", $destination, "sparse-checkout", "set") + $SparsePaths)
    } else {
        Invoke-Git -GitArgs @("clone", $Url, $destination)
    }
}

Ensure-Repo `
    -Name "mujoco_menagerie" `
    -Url "https://github.com/google-deepmind/mujoco_menagerie.git" `
    -SparsePaths @(
        "franka_emika_panda",
        "unitree_go2",
        "unitree_g1",
        "unitree_h1",
        "robotiq_2f85"
    )

if ($IncludeReferences) {
    Ensure-Repo -Name "unitree_mujoco" -Url "https://github.com/unitreerobotics/unitree_mujoco.git"
    Ensure-Repo -Name "mujoco_playground" -Url "https://github.com/google-deepmind/mujoco_playground.git"
    Ensure-Repo -Name "panda_mujoco_gym" -Url "https://github.com/zichunxx/panda_mujoco_gym.git"
}

Write-Host "Open-source assets are available under $thirdParty"
Write-Host "Next: python -m winros --check-assets"
