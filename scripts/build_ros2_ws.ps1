param(
    [string]$WorkspaceRoot = "",
    [string]$Ros2Root = "C:\pixi_ws\ros2-windows",
    [string]$PythonExe = "C:\Python38\python.exe",
    [string]$VsDevCmd = "",
    [string]$CMakeExe = "",
    [string]$WindowsSdkBin = "",
    [string]$OpenSsl11Bin = "C:\pixi_ws\openssl11\Library\bin",
    [string]$Ros2DepsBin = "C:\pixi_ws\ros2-deps\Library\bin",
    [string]$TempRoot = "C:\tmp\winros-build",
    [switch]$NoClean,
    [switch]$SkipPythonPackages
)

$ErrorActionPreference = "Stop"

function Convert-ToCMakePath {
    param([string]$Path)
    return ($Path -replace "\\", "/")
}

function Resolve-FirstExistingPath {
    param(
        [string[]]$Candidates,
        [string]$Description
    )

    foreach ($candidate in $Candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    throw "Could not find $Description. Pass it explicitly to scripts\build_ros2_ws.ps1."
}

function Assert-PathInside {
    param(
        [string]$Child,
        [string]$Parent
    )

    $childFull = [System.IO.Path]::GetFullPath($Child)
    $parentFull = [System.IO.Path]::GetFullPath($Parent).TrimEnd("\") + "\"
    if (-not $childFull.StartsWith($parentFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to clean path outside expected build directory: $childFull"
    }
}

$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (-not $WorkspaceRoot) {
    $WorkspaceRoot = Join-Path $ProjectRoot "ros2_ws"
}

$InstallPrefix = Join-Path $WorkspaceRoot "install"
$InterfaceSrc = Join-Path $WorkspaceRoot "src\winros_interfaces"
$InterfaceBuild = Join-Path $WorkspaceRoot "build\winros_interfaces"

if (-not (Test-Path -LiteralPath (Join-Path $Ros2Root "setup.bat"))) {
    throw "ROS 2 setup.bat was not found at $Ros2Root."
}
if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw "Python executable was not found at $PythonExe."
}
if (-not (Test-Path -LiteralPath $InterfaceSrc)) {
    throw "winros_interfaces source package was not found at $InterfaceSrc."
}

if (-not $VsDevCmd) {
    $vsCandidates = @(
        "L:\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat",
        "${env:ProgramFiles}\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"
    )
    $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path -LiteralPath $vswhere) {
        $installPath = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
        if ($installPath) {
            $vsCandidates = @((Join-Path $installPath "Common7\Tools\VsDevCmd.bat")) + $vsCandidates
        }
    }
    $VsDevCmd = Resolve-FirstExistingPath -Candidates $vsCandidates -Description "Visual Studio VsDevCmd.bat"
}

if (-not $CMakeExe) {
    $cmakeCmd = Get-Command cmake -ErrorAction SilentlyContinue
    if ($cmakeCmd) {
        $CMakeExe = $cmakeCmd.Source
    } else {
        $CMakeExe = Resolve-FirstExistingPath -Candidates @(
            "L:\Cmake\bin\cmake.exe",
            "${env:ProgramFiles}\CMake\bin\cmake.exe",
            "${env:ProgramFiles(x86)}\CMake\bin\cmake.exe"
        ) -Description "cmake.exe"
    }
}

if (-not $WindowsSdkBin) {
    $sdkBase = "${env:ProgramFiles(x86)}\Windows Kits\10\bin"
    $sdkCandidates = @("C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64")
    if (Test-Path -LiteralPath $sdkBase) {
        $sdkCandidates += Get-ChildItem -LiteralPath $sdkBase -Directory |
            Sort-Object Name -Descending |
            ForEach-Object { Join-Path $_.FullName "x64" }
    }
    $WindowsSdkBin = Resolve-FirstExistingPath -Candidates $sdkCandidates -Description "Windows SDK x64 bin directory"
}

New-Item -ItemType Directory -Force -Path $TempRoot | Out-Null

if (-not $NoClean -and (Test-Path -LiteralPath $InterfaceBuild)) {
    Assert-PathInside -Child $InterfaceBuild -Parent (Join-Path $WorkspaceRoot "build")
    Remove-Item -LiteralPath $InterfaceBuild -Recurse -Force
}

$pythonDir = Split-Path -Parent $PythonExe
$pythonScripts = Join-Path $pythonDir "Scripts"
$cmakeBin = Split-Path -Parent $CMakeExe
$cmdFile = Join-Path $TempRoot "build_winros_interfaces.cmd"
$installPrefixCMake = Convert-ToCMakePath $InstallPrefix
$pythonCMake = Convert-ToCMakePath $PythonExe

@"
@echo off
setlocal EnableDelayedExpansion
call "$VsDevCmd" -arch=x64
if errorlevel 1 exit /b !errorlevel!
set TEMP=$TempRoot
set TMP=$TempRoot
set PATH=$WindowsSdkBin;$OpenSsl11Bin;$Ros2DepsBin;$pythonScripts;$pythonDir;$cmakeBin;%PATH%
call "$Ros2Root\setup.bat"
if errorlevel 1 exit /b !errorlevel!
"$CMakeExe" -S "$InterfaceSrc" -B "$InterfaceBuild" -G "NMake Makefiles" -DCMAKE_INSTALL_PREFIX=$installPrefixCMake -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=cl -DCMAKE_CXX_COMPILER=cl -DPython3_EXECUTABLE=$pythonCMake -DPython_EXECUTABLE=$pythonCMake -DPYTHON_EXECUTABLE=$pythonCMake
if errorlevel 1 exit /b !errorlevel!
"$CMakeExe" --build "$InterfaceBuild" --target install
if errorlevel 1 exit /b !errorlevel!
endlocal
"@ | Set-Content -LiteralPath $cmdFile -Encoding ASCII

Write-Host "Building winros_interfaces with CMake/NMake..."
& cmd.exe /c $cmdFile
if ($LASTEXITCODE -ne 0) {
    throw "winros_interfaces build failed with exit code $LASTEXITCODE."
}

if (-not $SkipPythonPackages) {
    Write-Host "Installing ROS 2 Python packages with ROS-compatible script layout..."
    $oldPath = $env:PATH
    $oldPythonPath = $env:PYTHONPATH
    try {
        $env:PATH = "$OpenSsl11Bin;$Ros2DepsBin;$pythonScripts;$pythonDir;$env:PATH"
        $env:PYTHONPATH = "$InstallPrefix\Lib\site-packages;$oldPythonPath"

        foreach ($packageName in @("winros_mujoco", "winros_robot_adapters")) {
            $packagePath = Join-Path $WorkspaceRoot "src\$packageName"
            if (-not (Test-Path -LiteralPath (Join-Path $packagePath "setup.py"))) {
                throw "setup.py was not found for $packageName at $packagePath."
            }

            Push-Location $packagePath
            try {
                & $PythonExe setup.py install --prefix $InstallPrefix
                if ($LASTEXITCODE -ne 0) {
                    throw "$packageName install failed with exit code $LASTEXITCODE."
                }
            } finally {
                Pop-Location
            }
        }
    } finally {
        $env:PATH = $oldPath
        $env:PYTHONPATH = $oldPythonPath
    }
}

Write-Host "ROS 2 workspace installed at $InstallPrefix"
Write-Host "Next: dot-source scripts\activate_ros2_winros.ps1 in a new PowerShell session."
