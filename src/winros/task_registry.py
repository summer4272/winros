from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from winros.config import paths


@dataclass(frozen=True)
class TaskDefinition:
    id: str
    title: str
    robot_family: str
    primary_robot: str
    primary_asset: str
    reference_assets: tuple[str, ...]
    initial_goal: str
    milestones: tuple[str, ...]


def _task_dir() -> Path:
    return paths().configs / "tasks"


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected a mapping in {path}")
    return data


def _load_task(path: Path) -> TaskDefinition:
    data = _load_yaml(path)
    return TaskDefinition(
        id=str(data["id"]),
        title=str(data["title"]),
        robot_family=str(data["robot_family"]),
        primary_robot=str(data["primary_robot"]),
        primary_asset=str(data["primary_asset"]),
        reference_assets=tuple(str(item) for item in data.get("reference_assets", [])),
        initial_goal=str(data["initial_goal"]),
        milestones=tuple(str(item) for item in data.get("milestones", [])),
    )


def list_tasks() -> list[TaskDefinition]:
    tasks = [_load_task(path) for path in sorted(_task_dir().glob("*.yaml"))]
    return sorted(tasks, key=lambda task: task.id)


def get_task(task_id: str) -> TaskDefinition:
    for task in list_tasks():
        if task.id == task_id:
            return task
    known = ", ".join(task.id for task in list_tasks())
    raise ValueError(f"Unknown task '{task_id}'. Known tasks: {known}")
