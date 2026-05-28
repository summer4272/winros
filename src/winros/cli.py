from __future__ import annotations

import argparse
import json
from pathlib import Path

from winros.asset_registry import get_asset, list_assets
from winros.robot_registry import list_robots, resolve_model
from winros.task_registry import list_tasks

try:
    from rich.console import Console
    from rich.table import Table
except ImportError:
    Console = None
    Table = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="WinROS local utilities")
    parser.add_argument("--dashboard", action="store_true", help="Start the local operator dashboard")
    parser.add_argument("--dashboard-host", default="127.0.0.1", help="Dashboard host")
    parser.add_argument("--dashboard-port", type=int, default=8765, help="Dashboard port")
    parser.add_argument("--list-robots", action="store_true", help="List built-in robot demos")
    parser.add_argument("--list-tasks", action="store_true", help="List planned robot task tracks")
    parser.add_argument("--list-envs", action="store_true", help="List Gymnasium training envs")
    parser.add_argument("--list-assets", action="store_true", help="List open-source asset candidates")
    parser.add_argument("--check-assets", action="store_true", help="Check local asset availability")
    parser.add_argument("--list-vla-providers", action="store_true", help="List VLA providers")
    parser.add_argument("--track", help="Filter assets by task track")
    parser.add_argument("--robot", default="two_link_arm", help="Built-in robot name")
    parser.add_argument("--asset", help="Open-source asset name from configs/assets")
    parser.add_argument("--model", help="Path to a MuJoCo MJCF model")
    parser.add_argument("--steps", type=int, default=1000, help="Number of MuJoCo steps")
    parser.add_argument("--episodes", type=int, default=3, help="Number of preview episodes")
    parser.add_argument("--action-scale", type=float, default=0.15, help="Preview action scale")
    parser.add_argument("--action-repeat", type=int, default=20, help="Preview action repeat")
    parser.add_argument("--preview-training", action="store_true", help="Run a realtime training preview")
    parser.add_argument("--env", help="Gymnasium env id for random rollout smoke tests")
    parser.add_argument("--render-env", action="store_true", help="Render --env rollout in a MuJoCo viewer")
    parser.add_argument("--train-env", help="Gymnasium env id to train with Stable-Baselines3")
    parser.add_argument("--play-model", help="Path to a saved Stable-Baselines3 model zip")
    parser.add_argument("--load-model", help="Continue training from a saved Stable-Baselines3 model zip")
    parser.add_argument("--algo", choices=["ppo", "sac"], default="sac", help="RL algorithm for --train-env")
    parser.add_argument("--timesteps", type=int, default=1000, help="Training timesteps for --train-env")
    parser.add_argument("--device", default="cuda", help="Training device for --train-env")
    parser.add_argument("--render-train", action="store_true", help="Periodically render the policy during training")
    parser.add_argument("--render-train-freq", type=int, default=5000, help="Training steps between render previews")
    parser.add_argument("--render-train-steps", type=int, default=300, help="Simulation steps per render preview")
    parser.add_argument("--render-train-episodes", type=int, default=5, help="Episodes per render-train preview")
    parser.add_argument("--batch-size", type=int, default=512, help="Training batch size for SAC")
    parser.add_argument("--gradient-steps", type=int, default=2, help="SAC gradient steps per environment step")
    parser.add_argument("--num-envs", type=int, default=1, help="Number of vectorized training envs")
    parser.add_argument("--vla-provider", help="VLA provider name for structured command generation")
    parser.add_argument("--vla-instruction", help="Natural-language instruction for --vla-provider")
    parser.add_argument("--vla-robot", default="dry_run_robot", help="Robot name for VLA command output")
    parser.add_argument("--vla-image", help="Optional image path for future VLA providers")
    parser.add_argument(
        "--vec-env",
        choices=["dummy", "subproc"],
        default="dummy",
        help="Vectorized env backend for --num-envs",
    )
    parser.add_argument("--viewer", action="store_true", help="Open the MuJoCo viewer")
    parser.add_argument("--realtime", action="store_true", help="Sleep according to simulator timestep")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    console = Console() if Console else None

    if args.dashboard:
        from winros.dashboard import run_dashboard

        return run_dashboard(host=args.dashboard_host, port=args.dashboard_port)

    if args.list_robots:
        if console and Table:
            table = Table(title="Built-in WinROS Robots")
            table.add_column("Name")
            table.add_column("Kind")
            table.add_column("Model")
            table.add_column("Notes")
            for robot in list_robots():
                table.add_row(robot.name, robot.kind, str(robot.model_path), robot.notes)
            console.print(table)
        else:
            for robot in list_robots():
                print(f"{robot.name}\t{robot.kind}\t{robot.model_path}\t{robot.notes}")
        return 0

    if args.list_tasks:
        tasks = list_tasks()
        if console and Table:
            table = Table(title="WinROS Task Tracks")
            table.add_column("ID")
            table.add_column("Robot")
            table.add_column("Primary Asset")
            table.add_column("Initial Goal")
            for task in tasks:
                table.add_row(task.id, task.primary_robot, task.primary_asset, task.initial_goal)
            console.print(table)
        else:
            for task in tasks:
                print(f"{task.id}\t{task.primary_robot}\t{task.primary_asset}\t{task.initial_goal}")
        return 0

    if args.list_envs:
        from winros.envs.registry import list_envs

        envs = list_envs()
        if console and Table:
            table = Table(title="WinROS Gymnasium Environments")
            table.add_column("ID")
            table.add_column("Task")
            table.add_column("Robot")
            table.add_column("Notes")
            for env in envs:
                table.add_row(env.id, env.task, env.robot, env.notes)
            console.print(table)
        else:
            for env in envs:
                print(f"{env.id}\t{env.task}\t{env.robot}\t{env.notes}")
        return 0

    if args.list_assets or args.check_assets:
        assets = list_assets(track=args.track)
        if console and Table:
            table = Table(title="WinROS Open-Source Assets")
            table.add_column("Name")
            table.add_column("Track")
            table.add_column("Robot")
            table.add_column("License")
            table.add_column("Available")
            table.add_column("Expected Path")
            for asset in assets:
                expected = asset.expected_model_path or asset.local_repo
                available = "yes" if asset.is_available else "no"
                table.add_row(
                    asset.name,
                    asset.track,
                    asset.robot,
                    asset.license,
                    available,
                    str(expected),
                )
            console.print(table)
        else:
            for asset in assets:
                expected = asset.expected_model_path or asset.local_repo
                available = "yes" if asset.is_available else "no"
                print(
                    f"{asset.name}\t{asset.track}\t{asset.robot}\t"
                    f"{asset.license}\t{available}\t{expected}"
                )
        return 0

    if args.list_vla_providers:
        from winros.vla import list_vla_providers

        providers = list_vla_providers()
        if console and Table:
            table = Table(title="WinROS VLA Providers")
            table.add_column("Name")
            table.add_column("Description")
            for provider in providers:
                table.add_row(provider.name, provider.description)
            console.print(table)
        else:
            for provider in providers:
                print(f"{provider.name}\t{provider.description}")
        return 0

    if args.vla_provider:
        from winros.vla import VLARequest, get_vla_provider

        if not args.vla_instruction:
            raise ValueError("--vla-provider requires --vla-instruction")
        provider = get_vla_provider(args.vla_provider)
        image_path = Path(args.vla_image) if args.vla_image else None
        command = provider.generate(
            VLARequest(
                instruction=args.vla_instruction,
                robot=args.vla_robot,
                image_path=image_path,
            )
        )
        print(json.dumps(command.to_dict(), indent=2))
        return 0

    if args.train_env:
        from winros.rl.train_sb3 import train_sb3

        summary = train_sb3(
            args.train_env,
            algo=args.algo,
            total_timesteps=args.timesteps,
            load_model=args.load_model,
            device=args.device,
            render_train=args.render_train,
            render_train_freq=args.render_train_freq,
            render_train_steps=args.render_train_steps,
            render_train_episodes=args.render_train_episodes,
            batch_size=args.batch_size,
            gradient_steps=args.gradient_steps,
            num_envs=args.num_envs,
            vec_env=args.vec_env,
        )
        print(
            "Training complete\n"
            f"Env: {summary.env_id}\n"
            f"Algo: {summary.algo}\n"
            f"Timesteps: {summary.total_timesteps}\n"
            f"Saved: {summary.output_path}"
        )
        return 0

    if args.play_model:
        from winros.rl.play_sb3 import play_sb3_model

        if not args.env:
            raise ValueError("--play-model requires --env so the policy knows what to control.")
        summary = play_sb3_model(
            args.env,
            args.play_model,
            algo=args.algo,
            episodes=args.episodes,
            steps=args.steps,
            render=args.render_env,
            realtime=args.realtime or args.render_env,
            device=args.device,
        )
        print(
            "Policy playback complete\n"
            f"Env: {summary.env_id}\n"
            f"Model: {summary.model_path}\n"
            f"Episodes: {summary.episodes}\n"
            f"Total reward: {summary.total_reward:.3f}"
        )
        return 0

    if args.env:
        from winros.envs.rollout import run_random_rollout

        summary = run_random_rollout(
            args.env,
            steps=args.steps,
            episodes=args.episodes,
            render=args.render_env,
            realtime=args.realtime or args.render_env,
        )
        print(
            "Environment rollout complete\n"
            f"Env: {summary.env_id}\n"
            f"Episodes: {summary.episodes}\n"
            f"Steps per episode limit: {summary.steps}\n"
            f"Total reward: {summary.total_reward:.3f}"
        )
        return 0

    if args.asset:
        asset = get_asset(args.asset)
        if asset.expected_model_path is None:
            raise ValueError(f"Asset '{args.asset}' does not define a runnable MJCF model_path.")
        if not asset.expected_model_path.exists():
            raise FileNotFoundError(
                f"Asset '{args.asset}' is not available at {asset.expected_model_path}. "
                "Run scripts\\fetch_open_assets.ps1 first."
            )
        model_path = asset.expected_model_path
    else:
        model_path = resolve_model(robot=args.robot, model=args.model)

    if args.preview_training:
        from winros.training_preview import run_training_preview

        summary = run_training_preview(
            model_path,
            episodes=args.episodes,
            steps_per_episode=args.steps,
            action_scale=args.action_scale,
            action_repeat=args.action_repeat,
            realtime=True,
        )
        print(
            "Training preview complete\n"
            f"Model: {summary.model_path}\n"
            f"Episodes: {summary.episodes}\n"
            f"Steps per episode: {summary.steps_per_episode}\n"
            f"Last episode reward: {summary.last_episode_reward:.3f}"
        )
        return 0

    from winros.mujoco_runner import run_model

    summary = run_model(model_path, steps=args.steps, viewer=args.viewer, realtime=args.realtime)
    lines = [
        "Simulation complete",
        f"Model: {summary.model_path}",
        f"Steps: {summary.steps}",
        f"Sim time: {summary.final_time:.3f}s",
        f"DOF: nq={summary.nq}, nv={summary.nv}, nu={summary.nu}",
        f"Final qpos: {summary.final_qpos}",
    ]
    if console:
        console.print("[bold green]Simulation complete[/bold green]")
        for line in lines[1:]:
            console.print(line)
    else:
        print("\n".join(lines))
    return 0
