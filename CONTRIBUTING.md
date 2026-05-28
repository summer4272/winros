# Contributing

Thanks for helping improve WinROS. The project is meant to be useful for
beginners first, so clear setup notes, reproducible examples, and safe dry-run
interfaces are as valuable as new algorithms.

## Development Setup

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_conda_env.ps1 -Torch cpu
. .\scripts\activate_winros.ps1
python -m pytest
```

For a lighter install without RL extras:

```powershell
python -m pip install -e ".[dev,sim]"
```

## Pull Requests

- Keep checkpoints, datasets, vendor SDKs, and `third_party/` downloads out of Git.
- Prefer dry-run paths for new hardware work.
- Add or update tests for Python interfaces.
- Add docs when changing setup, dashboard profiles, ROS 2 messages, or safety behavior.

## High-value Contributions

- Beginner setup reports for Windows, CUDA, ROS 2, and MuJoCo.
- Dashboard profiles that make existing scripts easier to discover.
- Small simulation tasks that run quickly on a normal laptop.
- VLA providers that return structured commands without touching hardware.
- ROS 2 interface improvements with tests and safety notes.
- Demo validation notes when a trained policy or recording script changes.

## Hardware Contributions

Real robot adapters must start in dry-run mode, publish telemetry, enforce
limits, and reject hardware commands until the adapter has explicit enable logic.
