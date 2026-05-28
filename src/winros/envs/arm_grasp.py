from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from gymnasium import spaces

from winros.asset_registry import get_asset
from winros.envs.base import StepReward, WinROSMujocoEnv


WORKCELL_XML = """<mujoco model="winros franka pick place">
  <include file="panda.xml"/>

  <statistic center="0.45 0 0.45" extent="1.2"/>

  <visual>
    <headlight diffuse="0.6 0.6 0.6" ambient="0.3 0.3 0.3" specular="0 0 0"/>
    <rgba haze="0.15 0.25 0.35 1"/>
    <global azimuth="130" elevation="-25"/>
  </visual>

  <asset>
    <texture type="skybox" builtin="gradient" rgb1="0.3 0.5 0.7" rgb2="0 0 0" width="512" height="3072"/>
    <texture type="2d" name="groundplane" builtin="checker" mark="edge" rgb1="0.22 0.28 0.32" rgb2="0.12 0.16 0.18"
      markrgb="0.8 0.8 0.8" width="300" height="300"/>
    <material name="groundplane" texture="groundplane" texuniform="true" texrepeat="5 5" reflectance="0.2"/>
    <material name="table_mat" rgba="0.45 0.45 0.42 1"/>
    <material name="cube_mat" rgba="0.1 0.45 0.85 1"/>
    <material name="target_mat" rgba="0.2 0.9 0.35 0.35"/>
  </asset>

  <worldbody>
    <light pos="0 0 1.8" dir="0 0 -1" directional="true"/>
    <geom name="floor" size="0 0 0.05" type="plane" material="groundplane"/>

    <body name="table" pos="0.55 0 0.2">
      <geom name="table_top" type="box" size="0.35 0.35 0.025" material="table_mat"/>
    </body>

    <body name="object_cube" pos="0.48 0.0 0.255">
      <freejoint name="object_cube_joint"/>
      <geom name="object_cube_geom" type="box" size="0.025 0.025 0.025" mass="0.05" material="cube_mat"
        condim="4" friction="1.2 0.01 0.0001"/>
    </body>

    <body name="target" pos="0.62 0.12 0.285">
      <geom name="target_marker" type="sphere" size="0.035" material="target_mat" contype="0" conaffinity="0"/>
    </body>
  </worldbody>
</mujoco>
"""


def ensure_franka_workcell() -> Path:
    asset = get_asset("franka_panda_menagerie")
    panda_scene = asset.expected_model_path
    if panda_scene is None:
        raise FileNotFoundError("franka_panda_menagerie does not define a model path")
    panda_dir = panda_scene.parent
    if not (panda_dir / "panda.xml").exists():
        raise FileNotFoundError(panda_dir / "panda.xml")

    workcell_path = panda_dir / "winros_pick_place.xml"
    if not workcell_path.exists() or workcell_path.read_text(encoding="utf-8") != WORKCELL_XML:
        workcell_path.write_text(WORKCELL_XML, encoding="utf-8")
    return workcell_path


