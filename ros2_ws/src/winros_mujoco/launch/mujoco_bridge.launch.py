from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    model_path = LaunchConfiguration("model_path")
    robot_name = LaunchConfiguration("robot_name")

    return LaunchDescription(
        [
            DeclareLaunchArgument("model_path"),
            DeclareLaunchArgument("robot_name", default_value="mujoco_robot"),
            Node(
                package="winros_mujoco",
                executable="mujoco_bridge",
                name="mujoco_bridge",
                output="screen",
                parameters=[
                    {
                        "model_path": model_path,
                        "robot_name": robot_name,
                    }
                ],
            ),
        ]
    )

