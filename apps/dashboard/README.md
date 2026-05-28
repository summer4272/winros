# Dashboard

The WinROS dashboard is served by the Python package:

```powershell
python -m winros --dashboard
```

It exposes safe local profiles for setup checks, MuJoCo simulation, RL smoke
tests, VLA dry-run command generation, ROS 2 workspace builds, and research
training launchers. User preferences are saved to `configs/dashboard.local.yaml`,
which is ignored by Git.

The dashboard does not bypass hardware gates. Real robots should still be
connected through ROS 2 adapters that start in dry-run mode.