class ArmGraspEnv(WinROSMujocoEnv):
    """
    Franka Panda 机械臂抓取 / 抬升 / 放置环境。

    改进重点：
    1. 修正 place 阶段目标高度，避免让方块中心去追一个悬空目标点；
    2. 增加夹爪中心、夹爪开合、方块速度、目标 XY 误差、上一时刻动作等观测；
    3. 使用阶段式 dense reward，把 reach、grasp、lift、place 分开；
    4. 方块跑飞或掉落时直接终止 episode，减少无效采样；
    5. 不再硬编码夹爪控制范围 0~255，而是自动读取 actuator ctrlrange。
    """

    TABLE_TOP_Z = 0.225
    CUBE_HALF_SIZE = 0.025
    CUBE_REST_Z = 0.255
    TARGET_MARKER_Z = 0.285

    def __init__(self, **kwargs) -> None:
        model_path = kwargs.pop("model_path", ensure_franka_workcell())
        self.task_stage = str(kwargs.pop("task_stage", "place"))

        # control_mode:
        # - cartesian: RL controls end-effector dx/dy/dz + gripper. IK converts it to legal joint targets.
        # - joint: legacy mode; RL directly controls 7 joint increments + gripper.
        self.control_mode = str(kwargs.pop("control_mode", "cartesian"))

        # 关节增量不要太大，否则初期随机策略会疯狂撞桌子、推飞方块。
        self.joint_delta_scale = float(kwargs.pop("joint_delta_scale", 0.025))
        self.cartesian_delta_scale = float(kwargs.pop("cartesian_delta_scale", 0.025))
        self.cartesian_joint_step_limit = float(kwargs.pop("cartesian_joint_step_limit", 0.045))
        self.ik_damping = float(kwargs.pop("ik_damping", 0.08))
        self.gripper_smoothing = float(kwargs.pop("gripper_smoothing", 0.45))

        # 课程学习 / 任务参数
        self.cube_random_span = float(
            kwargs.pop("cube_random_span", 0.02 if self.task_stage == "reach" else 0.035)
        )
        self.target_random_span = float(kwargs.pop("target_random_span", 0.025))
        self.success_hold_required = int(kwargs.pop("success_hold_required", 3))
        self.target_success_radius = float(kwargs.pop("target_success_radius", 0.045))
        self.lift_success_height = float(kwargs.pop("lift_success_height", 0.055))
        self.require_release_for_place = bool(kwargs.pop("require_release_for_place", False))
        self.pre_lift_push_limit = float(kwargs.pop("pre_lift_push_limit", 0.12))
        self.pre_lift_push_penalty_scale = float(kwargs.pop("pre_lift_push_penalty_scale", 14.0))
        self.tune_grasp_physics = bool(kwargs.pop("tune_grasp_physics", True))

        # 前期建议 False，等 nominal 环境能稳定成功后再打开。
        self.domain_randomization = bool(kwargs.pop("domain_randomization", False))

        # 注意：base class 可能在 __init__ 期间查询 observation size。
        # 所以这里提前固定，不依赖 self.model。
        self._extra_obs_size = 35

        default_episode_steps = (
            240 if self.task_stage == "reach"
            else 180 if self.task_stage == "lift"
            else 280
        )

        super().__init__(
            Path(model_path),
            frame_skip=kwargs.pop("frame_skip", 5),
            max_episode_steps=kwargs.pop("max_episode_steps", default_episode_steps),
            action_scale=kwargs.pop("action_scale", 1.0),
            keyframe=kwargs.pop("keyframe", "home"),
            **kwargs,
        )

        if self.control_mode == "cartesian":
            self.action_space = spaces.Box(-1.0, 1.0, shape=(4,), dtype=np.float32)
        elif self.control_mode != "joint":
            raise ValueError("control_mode must be 'cartesian' or 'joint'.")

        self.cube_body_id = self.mujoco.mj_name2id(
            self.model, self.mujoco.mjtObj.mjOBJ_BODY, "object_cube"
        )
        self.target_body_id = self.mujoco.mj_name2id(
            self.model, self.mujoco.mjtObj.mjOBJ_BODY, "target"
        )
        self.hand_body_id = self.mujoco.mj_name2id(
            self.model, self.mujoco.mjtObj.mjOBJ_BODY, "hand"
        )
        self.left_finger_body_id = self.mujoco.mj_name2id(
            self.model, self.mujoco.mjtObj.mjOBJ_BODY, "left_finger"
        )
        self.right_finger_body_id = self.mujoco.mj_name2id(
            self.model, self.mujoco.mjtObj.mjOBJ_BODY, "right_finger"
        )
        self.cube_joint_id = self.mujoco.mj_name2id(
            self.model, self.mujoco.mjtObj.mjOBJ_JOINT, "object_cube_joint"
        )
        self.cube_geom_id = self.mujoco.mj_name2id(
            self.model, self.mujoco.mjtObj.mjOBJ_GEOM, "object_cube_geom"
        )
        self.table_geom_id = self.mujoco.mj_name2id(
            self.model, self.mujoco.mjtObj.mjOBJ_GEOM, "table_top"
        )
        self.finger_collision_geom_ids = [
            geom_id
            for geom_id in range(int(self.model.ngeom))
            if int(self.model.geom_bodyid[geom_id]) in {self.left_finger_body_id, self.right_finger_body_id}
            and int(self.model.geom_contype[geom_id]) != 0
        ]

        self.target_pos = np.array([0.62, 0.12, self.CUBE_REST_Z], dtype=float)
        self.initial_cube_pos = np.array([0.48, 0.0, self.CUBE_REST_Z], dtype=float)
        self.initial_cube_target_dist_xy = float(
            np.linalg.norm(self.initial_cube_pos[:2] - self.target_pos[:2])
        )
        self.arm_ctrl_target = np.zeros(7, dtype=float)
        self.home_arm_qpos = np.asarray(self.model.key_qpos[0, :7], dtype=float).copy()
        self.ee_target_pos = np.zeros(3, dtype=float)
        self.last_action = np.zeros(int(self.model.nu), dtype=float)
        self.success_hold = 0
        self._configure_grasp_physics()

    @property
    def extra_observation_size(self) -> int:
        return self._extra_obs_size

    def _reset_model(self, options: dict[str, Any]) -> None:
        super()._reset_model(options)
        rng = self.np_random
        self._configure_grasp_physics()

        if self.domain_randomization:
            # 轻量 domain randomization。
            # 前期不要范围太大，否则 RL 还没学会基本抓取就被扰动搞崩。
            self.model.geom_friction[self.cube_geom_id, 0] = rng.uniform(0.8, 1.6)
            self.model.geom_friction[self.table_geom_id, 0] = rng.uniform(0.8, 1.4)
            self.model.body_mass[self.cube_body_id] = rng.uniform(0.035, 0.075)

        cube_xy = np.array([0.48, 0.0], dtype=float) + rng.uniform(
            [-self.cube_random_span, -self.cube_random_span],
            [self.cube_random_span, self.cube_random_span],
        )

        target_xy = np.array([0.58, 0.08], dtype=float) + rng.uniform(
            [-self.target_random_span, -self.target_random_span],
            [self.target_random_span, self.target_random_span],
        )

        self.initial_cube_pos = np.array(
            [cube_xy[0], cube_xy[1], self.CUBE_REST_Z],
            dtype=float,
        )

        # 重点：
        # reward 目标使用方块在桌面上稳定放置时的中心高度 CUBE_REST_Z。
        # marker 可以画高一点，仅用于可视化。
        self.target_pos = np.array(
            [target_xy[0], target_xy[1], self.CUBE_REST_Z],
            dtype=float,
        )
        self.initial_cube_target_dist_xy = float(
            np.linalg.norm(self.initial_cube_pos[:2] - self.target_pos[:2])
        )

        qpos_addr = int(self.model.jnt_qposadr[self.cube_joint_id])
        self.data.qpos[qpos_addr: qpos_addr + 7] = np.array(
            [cube_xy[0], cube_xy[1], self.CUBE_REST_Z, 1.0, 0.0, 0.0, 0.0],
            dtype=float,
        )

        self.model.body_pos[self.target_body_id] = np.array(
            [target_xy[0], target_xy[1], self.TARGET_MARKER_Z],
            dtype=float,
        )

        self.data.ctrl[:] = self.model.key_ctrl[0]
        self.arm_ctrl_target = self.data.ctrl[:7].copy()
        self.last_action = np.zeros(int(self.model.nu), dtype=float)
        self.success_hold = 0

        self.mujoco.mj_forward(self.model, self.data)
        self.ee_target_pos = self._clamp_ee_target(self._pinch_center())

    def _configure_grasp_physics(self) -> None:
        if not self.tune_grasp_physics:
            return
        self.model.geom_friction[self.cube_geom_id] = np.array([3.0, 0.08, 0.003], dtype=float)
        self.model.geom_condim[self.cube_geom_id] = 4
        self.model.body_mass[self.cube_body_id] = 0.025
        for geom_id in self.finger_collision_geom_ids:
            self.model.geom_friction[geom_id] = np.array([3.0, 0.08, 0.003], dtype=float)
            self.model.geom_condim[geom_id] = 4

    def _ctrl_open_close(self) -> tuple[float, float]:
        """
        返回夹爪 fully open 和 fully close 对应的控制量。

        原代码默认 0~255，但不同模型的 actuator ctrlrange 不一定一样。
        这里直接从 MuJoCo model 里读取。
        """
        if self.model.nu < 8:
            return 1.0, 0.0

        low, high = self.model.actuator_ctrlrange[7]
        open_ctrl = float(high)
        close_ctrl = float(low)
        return open_ctrl, close_ctrl

    def _gripper_open_fraction(self) -> float:
        """
        返回夹爪打开比例：
        1.0 表示完全打开；
        0.0 表示完全闭合。
        """
        if self.model.nu < 8:
            return 1.0

        open_ctrl, close_ctrl = self._ctrl_open_close()
        denom = max(abs(open_ctrl - close_ctrl), 1e-6)

        return float(
            np.clip(
                (float(self.data.ctrl[7]) - close_ctrl) / denom,
                0.0,
                1.0,
            )
        )

    def _apply_action(self, action: np.ndarray) -> None:
        action = np.asarray(action, dtype=float).reshape(-1)
        raw_action = np.clip(action, -1.0, 1.0)
        expected = int(self.model.nu)
        self.last_action = np.pad(
            raw_action,
            (0, max(0, expected - raw_action.size)),
        )[:expected].copy()

        if self.model.nu < 8:
            super()._apply_action(raw_action)
            return

        if self.control_mode == "cartesian":
            self._apply_cartesian_arm_action(raw_action)
            gripper_action_index = 3
        else:
            joint_action = np.pad(raw_action, (0, max(0, 8 - raw_action.size)))[:8]
            # 前 7 维控制机械臂关节位置增量。
            for index in range(7):
                low, high = self.model.actuator_ctrlrange[index]

                self.arm_ctrl_target[index] = np.clip(
                    self.arm_ctrl_target[index] + float(joint_action[index]) * self.joint_delta_scale,
                    float(low),
                    float(high),
                )

                self.data.ctrl[index] = self.arm_ctrl_target[index]
            gripper_action_index = 7

        open_ctrl, close_ctrl = self._ctrl_open_close()

        if self.task_stage == "reach":
            # reach 阶段只训练靠近方块，夹爪保持打开，减少任务难度。
            gripper_target = open_ctrl
        else:
            # cartesian: action[3] = gripper; joint legacy: action[7] = gripper.
            # +1 表示完全打开；-1 表示完全闭合。
            gripper_action = (
                float(raw_action[gripper_action_index])
                if raw_action.size > gripper_action_index
                else 1.0
            )
            gripper_open_fraction = 0.5 * (gripper_action + 1.0)
            gripper_target = close_ctrl + gripper_open_fraction * (open_ctrl - close_ctrl)

        self.data.ctrl[7] = (
            (1.0 - self.gripper_smoothing) * float(self.data.ctrl[7])
            + self.gripper_smoothing * gripper_target
        )

    def _apply_cartesian_arm_action(self, action: np.ndarray) -> None:
        cartesian_action = np.pad(action, (0, max(0, 3 - action.size)))[:3]
        # Velocity-style Cartesian control. The action means "move by this much in
        # this substep", so the target cannot drift far ahead of the physical arm.
        delta = cartesian_action * (self.cartesian_delta_scale / max(1, self.frame_skip))
        current_pos = self._pinch_center()
        self.ee_target_pos = self._clamp_ee_target(current_pos + delta)

        jac_arm = self._pinch_center_jacobian()[:, :7]
        pos_error = np.clip(self.ee_target_pos - current_pos, -0.02, 0.02)

        damping_eye = (self.ik_damping ** 2) * np.eye(3)
        dq_task = jac_arm.T @ np.linalg.solve(jac_arm @ jac_arm.T + damping_eye, pos_error)

        # Null-space posture pull keeps the arm away from strange IK poses while preserving task motion.
        q_current = self.data.qpos[:7].copy()
        posture_error = self.home_arm_qpos - q_current
        pseudo_inv = jac_arm.T @ np.linalg.solve(jac_arm @ jac_arm.T + damping_eye, np.eye(3))
        null_projector = np.eye(7) - pseudo_inv @ jac_arm
        dq_posture = 0.08 * (null_projector @ posture_error)

        dq = np.clip(
            dq_task + dq_posture,
            -self.cartesian_joint_step_limit,
            self.cartesian_joint_step_limit,
        )

        for index in range(7):
            low, high = self.model.actuator_ctrlrange[index]
            self.arm_ctrl_target[index] = np.clip(
                q_current[index] + dq[index],
                float(low),
                float(high),
            )
            self.data.ctrl[index] = self.arm_ctrl_target[index]

    def _clamp_ee_target(self, target: np.ndarray) -> np.ndarray:
        # Workspace chosen around the table and cube. This prevents IK from asking for
        # physically unreachable or table-penetrating poses.
        low = np.array([0.32, -0.28, self.CUBE_REST_Z + 0.025], dtype=float)
        high = np.array([0.76, 0.28, 0.56], dtype=float)
        return np.clip(np.asarray(target, dtype=float), low, high)

    def _pinch_center_jacobian(self) -> np.ndarray:
        jac_left_pos = np.zeros((3, int(self.model.nv)), dtype=float)
        jac_left_rot = np.zeros((3, int(self.model.nv)), dtype=float)
        jac_right_pos = np.zeros((3, int(self.model.nv)), dtype=float)
        jac_right_rot = np.zeros((3, int(self.model.nv)), dtype=float)
        self.mujoco.mj_jacBody(
            self.model,
            self.data,
            jac_left_pos,
            jac_left_rot,
            self.left_finger_body_id,
        )
        self.mujoco.mj_jacBody(
            self.model,
            self.data,
            jac_right_pos,
            jac_right_rot,
            self.right_finger_body_id,
        )
        return 0.5 * (jac_left_pos + jac_right_pos)

    def _pinch_center(self) -> np.ndarray:
        left_finger_pos = self.data.xpos[self.left_finger_body_id]
        right_finger_pos = self.data.xpos[self.right_finger_body_id]
        return 0.5 * (left_finger_pos + right_finger_pos)

    def _pregrasp_pos(self, cube_pos: np.ndarray) -> np.ndarray:
        return np.array(
            [
                float(cube_pos[0]),
                float(cube_pos[1]),
                self.CUBE_REST_Z + 0.045,
            ],
            dtype=float,
        )

    def _extra_obs(self) -> np.ndarray:
        pinch_center = self._pinch_center()
        cube_pos = self.data.xpos[self.cube_body_id]

        # cvel: body spatial velocity。
        # 后 3 维一般对应线速度部分。
        cube_vel = self.data.cvel[self.cube_body_id, 3:6]

        gripper_open = self._gripper_open_fraction()
        lift_height = max(0.0, float(cube_pos[2]) - self.CUBE_REST_Z)
        xy_target_dist = float(np.linalg.norm(cube_pos[:2] - self.target_pos[:2]))
        pregrasp_pos = self._pregrasp_pos(cube_pos)
        pregrasp_error = pregrasp_pos - pinch_center

        last_action_obs = np.pad(
            self.last_action[:8],
            (0, max(0, 8 - self.last_action[:8].size)),
        )[:8]

        obs = np.concatenate(
            [
                pinch_center,                              # 3
                cube_pos,                                  # 3
                self.target_pos,                           # 3
                cube_pos - pinch_center,                   # 3
                pregrasp_error,                            # 3
                self.target_pos - cube_pos,                # 3
                cube_vel,                                  # 3
                np.array(
                    [
                        gripper_open,
                        lift_height,
                        xy_target_dist,
                        float(np.linalg.norm(pregrasp_error)),
                        float(np.linalg.norm(pregrasp_error[:2])),
                        abs(float(pregrasp_error[2])),
                    ],
                    dtype=float,
                ),                                        # 6
                last_action_obs,                           # 8
            ]
        ).astype(np.float32)

        return obs

    def _compute_reward(self) -> StepReward:
        hand_pos = self.data.xpos[self.hand_body_id]
        cube_pos = self.data.xpos[self.cube_body_id]
        left_finger_pos = self.data.xpos[self.left_finger_body_id]
        right_finger_pos = self.data.xpos[self.right_finger_body_id]

        pinch_center = 0.5 * (left_finger_pos + right_finger_pos)
        ee_target_error = float(np.linalg.norm(self.ee_target_pos - pinch_center))
        pregrasp_pos = self._pregrasp_pos(cube_pos)
        pregrasp_dist = float(np.linalg.norm(pinch_center - pregrasp_pos))
        pregrasp_xy_dist = float(np.linalg.norm(pinch_center[:2] - pregrasp_pos[:2]))
        pregrasp_z_error = abs(float(pinch_center[2] - pregrasp_pos[2]))

        hand_cube_dist = float(np.linalg.norm(hand_pos - cube_pos))
        pinch_cube_dist = float(np.linalg.norm(pinch_center - cube_pos))

        left_cube_dist = float(np.linalg.norm(left_finger_pos - cube_pos))
        right_cube_dist = float(np.linalg.norm(right_finger_pos - cube_pos))
        finger_cube_dist = 0.5 * (left_cube_dist + right_cube_dist)

        cube_target_dist_3d = float(np.linalg.norm(cube_pos - self.target_pos))
        cube_target_dist_xy = float(np.linalg.norm(cube_pos[:2] - self.target_pos[:2]))

        cube_displacement = float(np.linalg.norm(cube_pos[:2] - self.initial_cube_pos[:2]))
        cube_height = float(cube_pos[2])
        lift_height = max(0.0, cube_height - self.CUBE_REST_Z)

        cube_out_of_bounds = (
            cube_displacement > 0.24
            or cube_height < 0.18
            or cube_height > 0.65
        )

        gripper_open = self._gripper_open_fraction()
        gripper_closed = float(np.clip(1.0 - gripper_open, 0.0, 1.0))

        near_cube = pinch_cube_dist < 0.075
        centered_grasp = (
            pinch_cube_dist < 0.055
            and finger_cube_dist < 0.080
        )
        grasp_candidate = (
            centered_grasp
            and gripper_closed > 0.65
        )

        reached = (
            pregrasp_dist < 0.065
            and pregrasp_xy_dist < 0.055
            and pregrasp_z_error < 0.055
            and cube_displacement < 0.085
        )

        lifted = cube_height > self.CUBE_REST_Z + self.lift_success_height
        pre_lift_cube_motion = 0.0 if lifted else cube_displacement
        target_progress_without_lift = (
            max(0.0, self.initial_cube_target_dist_xy - cube_target_dist_xy)
            if not lifted
            else 0.0
        )
        premature_push = (
            not lifted
            and cube_displacement > self.pre_lift_push_limit
        )

        carried_to_target = (
            lifted
            and cube_target_dist_xy < self.target_success_radius
        )

        released_on_target = (
            cube_target_dist_xy < self.target_success_radius
            and cube_height < self.CUBE_REST_Z + 0.035
            and gripper_open > 0.55
        )

        if self.require_release_for_place:
            placed = released_on_target
        else:
            # 前期不强制 release，先让策略学会“抓起并搬到目标点”。
            placed = carried_to_target

        # -----------------------------
        # Dense reward shaping
        # -----------------------------

        # 1. Reach means moving the pinch center to a pre-grasp point above the cube.
        reach_reward = 8.0 * np.exp(-12.0 * pregrasp_dist)

        # 2. 两个 finger 都靠近方块，而不是只让 hand body 靠近
        finger_align_reward = 2.0 * np.exp(-10.0 * pregrasp_xy_dist)

        # 3. 离方块远时鼓励夹爪打开，避免一路闭着夹爪乱戳
        open_before_contact_reward = (
            0.8 * gripper_open
            if pinch_cube_dist > 0.09
            else 0.0
        )

        # 4. 只有方块真的在两指中间时，闭合夹爪才奖励。
        close_near_cube_reward = (
            2.0 * gripper_closed
            if centered_grasp
            else 0.0
        )

        grasp_bonus = 5.0 if grasp_candidate else 0.0

        # 5. 离方块远还闭合，强扣分，避免学成“闭爪推方块”。
        close_far_penalty = (
            2.5 * gripper_closed
            if pinch_cube_dist > 0.09
            else 0.0
        )

        # 6. 抬升奖励：只有可能抓住后，或者已经有一点抬升时才给
        lift_reward = (
            32.0 * np.clip(lift_height / 0.085, 0.0, 1.0)
            if grasp_candidate or lift_height > 0.005
            else 0.0
        )

        # 7. 放置奖励：只有 lifted 后才开始鼓励去目标点
        xy_place_reward = (
            10.0 * np.exp(-16.0 * cube_target_dist_xy)
            if lifted
            else 0.0
        )

        # 8. 搬运时保持合适高度
        carry_height_reward = (
            1.5 * np.exp(-30.0 * abs(lift_height - 0.075))
            if lifted
            else 0.0
        )

        # 9. 如果要求 release，则成功释放时给奖励
        release_reward = (
            3.0 * gripper_open
            if self.require_release_for_place and released_on_target
            else 0.0
        )

        progress_reward = 0.5 * np.exp(-7.0 * hand_cube_dist)
        push_without_lift_penalty = self.pre_lift_push_penalty_scale * pre_lift_cube_motion
        target_push_penalty = 18.0 * target_progress_without_lift

        action_cost = 0.003 * float(np.dot(self.last_action, self.last_action))
        action_smooth_cost = 0.001 * float(np.linalg.norm(self.last_action[:7]))
        velocity_cost = 0.00015 * float(np.dot(self.data.qvel, self.data.qvel))

        if self.task_stage == "reach":
            step_success = reached

            reward = (
                reach_reward
                + finger_align_reward
                + open_before_contact_reward
                + progress_reward
                - 2.0 * pregrasp_dist
                - 6.0 * cube_displacement
                - close_far_penalty
                - action_cost
                - velocity_cost
            )

            if reached:
                reward += 12.0

        elif self.task_stage == "lift":
            step_success = lifted

            reward = (
                reach_reward
                + finger_align_reward
                + close_near_cube_reward
                + grasp_bonus
                + lift_reward
                + progress_reward
                - push_without_lift_penalty
                - target_push_penalty
                - close_far_penalty
                - action_cost
                - action_smooth_cost
                - velocity_cost
            )

            if lifted:
                reward += 55.0

        else:
            step_success = placed

            # place 必须先学成 lift；抬起前只给少量靠近奖励，推着方块去目标点会被扣分。
            pre_lift_shaping = (
                0.45 * reach_reward
                + 0.65 * finger_align_reward
                + close_near_cube_reward
                + 0.35 * progress_reward
            )

            reward = (
                pre_lift_shaping
                + grasp_bonus
                + lift_reward
                + xy_place_reward
                + carry_height_reward
                + release_reward
                - 0.25 * cube_target_dist_3d
                - push_without_lift_penalty
                - target_push_penalty
                - close_far_penalty
                - action_cost
                - action_smooth_cost
                - velocity_cost
            )

            if lifted:
                reward += 22.0

            if placed:
                reward += 85.0

        if self.task_stage in {"lift", "place"} and premature_push:
            reward -= 35.0
            step_success = False

        if cube_out_of_bounds:
            reward -= 30.0
            step_success = False

        # 连续若干 step 满足成功条件才算真正成功，避免偶然碰到目标点。
        if step_success:
            self.success_hold += 1
        else:
            self.success_hold = 0

        success = self.success_hold >= self.success_hold_required

        if success:
            reward += 25.0

        # 成功或者明显失败都终止 episode。
        terminated = bool(
            success
            or cube_out_of_bounds
            or (self.task_stage in {"lift", "place"} and premature_push)
        )

        return StepReward(
            reward=float(reward),
            terminated=terminated,
            info={
                "task": "arm_grasp",
                "stage": self.task_stage,
                "control_mode": self.control_mode,

                "hand_cube_dist": hand_cube_dist,
                "pinch_cube_dist": pinch_cube_dist,
                "finger_cube_dist": finger_cube_dist,
                "pregrasp_dist": pregrasp_dist,
                "pregrasp_xy_dist": pregrasp_xy_dist,
                "pregrasp_z_error": pregrasp_z_error,
                "ee_target_error": ee_target_error,

                "cube_target_dist_3d": cube_target_dist_3d,
                "cube_target_dist_xy": cube_target_dist_xy,
                "cube_displacement": cube_displacement,
                "pre_lift_cube_motion": pre_lift_cube_motion,
                "target_progress_without_lift": target_progress_without_lift,
                "premature_push": premature_push,
                "cube_height": cube_height,
                "lift_height": lift_height,

                "cube_out_of_bounds": cube_out_of_bounds,

                "reached": reached,
                "lifted": lifted,
                "carried_to_target": carried_to_target,
                "released_on_target": released_on_target,

                "gripper_open": gripper_open,
                "gripper_closed": gripper_closed,
                "centered_grasp": centered_grasp,
                "grasp_candidate": grasp_candidate,

                "success_hold": self.success_hold,
                "success": bool(success),

                # 拆开奖励项，方便你看 tensorboard/debug 日志。
                "reward_reach": float(reach_reward),
                "reward_finger_align": float(finger_align_reward),
                "reward_close_near": float(close_near_cube_reward),
                "reward_grasp_bonus": float(grasp_bonus),
                "reward_lift": float(lift_reward),
                "reward_xy_place": float(xy_place_reward),
                "penalty_push_without_lift": float(push_without_lift_penalty),
                "penalty_target_push": float(target_push_penalty),
                "reward_action_cost": float(action_cost),
                "cube_target_dist": cube_target_dist_xy,
            },
        )


