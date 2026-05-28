from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import sleep

import numpy as np

from winros.rl.random_policy import StatefulRandomPolicy


@dataclass(frozen=True)
class TrainingPreviewSummary:
    model_path: Path
    episodes: int
    steps_per_episode: int
    final_time: float
    last_episode_reward: float


def _load_mujoco():
    try:
        import mujoco
    except ImportError as exc:
        raise RuntimeError("MuJoCo is not installed in the active Python environment.") from exc
    return mujoco


def run_training_preview(
    model_path: str | Path,
    *,
    episodes: int = 3,
    steps_per_episode: int = 1000,
    action_repeat: int = 20,
    action_scale: float = 0.15,
    realtime: bool = True,
    seed: int | None = 7,
) -> TrainingPreviewSummary:
    mujoco = _load_mujoco()
    import mujoco.viewer

    path = Path(model_path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)

    model = mujoco.MjModel.from_xml_path(str(path))
    data = mujoco.MjData(model)
    policy = StatefulRandomPolicy(action_dim=int(model.nu), low=-1.0, high=1.0, seed=seed)
    action = np.zeros(int(model.nu), dtype=float)
    last_episode_reward = 0.0

    print(
        f"Training preview started: model={path}, episodes={episodes}, "
        f"steps_per_episode={steps_per_episode}, nu={model.nu}",
        flush=True,
    )

    with mujoco.viewer.launch_passive(model, data) as handle:
        for episode in range(1, episodes + 1):
            mujoco.mj_resetData(model, data)
            episode_reward = 0.0

            for step in range(steps_per_episode):
                if model.nu and step % action_repeat == 0:
                    action = policy.sample()

                _apply_action(model, data, action, action_scale=action_scale)
                mujoco.mj_step(model, data)
                reward = _proxy_reward(model, data)
                episode_reward += reward

                if step % 100 == 0:
                    print(
                        f"episode={episode} step={step} "
                        f"time={data.time:.3f}s reward={episode_reward:.3f}",
                        flush=True,
                    )

                handle.sync()
                if realtime:
                    sleep(float(model.opt.timestep))

            last_episode_reward = float(episode_reward)
            print(f"episode={episode} done total_reward={episode_reward:.3f}", flush=True)

    return TrainingPreviewSummary(
        model_path=path,
        episodes=episodes,
        steps_per_episode=steps_per_episode,
        final_time=float(data.time),
        last_episode_reward=last_episode_reward,
    )


def _apply_action(model, data, action: np.ndarray, *, action_scale: float) -> None:
    if data.ctrl.size == 0:
        return

    for index in range(data.ctrl.size):
        raw = float(action[index])
        if bool(model.actuator_ctrllimited[index]):
            low, high = model.actuator_ctrlrange[index]
            center = 0.5 * (float(low) + float(high))
            half_span = 0.5 * (float(high) - float(low))
            data.ctrl[index] = center + raw * half_span * action_scale
        else:
            data.ctrl[index] = raw * action_scale


def _proxy_reward(model, data) -> float:
    survival = 0.01
    velocity_penalty = 0.001 * float(np.dot(data.qvel, data.qvel))
    control_penalty = 0.0005 * float(np.dot(data.ctrl, data.ctrl)) if model.nu else 0.0
    return survival - velocity_penalty - control_penalty
