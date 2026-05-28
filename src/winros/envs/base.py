from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import sleep
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces


@dataclass(frozen=True)
class StepReward:
    reward: float
    terminated: bool
    info: dict[str, Any]


class WinROSMujocoEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 60}

    def __init__(
        self,
        model_path: str | Path,
        *,
        frame_skip: int = 5,
        max_episode_steps: int = 1000,
        action_scale: float = 1.0,
        render_mode: str | None = None,
        keyframe: str | None = None,
        realtime: bool = False,
    ) -> None:
        self.mujoco = self._load_mujoco()
        self.model_path = Path(model_path).resolve()
        if not self.model_path.exists():
            raise FileNotFoundError(self.model_path)

        self.model = self.mujoco.MjModel.from_xml_path(str(self.model_path))
        self.data = self.mujoco.MjData(self.model)
        self.frame_skip = int(frame_skip)
        self.max_episode_steps = int(max_episode_steps)
        self.action_scale = float(action_scale)
        self.render_mode = render_mode
        self.keyframe = keyframe
        self.realtime = realtime
        self.elapsed_steps = 0
        self._viewer = None
        self._renderer = None

        self.action_space = spaces.Box(-1.0, 1.0, shape=(int(self.model.nu),), dtype=np.float32)
        obs_size = int(self.model.nq + self.model.nv + self.extra_observation_size)
        self.observation_space = spaces.Box(-np.inf, np.inf, shape=(obs_size,), dtype=np.float32)

    @staticmethod
    def _load_mujoco():
        try:
            import mujoco
        except ImportError as exc:
            raise RuntimeError("MuJoCo is not installed in the active Python environment.") from exc
        return mujoco

    @property
    def extra_observation_size(self) -> int:
        return 0

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        super().reset(seed=seed)
        self.elapsed_steps = 0
        self._reset_model(options or {})
        obs = self._get_obs()
        return obs, {"model_path": str(self.model_path)}

    def step(self, action: np.ndarray) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        action = np.asarray(action, dtype=float)
        action = np.clip(action, -1.0, 1.0)
        for _ in range(self.frame_skip):
            self._apply_action(action)
            self.mujoco.mj_step(self.model, self.data)

        self.elapsed_steps += 1
        step_reward = self._compute_reward()
        truncated = self.elapsed_steps >= self.max_episode_steps
        obs = self._get_obs()

        if self.render_mode == "human":
            self.render()
            if self.realtime:
                sleep(float(self.model.opt.timestep) * self.frame_skip)

        return obs, step_reward.reward, step_reward.terminated, truncated, step_reward.info

    def render(self):
        if self.render_mode == "human":
            if self._viewer is None:
                import mujoco.viewer

                self._viewer = mujoco.viewer.launch_passive(self.model, self.data)
            self._viewer.sync()
            return None

        if self.render_mode == "rgb_array":
            if self._renderer is None:
                self._renderer = self.mujoco.Renderer(self.model)
            self._renderer.update_scene(self.data)
            return self._renderer.render()

        return None

    def close(self) -> None:
        if self._viewer is not None:
            self._viewer.close()
            self._viewer = None
        if self._renderer is not None:
            self._renderer.close()
            self._renderer = None

    def _reset_model(self, options: dict[str, Any]) -> None:
        key_id = -1
        if self.keyframe:
            key_id = self.mujoco.mj_name2id(self.model, self.mujoco.mjtObj.mjOBJ_KEY, self.keyframe)
        if key_id >= 0:
            self.mujoco.mj_resetDataKeyframe(self.model, self.data, key_id)
        else:
            self.mujoco.mj_resetData(self.model, self.data)
        self.mujoco.mj_forward(self.model, self.data)

    def _get_obs(self) -> np.ndarray:
        parts = [self.data.qpos.copy(), self.data.qvel.copy(), self._extra_obs()]
        return np.concatenate(parts).astype(np.float32)

    def _extra_obs(self) -> np.ndarray:
        return np.zeros(0, dtype=np.float32)

    def _apply_action(self, action: np.ndarray) -> None:
        if self.model.nu == 0:
            return

        for index in range(int(self.model.nu)):
            raw = float(action[index]) * self.action_scale
            if bool(self.model.actuator_ctrllimited[index]):
                low, high = self.model.actuator_ctrlrange[index]
                center = 0.5 * (float(low) + float(high))
                half_span = 0.5 * (float(high) - float(low))
                self.data.ctrl[index] = center + raw * half_span
            else:
                self.data.ctrl[index] = raw

    def _body_pos(self, name: str) -> np.ndarray:
        body_id = self.mujoco.mj_name2id(self.model, self.mujoco.mjtObj.mjOBJ_BODY, name)
        if body_id < 0:
            raise ValueError(f"Body '{name}' was not found in {self.model_path}")
        return self.data.xpos[body_id].copy()

    def _compute_reward(self) -> StepReward:
        control_cost = 0.001 * float(np.dot(self.data.ctrl, self.data.ctrl)) if self.model.nu else 0.0
        velocity_cost = 0.001 * float(np.dot(self.data.qvel, self.data.qvel))
        return StepReward(reward=0.01 - control_cost - velocity_cost, terminated=False, info={})
