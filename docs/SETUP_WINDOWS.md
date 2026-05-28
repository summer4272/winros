# Windows Setup

This project is designed for native Windows first, with optional WSL or container workflows later.

## Recommended Tracks

### Stable Track

- Windows 10 or Windows 11.
- ROS 2 Jazzy.
- MuJoCo Python package.
- Python 3.10 or newer for the main WinROS simulation, RL, and tooling environment.

### Experimental Track

- Windows 11.
- ROS 2 Lyrical prerelease binaries.
- Same Python and MuJoCo setup.

## ROS 2 Notes

Use a short install path for ROS 2 because Windows path length can become a problem. The Jazzy documentation currently uses `C:\pixi_ws` and notes that binary packages are not relocatable.

On this machine the working ROS 2 Windows track is:

- ROS 2 Jazzy Patch 3 (`release-jazzy-20241223`) at `C:\pixi_ws\ros2-windows`.
- Python 3.8.10 at `C:\Python38`, because the Patch 3 scripts and binary extensions target Python 3.8.
- Extra runtime DLL paths at `C:\pixi_ws\openssl11\Library\bin` and `C:\pixi_ws\ros2-deps\Library\bin`.
- MuJoCo `3.1.6` installed into `C:\Python38` for the ROS 2 bridge.

The newer Jazzy Patch 7 archive tested on 2026-05-25 failed to import `rclpy` on this Windows host with an `_rclpy_pybind11` DLL load error. It was kept aside as `C:\pixi_ws\ros2-windows-20260128-broken`; use Patch 3 until the upstream Windows binary issue is resolved locally.

Build the workspace:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_ros2_ws.ps1
```

Activate ROS 2 plus the WinROS workspace in each new PowerShell session:

```powershell
. .\scripts\activate_ros2_winros.ps1
ros2 pkg list | findstr winros
ros2 interface show winros_interfaces/msg/RobotTelemetry
```

Smoke-test the dry-run adapter:

```powershell
ros2 run winros_robot_adapters dry_run_adapter
```

In another activated terminal you should see `/winros_dry_run_adapter`, `/joint_command`, and `/telemetry`:

```powershell
ros2 node list
ros2 topic list
```

Smoke-test the MuJoCo bridge:

```powershell
ros2 run winros_mujoco mujoco_bridge --ros-args -p model_path:="$PWD\sim\mujoco\models\two_link_arm.xml"
```

In another activated terminal you should see `/winros_mujoco_bridge`, `/joint_states`, and `/telemetry`.

## Conda Setup

Recommended project-local environment:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_conda_env.ps1
. .\scripts\activate_winros.ps1
```

On an RTX 4060 Laptop GPU with an up-to-date driver, the default script installs CUDA PyTorch from the `cu128` wheel index. For CPU-only setup:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_conda_env.ps1 -Torch cpu
```

If Conda activation is not initialized in PowerShell, dot-source the local helper instead:

```powershell
. .\scripts\activate_winros.ps1
```

## Python venv Setup

Base simulation and development environment:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_python.ps1 -Profile dev -Torch none
```

CPU PyTorch:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_python.ps1 -Profile rl -Torch cpu
```

CUDA PyTorch:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_python.ps1 -Profile rl -Torch cu126
```

Check CUDA availability:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_env.ps1
```

## Low-VRAM Defaults

- Prefer CPU or small CUDA batches for first experiments.
- Use small MuJoCo models and short rollouts.
- Keep replay buffers on disk when possible.
- Avoid loading VLA model weights in the base process.
- Use dry-run command validation before real hardware.
