# Dashboard

The dashboard is a local operator console for beginners and researchers. It is
served from the Python package and does not need Node.js:

```powershell
python -m winros --dashboard
```

Open the printed local URL, usually `http://127.0.0.1:8765`.

## Profiles

Profiles are command templates exposed to the UI. The built-in profiles cover:

- environment checks;
- MuJoCo built-in simulations;
- short RL rollouts and smoke training;
- VLA dry-run command generation;
- ROS 2 workspace builds;
- dry-run robot adapter launch;
- longer Unitree research runs.

The backend launches only known profiles. Hardware mode is intentionally locked
until a concrete adapter implements its own checks.

## Customization

Dashboard defaults live in `configs/dashboard.yaml`. Local preferences and
private lab commands can be placed in `configs/dashboard.local.yaml`; this file
is ignored by Git.

Example local profile:

```yaml
custom_profiles:
  - id: lab_status
    title: Lab Status
    group: Custom
    mode: dry_run
    summary: Show local lab status.
    command:
      - powershell.exe
      - -ExecutionPolicy
      - Bypass
      - -File
      - scripts/check_env.ps1
```

Prefer keeping hardware commands out of custom profiles until the adapter has
watchdogs, limit checks, and a visible dry-run state.
