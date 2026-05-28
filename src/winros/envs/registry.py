from __future__ import annotations

from dataclasses import dataclass

from winros.external_envs import (
    PANDA_MUJOCO_GYM_ENV_IDS,
    register_external_envs,
)


@dataclass(frozen=True)
class EnvDefinition:
    id: str
    task: str
    robot: str
    notes: str


ENV_DEFINITIONS: dict[str, EnvDefinition] = {
    "WinROSArmReach-v0": EnvDefinition(
        id="WinROSArmReach-v0",
        task="arm_grasp_reach",
        robot="Franka Emika Panda",
        notes="Curriculum stage 1: move the gripper near the cube.",
    ),
    "WinROSArmLift-v0": EnvDefinition(
        id="WinROSArmLift-v0",
        task="arm_grasp_lift",
        robot="Franka Emika Panda",
        notes="Curriculum stage 2: approach, close the gripper, and lift the cube.",
    ),
    "WinROSArmPlace-v0": EnvDefinition(
        id="WinROSArmPlace-v0",
        task="arm_grasp_place",
        robot="Franka Emika Panda",
        notes="Curriculum stage 3: lift and place the cube at the target marker.",
    ),
    "WinROSArmGrasp-v0": EnvDefinition(
        id="WinROSArmGrasp-v0",
        task="arm_grasp",
        robot="Franka Emika Panda",
        notes="Tabletop cube pick-place workcell with Panda and a target marker.",
    ),
    "WinROSArmRLV2Reach-v0": EnvDefinition(
        id="WinROSArmRLV2Reach-v0",
        task="arm_rl_v2_reach",
        robot="Franka Emika Panda",
        notes="ArmRL-v2 stage 1: Cartesian end-effector reach with posture and joint-limit rewards.",
    ),
    "WinROSArmRLV2Lift-v0": EnvDefinition(
        id="WinROSArmRLV2Lift-v0",
        task="arm_rl_v2_lift",
        robot="Franka Emika Panda",
        notes="ArmRL-v2 stage 2: two-finger contact, close timing, and stable lift.",
    ),
    "WinROSArmRLV2Place-v0": EnvDefinition(
        id="WinROSArmRLV2Place-v0",
        task="arm_rl_v2_place",
        robot="Franka Emika Panda",
        notes="ArmRL-v2 stage 3: lift, transport, and place with task-specific constraints.",
    ),
    "WinROSQuadrupedLocomotion-v0": EnvDefinition(
        id="WinROSQuadrupedLocomotion-v0",
        task="quadruped_locomotion",
        robot="Unitree Go2",
        notes="Commanded velocity tracking scaffold on flat MuJoCo ground.",
    ),
    "WinROSHumanoidLocomotion-v0": EnvDefinition(
        id="WinROSHumanoidLocomotion-v0",
        task="humanoid_locomotion",
        robot="Unitree G1",
        notes="Standing and slow velocity tracking scaffold for humanoid locomotion.",
    ),
}

EXTERNAL_ENV_DEFINITIONS: dict[str, EnvDefinition] = {
    env_id: EnvDefinition(
        id=env_id,
        task="external_panda_goal_env",
        robot="Franka Emika Panda",
        notes="MIT third-party baseline from zichunxx/panda_mujoco_gym.",
    )
    for env_id in PANDA_MUJOCO_GYM_ENV_IDS
}
EXTERNAL_ENV_DEFINITIONS.update(
    {
        "Ant-v5": EnvDefinition(
            id="Ant-v5",
            task="external_quadruped_locomotion",
            robot="MuJoCo Ant quadruped baseline",
            notes="Gymnasium MuJoCo four-legged locomotion baseline.",
        ),
        "Humanoid-v5": EnvDefinition(
            id="Humanoid-v5",
            task="external_humanoid_locomotion",
            robot="MuJoCo Humanoid baseline",
            notes="Gymnasium MuJoCo humanoid locomotion baseline.",
        ),
    }
)
EXTERNAL_ENV_DEFINITIONS.update(
    {
        "FetchPickAndPlace-v4": EnvDefinition(
            id="FetchPickAndPlace-v4",
            task="external_arm_pick_place_rl",
            robot="Fetch robot arm",
            notes="Gymnasium Robotics sparse pick-place benchmark for RL + HER.",
        ),
        "FetchPickAndPlaceDense-v4": EnvDefinition(
            id="FetchPickAndPlaceDense-v4",
            task="external_arm_pick_place_rl_dense",
            robot="Fetch robot arm",
            notes="Gymnasium Robotics dense pick-place benchmark for faster RL baseline training.",
        ),
    }
)


def list_envs() -> list[EnvDefinition]:
    envs = [ENV_DEFINITIONS[env_id] for env_id in sorted(ENV_DEFINITIONS)]
    envs.extend(
        EXTERNAL_ENV_DEFINITIONS[env_id]
        for env_id in register_external_envs()
        if env_id in EXTERNAL_ENV_DEFINITIONS
    )
    return envs
