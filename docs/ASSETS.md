# Open-Source Simulation Assets

WinROS keeps third-party robot assets out of the Git history by default. The repository stores manifests, task bindings, and fetch scripts; downloaded assets live under `third_party/`, which is ignored by Git.

## Primary Choices

| Track | Primary asset | Source | License | Why |
| --- | --- | --- | --- | --- |
| Arm grasping | Franka Emika Panda | MuJoCo Menagerie | Apache-2.0 | Common benchmark arm, mature MJCF, easy to extend into tabletop grasping. |
| Quadruped locomotion | Unitree Go2 | MuJoCo Menagerie | BSD-3-Clause | Practical target for sim-to-real, 12-DoF model, Unitree ecosystem has deployment references. |
| Humanoid locomotion | Unitree G1 | MuJoCo Menagerie | BSD-3-Clause | Current humanoid target with available MJCF and Unitree low-level deployment references. |

## Reference Repositories

- `google-deepmind/mujoco_menagerie`: curated MuJoCo models. Use this as the first model source.
- `unitreerobotics/unitree_mujoco`: Unitree simulator and low-level DDS message reference for Go2, H1, and G1-style deployment.
- `google-deepmind/mujoco_playground`: reference structure for GPU-accelerated RL and sim-to-real task design.
- `zichunxx/panda_mujoco_gym`: MIT-licensed reference for Franka push, slide, and pick-and-place tasks.

## Local Layout

Expected local paths after fetching:

```text
third_party/
|-- mujoco_menagerie/
|   |-- franka_emika_panda/scene.xml
|   |-- unitree_go2/scene.xml
|   |-- unitree_g1/scene.xml
|   `-- unitree_h1/scene.xml
|-- unitree_mujoco/
|-- mujoco_playground/
`-- panda_mujoco_gym/
```

Check local availability:

```powershell
python -m winros --check-assets
```

Run a downloaded model:

```powershell
python -m winros --asset franka_panda_menagerie --steps 100
python -m winros --asset unitree_go2_menagerie --steps 100
python -m winros --asset unitree_g1_menagerie --steps 100
```

Fetch the external repositories:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\fetch_open_assets.ps1
```

Use `-IncludeReferences` if you also want the larger reference repositories:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\fetch_open_assets.ps1 -IncludeReferences
```
