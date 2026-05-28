from __future__ import annotations

from pathlib import Path

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from winros_interfaces.msg import RobotTelemetry


class MujocoBridgeNode(Node):
    def __init__(self) -> None:
        super().__init__("winros_mujoco_bridge")
        self.declare_parameter("model_path", "")
        self.declare_parameter("robot_name", "mujoco_robot")
        self.declare_parameter("step_hz", 500.0)
        self.declare_parameter("publish_hz", 30.0)

        self.robot_name = self.get_parameter("robot_name").value
        model_path = str(self.get_parameter("model_path").value)
        if not model_path:
            raise ValueError("Parameter 'model_path' is required.")

        import mujoco

        self._mujoco = mujoco
        self._model_path = Path(model_path)
        self._model = mujoco.MjModel.from_xml_path(str(self._model_path))
        self._data = mujoco.MjData(self._model)
        self._joint_names = [
            mujoco.mj_id2name(self._model, mujoco.mjtObj.mjOBJ_JOINT, i) or f"joint_{i}"
            for i in range(self._model.njnt)
        ]

        self._joint_pub = self.create_publisher(JointState, "joint_states", 10)
        self._telemetry_pub = self.create_publisher(RobotTelemetry, "telemetry", 10)

        step_hz = float(self.get_parameter("step_hz").value)
        publish_hz = float(self.get_parameter("publish_hz").value)
        self.create_timer(1.0 / step_hz, self._step)
        self.create_timer(1.0 / publish_hz, self._publish)

    def _step(self) -> None:
        self._mujoco.mj_step(self._model, self._data)

    def _publish(self) -> None:
        now = self.get_clock().now().to_msg()

        joint_state = JointState()
        joint_state.header.stamp = now
        joint_state.name = self._joint_names
        joint_state.position = [float(x) for x in self._data.qpos[: len(self._joint_names)]]
        joint_state.velocity = [float(x) for x in self._data.qvel[: len(self._joint_names)]]
        self._joint_pub.publish(joint_state)

        telemetry = RobotTelemetry()
        telemetry.header.stamp = now
        telemetry.robot_name = str(self.robot_name)
        telemetry.source = "mujoco"
        telemetry.mode = "sim"
        telemetry.joint_position = joint_state.position
        telemetry.joint_velocity = joint_state.velocity
        telemetry.joint_effort = []
        telemetry.warnings = []
        self._telemetry_pub.publish(telemetry)


def main() -> None:
    rclpy.init()
    node = MujocoBridgeNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

