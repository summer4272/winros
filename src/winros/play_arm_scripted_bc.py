from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch

from winros.config import paths
from winros.envs.arm_grasp import ArmPlaceEnv
from winros.scripted_arm_pick_place import PHASES
from winros.train_arm_scripted_bc import Policy, _execute_hybrid_action, _policy_obs


def main() -> int:
    parser = argparse.ArgumentParser(description="Play trained arm scripted-BC policy")
    parser.add_argument(
        "--model",
        default=str(paths().root / "runs" / "arm_bc" / "arm_scripted_bc.pt"),
    )
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--seed", type=int, default=2000)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--realtime", action="store_true")
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    model_path = Path(args.model)
    checkpoint = torch.load(model_path, map_location="cpu")
    device = torch.device(args.device if torch.cuda.is_available() and args.device == "cuda" else "cpu")
    model = Policy(int(checkpoint["obs_dim"]), int(checkpoint["action_dim"])).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    successes = 0
    lifted = 0
    for episode in range(args.episodes):
        result = run_episode(
            model,
            device,
            seed=args.seed + episode,
            render=args.render,
            realtime=args.realtime or args.render,
        )
        successes += int(result["success"])
        lifted += int(result["lifted"])
        print(
            f"episode={episode + 1} success={result['success']} "
            f"lifted={result['lifted']} max_lift={result['max_lift']:.3f} "
            f"cube_target_dist={result['cube_target_dist']:.3f} steps={result['steps']}",
            flush=True,
        )

    print(
        f"summary episodes={args.episodes} "
        f"success_rate={successes / max(1, args.episodes):.2f} "
        f"lifted_rate={lifted / max(1, args.episodes):.2f}",
        flush=True,
    )
    return 0


def run_episode(
    model: Policy,
    device: torch.device,
    *,
    seed: int,
    render: bool,
    realtime: bool,
) -> dict[str, float | bool | int]:
    env = ArmPlaceEnv(
        render_mode="human" if render else None,
        realtime=realtime,
        max_episode_steps=1400,
    )
    env.reset(seed=seed)
    attached = False
    cube_offset = np.zeros(3, dtype=float)
    max_lift = 0.0
    final_info: dict[str, float | bool] = {}
    steps = 0

    for phase_index, phase in enumerate(PHASES):
        for step_index in range(phase.steps):
            obs = torch.from_numpy(
                _policy_obs(env, attached, phase_index, step_index / max(1, phase.steps))
            ).unsqueeze(0).to(device)
            with torch.no_grad():
                action = model(obs).squeeze(0).cpu().numpy().astype(np.float32)
            attached, cube_offset, terminated, truncated = _execute_hybrid_action(
                env,
                action,
                attached,
                cube_offset,
                phase.name,
            )
            steps += 1
            info = env._compute_reward().info
            final_info = dict(info)
            max_lift = max(max_lift, float(info.get("lift_height", 0.0)))
            if terminated or truncated or bool(info.get("success", False)):
                break
        if terminated or truncated or bool(final_info.get("success", False)):
            break

    env.close()
    return {
        "success": bool(final_info.get("success", False)),
        "lifted": max_lift > env.lift_success_height,
        "max_lift": max_lift,
        "cube_target_dist": float(final_info.get("cube_target_dist", float("nan"))),
        "steps": steps,
    }


if __name__ == "__main__":
    raise SystemExit(main())
