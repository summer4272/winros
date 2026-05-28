# WinROS Task Tracks

The first public roadmap is organized around three task tracks. Each track shares the same principle: use open simulation assets, keep training code and reward design in WinROS, and only touch hardware through explicit adapters.

## 1. Mechanical Arm Grasping

Primary robot: Franka Emika Panda.

Initial task: cube pick-and-place on a tabletop. Start with state observations, then add camera and VLA goal conditioning later.

First policy baseline: HER with SAC or TQC. The innovation area is staged skill design, visual goal grounding, and a safety filter that converts policy output into bounded robot commands.

Hardware path: read-only telemetry first, then dry-run command validation, then low-speed joint or end-effector command tests.

## 2. Quadruped Locomotion

Primary robot: Unitree Go2.

Initial task: commanded planar velocity tracking on flat ground. Add turning, rough terrain, perturbations, and recovery after the baseline is stable.

First policy baseline: PPO with domain randomization. The innovation area is command-conditioned gait selection, terrain-aware reward shaping, and hardware-aware latency randomization.

Hardware path: map WinROS joint commands to Unitree low-level command schema in dry-run mode before enabling any real motor path.

## 3. Humanoid Locomotion

Primary robot: Unitree G1. Unitree H1 stays as a fallback/comparison model.

Initial task: stable standing and balance recovery, then slow commanded walking.

First policy baseline: PPO with staged stand-to-walk curriculum. The innovation area is recovery skill selection, action smoothing, and fall prediction before command publish.

Hardware path: read-only low-level state, simulated DDS domain separated from real robot domain, explicit e-stop requirement before any hardware command path.

## Shared Interfaces

All tracks should use the same ROS2 surface first:

- `winros_interfaces/msg/JointCommand`
- `winros_interfaces/msg/RobotTelemetry`
- `winros_interfaces/action/MoveJoints`

Track-specific adapters can translate this platform contract to vendor SDKs later.

## Realtime Visualization

Before formal training is connected, use the preview runner to verify that MuJoCo rendering, episode stepping, and live reward logging work:

```powershell
python -m winros --asset franka_panda_menagerie --preview-training --episodes 3 --steps 1000
python -m winros --asset unitree_go2_menagerie --preview-training --episodes 3 --steps 1000 --action-scale 0.05
python -m winros --asset unitree_g1_menagerie --preview-training --episodes 1 --steps 1000 --action-scale 0.03
```

This preview currently uses a random policy as a placeholder. The formal SAC/PPO training loops should reuse the same visualization path.

## Gymnasium Environments

The first trainable environment IDs are:

- `WinROSArmGrasp-v0`
- `WinROSQuadrupedLocomotion-v0`
- `WinROSHumanoidLocomotion-v0`

Smoke-test them without rendering:

```powershell
python -m winros --env WinROSArmGrasp-v0 --episodes 1 --steps 300
python -m winros --env WinROSQuadrupedLocomotion-v0 --episodes 1 --steps 300
python -m winros --env WinROSHumanoidLocomotion-v0 --episodes 1 --steps 300
```

Add `--render-env` to watch the rollout in MuJoCo.

Run a tiny Stable-Baselines3 smoke training job:

```powershell
python -m winros --train-env WinROSArmGrasp-v0 --algo sac --timesteps 128 --device cuda
```

Checkpoints are written under `runs/sb3/`, which is ignored by Git.

Watch a saved policy:

```powershell
python -m winros --env WinROSArmGrasp-v0 --play-model .\runs\sb3\WinROSArmGrasp-v0_sac_128_steps.zip --algo sac --episodes 1 --steps 300 --render-env --device cuda
```

To watch training progress directly, enable periodic rendering:

```powershell
python -m winros --train-env WinROSArmGrasp-v0 --algo sac --timesteps 20000 --device cuda --render-train --render-train-freq 5000 --render-train-steps 300
```
