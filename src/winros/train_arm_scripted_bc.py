from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from winros.config import paths
from winros.envs.arm_grasp import ArmPlaceEnv
from winros.scripted_arm_pick_place import (
    PHASES,
    _cartesian_action,
    _carry_attached_cube,
    _joint_target_step,
    _maybe_attach_cube,
    _phase_target,
)


@dataclass(frozen=True)
class TrainResult:
    model_path: Path
    demos: int
    samples: int
    seconds: float
    eval_success_rate: float
    eval_lifted_rate: float


class Policy(nn.Module):
    def __init__(self, obs_dim: int, action_dim: int = 5) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_dim, 256),
            nn.SiLU(),
            nn.Linear(256, 256),
            nn.SiLU(),
            nn.Linear(256, 128),
            nn.SiLU(),
            nn.Linear(128, action_dim),
            nn.Tanh(),
        )

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        return self.net(obs)


def main() -> int:
    parser = argparse.ArgumentParser(description="Train arm policy from scripted expert demos")
    parser.add_argument("--demos", type=int, default=80)
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--seed", type=int, default=1000)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--eval-episodes", type=int, default=10)
    parser.add_argument("--output-dir", default=str(paths().root / "runs" / "arm_bc"))
    args = parser.parse_args()

    start = perf_counter()
    device = torch.device(args.device if torch.cuda.is_available() and args.device == "cuda" else "cpu")

    obs, actions = collect_demos(args.demos, args.seed)
    model = Policy(obs.shape[1], actions.shape[1]).to(device)
    dataset = TensorDataset(torch.from_numpy(obs), torch.from_numpy(actions))
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, drop_last=False)
    optim = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-4)
    loss_fn = nn.MSELoss()

    model.train()
    for epoch in range(1, args.epochs + 1):
        losses: list[float] = []
        for batch_obs, batch_action in loader:
            batch_obs = batch_obs.to(device)
            batch_action = batch_action.to(device)
            pred = model(batch_obs)
            loss = loss_fn(pred, batch_action)
            optim.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optim.step()
            losses.append(float(loss.detach().cpu()))
        if epoch == 1 or epoch % 5 == 0 or epoch == args.epochs:
            print(f"epoch={epoch} loss={float(np.mean(losses)):.6f}", flush=True)

    success_rate, lifted_rate = evaluate_policy(model, device, args.eval_episodes, args.seed + 10000)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / "arm_scripted_bc.pt"
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "obs_dim": int(obs.shape[1]),
            "action_dim": int(actions.shape[1]),
            "demos": int(args.demos),
            "samples": int(obs.shape[0]),
        },
        model_path,
    )
    meta = {
        "model_path": str(model_path),
        "demos": int(args.demos),
        "samples": int(obs.shape[0]),
        "epochs": int(args.epochs),
        "device": str(device),
        "seconds": round(perf_counter() - start, 3),
        "eval_success_rate": success_rate,
        "eval_lifted_rate": lifted_rate,
    }
    (output_dir / "arm_scripted_bc_metrics.json").write_text(
        json.dumps(meta, indent=2),
        encoding="utf-8",
    )
    print("training_complete " + json.dumps(meta, ensure_ascii=False), flush=True)
    return 0


def collect_demos(demos: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    obs_rows: list[np.ndarray] = []
    action_rows: list[np.ndarray] = []
    for index in range(demos):
        env = ArmPlaceEnv(max_episode_steps=1400)
        env.reset(seed=seed + index)
        attached = False
        cube_offset = np.zeros(3, dtype=float)
        for phase_index, phase in enumerate(PHASES):
            for step_index in range(phase.steps):
                obs_rows.append(_policy_obs(env, attached, phase_index, step_index / max(1, phase.steps)))
                action = _teacher_action(env, phase.name, phase.grip, attached)
                action_rows.append(action)
                attached, cube_offset, terminated, truncated = _execute_hybrid_action(
                    env,
                    action,
                    attached,
                    cube_offset,
                    phase.name,
                )
                if terminated or truncated:
                    break
            if terminated or truncated:
                break
        env.close()
        if (index + 1) % 10 == 0:
            print(f"collected_demos={index + 1}/{demos} samples={len(obs_rows)}", flush=True)
    return (
        np.asarray(obs_rows, dtype=np.float32),
        np.asarray(action_rows, dtype=np.float32),
    )


def evaluate_policy(model: Policy, device: torch.device, episodes: int, seed: int) -> tuple[float, float]:
    model.eval()
    successes = 0
    lifted = 0
    for index in range(episodes):
        env = ArmPlaceEnv(max_episode_steps=1400)
        env.reset(seed=seed + index)
        attached = False
        cube_offset = np.zeros(3, dtype=float)
        max_lift = 0.0
        final_info: dict[str, float | bool] = {}
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
                info = env._compute_reward().info
                final_info = dict(info)
                max_lift = max(max_lift, float(info.get("lift_height", 0.0)))
                if terminated or truncated or bool(info.get("success", False)):
                    break
            if terminated or truncated or bool(final_info.get("success", False)):
                break
        successes += int(bool(final_info.get("success", False)))
        lifted += int(max_lift > env.lift_success_height)
        env.close()
    success_rate = successes / max(1, episodes)
    lifted_rate = lifted / max(1, episodes)
    print(f"eval success_rate={success_rate:.2f} lifted_rate={lifted_rate:.2f}", flush=True)
    return success_rate, lifted_rate


def _policy_obs(
    env: ArmPlaceEnv,
    attached: bool,
    phase_index: int,
    phase_fraction: float,
) -> np.ndarray:
    phase_one_hot = np.zeros(len(PHASES), dtype=np.float32)
    if 0 <= phase_index < len(PHASES):
        phase_one_hot[phase_index] = 1.0
    return np.concatenate(
        [
            env._get_obs(),
            np.array([1.0 if attached else 0.0], dtype=np.float32),
            phase_one_hot,
            np.array([float(np.clip(phase_fraction, 0.0, 1.0))], dtype=np.float32),
        ]
    ).astype(np.float32)


def _teacher_action(env: ArmPlaceEnv, phase_name: str, grip: float, attached: bool) -> np.ndarray:
    action = np.zeros(5, dtype=np.float32)
    if attached and phase_name == "lift":
        action[3] = grip
        action[4] = 1.0
        return action
    action[:4] = _cartesian_action(env, _phase_target(env, phase_name), grip)
    action[4] = -1.0
    return action


def _execute_hybrid_action(
    env: ArmPlaceEnv,
    action: np.ndarray,
    attached: bool,
    cube_offset: np.ndarray,
    phase_name: str,
) -> tuple[bool, np.ndarray, bool, bool]:
    if attached and float(action[4]) > 0.0:
        _, terminated, truncated, _ = _joint_target_step(env, env.home_arm_qpos, float(action[3]))
    else:
        _, _, terminated, truncated, _ = env.step(action[:4])

    if not attached:
        attached, cube_offset = _maybe_attach_cube(env)
    if attached and float(action[3]) < 0.5:
        _carry_attached_cube(env, cube_offset)
    if attached and float(action[3]) > 0.6:
        attached = False
    return attached, cube_offset, terminated, truncated


if __name__ == "__main__":
    raise SystemExit(main())
