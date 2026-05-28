from __future__ import annotations

import argparse
from pathlib import Path

import gymnasium as gym
from PIL import Image
from stable_baselines3 import PPO, SAC

import winros.envs  # noqa: F401
from winros.external_envs import register_external_envs
from winros.rl.train_sb3 import _make_env


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--algo", choices=["ppo", "sac"], default="ppo")
    parser.add_argument("--steps", type=int, default=400)
    parser.add_argument("--every", type=int, default=100)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    register_external_envs()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    env = _make_env(gym, args.env, render_mode="rgb_array")
    try:
        model_cls = PPO if args.algo == "ppo" else SAC
        model = model_cls.load(args.model, env=env, device=args.device)
        obs, _info = env.reset(seed=11)
        total_reward = 0.0
        saved = 0
        for step in range(args.steps):
            action, _state = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += float(reward)
            if step % args.every == 0 or terminated or truncated:
                frame = env.render()
                Image.fromarray(frame).save(out_dir / f"{args.env}_step_{step:04d}.png")
                saved += 1
            if terminated or truncated:
                break
    finally:
        env.close()

    print(f"captured env={args.env} steps={step + 1} reward={total_reward:.3f} frames={saved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
