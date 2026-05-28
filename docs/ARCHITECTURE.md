# Architecture

WinROS is split into four layers so each part can evolve without forcing the rest of the system to change.

## 1. Robot Interface Layer

This is the contract every simulated or real robot should satisfy.

- state: joint state, pose, velocity, sensors, health, warnings;
- commands: joint targets, base velocity, mode changes, task actions;
- safety: dry-run flag, mode gating, timeout, limits, e-stop integration;
- timing: source timestamp and publish rate are part of telemetry.

ROS 2 messages live in `ros2_ws/src/winros_interfaces`.

## 2. Simulation Layer

MuJoCo owns fast local dynamics and visual simulation.

- `sim/mujoco/models` contains small MJCF models.
- `src/winros/mujoco_runner.py` can load and step models without ROS.
- `ros2_ws/src/winros_mujoco` bridges simulation state into ROS 2.

Keep models small at first. A stable two-link arm and differential-drive base are better than a beautiful but fragile full humanoid.

## 3. Learning Layer

The learning layer should treat simulators and robots through the same robot interface.

- CPU-friendly RL first: PPO/SAC only after the observation/action contract is stable.
- VLA is optional and should start as an adapter that produces structured robot commands.
- Large model weights, datasets, and checkpoints stay outside Git by default.

## 4. Operator Layer

The operator layer is for humans.

- dashboard for telemetry, logs, plans, and commands;
- bag replay and comparison;
- explicit visual indicators for sim, dry-run, and hardware-enabled modes.

This layer should not bypass safety gates. It calls the same interfaces as scripts and agents.

The first implementation is the local dashboard served by `python -m winros --dashboard`.
It exposes command profiles from a whitelist and stores private UI preferences in
`configs/dashboard.local.yaml`.

## 5. VLA Adapter Layer

VLA providers convert language or vision-language input into structured robot
commands. The base repository includes a deterministic `rules` provider for
interface tests. Future providers can use local models or remote APIs, but their
outputs should still pass command validation before simulation or hardware.
