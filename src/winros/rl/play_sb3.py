from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import sleep

import winros.envs  # noqa: F401
from winros.external_envs import register_external_envs
from winros.rl.train_sb3 import _make_env


@dataclass(frozen=True)
class PlaySummary:
    env_id: str
    model_path: Path
    episodes: int
    total_reward: float


def play_sb3_model(
    env_id: str,
    model_path: str | Path,
    *,
    algo: str = "sac",
    episodes: int = 3,
    steps: int = 300,
    render: bool = True,
    realtime: bool = True,
    device: str = "cuda",
) -> PlaySummary:
    try:
        import gymnasium as gym
        from stable_baselines3 import PPO, SAC
    except ImportError as exc:
        raise RuntimeError("Stable-Baselines3 is not installed in the active environment.") from exc

    register_external_envs()
    path = Path(model_path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)

    env = _make_env(gym, env_id, render_mode="human" if render else None, realtime=realtime)
    total_reward = 0.0
    try:
        algo_key = algo.lower()
        if algo_key == "sac":
            model = SAC.load(path, env=env, device=device)
        elif algo_key == "ppo":
            model = PPO.load(path, env=env, device=device)
        else:
            raise ValueError("Unsupported algo. Use 'ppo' or 'sac'.")

        for episode in range(1, episodes + 1):
            obs, info = env.reset()
            del info
            episode_reward = 0.0
            for step in range(steps):
                action, _state = model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = env.step(action)
                episode_reward += float(reward)
                if step % 100 == 0:
                    print(
                        f"play env={env_id} episode={episode} step={step} "
                        f"reward={episode_reward:.3f} info={info}",
                        flush=True,
                    )
                if realtime and not render:
                    sleep(0.01)
                if terminated or truncated:
                    break
            total_reward += episode_reward
            print(
                f"play env={env_id} episode={episode} done "
                f"steps={step + 1} reward={episode_reward:.3f}",
                flush=True,
            )
    finally:
        env.close()

    return PlaySummary(
        env_id=env_id,
        model_path=path,
        episodes=episodes,
        total_reward=total_reward,
    )
