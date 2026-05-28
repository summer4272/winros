# Open-source baselines

WinROS keeps third-party research environments under `third_party/` so the
platform pipeline can be validated before we replace pieces with our own
research code.

## Franka Panda Pick-and-Place

- Source: `https://github.com/zichunxx/panda_mujoco_gym`
- Local path: `third_party/panda_mujoco_gym`
- License: MIT
- Env IDs:
  - `FrankaPickAndPlaceSparse-v0`
  - `FrankaPickAndPlaceDense-v0`
  - `FrankaPushSparse-v0`
  - `FrankaPushDense-v0`
  - `FrankaSlideSparse-v0`
  - `FrankaSlideDense-v0`

These environments use GoalEnv-style dictionary observations:
`observation`, `achieved_goal`, and `desired_goal`. In WinROS, SAC switches to
`MultiInputPolicy` and HER replay automatically for these envs.

## Locomotion baselines

- Quadruped pipeline baseline: `Ant-v5`
- Humanoid pipeline baseline: `Humanoid-v5`
- Source documentation: `https://gymnasium.farama.org/environments/mujoco/`
- License: Gymnasium/MuJoCo assets and code are third-party open-source
  dependencies.

These two environments are not Unitree-specific robot models. They are used as
stable overnight baselines to prove the WinROS locomotion training, logging,
model saving, and playback path. The next Unitree-specific target is:

- `https://github.com/unitreerobotics/unitree_rl_mjlab`

`unitree_rl_mjlab` supports MuJoCo-based Unitree Go2 and G1 training/playback,
and is the preferred next integration once the WinROS baseline pipeline is
validated.

## Unitree MJLab integration

- Source: `https://github.com/unitreerobotics/unitree_rl_mjlab`
- Local path: `third_party/unitree_rl_mjlab`
- License: Apache-2.0
- Quadruped task: `Unitree-Go2-Flat`
- Humanoid task: `Unitree-G1-Flat`
- Algorithm stack: MJLab + MuJoCo Warp + RSL-RL PPO

This is the higher-quality locomotion path. Compared with SB3 `Ant-v5` and
`Humanoid-v5`, it uses actual Unitree robot models, parallel GPU simulation,
privileged critic observations, domain randomization, push perturbations,
velocity-command curriculum, and exports ONNX policies for deployment.

Validated local dependency pins:

- `mujoco==3.5.0`
- `mujoco-warp==3.5.0`
- `warp-lang==1.12.0`
- `mjlab==1.2.0`
- `scipy`

The official setup metadata currently does not pin every compatible dependency
tightly enough on Windows; `mujoco==3.8.1` and `warp-lang==1.13.0` failed local
smoke tests, so WinROS pins the versions above for MJLab.
