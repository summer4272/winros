# ROS 2 Packages

The ROS 2 workspace lives in `ros2_ws`.

## winros_interfaces

Shared messages, services, and actions:

- `RobotTelemetry.msg`: robot state and health summary;
- `JointCommand.msg`: dry-run-safe joint command;
- `SetRobotMode.srv`: request mode changes;
- `MoveJoints.action`: long-running joint motion command.

## winros_mujoco

MuJoCo to ROS 2 bridge:

- loads an MJCF model;
- steps simulation on a timer;
- publishes `sensor_msgs/msg/JointState`;
- publishes `winros_interfaces/msg/RobotTelemetry`.

## winros_robot_adapters

Hardware-facing package:

- accepts `JointCommand`;
- publishes telemetry;
- exposes `SetRobotMode`;
- stays in dry-run unless hardware is explicitly enabled.

