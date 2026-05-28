from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from winros.asset_registry import get_asset
from winros.envs.base import StepReward, WinROSMujocoEnv


class QuadrupedLocomotionEnv(WinROSMujocoEnv):
    def __init__(self, **kwargs) -> None:
        asset = get_asset("unitree_go2_menagerie")
        model_path = kwargs.pop("model_path", asset.expected_model_path)
        if model_path is None:
            raise FileNotFoundError("unitree_go2_menagerie does not define a model path")
        super().__init__(
            Path(model_path),
            frame_skip=kwargs.pop("frame_skip", 5),
            max_episode_steps=kwargs.pop("max_episode_steps", 300),
            action_scale=kwargs.pop("action_scale", 0.08),
            keyframe=kwargs.pop("keyframe", "home"),
            **kwargs,
        )
        self.command = np.array([0.5, 0.0, 0.0], dtype=float)
        self.base_body_id = self.mujoco.mj_name2id(self.model, self.mujoco.mjtObj.mjOBJ_BODY, "base")

    @property
    def extra_observation_size(self) -> int:
        return 3

    def _reset_model(self, options: dict[str, Any]) -> None:
        super()._reset_model(options)
        self.command = np.array(
            [
                float(options.get("vx", self.np_random.uniform(0.2, 0.7))),
                float(options.get("vy", 0.0)),
                float(options.get("yaw_rate", self.np_random.uniform(-0.3, 0.3))),
            ],
            dtype=float,
        )
        self.mujoco.mj_forward(self.model, self.data)

    def _extra_obs(self) -> np.ndarray:
        return self.command.copy()

    def _compute_reward(self) -> StepReward:
        base_height = float(self.data.xpos[self.base_body_id][2])
        linear_velocity = self.data.qvel[:3].copy()
        yaw_rate = float(self.data.qvel[5]) if self.data.qvel.size > 5 else 0.0
        velocity_error = float((linear_velocity[0] - self.command[0]) ** 2)
        yaw_error = float((yaw_rate - self.command[2]) ** 2)
        height_error = float((base_height - 0.32) ** 2)
        control_cost = 0.0005 * float(np.dot(self.data.ctrl, self.data.ctrl))
        reward = 1.0 - velocity_error - 0.25 * yaw_error - 2.0 * height_error - control_cost
        terminated = base_height < 0.18

        return StepReward(
            reward=reward,
            terminated=terminated,
            info={
                "task": "quadruped_locomotion",
                "base_height": base_height,
                "command_vx": float(self.command[0]),
                "actual_vx": float(linear_velocity[0]),
                "fallen": terminated,
            },
        )
