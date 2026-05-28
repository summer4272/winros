from __future__ import annotations

from dataclasses import dataclass
from time import sleep

import gymnasium as gym
import numpy as np

import winros.envs  # noqa: F401


@dataclass(frozen=True)
class RolloutSummary:
    env_id: str
    steps: int
    episodes: int
    total_reward: float


def run_random_rollout(
    env_id: str,
    *,
    steps: int = 300,
    episodes: int = 1,
    render: bool = False,
    realtime: bool = False,
    seed: int | None = 7,
) -> RolloutSummary:
    render_mode = "human" if render else None
    env = gym.make(env_id, render_mode=render_mode, realtime=realtime)
    rng = np.random.default_rng(seed)
    total_reward = 0.0
    completed_episodes = 0

    try:
        for episode in range(1, episodes + 1):
            obs, info = env.reset(seed=None if seed is None else seed + episode)
            del obs, info
            episode_reward = 0.0
            for step in range(steps):
                action = rng.uniform(-1.0, 1.0, size=env.action_space.shape).astype(np.float32)
                obs, reward, terminated, truncated, info = env.step(action)
                del obs
                episode_reward += float(reward)
                if step % 100 == 0:
                    print(
                        f"env={env_id} episode={episode} step={step} "
                        f"reward={episode_reward:.3f} info={info}",
                        flush=True,
                    )
                if realtime and not render:
                    sleep(0.01)
                if terminated or truncated:
                    break

            completed_episodes += 1
            total_reward += episode_reward
            print(
                f"env={env_id} episode={episode} done "
                f"steps={step + 1} reward={episode_reward:.3f}",
                flush=True,
            )
    finally:
        env.close()

    return RolloutSummary(
        env_id=env_id,
        steps=steps,
        episodes=completed_episodes,
        total_reward=total_reward,
    )
