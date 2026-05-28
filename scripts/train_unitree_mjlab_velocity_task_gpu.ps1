param(
  [Parameter(Mandatory = $true)]
  [string]$Task,
  [int]$NumEnvs = 512,
  [int]$MaxIterations = 8000,
  [int]$SaveInterval = 100,
  [string]$RunName = "",
  [switch]$Resume,
  [string]$LoadRun = "",
  [string]$LoadCheckpoint = ""
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$repo = Join-Path $root "third_party\unitree_rl_mjlab"
$python = Join-Path $root ".conda\winros\python.exe"

Set-Location $repo

$argsList = @(
  "scripts\train.py",
  $Task,
  "--env.scene.num-envs=$NumEnvs",
  "--agent.max-iterations=$MaxIterations",
  "--agent.save-interval=$SaveInterval",
  "--agent.logger=tensorboard"
)

if ($RunName -ne "") {
  $argsList += "--agent.run-name=$RunName"
}

if ($Resume) {
  $argsList += "--agent.resume=True"
}

if ($LoadRun -ne "") {
  $argsList += "--agent.load-run=$LoadRun"
}

if ($LoadCheckpoint -ne "") {
  $argsList += "--agent.load-checkpoint=$LoadCheckpoint"
}

& $python @argsList

