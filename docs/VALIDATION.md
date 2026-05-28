# Validation

This document records the public validation state for the repository.

Validation date: 2026-05-28

Latest local checks:

- `python -m pytest`: 10 passed, 4 skipped
- `python -m py_compile .\scripts\build_showcase_demo.py .\scripts\record_unitree_mjlab_demo.py`: passed
- `python -m json.tool .\docs\assets\demo\manifest.json`: passed

## Public Demo Assets

| Asset | Robot | Task | File | Provenance |
| --- | --- | --- | --- | --- |
| G1 fast run | Unitree G1 | FastRunV1 | `docs/assets/demo/g1_fast_run.mp4` | Trained-policy inference preview |
| Go2 fast run | Unitree Go2 | FastFlat | `docs/assets/demo/go2_fast_run.mp4` | Trained-policy inference preview |
| Go2 stairs | Unitree Go2 | StairsForwardV3 | `docs/assets/demo/go2_stairs.mp4` | Trained-policy inference preview |
| Showcase | WinROS dashboard demo | Combined preview | `docs/assets/demo/winros_showcase.webm` | `scripts/build_showcase_demo.py` |

Machine-readable metadata:

```text
docs/assets/demo/manifest.json
```

## Training Run References

The public repository records run identifiers only. Full checkpoints are not
distributed.

| Profile | External run identifier | Model file |
| --- | --- | --- |
| `g1_fast_run` | `g1_velocity/2026-05-27_20-30-43_unitree_g1_fast_run_v1_20260527_203014` | `model_22998.pt` |
| `go2_fast_run` | `go2_velocity/2026-05-27_00-46-23_unitree_go2_fast_flat_20260527_004601` | `model_11999.pt` |
| `go2_stairs` | `go2_velocity/2026-05-28_01-36-34_unitree_go2_stairs_forward_v3_20260528_013607` | `model_8999.pt` |

## Rebuilding the Demo

Place the external Unitree MJLab repository under:

```text
third_party/unitree_rl_mjlab
```

Then run:

```powershell
python .\scripts\record_unitree_mjlab_demo.py --profile all --steps 240
python .\scripts\build_showcase_demo.py
```

The first command records source videos from matching local checkpoints. The
second command rebuilds the public showcase video, poster, and manifest.

## Release Checks

```powershell
python -m pytest
python -m py_compile .\scripts\build_showcase_demo.py .\scripts\record_unitree_mjlab_demo.py
python -m json.tool .\docs\assets\demo\manifest.json
```

Manual checks:

- open `docs/demo/index.html` and confirm all videos load;
- open the dashboard and confirm profile metadata is visible;
- confirm `runs/`, `third_party/`, checkpoints, SDKs, datasets, secrets, and
  hardware credentials are not tracked by Git;
- confirm the README poster and demo links are valid.
