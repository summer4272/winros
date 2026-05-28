from __future__ import annotations

from dataclasses import dataclass, field
from time import time


@dataclass(frozen=True)
class JointStateSnapshot:
    names: tuple[str, ...]
    position: tuple[float, ...]
    velocity: tuple[float, ...]
    effort: tuple[float, ...] = ()


@dataclass(frozen=True)
class RobotTelemetry:
    robot_name: str
    source: str
    mode: str
    joint_state: JointStateSnapshot
    timestamp: float = field(default_factory=time)
    warnings: tuple[str, ...] = ()

