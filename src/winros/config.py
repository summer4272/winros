from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    sim_models: Path
    configs: Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def paths() -> ProjectPaths:
    root = project_root()
    return ProjectPaths(
        root=root,
        sim_models=root / "sim" / "mujoco" / "models",
        configs=root / "configs",
    )

