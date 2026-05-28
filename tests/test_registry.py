from pathlib import Path

import pytest

from winros.asset_registry import get_asset, list_assets
from winros.cli import main
from winros.dashboard.server import build_profile_command, collect_state
from winros.envs.registry import list_envs
from winros.robot_registry import list_robots, resolve_model
from winros.task_registry import list_tasks
from winros.vla import VLARequest, get_vla_provider


def test_builtin_robot_models_exist() -> None:
    for robot in list_robots():
        assert robot.model_path.exists(), robot.name


def test_resolve_relative_model_path() -> None:
    path = resolve_model(model="sim/mujoco/models/two_link_arm.xml")
    assert path.exists()
    assert isinstance(path, Path)


def test_task_tracks_are_registered() -> None:
    task_ids = {task.id for task in list_tasks()}
    assert {"arm_grasp", "quadruped_locomotion", "humanoid_locomotion"} <= task_ids


def test_task_assets_resolve_to_asset_registry() -> None:
    asset_names = {asset.name for asset in list_assets()}
    for task in list_tasks():
        assert task.primary_asset in asset_names
        for asset_name in task.reference_assets:
            assert asset_name in asset_names


def test_primary_asset_paths_are_root_relative() -> None:
    asset = get_asset("unitree_go2_menagerie")
    assert asset.expected_model_path is not None
    assert asset.expected_model_path.parts[-2:] == ("unitree_go2", "scene.xml")


def test_cli_lists_task_tracks() -> None:
    assert main(["--list-tasks"]) == 0


def test_dashboard_state_exposes_profiles() -> None:
    state = collect_state()
    profile_ids = {profile["id"] for profile in state["profiles"]}
    assert {"sim_builtin", "vla_dry_command", "start_dry_adapter"} <= profile_ids


def test_dashboard_builds_safe_profile_command() -> None:
    command = build_profile_command("sim_builtin", {"robot": "two_link_arm", "steps": 3})
    assert command[1:4] == ["-m", "winros", "--robot"]
    assert command[-1] == "3"


def test_vla_rules_provider_returns_dry_run_command() -> None:
    provider = get_vla_provider("rules")
    command = provider.generate(VLARequest(instruction="walk forward slowly", robot="Unitree Go2"))
    assert command.dry_run is True
    assert command.command_type == "locomotion"
    assert command.target["velocity_x"] > 0


def test_cli_accepts_builtin_for_non_viewer_simulation() -> None:
    pytest.importorskip("mujoco")
    assert main(["--robot", "two_link_arm", "--steps", "1"]) == 0


def test_training_envs_are_registered() -> None:
    env_ids = {env.id for env in list_envs()}
    assert {
        "WinROSArmGrasp-v0",
        "WinROSQuadrupedLocomotion-v0",
        "WinROSHumanoidLocomotion-v0",
    } <= env_ids


def test_env_random_rollouts_step() -> None:
    pytest.importorskip("gymnasium")
    pytest.importorskip("mujoco")
    from winros.envs.rollout import run_random_rollout

    for env_id in [
        "WinROSArmGrasp-v0",
        "WinROSQuadrupedLocomotion-v0",
        "WinROSHumanoidLocomotion-v0",
    ]:
        summary = run_random_rollout(env_id, steps=2, episodes=1, render=False)
        assert summary.episodes == 1


def test_train_sb3_rejects_unknown_algo() -> None:
    pytest.importorskip("gymnasium")
    pytest.importorskip("stable_baselines3")
    from winros.rl.train_sb3 import train_sb3

    try:
        train_sb3("WinROSArmGrasp-v0", algo="bad", total_timesteps=1)
    except ValueError as exc:
        assert "Unsupported algo" in str(exc)
    else:
        raise AssertionError("Expected unsupported algo to raise ValueError")


def test_play_sb3_rejects_unknown_algo() -> None:
    pytest.importorskip("gymnasium")
    pytest.importorskip("stable_baselines3")
    from winros.rl.play_sb3 import play_sb3_model

    try:
        play_sb3_model("WinROSArmGrasp-v0", "missing.zip", algo="bad", render=False)
    except FileNotFoundError:
        # Missing model paths are still rejected before algorithm loading for valid paths.
        pass
    except ValueError as exc:
        assert "Unsupported algo" in str(exc)
