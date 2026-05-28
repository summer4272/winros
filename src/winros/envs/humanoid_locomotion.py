from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from winros.asset_registry import get_asset
from winros.envs.base import StepReward, WinROSMujocoEnv


class HumanoidLocomotionEnv(WinROSMujocoEnv):
    def __init__(self, **kwargs) -> None:
        asset = get_asset("unitree_g1_menagerie")
        model_path = kwargs.pop("model_path", asset.expected_model_path)
        if model_path is None:
            raise FileNotFoundError("unitree_g1_menagerie does not define a model path")
        super().__init__(
            Path(model_path),
            frame_skip=kwargs.pop("frame_skip", 5),
            max_episode_steps=kwargs.pop("max_episode_steps", 300),
            action_scale=kwargs.pop("action_scale", 0.04),
            keyframe=kwargs.pop("keyframe", "stand"),
            **kwargs,
        )
        self.command = np.array([0.0, 0.0, 0.0], dtype=float)
        self.pelvis_body_id = self.mujoco.mj_name2id(
            self.model, self.mujoco.mjtObj.mjOBJ_BODY, "pelvis"
        )

    @property
    def extra_observation_size(self) -> int:
        return 3

    def _reset_model(self, options: dict[str, Any]) -> None:
        super()._reset_model(options)
        self.command = np.array(
            [
                float(options.get("vx", self.np_random.uniform(0.0, 0.25))),
                float(options.get("vy", 0.0)),
                float(options.get("yaw_rate", self.np_random.uniform(-0.15, 0.15))),
            ],
            dtype=float,
        )
        self.mujoco.mj_forward(self.model, self.data)

    def _extra_obs(self) -> np.ndarray:
        return self.command.copy()

    def _compute_reward(self) -> StepReward:
        pelvis_height = float(self.data.xpos[self.pelvis_body_id][2])
        root_quat = self.data.qpos[3:7].copy()
        upright = float(root_quat[0] ** 2 - root_quat[1] ** 2 - root_quat[2] ** 2 + root_quat[3] ** 2)
        vx = float(self.data.qvel[0]) if self.data.qvel.size else 0.0
        velocity_error = float((vx - self.command[0]) ** 2)
        height_error = float((pelvis_height - 0.79) ** 2)
        control_cost = 0.0002 * float(np.dot(self.data.ctrl, self.data.ctrl))
        velocity_cost = 0.0005 * float(np.dot(self.data.qvel, self.data.qvel))
        reward = 1.0 + upright - velocity_error - 4.0 * height_error - control_cost - velocity_cost
        terminated = pelvis_height < 0.45 or upright < 0.25

        return StepReward(
            reward=reward,
            terminated=terminated,
            info={
                "task": "humanoid_locomotion",
                "pelvis_height": pelvis_height,
                "upright": upright,
                "command_vx": float(self.command[0]),
                "actual_vx": vx,
                "fallen": terminated,
            },
        )
