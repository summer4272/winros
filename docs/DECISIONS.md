# Technical Decisions

## D001: Use ROS 2 Jazzy as the first stable Windows baseline

Date: 2026-05-25

ROS 2 Lyrical is the latest LTS, but the official Windows binary page currently describes prerelease binaries. Jazzy remains supported and has Windows binary instructions, so the first public baseline uses Jazzy while leaving room for Lyrical later.

## D002: Keep PyTorch out of the default dependency set

Date: 2026-05-25

PyTorch wheel selection depends on the local GPU, CUDA support, and driver. The default Python install only includes simulation and development dependencies. `scripts/setup_python.ps1` can install CPU or CUDA PyTorch when requested.

## D003: Hardware adapters are dry-run by default

Date: 2026-05-25

Real robot control must require an explicit `enable_hardware` setting. The first adapter publishes telemetry and accepts commands, but does not send motion to hardware.

## D004: MuJoCo is the first simulator

Date: 2026-05-25

MuJoCo is suitable for fast local control and RL experiments on Windows. Gazebo and Webots can be added later through separate adapters if needed.

