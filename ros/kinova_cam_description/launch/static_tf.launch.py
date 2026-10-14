"""TF estático end_effector_link -> camera_link para uma versão do anel.

    ros2 launch kinova_cam_description static_tf.launch.py version:=ring_rgb

Gerado por scripts/ros_export.py (kinova-cam); valores em config/camera_mounts.yaml.
"""

import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _publisher(context):
    share = get_package_share_directory("kinova_cam_description")
    with open(os.path.join(share, "config", "camera_mounts.yaml")) as f:
        mounts = yaml.safe_load(f)
    version = LaunchConfiguration("version").perform(context)
    m = mounts[version]
    x, y, z = (str(v) for v in m["xyz"])
    qx, qy, qz, qw = (str(v) for v in m["quat_xyzw"])
    return [
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="kinova_cam_static_tf",
            arguments=["--x", x, "--y", y, "--z", z, "--qx", qx, "--qy", qy, "--qz", qz, "--qw", qw,
                       "--frame-id", LaunchConfiguration("parent").perform(context),
                       "--child-frame-id", LaunchConfiguration("child").perform(context)],
        )
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("version", default_value="ring_rgb", description="ring | ring_rgb | ring_stereo | ring_d405"),
        DeclareLaunchArgument("parent", default_value="end_effector_link"),
        DeclareLaunchArgument("child", default_value="camera_link"),
        OpaqueFunction(function=_publisher),
    ])
