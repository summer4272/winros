from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import winros.envs  # noqa: F401
from winros.config import paths
from winros.external_envs import register_external_envs


@dataclass(frozen=True)
class TrainingSummary:
    env_id: str
    algo: str
    total_timesteps: int
    output_path: Path


def train_sb3(
    env_id: str,
    *,
    algo: str = "ppo",
    total_timesteps: int = 1000,
    output_dir: str | Path | None = None,
    load_model: str | Path | None = None,
    seed: int = 7,
    device: str = "cuda",
    render_train: bool = False,
    render_train_freq: int = 5000,
    render_train_steps: int = 300,
    render_train_episodes: int = 5,
    batch_size: int = 512,
    gradient_steps: int = 2,
    num_envs: int = 1,
    vec_env: str = "dummy",
) -> TrainingSummary:
    try:
        import gymnasium as gym
        from gymnasium import spaces
        from stable_baselines3 import PPO, SAC
        from stable_baselines3.common.callbacks import BaseCallback
        from stable_baselines3.common.callbacks import CallbackList
        from stable_baselines3.common.callbacks import CheckpointCallback
        from stable_baselines3.common.monitor import Monitor
        from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
        from stable_baselines3.her.her_replay_buffer import HerReplayBuffer
    except ImportError as exc:
        raise RuntimeError(
            "Stable-Baselines3 training dependencies are not installed. "
            "Run scripts\\setup_conda_env.ps1 with the rl profile enabled."
        ) from exc

    register_external_envs()
    output_root = Path(output_dir) if output_dir else paths().root / "runs" / "sb3"
    output_root.mkdir(parents=True, exist_ok=True)

    class RenderTrainCallback(BaseCallback):
        def __init__(self) -> None:
            super().__init__(verbose=0)
            self.best_score = float("-inf")

        def _on_step(self) -> bool:
            if not render_train:
                return True
            if render_train_freq <= 0 or self.num_timesteps % render_train_freq != 0:
                return True

            print(
                f"[render-train] num_timesteps={self.num_timesteps}, "
                f"showing current policy for {render_train_steps} steps",
                flush=True,
            )
            eval_env = _make_env(gym, env_id, render_mode="human", realtime=True)
            try:
                stats = _evaluate_policy(
                    self.model,
                    eval_env,
                    steps=render_train_steps,
                    episodes=render_train_episodes,
                )
                print(
                    "[render-train] "
                    f"reward={stats['mean_reward']:.3f} "
                    f"success_rate={stats['success_rate']:.2f} "
                    f"reached_rate={stats['reached_rate']:.2f} "
                    f"lifted_rate={stats['lifted_rate']:.2f} "
                    f"centered_grasp_rate={stats['centered_grasp_rate']:.2f} "
                    f"premature_push_rate={stats['premature_push_rate']:.2f} "
                    f"out_of_bounds_rate={stats['out_of_bounds_rate']:.2f} "
                    f"mean_cube_target_dist={stats['mean_cube_target_dist']:.3f} "
                    f"max_lift_height={stats['max_lift_height']:.3f} "
                    f"mean_x_velocity={stats['mean_x_velocity']:.3f} "
                    f"mean_forward_reward={stats['mean_forward_reward']:.3f}",
                    flush=True,
                )
                score = _preview_score(stats)
                if score > self.best_score:
                    self.best_score = score
                    best_path = output_root / f"{env_id}_{algo_key}_best_render_train"
                    self.model.save(best_path)
                    print(
                        f"[render-train] saved best preview model: {best_path.with_suffix('.zip')}",
                        flush=True,
                    )
            except Exception as exc:  # Keep long training alive if a viewer window fails.
                print(f"[render-train] skipped because viewer failed: {exc}", flush=True)
            finally:
                eval_env.close()

            return True

    env = _make_training_env(
        gym,
        env_id,
        num_envs=max(1, num_envs),
        vec_env=vec_env,
        monitor_cls=Monitor,
        dummy_vec_env_cls=DummyVecEnv,
        subproc_vec_env_cls=SubprocVecEnv,
    )
    try:
        algo_key = algo.lower()
        policy_name = "MultiInputPolicy" if isinstance(env.observation_space, spaces.Dict) else "MlpPolicy"
        if algo_key == "ppo":
            ppo_kwargs = _ppo_kwargs_for_env(env_id, policy_name, batch_size, max(1, num_envs))
            model = PPO(
                policy_name,
                env,
                verbose=1,
                seed=seed,
                device=device,
                **ppo_kwargs,
            )
        elif algo_key == "sac":
            sac_kwargs: dict[str, Any] = {}
            if policy_name == "MultiInputPolicy":
                sac_kwargs = {
                    "replay_buffer_class": HerReplayBuffer,
                    "replay_buffer_kwargs": {
                        "n_sampled_goal": 4,
                        "goal_selection_strategy": "future",
                    },
                }
            sac_config = _sac_kwargs_for_env(
                env_id,
                batch_size=batch_size,
                gradient_steps=gradient_steps,
            )
            model = SAC(
                policy_name,
                env,
                verbose=1,
                seed=seed,
                device=device,
                **sac_config,
                **sac_kwargs,
            )
        else:
            raise ValueError("Unsupported algo. Use 'ppo' or 'sac'.")

        if load_model:
            load_path = Path(load_model)
            if not load_path.exists():
                raise FileNotFoundError(load_path)
            if algo_key == "ppo":
                model = PPO.load(load_path, env=env, device=device)
            else:
                model = SAC.load(load_path, env=env, device=device)

        callbacks: list[Any] = [
            CheckpointCallback(
                save_freq=max(10_000 // max(1, num_envs), 1),
                save_path=str(output_root / "checkpoints"),
                name_prefix=f"{env_id}_{algo_key}",
                save_replay_buffer=algo_key == "sac",
                save_vecnormalize=True,
            )
        ]
        if render_train:
            callbacks.append(RenderTrainCallback())
        callback: Any = CallbackList(callbacks)
        model.learn(total_timesteps=total_timesteps, callback=callback, reset_num_timesteps=load_model is None)
        output_path = output_root / f"{env_id}_{algo_key}_{total_timesteps}_steps"
        model.save(output_path)
    finally:
        env.close()

    return TrainingSummary(
        env_id=env_id,
        algo=algo.lower(),
        total_timesteps=total_timesteps,
        output_path=output_path.with_suffix(".zip"),
    )


def _make_env(gym: Any, env_id: str, **kwargs: Any) -> Any:
    if env_id == "FetchPickAndPlaceDense-v4":
        import gymnasium_robotics  # noqa: F401

        return gym.make("FetchPickAndPlace-v4", reward_type="dense", **kwargs)
    if env_id == "FetchPickAndPlace-v4":
        import gymnasium_robotics  # noqa: F401

    try:
        return gym.make(env_id, **kwargs)
    except TypeError:
        kwargs.pop("realtime", None)
        return gym.make(env_id, **kwargs)


def _make_training_env(
    gym: Any,
    env_id: str,
    *,
    num_envs: int,
    vec_env: str,
    monitor_cls: Any,
    dummy_vec_env_cls: Any,
    subproc_vec_env_cls: Any,
) -> Any:
    if num_envs <= 1:
        return monitor_cls(_make_env(gym, env_id))

    def make_one(rank: int) -> Any:
        def _init() -> Any:
            env = _make_env(gym, env_id)
            env.reset(seed=7 + rank)
            return monitor_cls(env)

        return _init

    env_fns = [make_one(rank) for rank in range(num_envs)]
    if vec_env.lower() == "subproc":
        return subproc_vec_env_cls(env_fns, start_method="spawn")
    if vec_env.lower() != "dummy":
        raise ValueError("--vec-env must be 'dummy' or 'subproc'.")
    return dummy_vec_env_cls(env_fns)


def _evaluate_policy(model: Any, env: Any, *, steps: int, episodes: int) -> dict[str, float]:
    import numpy as np

    rewards: list[float] = []
    success_count = 0
    reached_count = 0
    lifted_count = 0
    centered_grasp_count = 0
    premature_push_count = 0
    out_of_bounds_count = 0
    cube_target_distances: list[float] = []
    lift_heights: list[float] = []
    x_velocities: list[float] = []
    forward_rewards: list[float] = []

    for _episode in range(episodes):
        obs, _info = env.reset()
        episode_reward = 0.0
        final_info: dict[str, Any] = {}
        for _step in range(steps):
            action, _state = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            episode_reward += float(reward)
            final_info = dict(info)
            if isinstance(obs, dict) and "achieved_goal" in obs and "desired_goal" in obs:
                achieved_goal = np.asarray(obs["achieved_goal"], dtype=float)
                desired_goal = np.asarray(obs["desired_goal"], dtype=float)
                final_info["cube_target_dist"] = float(np.linalg.norm(achieved_goal - desired_goal))
            if "x_velocity" in info:
                x_velocities.append(float(info["x_velocity"]))
            if "forward_reward" in info:
                forward_rewards.append(float(info["forward_reward"]))
            if "lift_height" in info:
                lift_heights.append(float(info["lift_height"]))
            if terminated or truncated:
                break
        rewards.append(episode_reward)
        success = _info_flag(final_info, "success", fallback_key="is_success")
        success_count += int(success)
        reached_count += int(_info_flag(final_info, "reached") or success)
        lifted_count += int(_info_flag(final_info, "lifted"))
        centered_grasp_count += int(_info_flag(final_info, "centered_grasp"))
        premature_push_count += int(_info_flag(final_info, "premature_push"))
        out_of_bounds_count += int(_info_flag(final_info, "cube_out_of_bounds"))
        if "cube_target_dist" in final_info:
            cube_target_distances.append(float(final_info["cube_target_dist"]))

    return {
        "mean_reward": float(sum(rewards) / max(1, len(rewards))),
        "success_rate": float(success_count / max(1, episodes)),
        "reached_rate": float(reached_count / max(1, episodes)),
        "lifted_rate": float(lifted_count / max(1, episodes)),
        "centered_grasp_rate": float(centered_grasp_count / max(1, episodes)),
        "premature_push_rate": float(premature_push_count / max(1, episodes)),
        "out_of_bounds_rate": float(out_of_bounds_count / max(1, episodes)),
        "mean_cube_target_dist": (
            float(sum(cube_target_distances) / len(cube_target_distances))
            if cube_target_distances
            else float("nan")
        ),
        "mean_x_velocity": (
            float(sum(x_velocities) / len(x_velocities)) if x_velocities else float("nan")
        ),
        "max_lift_height": (
            float(max(lift_heights)) if lift_heights else float("nan")
        ),
        "mean_forward_reward": (
            float(sum(forward_rewards) / len(forward_rewards)) if forward_rewards else float("nan")
        ),
    }


def _info_flag(info: dict[str, Any], key: str, *, fallback_key: str | None = None) -> bool:
    value = info.get(key, info.get(fallback_key, False) if fallback_key else False)
    try:
        return bool(float(value) > 0.5)
    except (TypeError, ValueError):
        return bool(value)


def _ppo_kwargs_for_env(
    env_id: str,
    policy_name: str,
    batch_size: int,
    num_envs: int = 1,
) -> dict[str, Any]:
    if env_id == "Humanoid-v5":
        return {
            "n_steps": 4096,
            "batch_size": max(256, min(batch_size, 1024)),
            "n_epochs": 10,
            "learning_rate": 3e-4,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "clip_range": 0.2,
            "ent_coef": 0.0,
            "vf_coef": 0.5,
            "max_grad_norm": 0.5,
            "policy_kwargs": {"net_arch": [512, 512]},
        }
    if env_id == "Ant-v5":
        return {
            "n_steps": 2048,
            "batch_size": max(256, min(batch_size, 1024)),
            "n_epochs": 10,
            "learning_rate": 3e-4,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "clip_range": 0.2,
            "ent_coef": 0.0,
            "vf_coef": 0.5,
            "max_grad_norm": 0.5,
            "policy_kwargs": {"net_arch": [256, 256]},
        }
    if env_id.startswith("WinROSArm"):
        rollout_steps = 256
        rollout_batch = rollout_steps * max(1, num_envs)
        return {
            "n_steps": rollout_steps,
            "batch_size": max(64, min(batch_size, rollout_batch)),
            "n_epochs": 8,
            "learning_rate": 2.5e-4,
            "gamma": 0.985,
            "gae_lambda": 0.94,
            "clip_range": 0.2,
            "ent_coef": 0.01,
            "vf_coef": 0.5,
            "max_grad_norm": 0.5,
            "policy_kwargs": {"net_arch": [512, 256, 128]},
        }
    return {
        "n_steps": 64,
        "batch_size": 32,
        "learning_rate": 3e-4,
        "gamma": 0.98,
        "policy_kwargs": {"net_arch": [512, 512]} if policy_name == "MlpPolicy" else {},
    }


def _sac_kwargs_for_env(
    env_id: str,
    *,
    batch_size: int,
    gradient_steps: int,
) -> dict[str, Any]:
    if env_id.startswith("FetchPickAndPlace"):
        return {
            "buffer_size": 1_000_000,
            "batch_size": max(128, min(batch_size, 256)),
            "learning_rate": 1e-3,
            "learning_starts": 5_000,
            "train_freq": 1,
            "gradient_steps": max(1, gradient_steps),
            "gamma": 0.95,
            "tau": 0.05,
            "ent_coef": 0.05,
            "target_update_interval": 1,
            "policy_kwargs": {"net_arch": [256, 256, 256]},
        }
    return {
        "buffer_size": 100_000,
        "batch_size": batch_size,
        "learning_rate": 3e-4,
        "learning_starts": 64,
        "train_freq": 1,
        "gradient_steps": gradient_steps,
        "gamma": 0.98,
        "tau": 0.02,
        "policy_kwargs": {"net_arch": [512, 512, 256]},
    }


def _preview_score(stats: dict[str, float]) -> float:
    if stats["mean_x_velocity"] == stats["mean_x_velocity"]:
        return stats["mean_reward"] + 10.0 * stats["mean_x_velocity"]
    if stats["mean_cube_target_dist"] == stats["mean_cube_target_dist"]:
        return (
            1000.0 * stats["success_rate"]
            + 100.0 * stats["lifted_rate"]
            + 25.0 * stats["centered_grasp_rate"]
            + 10.0 * stats["reached_rate"]
            + stats["mean_reward"]
            - 25.0 * stats["mean_cube_target_dist"]
            - 100.0 * stats["out_of_bounds_rate"]
            - 100.0 * stats["premature_push_rate"]
        )
    return (
        1000.0 * stats["success_rate"]
        + 100.0 * stats["lifted_rate"]
        + 25.0 * stats["centered_grasp_rate"]
        + 10.0 * stats["reached_rate"]
        + stats["mean_reward"]
        - 100.0 * stats["out_of_bounds_rate"]
        - 100.0 * stats["premature_push_rate"]
    )
