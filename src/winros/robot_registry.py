from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from winros.config import paths


@dataclass(frozen=True)
class RobotDefinition:
    name: str
    kind: str
    model_path: Path
    notes: str


def _root_relative(path: str) -> Path:
    return paths().root / path


BUILTIN_ROBOTS: dict[str, RobotDefinition] = {
    "two_link_arm": RobotDefinition(
        name="two_link_arm",
        kind="arm",
        model_path=_root_relative("sim/mujoco/models/two_link_arm.xml"),
        notes="Small 2-DOF arm for joint-control and RL smoke tests.",
    ),
    "differential_drive": RobotDefinition(
        name="differential_drive",
        kind="wheeled",
        model_path=_root_relative("sim/mujoco/models/differential_drive.xml"),
        notes="Simple differential-drive base for local mobility experiments.",
    ),
}


def list_robots() -> list[RobotDefinition]:
    return [BUILTIN_ROBOTS[name] for name in sorted(BUILTIN_ROBOTS)]


def resolve_model(robot: str | None = None, model: str | None = None) -> Path:
    if model:
        candidate = Path(model)
        if not candidate.is_absolute():
            candidate = paths().root / candidate
        return candidate

    if robot is None:
        robot = "two_link_arm"

    try:
        return BUILTIN_ROBOTS[robot].model_path
    except KeyError as exc:
        known = ", ".join(sorted(BUILTIN_ROBOTS))
        raise ValueError(f"Unknown robot '{robot}'. Known robots: {known}") from exc

