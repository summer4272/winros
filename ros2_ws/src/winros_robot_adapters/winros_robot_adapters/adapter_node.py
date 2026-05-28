from __future__ import annotations

import rclpy
from rclpy.node import Node
from winros_interfaces.msg import JointCommand, RobotTelemetry
from winros_interfaces.srv import SetRobotMode


class DryRunAdapterNode(Node):
    def __init__(self) -> None:
        super().__init__("winros_dry_run_adapter")
        self.declare_parameter("robot_name", "dry_run_robot")
        self.declare_parameter("enable_hardware", False)
        self.declare_parameter("publish_hz", 10.0)

        self.robot_name = str(self.get_parameter("robot_name").value)
        self.hardware_enabled = bool(self.get_parameter("enable_hardware").value)
        self.mode = "hardware" if self.hardware_enabled else "dry_run"
        self.last_command_id = ""
        self.warnings: list[str] = []

        self.create_subscription(JointCommand, "joint_command", self._on_joint_command, 10)
        self.create_service(SetRobotMode, "set_robot_mode", self._on_set_robot_mode)
        self._telemetry_pub = self.create_publisher(RobotTelemetry, "telemetry", 10)

        publish_hz = float(self.get_parameter("publish_hz").value)
        self.create_timer(1.0 / publish_hz, self._publish)

    def _on_joint_command(self, msg: JointCommand) -> None:
        if msg.robot_name and msg.robot_name != self.robot_name:
            return
        self.last_command_id = msg.command_id
        if not self.hardware_enabled or msg.dry_run:
            self.get_logger().info(
                f"Dry-run accepted command {msg.command_id} for {len(msg.joint_names)} joints"
            )
            return

        self.warnings.append("Hardware command path is not implemented yet.")
        self.get_logger().warning("Hardware enabled, but no vendor driver is attached.")

    def _on_set_robot_mode(self, request, response):
        if request.robot_name and request.robot_name != self.robot_name:
            response.accepted = False
            response.message = "Robot name does not match this adapter."
            return response

        if request.enable_hardware:
            response.accepted = False
            response.message = "Hardware mode requires a concrete vendor adapter."
            return response

        self.hardware_enabled = False
        self.mode = request.mode or "dry_run"
        response.accepted = True
        response.message = f"Mode set to {self.mode}."
        return response

    def _publish(self) -> None:
        msg = RobotTelemetry()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.robot_name = self.robot_name
        msg.source = "adapter"
        msg.mode = self.mode
        msg.warnings = self.warnings[-10:]
        self._telemetry_pub.publish(msg)


def main() -> None:
    rclpy.init()
    node = DryRunAdapterNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

