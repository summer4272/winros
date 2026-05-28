from __future__ import annotations

from importlib import import_module
from typing import Any


ENV_SPECS: dict[str, str] = {
    "WinROSArmReach-v0": "winros.envs.arm_grasp:ArmReachEnv",
    "WinROSArmLift-v0": "winros.envs.arm_grasp:ArmLiftEnv",
    "WinROSArmPlace-v0": "winros.envs.arm_grasp:ArmPlaceEnv",
    "WinROSArmGrasp-v0": "winros.envs.arm_grasp:ArmGraspEnv",
    "WinROSArmRLV2Reach-v0": "winros.envs.arm_grasp:ArmRLV2ReachEnv",
    "WinROSArmRLV2Lift-v0": "winros.envs.arm_grasp:ArmRLV2LiftEnv",
    "WinROSArmRLV2Place-v0": "winros.envs.arm_grasp:ArmRLV2PlaceEnv",
    "WinROSQuadrupedLocomotion-v0": "winros.envs.quadruped_locomotion:QuadrupedLocomotionEnv",
    "WinROSHumanoidLocomotion-v0": "winros.envs.humanoid_locomotion:HumanoidLocomotionEnv",
}

_CLASS_MODULES = {
    "ArmGraspEnv": "winros.envs.arm_grasp",
    "ArmReachEnv": "winros.envs.arm_grasp",
    "ArmLiftEnv": "winros.envs.arm_grasp",
    "ArmPlaceEnv": "winros.envs.arm_grasp",
    "ArmRLV2Env": "winros.envs.arm_grasp",
    "ArmRLV2ReachEnv": "winros.envs.arm_grasp",
    "ArmRLV2LiftEnv": "winros.envs.arm_grasp",
    "ArmRLV2PlaceEnv": "winros.envs.arm_grasp",
    "QuadrupedLocomotionEnv": "winros.envs.quadruped_locomotion",
    "HumanoidLocomotionEnv": "winros.envs.humanoid_locomotion",
}


def register_envs() -> None:
    try:
        from gymnasium.envs.registration import register
    except ImportError as exc:
        raise RuntimeError("Gymnasium is required to register WinROS training envs.") from exc

    for env_id, entry_point in ENV_SPECS.items():
        try:
            register(id=env_id, entry_point=entry_point)
        except Exception as exc:
            if "Cannot re-register id" not in str(exc):
                raise


def __getattr__(name: str) -> Any:
    if name not in _CLASS_MODULES:
        raise AttributeError(name)
    module = import_module(_CLASS_MODULES[name])
    value = getattr(module, name)
    globals()[name] = value
    return value


try:
    register_envs()
except RuntimeError:
    pass


__all__ = [
    "ArmGraspEnv",
    "ArmReachEnv",
    "ArmLiftEnv",
    "ArmPlaceEnv",
    "ArmRLV2Env",
    "ArmRLV2ReachEnv",
    "ArmRLV2LiftEnv",
    "ArmRLV2PlaceEnv",
    "QuadrupedLocomotionEnv",
    "HumanoidLocomotionEnv",
    "ENV_SPECS",
    "register_envs",
]