class ArmReachEnv(ArmGraspEnv):
    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("task_stage", "reach")
        super().__init__(**kwargs)


class ArmLiftEnv(ArmGraspEnv):
    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("task_stage", "lift")
        super().__init__(**kwargs)


class ArmPlaceEnv(ArmGraspEnv):
    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("task_stage", "place")
        super().__init__(**kwargs)


class ArmRLV2Env(ArmGraspEnv):
    """Task-structured pure-RL Panda pick-place environment.

    V2 keeps the same Cartesian end-effector action interface as the original
    environment, but makes the reward more explicit: end-effector position,
    grasp alignment, lift, placement, per-joint soft limits, posture, velocity,
    and action smoothness are scored separately. It does not use demonstrations
    or scripted grasp assistance.
    """

    JOINT_SOFT_LIMIT_LOW = np.array([-2.45, -1.45, -2.55, -2.85, -2.55, 0.05, -2.65], dtype=float)
    JOINT_SOFT_LIMIT_HIGH = np.array([2.45, 1.45, 2.55, -0.15, 2.55, 3.45, 2.65], dtype=float)
    HOME_POSTURE_WEIGHT = np.array([0.20, 0.12, 0.10, 0.18, 0.08, 0.06, 0.04], dtype=float)

    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("control_mode", "cartesian")
        kwargs.setdefault("frame_skip", 4)
        kwargs.setdefault("cartesian_delta_scale", 0.018)
        kwargs.setdefault("cartesian_joint_step_limit", 0.035)
        kwargs.setdefault("ik_damping", 0.06)
        kwargs.setdefault("gripper_smoothing", 0.35)
        kwargs.setdefault("success_hold_required", 6)
        kwargs.setdefault("target_success_radius", 0.055)
        kwargs.setdefault("lift_success_height", 0.060)
        kwargs.setdefault("pre_lift_push_limit", 0.075)
        kwargs.setdefault("pre_lift_push_penalty_scale", 24.0)
        kwargs.setdefault("tune_grasp_physics", True)
        kwargs.setdefault("domain_randomization", False)
        super().__init__(**kwargs)
        self.prev_pinch_cube_dist = 0.0
        self.prev_cube_target_dist_xy = 0.0
        self.prev_action_v2 = np.zeros(4, dtype=float)

    def _reset_model(self, options: dict[str, Any]) -> None:
        super()._reset_model(options)
        pinch_center = self._pinch_center()
        cube_pos = self.data.xpos[self.cube_body_id]
        self.prev_pinch_cube_dist = float(np.linalg.norm(pinch_center - cube_pos))
        self.prev_cube_target_dist_xy = float(np.linalg.norm(cube_pos[:2] - self.target_pos[:2]))
        self.prev_action_v2 = np.zeros(4, dtype=float)

    def _pregrasp_pos(self, cube_pos: np.ndarray) -> np.ndarray:
        return np.array(
            [
                float(cube_pos[0]),
                float(cube_pos[1]),
                self.CUBE_REST_Z + 0.060,
            ],
            dtype=float,
        )

    def _contact_count_with_cube(self) -> tuple[int, bool, bool]:
        left_contact = False
        right_contact = False
        for index in range(int(self.data.ncon)):
            contact = self.data.contact[index]
            geom1 = int(contact.geom1)
            geom2 = int(contact.geom2)
            if self.cube_geom_id not in (geom1, geom2):
                continue
            other_geom = geom2 if geom1 == self.cube_geom_id else geom1
            other_body = int(self.model.geom_bodyid[other_geom])
            if other_body == self.left_finger_body_id:
                left_contact = True
            if other_body == self.right_finger_body_id:
                right_contact = True
        return int(left_contact) + int(right_contact), left_contact, right_contact

    def _joint_soft_limit_penalty(self) -> float:
        q = np.asarray(self.data.qpos[:7], dtype=float)
        low_violation = np.maximum(self.JOINT_SOFT_LIMIT_LOW - q, 0.0)
        high_violation = np.maximum(q - self.JOINT_SOFT_LIMIT_HIGH, 0.0)
        return float(np.sum((low_violation + high_violation) ** 2))

    def _posture_penalty(self) -> float:
        q = np.asarray(self.data.qpos[:7], dtype=float)
        err = q - self.home_arm_qpos
        return float(np.sum(self.HOME_POSTURE_WEIGHT * err * err))

    def _downward_alignment(self) -> float:
        # Panda hand local z should point roughly downward for top-down cube grasps.
        mat = np.asarray(self.data.xmat[self.hand_body_id], dtype=float).reshape(3, 3)
        local_z_world = mat[:, 2]
        return float(np.clip(np.dot(-local_z_world, np.array([0.0, 0.0, -1.0])), -1.0, 1.0))

    def _compute_reward(self) -> StepReward:
        cube_pos = self.data.xpos[self.cube_body_id]
        left_finger_pos = self.data.xpos[self.left_finger_body_id]
        right_finger_pos = self.data.xpos[self.right_finger_body_id]
        pinch_center = 0.5 * (left_finger_pos + right_finger_pos)
        pregrasp_pos = self._pregrasp_pos(cube_pos)

        pinch_cube_dist = float(np.linalg.norm(pinch_center - cube_pos))
        pregrasp_dist = float(np.linalg.norm(pinch_center - pregrasp_pos))
        pregrasp_xy_dist = float(np.linalg.norm(pinch_center[:2] - cube_pos[:2]))
        vertical_error = abs(float(pinch_center[2] - pregrasp_pos[2]))
        cube_target_dist_xy = float(np.linalg.norm(cube_pos[:2] - self.target_pos[:2]))
        cube_target_dist_3d = float(np.linalg.norm(cube_pos - self.target_pos))
        cube_displacement = float(np.linalg.norm(cube_pos[:2] - self.initial_cube_pos[:2]))
        lift_height = max(0.0, float(cube_pos[2]) - self.CUBE_REST_Z)
        cube_vel = np.asarray(self.data.cvel[self.cube_body_id, 3:6], dtype=float)

        gripper_open = self._gripper_open_fraction()
        gripper_closed = float(np.clip(1.0 - gripper_open, 0.0, 1.0))
        contact_count, left_contact, right_contact = self._contact_count_with_cube()
        two_finger_contact = contact_count >= 2

        left_cube_dist = float(np.linalg.norm(left_finger_pos - cube_pos))
        right_cube_dist = float(np.linalg.norm(right_finger_pos - cube_pos))
        finger_balance_error = abs(left_cube_dist - right_cube_dist)
        centered_grasp = (
            pregrasp_xy_dist < 0.040
            and vertical_error < 0.070
            and finger_balance_error < 0.030
        )
        reached = (
            pregrasp_dist < 0.060
            and pregrasp_xy_dist < 0.045
            and vertical_error < 0.060
            and cube_displacement < 0.070
        )
        grasped = (
            two_finger_contact
            and gripper_closed > 0.45
            and centered_grasp
        )
        lifted = lift_height > self.lift_success_height
        carried_to_target = lifted and cube_target_dist_xy < self.target_success_radius
        placed = (
            cube_target_dist_xy < self.target_success_radius
            and lift_height < 0.040
            and gripper_open > 0.45
        )

        cube_out_of_bounds = (
            cube_displacement > 0.22
            or float(cube_pos[2]) < 0.18
            or float(cube_pos[2]) > 0.65
        )
        premature_push = (
            self.task_stage in {"lift", "place"}
            and not lifted
            and cube_displacement > self.pre_lift_push_limit
        )

        reach_reward = 10.0 * np.exp(-18.0 * pregrasp_dist)
        xy_align_reward = 5.0 * np.exp(-22.0 * pregrasp_xy_dist)
        z_align_reward = 2.0 * np.exp(-28.0 * vertical_error)
        orientation_reward = 1.0 * max(0.0, self._downward_alignment())
        approach_progress = 3.0 * np.clip(self.prev_pinch_cube_dist - pinch_cube_dist, -0.02, 0.02) / 0.02
        place_progress = (
            4.0 * np.clip(self.prev_cube_target_dist_xy - cube_target_dist_xy, -0.02, 0.02) / 0.02
            if lifted
            else 0.0
        )
        open_far_reward = 0.8 * gripper_open if pinch_cube_dist > 0.090 else 0.0
        close_at_grasp_reward = 3.0 * gripper_closed if centered_grasp else 0.0
        contact_reward = 2.0 * contact_count
        grasp_reward = 8.0 if grasped else 0.0
        lift_reward = 38.0 * np.clip(lift_height / 0.10, 0.0, 1.0) if grasped or lift_height > 0.005 else 0.0
        carry_height_reward = 2.0 * np.exp(-35.0 * abs(lift_height - 0.085)) if lifted else 0.0
        target_reward = 16.0 * np.exp(-18.0 * cube_target_dist_xy) if lifted else 0.0
        release_reward = 7.0 * gripper_open if carried_to_target else 0.0

        close_far_penalty = 4.0 * gripper_closed if pinch_cube_dist > 0.10 else 0.0
        push_penalty = self.pre_lift_push_penalty_scale * cube_displacement if not lifted else 0.0
        target_push_penalty = (
            18.0 * max(0.0, self.initial_cube_target_dist_xy - cube_target_dist_xy)
            if not lifted
            else 0.0
        )
        joint_limit_penalty = 8.0 * self._joint_soft_limit_penalty()
        posture_penalty = 0.25 * self._posture_penalty()
        joint_velocity_penalty = 0.00035 * float(np.dot(self.data.qvel[:7], self.data.qvel[:7]))
        cube_speed_penalty = 0.08 * float(np.dot(cube_vel, cube_vel))
        action_cost = 0.006 * float(np.dot(self.last_action[:4], self.last_action[:4]))
        action_smooth_cost = 0.010 * float(np.dot(self.last_action[:4] - self.prev_action_v2, self.last_action[:4] - self.prev_action_v2))

        if self.task_stage == "reach":
            step_success = reached
            reward = (
                reach_reward
                + xy_align_reward
                + z_align_reward
                + orientation_reward
                + approach_progress
                + open_far_reward
                - 10.0 * cube_displacement
                - close_far_penalty
                - joint_limit_penalty
                - posture_penalty
                - joint_velocity_penalty
                - action_cost
                - action_smooth_cost
            )
            if reached:
                reward += 25.0
        elif self.task_stage == "lift":
            step_success = lifted
            reward = (
                reach_reward
                + xy_align_reward
                + z_align_reward
                + orientation_reward
                + approach_progress
                + close_at_grasp_reward
                + contact_reward
                + grasp_reward
                + lift_reward
                - push_penalty
                - target_push_penalty
                - close_far_penalty
                - joint_limit_penalty
                - posture_penalty
                - joint_velocity_penalty
                - cube_speed_penalty
                - action_cost
                - action_smooth_cost
            )
            if lifted:
                reward += 70.0
        else:
            step_success = carried_to_target or placed
            reward = (
                0.55 * reach_reward
                + 0.65 * xy_align_reward
                + 0.50 * z_align_reward
                + orientation_reward
                + approach_progress
                + close_at_grasp_reward
                + contact_reward
                + grasp_reward
                + lift_reward
                + carry_height_reward
                + target_reward
                + release_reward
                + place_progress
                - 0.35 * cube_target_dist_3d
                - push_penalty
                - target_push_penalty
                - close_far_penalty
                - joint_limit_penalty
                - posture_penalty
                - joint_velocity_penalty
                - cube_speed_penalty
                - action_cost
                - action_smooth_cost
            )
            if lifted:
                reward += 20.0
            if carried_to_target:
                reward += 95.0
            if placed:
                reward += 120.0

        if premature_push:
            reward -= 45.0
            step_success = False
        if cube_out_of_bounds:
            reward -= 50.0
            step_success = False

        self.success_hold = self.success_hold + 1 if step_success else 0
        success = self.success_hold >= self.success_hold_required
        if success:
            reward += 35.0

        self.prev_pinch_cube_dist = pinch_cube_dist
        self.prev_cube_target_dist_xy = cube_target_dist_xy
        self.prev_action_v2 = self.last_action[:4].copy()

        terminated = bool(success or premature_push or cube_out_of_bounds)

        return StepReward(
            reward=float(reward),
            terminated=terminated,
            info={
                "task": "arm_rl_v2",
                "stage": self.task_stage,
                "control_mode": self.control_mode,
                "success": bool(success),
                "reached": bool(reached),
                "lifted": bool(lifted),
                "carried_to_target": bool(carried_to_target),
                "released_on_target": bool(placed),
                "centered_grasp": bool(centered_grasp),
                "grasp_candidate": bool(grasped),
                "two_finger_contact": bool(two_finger_contact),
                "left_contact": bool(left_contact),
                "right_contact": bool(right_contact),
                "premature_push": bool(premature_push),
                "cube_out_of_bounds": bool(cube_out_of_bounds),
                "pregrasp_dist": pregrasp_dist,
                "pregrasp_xy_dist": pregrasp_xy_dist,
                "pregrasp_z_error": vertical_error,
                "pinch_cube_dist": pinch_cube_dist,
                "cube_target_dist": cube_target_dist_xy,
                "cube_target_dist_3d": cube_target_dist_3d,
                "cube_displacement": cube_displacement,
                "cube_height": float(cube_pos[2]),
                "lift_height": lift_height,
                "gripper_open": gripper_open,
                "gripper_closed": gripper_closed,
                "contact_count": float(contact_count),
                "joint_limit_penalty": float(joint_limit_penalty),
                "posture_penalty": float(posture_penalty),
                "reward_reach": float(reach_reward),
                "reward_xy_align": float(xy_align_reward),
                "reward_contact": float(contact_reward),
                "reward_lift": float(lift_reward),
                "reward_target": float(target_reward),
                "penalty_push_without_lift": float(push_penalty),
                "penalty_target_push": float(target_push_penalty),
            },
        )


class ArmRLV2ReachEnv(ArmRLV2Env):
    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("task_stage", "reach")
        kwargs.setdefault("max_episode_steps", 180)
        kwargs.setdefault("cube_random_span", 0.020)
        kwargs.setdefault("target_random_span", 0.015)
        super().__init__(**kwargs)


class ArmRLV2LiftEnv(ArmRLV2Env):
    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("task_stage", "lift")
        kwargs.setdefault("max_episode_steps", 260)
        kwargs.setdefault("cube_random_span", 0.025)
        kwargs.setdefault("target_random_span", 0.020)
        super().__init__(**kwargs)


class ArmRLV2PlaceEnv(ArmRLV2Env):
    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("task_stage", "place")
        kwargs.setdefault("max_episode_steps", 340)
        kwargs.setdefault("cube_random_span", 0.030)
        kwargs.setdefault("target_random_span", 0.025)
        super().__init__(**kwargs)
