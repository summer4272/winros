from __future__ import annotations

import argparse
import os
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO = Path("D:/winros/third_party/unitree_rl_mjlab")
DEFAULT_OUTPUT_DIR = ROOT / "docs" / "assets" / "demo"


@dataclass(frozen=True)
class DemoProfile:
    key: str
    title: str
    task: str
    experiment: str
    run_pattern: str
    output_name: str


PROFILES = {
    "g1_fast_run": DemoProfile(
        key="g1_fast_run",
        title="人形机器人快跑",
        task="Unitree-G1-FastRunV1",
        experiment="g1_velocity",
        run_pattern="_unitree_g1_fast_run_v1_",
        output_name="g1_fast_run.mp4",
    ),
    "go2_fast_run": DemoProfile(
        key="go2_fast_run",
        title="机器狗快跑",
        task="Unitree-Go2-FastFlat",
        experiment="go2_velocity",
        run_pattern="_unitree_go2_fast_flat_",
        output_name="go2_fast_run.mp4",
    ),
    "go2_stairs": DemoProfile(
        key="go2_stairs",
        title="机器狗上楼梯",
        task="Unitree-Go2-StairsForwardV3",
        experiment="go2_velocity",
        run_pattern="_unitree_go2_stairs_forward_v3_",
        output_name="go2_stairs.mp4",
    ),
}


def latest_checkpoint(repo: Path, profile: DemoProfile) -> Path:
    root = repo / "logs" / "rsl_rl" / profile.experiment
    if not root.exists():
        raise FileNotFoundError(root)
    runs = [
        path
        for path in root.iterdir()
        if path.is_dir() and profile.run_pattern in path.name
    ]
    if not runs:
        raise FileNotFoundError(f"No runs matching {profile.run_pattern} under {root}")
    runs.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    for run in runs:
        models = sorted(
            run.glob("model_*.pt"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if models:
            return models[0]
    raise FileNotFoundError(f"No model_*.pt files found for {profile.key}")


def setup_imports(repo: Path) -> None:
    repo = repo.resolve()
    os.chdir(repo)
    for candidate in (repo, repo / "src"):
        candidate_str = str(candidate)
        if candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)


def record_profile(
    repo: Path,
    profile: DemoProfile,
    checkpoint: Path,
    output_dir: Path,
    *,
    steps: int,
    width: int,
    height: int,
    num_envs: int,
    device: str,
) -> Path:
    setup_imports(repo)

    import torch
    import mjlab.tasks  # noqa: F401
    import src.tasks  # noqa: F401
    from mjlab.envs import ManagerBasedRlEnv
    from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
    from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls
    from mjlab.utils.torch import configure_torch_backends
    from mjlab.utils.wrappers import VideoRecorder

    configure_torch_backends()

    env_cfg = load_env_cfg(profile.task, play=True)
    agent_cfg = load_rl_cfg(profile.task)
    env_cfg.scene.num_envs = num_envs
    env_cfg.viewer.width = width
    env_cfg.viewer.height = height

    temp_dir = output_dir / "_recordings" / profile.key
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    env = ManagerBasedRlEnv(cfg=env_cfg, device=device, render_mode="rgb_array")
    env = VideoRecorder(
        env,
        video_folder=temp_dir,
        step_trigger=lambda step: step == 0,
        video_length=steps,
        name_prefix=profile.key,
        disable_logger=False,
    )
    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)

    runner_cls = load_runner_cls(profile.task) or MjlabOnPolicyRunner
    runner = runner_cls(env, asdict(agent_cfg), device=device)
    runner.load(str(checkpoint), load_cfg={"actor": True}, strict=True, map_location=device)
    policy = runner.get_inference_policy(device=device)

    try:
        reset = getattr(env, "reset", None)
        if reset is not None:
            reset()
        with torch.no_grad():
            for _step in range(steps):
                obs = env.get_observations()
                actions = policy(obs)
                env.step(actions)
    finally:
        env.close()

    recorded = sorted(temp_dir.glob("*.mp4"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not recorded:
        raise RuntimeError(f"No video was recorded for {profile.key}")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / profile.output_name
    shutil.copy2(recorded[0], output_path)
    shutil.rmtree(temp_dir)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Record latest Unitree MJLab policies for WinROS demo.")
    parser.add_argument(
        "--profile",
        choices=["all", *PROFILES.keys()],
        default="all",
        help="Demo profile to record.",
    )
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--steps", type=int, default=240)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--num-envs", type=int, default=1)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = (ROOT / output_dir).resolve()

    selected = list(PROFILES.values()) if args.profile == "all" else [PROFILES[args.profile]]
    for profile in selected:
        checkpoint = latest_checkpoint(args.repo, profile)
        print(f"[WinROS demo] {profile.title}: {checkpoint}")
        output = record_profile(
            args.repo,
            profile,
            checkpoint,
            output_dir,
            steps=args.steps,
            width=args.width,
            height=args.height,
            num_envs=args.num_envs,
            device=args.device,
        )
        print(f"[WinROS demo] wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
