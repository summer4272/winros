# Roadmap

## Phase 0: Foundation

- Repository structure, license, and setup scripts.
- Windows environment checker.
- Minimal MuJoCo model runner.
- ROS 2 interface package.
- Dry-run hardware adapter skeleton.

## Phase 1: Local Simulation

- Arm demo with joint command and telemetry.
- Differential-drive demo with velocity command.
- ROS 2 bridge for MuJoCo state.
- Record and replay telemetry.

## Phase 2: Planning and Control

- MoveIt 2 integration notes for arm planning.
- Nav2-compatible interface notes for wheeled robots.
- Controller abstraction for position, velocity, and torque control.
- Safety limits in config files.

## Phase 3: Learning

- Gymnasium-style wrapper around simulated robots.
- Random policy, then PPO baseline.
- Checkpoint and experiment logging.
- Low-VRAM training presets.

## Phase 4: VLA

- VLA adapter interface: image/text/task in, structured robot command out.
- Local small-model path and remote-provider path.
- Command validation before execution.
- Dataset schema for demonstrations.
- Dashboard profile for dry-run VLA command generation.

## Phase 5: Real Robots

- Vendor-neutral hardware adapter contract.
- First vendor adapter.
- E-stop and watchdog integration.
- Dashboard hardware mode controls.

## Phase 6: Open Source Polish

- GitHub Actions.
- Contribution guide.
- Issue templates.
- Versioned examples and docs.
- Chinese quickstart and beginner dashboard workflow.

## Phase 7: Community Evidence

- Keep the README focused on the problem WinROS solves, not only on features.
- Maintain demo videos, manifests, and validation notes for each public release.
- Add small, beginner-friendly tasks for dashboard, docs, simulation, VLA, and ROS 2.
- Publish reproducibility notes for every major trained-policy showcase.
- Separate public learning assets from private checkpoints, SDKs, and real-robot credentials.
