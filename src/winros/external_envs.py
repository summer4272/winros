from __future__ import annotations

import sys
from pathlib import Path

from winros.config import paths

PANDA_MUJOCO_GYM_ENV_IDS = (
    "FrankaSlideSparse-v0",
    "FrankaSlideDense-v0",
    "FrankaPushSparse-v0",
    "FrankaPushDense-v0",
    "FrankaPickAndPlaceSparse-v0",
    "FrankaPickAndPlaceDense-v0",
)

LOCOMOTION_BASELINE_ENV_IDS = (
    "Ant-v5",
    "Humanoid-v5",
)

FETCH_ROBOTICS_ENV_IDS = (
    "FetchPickAndPlace-v4",
    "FetchPickAndPlaceDense-v4",
)


def register_external_envs() -> list[str]:
    """Register optional third-party Gymnasium envs kept under third_party."""
    env_ids: list[str] = []
    _ensure_panda_mujoco_gym_path()
    try:
        import panda_mujoco_gym
    except ImportError:
        pass
    else:
        env_ids.extend(getattr(panda_mujoco_gym, "ENV_IDS", PANDA_MUJOCO_GYM_ENV_IDS))

    try:
        import gymnasium_robotics  # noqa: F401
    except ImportError:
        pass
    env_ids.extend(_available_gymnasium_envs(LOCOMOTION_BASELINE_ENV_IDS))
    env_ids.extend(_available_gymnasium_envs(("FetchPickAndPlace-v4",)))
    env_ids.append("FetchPickAndPlaceDense-v4")
    return env_ids


def _available_gymnasium_envs(env_ids: tuple[str, ...]) -> list[str]:
    try:
        import gymnasium as gym
    except ImportError:
        return []

    available: list[str] = []
    for env_id in env_ids:
        try:
            gym.spec(env_id)
        except Exception:
            continue
        available.append(env_id)
    return available


def _ensure_panda_mujoco_gym_path() -> None:
    repo_path = paths().root / "third_party" / "panda_mujoco_gym"
    if repo_path.exists():
        _prepend_sys_path(repo_path)


def _prepend_sys_path(path: Path) -> None:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
