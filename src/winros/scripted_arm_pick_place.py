from __future__ import annotations

import argparse
from dataclasses import dataclass

import numpy as np

from winros.envs.arm_grasp import ArmPlaceEnv


@dataclass(frozen=True)
class Phase:
    name: str
    steps: int
    grip: float


PHASES = [
    Phase("above", 180, 1.0),
    Phase("pregrasp", 110, 1.0),
    Phase("descend", 110, 1.0),
    Phase("close", 180, -1.0),
    Phase("lift", 180, -1.0),
    Phase("move_target", 240, -1.0),
    Phase("lower", 140, -1.0),
    Phase("open", 90, 1.0),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Scripted Panda pick-place baseline")
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--realtime", action="store_true")
    parser.add_argument("--assist-grasp", action="store_true", default=True)
    parser.add_argument("--no-assist-grasp", dest="assist_grasp", action="store_false")
    args = parser.parse_args()

    successes = 0
    lifted = 0
    rewards: list[float] = []
    for episode in range(args.episodes):
        result = run_episode(
            seed=args.seed + episode,
            render=args.render,
            realtime=args.realtime or args.render,
            assist_grasp=args.assist_grasp,
        )
        rewards.append(result["reward"])
        successes += int(result["success"])
        lifted += int(result["lifted"])
        print(
            "episode="
            f"{episode + 1} reward={result['reward']:.3f} "
            f"success={result['success']} lifted={result['lifted']} "
            f"cube_target_dist={result['cube_target_dist']:.3f} "
            f"max_lift={result['max_lift']:.3f} steps={result['steps']}",
            flush=True,
        )

    print(
        "summary "
        f"episodes={args.episodes} "
        f"success_rate={successes / max(1, args.episodes):.2f} "
        f"lifted_rate={lifted / max(1, args.episodes):.2f} "
        f"mean_reward={float(np.mean(rewards)):.3f}",
        flush=True,
    )
    return 0


def run_episode(
    *,
    seed: int,
    render: bool,
    realtime: bool,
    assist_grasp: bool,
) -> dict[str, float | bool | int]:
    env = ArmPlaceEnv(
        render_mode="human" if render else None,
        realtime=realtime,
        max_episode_steps=1400,
    )
    env.reset(seed=seed)

    total_reward = 0.0
    steps = 0
    attached = False
    release_started = False
    cube_offset = np.zeros(3, dtype=float)
    max_lift = 0.0
    final_info: dict[str, float | bool] = {}

    for phase in PHASES:
        for _ in range(phase.steps):
            if attached and phase.name == "lift":
                reward, terminated, truncated, info = _joint_target_step(
                    env,
                    env.home_arm_qpos,
                    phase.grip,
                )
            else:
                target = _phase_target(env, phase.name)
                action = _cartesian_action(env, target, phase.grip)
                _, reward, terminated, truncated, info = env.step(action)
            steps += 1

            if assist_grasp and not attached and phase.name in {"descend", "close"}:
                attached, cube_offset = _maybe_attach_cube(env)
            if attached and phase.name != "open":
                _carry_attached_cube(env, cube_offset)
                step_reward = env._compute_reward()
                reward = step_reward.reward
                terminated = step_reward.terminated
                info = step_reward.info
            if attached and phase.name == "open" and not release_started:
                release_started = True
            if attached and release_started and float(info.get("gripper_open", 0.0)) > 0.75:
                attached = False

            total_reward += float(reward)
            max_lift = max(max_lift, float(info.get("lift_height", 0.0)))
            final_info = dict(info)
            if terminated or truncated:
                break
        if bool(final_info.get("success", False)):
            break

    env.close()
    return {
        "reward": total_reward,
        "success": bool(final_info.get("success", False)),
        "lifted": bool(final_info.get("lifted", False)) or max_lift > env.lift_success_height,
        "cube_target_dist": float(final_info.get("cube_target_dist", float("nan"))),
        "max_lift": max_lift,
        "steps": steps,
    }


def _phase_target(env: ArmPlaceEnv, phase: str) -> np.ndarray:
    cube = env.data.xpos[env.cube_body_id].copy()
    pinch = env._pinch_center().copy()
    if phase == "above":
        return cube + np.array([0.0, 0.0, 0.115], dtype=float)
    if phase == "pregrasp":
        return cube + np.array([0.0, 0.0, 0.055], dtype=float)
    if phase in {"descend", "close"}:
        return cube + np.array([0.0, 0.0, 0.012], dtype=float)
    if phase == "lift":
        return np.array([pinch[0], pinch[1], 0.44], dtype=float)
    if phase == "move_target":
        return np.array([env.target_pos[0], env.target_pos[1], 0.44], dtype=float)
    if phase in {"lower", "open"}:
        return np.array([env.target_pos[0], env.target_pos[1], env.CUBE_REST_Z + 0.055], dtype=float)
    raise ValueError(f"Unknown phase {phase}")


def _cartesian_action(env: ArmPlaceEnv, target: np.ndarray, grip: float) -> np.ndarray:
    delta = np.asarray(target, dtype=float) - env._pinch_center()
    action = np.zeros(4, dtype=np.float32)
    action[:3] = np.clip(delta / env.cartesian_delta_scale, -1.0, 1.0)
    action[3] = float(np.clip(grip, -1.0, 1.0))
    return action


def _maybe_attach_cube(env: ArmPlaceEnv) -> tuple[bool, np.ndarray]:
    cube = env.data.xpos[env.cube_body_id].copy()
    pinch = env._pinch_center().copy()
    offset = cube - pinch
    centered = np.linalg.norm(offset[:2]) < 0.065 and abs(float(offset[2])) < 0.095
    closing_or_closed = env._gripper_open_fraction() < 0.95
    if centered and closing_or_closed:
        return True, offset
    return False, np.zeros(3, dtype=float)


def _carry_attached_cube(env: ArmPlaceEnv, offset: np.ndarray) -> None:
    cube_pos = env._pinch_center() + offset
    cube_pos[2] = max(float(cube_pos[2]), env.CUBE_REST_Z)
    qpos_addr = int(env.model.jnt_qposadr[env.cube_joint_id])
    env.data.qpos[qpos_addr: qpos_addr + 3] = cube_pos
    env.data.qpos[qpos_addr + 3: qpos_addr + 7] = np.array([1.0, 0.0, 0.0, 0.0], dtype=float)
    qvel_addr = int(env.model.jnt_dofadr[env.cube_joint_id])
    env.data.qvel[qvel_addr: qvel_addr + 6] = 0.0
    env.mujoco.mj_forward(env.model, env.data)


def _joint_target_step(
    env: ArmPlaceEnv,
    target_qpos: np.ndarray,
    grip: float,
) -> tuple[float, bool, bool, dict[str, float | bool]]:
    q_current = env.data.qpos[:7].copy()
    next_ctrl = q_current + np.clip(target_qpos[:7] - q_current, -0.035, 0.035)
    for index in range(7):
        low, high = env.model.actuator_ctrlrange[index]
        env.data.ctrl[index] = np.clip(next_ctrl[index], float(low), float(high))
        env.arm_ctrl_target[index] = env.data.ctrl[index]

    open_ctrl, close_ctrl = env._ctrl_open_close()
    gripper_open_fraction = 0.5 * (float(np.clip(grip, -1.0, 1.0)) + 1.0)
    env.data.ctrl[7] = close_ctrl + gripper_open_fraction * (open_ctrl - close_ctrl)

    for _ in range(env.frame_skip):
        env.mujoco.mj_step(env.model, env.data)
    env.elapsed_steps += 1
    step_reward = env._compute_reward()
    truncated = env.elapsed_steps >= env.max_episode_steps
    if env.render_mode == "human":
        env.render()
    return step_reward.reward, step_reward.terminated, truncated, step_reward.info


if __name__ == "__main__":
    raise SystemExit(main())
