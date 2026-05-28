param(
    [switch]$Json
)

$ErrorActionPreference = "Continue"

function Test-Tool {
    param([string]$Name)

    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) {
        return [ordered]@{ name = $Name; found = $true; path = $cmd.Source }
    }
    return [ordered]@{ name = $Name; found = $false; path = $null }
}

function Invoke-Version {
    param(
        [string]$Command,
        [string[]]$Args
    )

    try {
        $out = & $Command @Args 2>&1 | Select-Object -First 1
        return "$out"
    } catch {
        return $null
    }
}

$tools = @()
foreach ($toolName in @("python", "git", "pixi", "colcon", "ros2", "nvidia-smi")) {
    $tools += (Test-Tool $toolName)
}

$pythonChecks = [ordered]@{}
if ((Get-Command python -ErrorAction SilentlyContinue)) {
    $pythonChecks.version = & python -c "import sys; print(sys.version.split()[0])" 2>$null
    $pythonChecks.imports = @{}
    foreach ($module in @("mujoco", "torch", "yaml", "numpy")) {
        $code = "import importlib.util; print(importlib.util.find_spec('$module') is not None)"
        $result = & python -c $code 2>$null
        $pythonChecks.imports[$module] = ($result -eq "True")
    }
    $cudaCode = "import importlib.util; s=importlib.util.find_spec('torch'); import torch if False else None"
    $null = $cudaCode
    $torchCuda = & python -c "import importlib.util; s=importlib.util.find_spec('torch'); print('missing' if s is None else __import__('torch').cuda.is_available())" 2>$null
    $pythonChecks.torch_cuda_available = "$torchCuda"
}

$report = [ordered]@{
    root = (Get-Location).Path
    tools = $tools
    python = $pythonChecks
}

if ($Json) {
    $report | ConvertTo-Json -Depth 5
} else {
    Write-Host "WinROS environment check"
    Write-Host "Root: $($report.root)"
    Write-Host ""
    foreach ($tool in $tools) {
        $mark = if ($tool.found) { "OK " } else { "MISS" }
        Write-Host ("[{0}] {1} {2}" -f $mark, $tool.name, $tool.path)
    }
    if ($pythonChecks.version) {
        Write-Host ""
        Write-Host "Python: $($pythonChecks.version)"
        foreach ($key in $pythonChecks.imports.Keys) {
            Write-Host ("  import {0}: {1}" -f $key, $pythonChecks.imports[$key])
        }
        Write-Host "  torch cuda available: $($pythonChecks.torch_cuda_available)"
    }
}
