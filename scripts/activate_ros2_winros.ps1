param(
    [string]$ProjectRoot = "",
    [string]$Ros2Root = "C:\pixi_ws\ros2-windows",
    [string]$PythonRoot = "C:\Python38",
    [string]$OpenSsl11Bin = "C:\pixi_ws\openssl11\Library\bin",
    [string]$Ros2DepsBin = "C:\pixi_ws\ros2-deps\Library\bin",
    [string]$RmwImplementation = "rmw_fastrtps_cpp"
)

$ErrorActionPreference = "Stop"

function Add-PathEntries {
    param([string[]]$Entries)

    $existing = @($env:PATH -split ";" | Where-Object { $_ })
    $prefix = @($Entries | Where-Object { $_ -and (Test-Path -LiteralPath $_) })
    $env:PATH = (@($prefix + $existing) | Select-Object -Unique) -join ";"
}

function Prepend-EnvList {
    param(
        [string]$Name,
        [string[]]$Entries
    )

    $current = [Environment]::GetEnvironmentVariable($Name, "Process")
    $existing = @($current -split ";" | Where-Object { $_ })
    $prefix = @($Entries | Where-Object { $_ })
    [Environment]::SetEnvironmentVariable($Name, ((@($prefix + $existing) | Select-Object -Unique) -join ";"), "Process")
}

function Import-CmdEnvironment {
    param([string]$Command)

    $lines = & cmd.exe /v:on /c "$Command && set"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to import environment from: $Command"
    }

    foreach ($line in $lines) {
        if ($line -match "^([^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

if (-not $ProjectRoot) {
    $ProjectRoot = Split-Path -Parent $PSScriptRoot
}

$setupBat = Join-Path $Ros2Root "setup.bat"
$workspaceInstall = Join-Path $ProjectRoot "ros2_ws\install"

if (-not (Test-Path -LiteralPath $setupBat)) {
    throw "ROS 2 setup.bat was not found at $setupBat."
}
if (-not (Test-Path -LiteralPath $workspaceInstall)) {
    throw "WinROS ROS 2 install directory was not found at $workspaceInstall. Run scripts\build_ros2_ws.ps1 first."
}

Add-PathEntries @(
    $OpenSsl11Bin,
    $Ros2DepsBin,
    (Join-Path $PythonRoot "Scripts"),
    $PythonRoot
)

Import-CmdEnvironment "call `"$setupBat`" >nul 2>nul"

Add-PathEntries @(
    (Join-Path $workspaceInstall "bin"),
    (Join-Path $workspaceInstall "Scripts"),
    (Join-Path $workspaceInstall "lib\winros_mujoco"),
    (Join-Path $workspaceInstall "lib\winros_robot_adapters")
)

Prepend-EnvList "AMENT_PREFIX_PATH" @($workspaceInstall)
Prepend-EnvList "CMAKE_PREFIX_PATH" @($workspaceInstall)
Prepend-EnvList "PYTHONPATH" @((Join-Path $workspaceInstall "Lib\site-packages"))
$env:RMW_IMPLEMENTATION = $RmwImplementation

Write-Host "ROS 2 + WinROS workspace active in this PowerShell session."
Write-Host "Try: ros2 pkg list | findstr winros"
