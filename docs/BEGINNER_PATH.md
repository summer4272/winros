# Beginner Path

This page provides a suggested first-run sequence for new WinROS users.

## Step 1: View the Demo

Open the static demo page:

```text
docs/demo/index.html
```

The page shows three trained-policy previews:

- Unitree G1 fast running;
- Unitree Go2 fast running;
- Unitree Go2 stair climbing.

## Step 2: Open the Dashboard

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_conda_env.ps1
. .\scripts\activate_winros.ps1
python -m winros --dashboard
```

Open the local URL printed by the command, usually:

```text
http://127.0.0.1:8765
```

The dashboard exposes environment checks, simulations, RL smoke tests, VLA
dry-run profiles, ROS 2 build profiles, and research scripts.

## Step 3: Run a Minimal Simulation

```powershell
python -m winros --list-robots
python -m winros --robot two_link_arm --steps 1000
```

This verifies the basic Python, MuJoCo, and WinROS CLI path.

## Step 4: Run a VLA Dry-Run Command

```powershell
python -m winros --vla-provider rules --vla-robot "Unitree Go2" --vla-instruction "walk forward slowly"
```

The command returns a structured robot command without controlling hardware.
This keeps language-conditioned control behind a validation boundary.

## Step 5: Build the ROS 2 Workspace

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_ros2_ws.ps1
. .\scripts\activate_ros2_winros.ps1
ros2 pkg list | findstr winros
```

The workspace contains WinROS interface, bridge, and adapter packages.

## Contribution Paths

- Setup and documentation fixes for first-time Windows users.
- Dashboard profile improvements.
- Small simulation tasks and smoke tests.
- Reproducible RL baselines and evaluation scripts.
- ROS 2 interface and bridge improvements.
- Dry-run-first hardware adapters with documented safety limits.
